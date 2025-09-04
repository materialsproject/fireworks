"""
This example is explained in the tutorial on writing firetasks:
https://materialsproject.github.io/fireworks/guide_to_writing_firetasks.html
"""
import uuid
from fireworks import LaunchPad, Workflow, Firework, FWAction, PyTask
from fireworks import FiretaskBase, explicit_serialize
from fireworks.fw_config import LAUNCHPAD_LOC
from fireworks.core.rocket_launcher import launch_rocket


@explicit_serialize
class SummationTask(FiretaskBase):
    required_params = ['inputs', 'output']

    def run_task(self, fw_spec):
        inp = [fw_spec[i] for i in self['inputs']]
        return FWAction(update_spec={self['output']: sum(inp)})


@explicit_serialize
class IfNonstrictTask(FiretaskBase):
    required_params = ['condition', 'input_1', 'fw_id_1', 'input_2', 'fw_id_2',
                       'output', 'detour_name']

    def run_task(self, fw_spec):
        inp = self['input_1'] if fw_spec[self['condition']] else self['input_2']
        fw_id = self['fw_id_1'] if fw_spec[self['condition']] else self['fw_id_2']
        fwk = Firework(name=self['detour_name'], tasks=SummationTask(inputs=[inp],
                       output=self['output']))
        dct = {'detour': True, 'workflow': Workflow(fireworks=[fwk]), 'parents': [fw_id]}
        return FWAction(append_wfs=dct)


def get_ancestors(lpad, fw_id):
    """return a list of all ancestors' fw_ids of a node with fw_id"""
    wfl = lpad.workflows.find_one({'nodes': fw_id}, {'links': True})
    wfl_pl = Workflow.Links.from_dict(wfl['links']).parent_links
    parents = wfl_pl.get(fw_id, [])
    ancestors = set()
    while parents:
        ancestors.update(parents)
        new_parents = set()
        for par in iter(parents):
            new_parents.update(wfl_pl.get(par, []))
        parents = new_parents
    return list(ancestors)


def run_fireworks(lpad, fw_ids):
    """launch fireworks with the provided fw_ids"""
    while fw_ids:
        ready = lpad.get_fw_ids({'fw_id': {'$in': fw_ids}, 'state': 'READY'})
        if not ready:
            return
        for fw_id in ready:
            assert launch_rocket(lpad, fw_id=fw_id)
            fw_ids.remove(fw_id)


if __name__ == '__main__':
    lpad = LaunchPad.from_file(LAUNCHPAD_LOC)
    fw_0 = Firework(tasks=PyTask(func='builtins.print', args=['root node']))
    fw_1 = Firework(tasks=SummationTask(inputs=['a'], output='a'), spec={'a': 1})
    fw_2 = Firework(tasks=SummationTask(inputs=['b'], output='b'), spec={'b': 2})
    wf = Workflow(fireworks=[fw_0, fw_1, fw_2], links_dict={fw_0: [fw_1, fw_2]})
    lpad.add_wf(wf)

    det_name = uuid.uuid4().hex
    tsk_kwargs = {'detour_name': det_name, 'condition': 'x', 'input_1': 'a', 'input_2': 'b',
                  'fw_id_1': fw_1.fw_id, 'fw_id_2': fw_2.fw_id, 'output': 'c'}
    fw_if = Firework(tasks=IfNonstrictTask(**tsk_kwargs), spec={'x': True})
    wf_app = Workflow(fireworks=[fw_if])
    lpad.append_wf(wf_app, fw_ids=[fw_0.fw_id], detour=False, pull_spec_mods=True)

    run_fireworks(lpad, get_ancestors(lpad, fw_if.fw_id)+[fw_if.fw_id])
    det_id = lpad.fireworks.find_one({'name': det_name}, {'fw_id': True})['fw_id']
    run_fireworks(lpad, get_ancestors(lpad, det_id)+[det_id])

    lpad.get_fw_by_id(det_id).launches[-1].launch_id
    launch_id = lpad.get_fw_by_id(det_id).launches[-1].launch_id
    result = lpad.launches.find_one({'launch_id': launch_id})['action']['update_spec']
    print(result)
    assert result == {'c': 1}
