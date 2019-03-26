# coding: utf-8

from __future__ import unicode_literals

from copy import deepcopy


"""
This module contains:

    - A Workflow is a sequence of FireWorks as a DAG (directed acyclic graph).
"""

from collections import defaultdict, OrderedDict
import abc
from datetime import datetime
import os
import pprint

from monty.io import reverse_readline, zopen
from monty.os.path import zpath

from six import add_metaclass

from fireworks.fw_config import TRACKER_LINES, NEGATIVE_FWID_CTR, EXCEPT_DETAILS_ON_RERUN
from fireworks.core.fworker import FWorker
from fireworks.utilities.dict_mods import apply_mod
from fireworks.utilities.fw_serializers import FWSerializable, recursive_serialize, \
    recursive_deserialize, serialize_fw
from fireworks.utilities.fw_utilities import get_my_host, get_my_ip, NestedClassGetter

from typing import List, Dict

__author__ = "Anubhav Jain"
__credits__ = "Shyue Ping Ong"
__copyright__ = "Copyright 2013, The Materials Project"
__version__ = "0.1"
__maintainer__ = "Anubhav Jain"
__email__ = "ajain@lbl.gov"
__date__ = "Feb 5, 2013"

class Workflow(FWSerializable):
    """
    A Workflow connects a group of FireWorks in an execution order.
    """

    class Links(dict, FWSerializable):
        """
        An inner class for storing the DAG links between FireWorks
        """

        def __init__(self, *args, **kwargs):
            super(Workflow.Links, self).__init__(*args, **kwargs)

            for k, v in list(self.items()):
                if not isinstance(v, (list, tuple)):
                    self[k] = [v]  # v must be list

                self[k] = [x.fw_id if hasattr(x, "fw_id") else x for x in self[k]]

                if not isinstance(k, int):
                    if hasattr(k, "fw_id"):  # maybe it's a String?
                        self[k.fw_id] = self[k]
                    else:  # maybe it's a String?
                        try:
                            self[int(k)] = self[k]  # k must be int
                        except:
                            pass  # garbage input
                    del self[k]

        @property
        def nodes(self):
            """ Return list of all nodes"""
            allnodes = list(self.keys())
            for v in self.values():
                allnodes.extend(v)
            return list(set(allnodes))

        @property
        def parent_links(self):
            """
            Return a dict of child and its parents.

            Note: if performance of parent_links becomes an issue, override delitem/setitem to
            update parent_links
            """
            child_parents = defaultdict(list)
            for (parent, children) in self.items():
                for child in children:
                    child_parents[child].append(parent)
            return dict(child_parents)

        def to_dict(self):
            """
            Convert to str form for Mongo, which cannot have int keys.

            Returns:
                dict
            """
            return dict([(str(k), v) for (k, v) in self.items()])

        def to_db_dict(self):
            """
            Convert to str form for Mongo, which cannot have int keys .

            Returns:
                dict
            """
            m_dict = {
                'links': dict([(str(k), v) for (k, v) in self.items()]),
                'parent_links': dict([(str(k), v) for (k, v) in self.parent_links.items()]),
                'nodes': self.nodes}
            return m_dict

        @classmethod
        def from_dict(cls, m_dict):
            return Workflow.Links(m_dict)

        def __setstate__(self, state):
            for k, v in state:
                self[k] = v

        def __reduce__(self):
            """
            To support Pickling of inner classes (for multi-job launcher's multiprocessing).
            Return a class which can return this class when called with the appropriate tuple of
            arguments
            """
            state = list(self.items())
            return NestedClassGetter(), (Workflow, self.__class__.__name__, ), state

    def __init__(self, fireworks, links_dict=None, name=None, metadata=None, created_on=None,
                 updated_on=None, fw_states=None):
        """
        Args:
            fireworks ([Firework]): all FireWorks in this workflow.
            links_dict (dict): links between the FWs as (parent_id):[(child_id1, child_id2)]
            name (str): name of workflow.
            metadata (dict): metadata for this Workflow.
            created_on (datetime): time of creation
            updated_on (datetime): time of update
            fw_states (dict): leave this alone unless you are purposefully creating a Lazy-style WF
        """
        name = name or 'unnamed WF'  # prevent None names

        links_dict = links_dict if links_dict else {}

        # main dict containing mapping of an id to a Firework object
        self.id_fw = {}
        for fw in fireworks:
            if fw.fw_id in self.id_fw:
                raise ValueError('FW ids must be unique!')
            self.id_fw[fw.fw_id] = fw

            if fw.fw_id not in links_dict and fw not in links_dict:
                links_dict[fw.fw_id] = []

        self.links = Workflow.Links(links_dict)

        # add depends on
        for fw in fireworks:
            for pfw in fw.parents:
                if pfw.fw_id not in self.links:
                    raise ValueError(
                        "FW_id: {} defines a dependent link to FW_id: {}, but the latter was not "
                        "added to the workflow!".format(fw.fw_id, pfw.fw_id))
                if fw.fw_id not in self.links[pfw.fw_id]:
                    self.links[pfw.fw_id].append(fw.fw_id)

        self.name = name

        # sanity check: make sure the set of nodes from the links_dict is equal to the set
        # of nodes from id_fw
        if set(self.links.nodes) != set(map(int, self.id_fw.keys())):
            raise ValueError("Specified links don't match given FW")

        if len(self.links.nodes) == 0:
            raise ValueError("Workflow cannot be empty (must contain at least 1 FW)")

        self.metadata = metadata if metadata else {}
        self.created_on = created_on or datetime.utcnow()
        self.updated_on = updated_on or datetime.utcnow()

        # dict containing mapping of an id to a firework state. The states are stored locally and
        # redundantly for speed purpose
        if fw_states:
            self.fw_states = fw_states
        else:
            self.fw_states = {key:self.id_fw[key].state for key in self.id_fw}

    @property
    def fws(self):
        """
        Return list of all fireworks
        """
        return list(self.id_fw.values())

    @property
    def state(self):
        """
        Returns:
            state (str): state of workflow
        """
        m_state = 'READY'
        #states = [fw.state for fw in self.fws]
        states = self.fw_states.values()
        leaf_fw_ids = self.leaf_fw_ids  # to save recalculating this

        leaf_states = (self.fw_states[fw_id] for fw_id in leaf_fw_ids)
        if all(s == 'COMPLETED' for s in leaf_states):
            m_state = 'COMPLETED'
        elif all(s == 'ARCHIVED' for s in states):
            m_state = 'ARCHIVED'
        elif any(s == 'DEFUSED' for s in states):
            m_state = 'DEFUSED'
        elif any(s == 'PAUSED' for s in states):
            m_state = 'PAUSED'
        elif any(s == 'FIZZLED' for s in states):
            fizzled_ids = (fw_id for fw_id, state in self.fw_states.items()
                           if state == 'FIZZLED')
            for fizzled_id in fizzled_ids:
                # If a fizzled fw is a leaf fw, then the workflow is fizzled
                if (fizzled_id in leaf_fw_ids or
                    # Otherwise all children must be ok with the fizzled parent
                    not all(self.id_fw[child_id].spec.get('_allow_fizzled_parents', False)
                            for child_id in self.links[fizzled_id])):
                    m_state = 'FIZZLED'
                    break
            else:
                m_state = 'RUNNING'
        elif any(s == 'COMPLETED' for s in states) or any(s == 'RUNNING' for s in states):
            m_state = 'RUNNING'
        elif any(s == 'RESERVED' for s in states):
            m_state = 'RESERVED'
        return m_state

    def apply_action(self, action, fw_id):
        """
        Apply a FWAction on a Firework in the Workflow.

        Args:
            action (FWAction): action to apply
            fw_id (int): id of Firework on which to apply the action

        Returns:
            [int]: list of Firework ids that were updated or new
        """
        updated_ids = []

        # update the spec of the children FireWorks
        if action.update_spec:
            for cfid in self.links[fw_id]:
                self.id_fw[cfid].spec.update(action.update_spec)
                updated_ids.append(cfid)

        # update the spec of the children FireWorks using DictMod language
        if action.mod_spec:
            for cfid in self.links[fw_id]:
                for mod in action.mod_spec:
                    apply_mod(mod, self.id_fw[cfid].spec)
                    updated_ids.append(cfid)

        # defuse children
        if action.defuse_children:
            for cfid in self.links[fw_id]:
                self.id_fw[cfid].state = 'DEFUSED'
                self.fw_states[cfid] = 'DEFUSED'
                updated_ids.append(cfid)

        # defuse workflow
        if action.defuse_workflow:
            for fw_id in self.links.nodes:
                if self.id_fw[fw_id].state not in ['FIZZLED', 'COMPLETED']:
                    self.id_fw[fw_id].state = 'DEFUSED'
                    self.fw_states[fw_id] = 'DEFUSED'
                    updated_ids.append(fw_id)

        # add detour FireWorks. This should be done *before* additions
        if action.detours:
            for wf in action.detours:
                new_updates = self.append_wf(wf, [fw_id], detour=True, pull_spec_mods=False)
                if len(set(updated_ids).intersection(new_updates)) > 0:
                    raise ValueError(
                        "Cannot use duplicated fw_ids when dynamically detouring workflows!")
                updated_ids.extend(new_updates)

        # add additional FireWorks
        if action.additions:
            for wf in action.additions:
                new_updates = self.append_wf(wf, [fw_id], detour=False, pull_spec_mods=False)
                if len(set(updated_ids).intersection(new_updates)) > 0:
                    raise ValueError(
                        "Cannot use duplicated fw_ids when dynamically adding workflows!")
                updated_ids.extend(new_updates)

        return list(set(updated_ids))

    def rerun_fw(self, fw_id, updated_ids=None):
        """
        Archives the launches of a Firework so that it can be re-run.

        Args:
            fw_id (int): id of firework to tbe rerun
            updated_ids (set(int)): set of fireworks id to rerun

        Returns:
            [int]: list of Firework ids that were updated
        """

        updated_ids = updated_ids if updated_ids else set()
        m_fw = self.id_fw[fw_id]
        m_fw._rerun()
        updated_ids.add(fw_id)

        # refresh the states of the current fw before rerunning the children
        # so that they get the correct state of the parent.
        updated_ids.union(self.refresh(fw_id, updated_ids))

        # re-run all the children
        for child_id in self.links[fw_id]:
            if self.id_fw[child_id].state != 'WAITING':
                updated_ids = updated_ids.union(self.rerun_fw(child_id, updated_ids))

        return updated_ids

    def append_wf(self, new_wf, fw_ids, detour=False, pull_spec_mods=False):
        """
        Method to add a workflow as a child to a Firework
        Note: detours must have children that have STATE_RANK that is WAITING or below

        Args:
            new_wf (Workflow): New Workflow to add.
            fw_ids ([int]): ids of the parent Fireworks on which to add the Workflow.
            detour (bool): add children of the current Firework to the Workflow's leaves.
            pull_spec_mods (bool): pull spec mods of COMPLETED parents, refreshes the WF states.

        Returns:
            [int]: list of Firework ids that were updated or new
        """
        updated_ids = []

        root_ids = new_wf.root_fw_ids
        leaf_ids = new_wf.leaf_fw_ids

        # make sure detour runs do not link to ready/running/completed/etc. runs
        if detour:
            for fw_id in fw_ids:
                if fw_id in self.links:
                    # make sure all of these links are WAITING, else the DETOUR is not well defined
                    ready_run = [(f >= 0 and Firework.STATE_RANKS[self.fw_states[f]] > 1)
                                 for f in self.links[fw_id]]
                    if any(ready_run):
                        raise ValueError("fw_id: {}: Detour option only works if all children "
                                         "of detours are not READY to run and have not "
                                         "already run".format(fw_id))

        # make sure all new child fws have negative fw_id
        for new_fw in new_wf.fws:
            if new_fw.fw_id >= 0:  # note: this is also used later in the 'detour' code
                raise ValueError(
                    'FireWorks to add must use a negative fw_id! Got fw_id: {}'.format(new_fw.fw_id))

        # completed checks - go ahead and append
        for new_fw in new_wf.fws:
            self.id_fw[new_fw.fw_id] = new_fw  # add new_fw to id_fw

            if new_fw.fw_id in leaf_ids:
                if detour:
                    for fw_id in fw_ids:
                        # add children of current FW to new FW
                        self.links[new_fw.fw_id] = [f for f in self.links[fw_id] if f >= 0]
                else:
                    self.links[new_fw.fw_id] = []
            else:
                self.links[new_fw.fw_id] = new_wf.links[new_fw.fw_id]
            updated_ids.append(new_fw.fw_id)

        for fw_id in fw_ids:
            for root_id in root_ids:
                self.links[fw_id].append(root_id)  # add the root id as my child
                if pull_spec_mods:  # re-apply some actions of the parent
                    m_fw = self.id_fw[fw_id]  # get the parent FW
                    m_launch = self._get_representative_launch(m_fw)  # get Launch of parent
                    if m_launch:
                        # pull spec update
                        if m_launch.state == 'COMPLETED' and m_launch.action.update_spec:
                            new_wf.id_fw[root_id].spec.update(m_launch.action.update_spec)
                        # pull spec mods
                        if m_launch.state == 'COMPLETED' and m_launch.action.mod_spec:
                            for mod in m_launch.action.mod_spec:
                                apply_mod(mod, new_wf.id_fw[root_id].spec)

        for new_fw in new_wf.fws:
            updated_ids = self.refresh(new_fw.fw_id, set(updated_ids))

        return updated_ids

    def refresh(self, fw_id, updated_ids=None):
        """
        Refreshes the state of a Firework and any affected children.

        Args:
            fw_id (int): id of the Firework on which to perform the refresh
            updated_ids ([int])

        Returns:
            set(int): list of Firework ids that were updated
        """
        # these are the fw_ids to re-enter into the database
        updated_ids = updated_ids if updated_ids else set()

        fw = self.id_fw[fw_id]
        prev_state = fw.state

        # if we're paused, defused or archived, just skip altogether
        if fw.state == 'DEFUSED' or fw.state == 'ARCHIVED' or fw.state == 'PAUSED':
            self.fw_states[fw_id] = fw.state
            return updated_ids

        completed_parent_states = ['COMPLETED']
        if fw.spec.get('_allow_fizzled_parents'):
            completed_parent_states.append('FIZZLED')

        # check parent states for any that are not completed
        for parent in self.links.parent_links.get(fw_id, []):
            if self.fw_states[parent] not in completed_parent_states:
                m_state = 'WAITING'
                break

        else:  # not DEFUSED/ARCHIVED, and all parents are done running. Now the state depends on the launch status
            # my state depends on launch whose state has the highest 'score' in STATE_RANKS
            m_launch = self._get_representative_launch(fw)
            m_state = m_launch.state if m_launch else 'READY'
            m_action = m_launch.action if (m_launch and m_launch.state == "COMPLETED") else None

            # report any FIZZLED parents if allow_fizzed allows us to handle FIZZLED jobs
            if fw.spec.get('_allow_fizzled_parents') and "_fizzled_parents" not in fw.spec:
                parent_fws = [self.id_fw[p].to_dict() for p in self.links.parent_links.get(fw_id, [])
                              if self.id_fw[p].state == 'FIZZLED']
                if len(parent_fws) > 0:
                    fw.spec['_fizzled_parents'] = parent_fws
                    updated_ids.add(fw_id)

        fw.state = m_state
        # Brings self.fw_states in sync with fw_states in db
        self.fw_states[fw_id] = m_state

        if m_state != prev_state:
            updated_ids.add(fw_id)

            if m_state == 'COMPLETED':
                updated_ids = updated_ids.union(self.apply_action(m_action, fw.fw_id))

            # refresh all the children that could possibly now be READY to run
            # note that "FIZZLED" is for _allow_fizzled_parents children
            if m_state in ['COMPLETED', 'FIZZLED']:
                for child_id in self.links[fw_id]:
                    updated_ids = updated_ids.union(self.refresh(child_id, updated_ids))

        self.updated_on = datetime.utcnow()

        return updated_ids

    @property
    def root_fw_ids(self):
        """
        Gets root FireWorks of this workflow (those with no parents).

        Returns:
            [int]: Firework ids of root FWs
        """
        all_ids = set(self.links.nodes)
        child_ids = set(self.links.parent_links.keys())
        root_ids = all_ids.difference(child_ids)
        return list(root_ids)

    @property
    def leaf_fw_ids(self):
        """
        Gets leaf FireWorks of this workflow (those with no children).

        Returns:
            [int]: Firework ids of leaf FWs
        """
        leaf_ids = []
        for id, children in self.links.items():
            if len(children) == 0:
                leaf_ids.append(id)
        return leaf_ids

    def _reassign_ids(self, old_new):
        """
        Internal method to reassign Firework ids, e.g. due to database insertion.

        Args:
            old_new (dict)
        """
        # update id_fw
        new_id_fw = {}
        for (fwid, fws) in self.id_fw.items():
            new_id_fw[old_new.get(fwid, fwid)] = fws
        self.id_fw = new_id_fw

        # update the Links
        new_l = {}
        for (parent, children) in self.links.items():
            new_l[old_new.get(parent, parent)] = [old_new.get(child, child) for child in children]
        self.links = Workflow.Links(new_l)

        # update the states
        new_fw_states = {}
        for (fwid, fw_state) in self.fw_states.items():
            new_fw_states[old_new.get(fwid, fwid)] = fw_state
        self.fw_states = new_fw_states

    def to_dict(self):
        return {'fws': [f.to_dict() for f in self.id_fw.values()],
                'links': self.links.to_dict(),
                'name': self.name,
                'metadata': self.metadata,
                'updated_on': self.updated_on,
                'created_on': self.created_on}

    def to_db_dict(self):
        m_dict = self.links.to_db_dict()
        m_dict['metadata'] = self.metadata
        m_dict['state'] = self.state
        m_dict['name'] = self.name
        m_dict['created_on'] = self.created_on
        m_dict['updated_on'] = self.updated_on
        m_dict['fw_states'] = dict([(str(k), v) for (k, v) in self.fw_states.items()])
        return m_dict

    def to_display_dict(self):
        m_dict = self.to_db_dict()
        nodes = sorted(m_dict['nodes'])
        m_dict['name--id'] = self.name + '--' + str(nodes[0])
        m_dict['launch_dirs'] = OrderedDict([(self._str_fw(x), [l.launch_dir for l in self.id_fw[x].launches])
                                             for x in nodes])
        m_dict['states'] = OrderedDict([(self._str_fw(x), self.id_fw[x].state) for x in nodes])
        m_dict['nodes'] = [self._str_fw(x) for x in nodes]
        m_dict['links'] = OrderedDict([(self._str_fw(k), [self._str_fw(v) for v in a])
                                       for k, a in m_dict['links'].items()])
        m_dict['parent_links'] = OrderedDict([(self._str_fw(k), [self._str_fw(v) for v in a])
                                              for k, a in m_dict['parent_links'].items()])
        m_dict['states_list'] = '-'.join([a[0:4] for a in m_dict['states'].values()])
        return m_dict

    def _str_fw(self, fw_id):
        """
        Get a string representation of the firework with the given id.

        Args:
            fw_id (int): firework id

        Returns:
            str
        """
        return self.id_fw[int(fw_id)].name + '--' + str(fw_id)

    @staticmethod
    def _get_representative_launch(fw):
        """
        Returns a representative launch(one with the largest state rank) for the given firework.
        If there are multiple COMPLETED launches, the one with the most recent update time is
        returned.

        Args:
            fw (Firework)

        Returns:
            Launch
        """
        max_score = Firework.STATE_RANKS['ARCHIVED']  # state rank must be greater than this
        m_launch = None
        completed_launches = []
        for l in fw.launches:
            if Firework.STATE_RANKS[l.state] > max_score:
                max_score = Firework.STATE_RANKS[l.state]
                m_launch = l
                if l.state == 'COMPLETED':
                    completed_launches.append(l)
        if completed_launches:
            return max(completed_launches, key=lambda v: v.time_end)
        return m_launch

    @classmethod
    def from_wflow(cls, wflow):
        """
        Create a fresh Workflow from an existing one.

        Args:
            wflow (Workflow)

        Returns:
            Workflow
        """
        new_wf = Workflow.from_dict(wflow.to_dict())
        new_wf.reset(reset_ids=True)
        return new_wf

    def reset(self, reset_ids=True):
        """
        Reset the states of all Fireworks in this workflow to 'WAITING'.

        Args:
            reset_ids (bool): if ``True``, give each Firework a new id.
        """
        if reset_ids:
            old_new = {}  # mapping between old and new Firework ids
            for fw_id, fw in self.id_fw.items():
                global NEGATIVE_FWID_CTR
                NEGATIVE_FWID_CTR -= 1
                new_id = NEGATIVE_FWID_CTR
                old_new[fw_id] = new_id
                fw.fw_id = new_id
            self._reassign_ids(old_new)
        # reset states
        for fw in self.fws:
            fw.state = 'WAITING'
        self.fw_states = {key: self.id_fw[key].state for key in self.id_fw}

    @classmethod
    def from_dict(cls, m_dict):
        """
        Return Workflow from its dict representation.

        Args:
            m_dict (dict): either a Workflow dict or a Firework dict

        Returns:
            Workflow
        """
        # accept
        if 'fws' in m_dict:
            created_on = m_dict.get('created_on')
            updated_on = m_dict.get('updated_on')
            return Workflow([Firework.from_dict(f) for f in m_dict['fws']],
                            Workflow.Links.from_dict(m_dict['links']), m_dict.get('name'),
                            m_dict['metadata'], created_on, updated_on)
        else:
            return Workflow.from_Firework(Firework.from_dict(m_dict))

    @classmethod
    def from_Firework(cls, fw, name=None, metadata=None):
        """
        Return Workflow from the given Firework.

        Args:
            fw (Firework)
            name (str): New workflow's name. if not provided, the firework name is used
            metadata (dict): New workflow's metadata.

        Returns:
            Workflow
        """
        name = name if name else fw.name
        return Workflow([fw], None, name=name, metadata=metadata, created_on=fw.created_on,
                        updated_on=fw.updated_on)

    def __str__(self):
        return 'Workflow object: (fw_ids: {} , name: {})'.format(self.id_fw.keys(), self.name)

    def remove_fws(self, fw_ids):
        """
        Remove the fireworks corresponding to the input firework ids and update the workflow i.e the
        parents of the removed fireworks become the parents of the children fireworks (only if the
        children dont have any other parents).

        Args:
            fw_ids (list): list of fw ids to remove.

        """
        # not working with the copies, causes spurious behavior
        wf_dict = deepcopy(self.as_dict())
        orig_parent_links = deepcopy(self.links.parent_links)
        fws = wf_dict["fws"]

        # update the links dict: remove fw_ids and link their parents to their children (if they don't
        # have any other parents).
        for fid in fw_ids:
            children = wf_dict["links"].pop(str(fid))
            # root node --> no parents
            try:
                parents = orig_parent_links[int(fid)]
            except KeyError:
                parents = []
            # remove the firework from their parent links and re-link their parents to the children.
            for p in parents:
                wf_dict["links"][str(p)].remove(fid)
                # adopt the children
                for c in children:
                    # adopt only if the child doesn't have any other parents.
                    if len(orig_parent_links[int(c)]) == 1:
                        wf_dict["links"][str(p)].append(c)

        # update the list of fireworks.
        wf_dict["fws"] = [f for f in fws if f["fw_id"] not in fw_ids]

        new_wf = Workflow.from_dict(wf_dict)
        self.fw_states = new_wf.fw_states
        self.id_fw = new_wf.id_fw
        self.links = new_wf.links
