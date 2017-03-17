__author__ = 'Ivan Kondov'
__email__ = 'ivan.kondov@kit.edu'
__copyright__ = 'Copyright 2017, Karlsruhe Institute of Technology'

from igraph import Graph


def translate_keys(d, key, tr):
    new = {}
    for k, v in d.items():
        if isinstance(v, dict):
            newv = translate_keys(v, key, tr)
        elif isinstance(v, list):
            newv = []
            for item in v:
                if isinstance(item, dict):
                    newv.append(translate_keys(item, key, tr))
                else:
                    newv.append(item)
        else:
            newv = v
        if k == key:
            new[tr] = newv
        else:
            new[k] = newv
    return new


class DAGFlow(Graph):
    """ The purpose of this class is to help construction, validation and 
    visualization of workflows. Currently it imports and exports fireworks 
    workflows but it is open for other workflow formats. 
    """

    def __init__(self, steps=None, links=None, nlinks=None, name=None, **kwargs):
        Graph.__init__(self, directed=True, graph_attrs={'name': name})

        if steps:
            for step in steps:
                self.set_io_fields(step)
                self.add_vertex(**step)
            assert len(steps)==1 or links or nlinks, (
                'steps must be defined with links'
            )
            if nlinks:
                self.add_ctrlflow_links(self.get_links(nlinks))
            elif links:
                self.add_ctrlflow_links(links)
            self.validate()
            self.check_dataflow()
            self.add_dataflow_links()
            self.validate()

        if kwargs:
            self.kwargs = kwargs


    @classmethod
    def from_file(cls, filename):
        """ Loads a DAGFlow dictionary and returns a new DAGFlow object """
        import json
        with open(filename, 'r') as infile:
            dct = json.load(infile)
        return cls(**dct)


    @classmethod
    def from_fireworks(cls, fireworkflow):
        """ Converts a fireworks workflow object into a new DAGFlow object """
        wfd = fireworkflow.to_dict()
        if 'name' in wfd.keys():
            name = wfd['name']
        fw_idx = {}
        steps = []
        for idx, fw in enumerate(wfd['fws']):
            fw_idx[str(fw['fw_id'])] = idx
            step = {}
            step['name'] = fw['name']
            step['id'] = fw['fw_id']
            steps.append(step)

        links = []
        for src in wfd['links'].keys():
            for trg in wfd['links'][src]:
                links.append((int(src), trg))

        for idx, fw in enumerate(wfd['fws']):
            step = steps[idx]
            spec = fw['spec']
            spec = translate_keys(spec, '_tasks', 'tasks')
            spec = translate_keys(spec, '_fw_name', 'name')
            step.update(spec)
            tasks = step['tasks']
            step['data'] = []
            for key in spec.keys():
                for task in tasks:
                    if 'inputs' in task.keys() and key in task['inputs']:
                        step['data'].append(key)
        return cls(steps=steps, links=links, name=name)


    @classmethod
    def from_cwl(cls, cwldoc):
        """ Not implemented """
        pass


    def get_links(self, nlinks):
        """ Translates named links into links between step ids """
        links = []
        for link in nlinks:
            source = [ v['id'] for v in self.vs if v['name'] == link[0] ]
            target = [ v['id'] for v in self.vs if v['name'] == link[1] ]
            links.append((source, target))
        return links


    def get_ctrlflow_links(self):
        """ Returns a list of unique tuples of link ids """
        links = []
        for ilink in set([ link.tuple for link in self.es ]):
            source = self.vs[ilink[0]]['id']
            target = self.vs[ilink[1]]['id']
            links.append((source, target))
        return links


    def get_ctrlflow_links_dict(self):
        dlinks = {}
        for step in self.vs:
            dlinks[str(step['id'])] = []
        links = self.get_ctrlflow_links()
        for link in links:
            dlinks[str(link[0])].append(link[1])
        return dlinks


    def add_ctrlflow_links(self, links):
        for link in links:
            source = self.get_index(link[0])
            target = self.get_index(link[1])
            self.add_edge(source, target, **{'label': ' '})


    def add_dataflow_links(self, step_id=None, mode='both'):
        if step_id:
            vidx = self.get_index(step_id)
            vertex = self.vs[vidx]
            if mode in ['out', 'both']:
                for entity in vertex['outputs']:
                    for cidx in self.get_targets(vertex, entity):
                        self.add_edge(vidx, cidx, **{'label': entity})
            if mode in ['in', 'both']:
                for entity in vertex['inputs']:
                    for pidx in self.get_sources(vertex, entity):
                        if pidx != vidx:
                            self.add_edge(pidx, vidx, **{'label': entity})
        else:
            for parent in self.vs:
                pidx = parent.index
                for entity in parent['outputs']:
                    for cidx in self.get_targets(parent, entity):
                         self.add_edge(pidx, cidx, **{'label': entity})


    def delete_ctrlflow_links(self):
        lst = [ link.index for link in self.es if link['label'] == ' ' ]
        self.delete_edges(lst)


    def delete_dataflow_links(self):
        lst = [ link.index for link in self.es if link['label'] != ' ' ]
        self.delete_edges(lst)


    def check_dataflow(self):
        if len(self.vs) == 1: return
        # check for shared output data entities
        for v in self.vs:
            outputs = v['outputs']
            assert len(outputs) == len(set(outputs)), (
                'The tasks in a workflow step may not share output fields.',
                [x for n, x in enumerate(outputs) if x in outputs[:n]]
            )
        # evaluate matching sources
        for v in self.vs:
            for entity in v['inputs']:
                sources = self.get_sources(v, entity)
                assert len(sources) == 1, (
                    'An input field must have exactly one source', 
                    'step', v['name'], 'entity', entity, 'sources', sources
                )


    def get_sources(self, step, entity):
        """ Returns a list of IDs of all predecessor steps 
        that are data sources for the specified step. """
        lst = []
        for parent in set(self.predecessors(step)):
            if entity in self.vs[parent]['outputs']:
                lst.append(parent)
        if entity in step['data']:
            lst.append(step.index)
        return lst


    def get_targets(self, step, entity):
        """ Returns a list of IDs of all successor steps 
        that are data targets for the specified step. """
        lst = []
        for child in set(self.successors(step)):
            if entity in self.vs[child]['inputs']:
                lst.append(child)
        return lst


    @staticmethod
    def set_io_fields(step):
        """ Set io keys as step attributes """
        for item in ['inputs', 'outputs']:
            step[item] = []
            for task in step['tasks']:
                if item in task.keys():
                    if type(task[item]) is list:
                        step[item].extend(task[item])
                    else:
                        step[item].append(task[item])
        # some tasks may share inputs
        step['inputs'] = list(set(step['inputs']))


    def get_steps(self):
        """ Returns a list of dictionaries describing the steps """ 
        steps = [vertex.attributes() for vertex in self.vs]
        for step in steps:
            for item in ['inputs', 'outputs']:
                if item in step.keys():
                    del(item)
        return steps


    def add_step(self, step, children, parents):
        """ Insert a new step to the workflow """
        self.set_io_fields(step)
        self.add_vertex(**step)
        links = []
        for idx in children:
            links.append((step['id'], idx))
        for idx in parents:
            links.append((idx, step['id']))
        self.add_ctrlflow_links(links)
        self.validate()
        self.check_dataflow()
        self.add_dataflow_links(step['id'])
        self.validate()


    def delete_steps(self, step_ids):
        """ Delete steps from the workflow """
        lst = [self.get_index(step_id) for step_id in step_ids]
        self.delete_vertices(lst)
        self.validate()
        self.check_dataflow()


    def extend(self, workflow, links):
        """ Extend the workflow with another workflow """
        assert is_instance(workflow, self)
        workflow.validate()
        step_ids = self.vs['id'] + workflow.vs['id']
        assert len(step_ids) == len(set(step_ids)), (
            'workflow steps must have unique IDs'
        )        

        self += workflow
        self.add_ctrlflow_links(links)
        self.delete_dataflow_links()
        self.add_dataflow_links()
        self.validate()
        self.check_dataflow()


    def add_step_labels(self):
        for v in self.vs:
            v['label'] = v['name'] + ', id: ' + str(v['id'])


    def get_index(self, step_id):
        for v in self.vs:
            if v['id'] == step_id:
                return v.index


    def validate(self):
        """ Validate the workflow """
        assert self.is_dag(), (
            'the workflow graph must be a DAG'
        )
        assert self.is_connected(mode='weak'), (
            'the workflow graph must be connected'
        )
        assert len(self.vs['id']) == len(set(self.vs['id'])), (
            'workflow steps must have unique IDs'
        )


    def show_steps(self, step_ids):
        for step_id in step_ids:
            print()
            print('Step ID', step_id)
            step_index = self.get_index(step_id)
            step = self.vs[step_index]
            print('Tasks:')
            for task in step['tasks']:
                print('  name', task['_fw_name'], task)
            print('Upstream links:',
                [ self.es[i].tuple for i in self.incident(step, mode='in') ])
            print('Downstream links:',
                [ self.es[i].tuple for i in self.incident(step, mode='out') ])


    def to_dict(self):
        """ Returns a dictionary that can be passed to the constructor """
        dct = {}
        dct['name'] = self['name']
        dct['steps'] = self.get_steps()            
        dct['links'] = self.get_ctrlflow_links()
        return dct


    def to_fireworks(self, method='from dict'):
        """ Returns a fireworks workflow object """
        from fireworks import Workflow
        import json

        if method == 'from dict':
            fws = []
            for step in self.get_steps():
                spec = step.copy()
                for key in ['id', 'data', 'name', 'inputs', 'outputs']:
                    del(spec[key])
                spec = translate_keys(spec, 'tasks', '_tasks')
                spec = translate_keys(spec, 'name', '_fw_name')
                fws.append({
                    'name': step['name'],
                    'fw_id': step['id'],
                    'spec': spec
                })
            dct = {
                'fws': fws,
                'links': self.get_ctrlflow_links_dict(),
                'name': self['name'],
                'metadata': {}
            }
            return Workflow.from_dict(dct)
        if method == 'from object':
            return Workflow(
                fireworks = [Firework(step) for step in self.get_steps()],
                links = self.get_ctrlflow_links_dict(),
                name = self['name']
            )


    def to_cwl(self):
        """ Not implemented """
        pass


    def to_file(self, filename):
        """ Write the DAGFlow dictionary to a file"""
        import json
        dct = self.to_dict()
        with open(filename, 'w') as outfile:
            json.dump(dct, outfile, indent=4, separators=(',', ': '))


    def to_dot(self, filename='wf.dot', view='control flow'):
        """ Writes the workflow into a file in DOT format """
        if view == 'control flow':
            g = self.copy()
            g.delete_dataflow_links()
            g.write_dot(filename)
        elif view == 'data flow':
            g = self.copy()
            g.delete_ctrlflow_links()
            g.write_dot(filename)
        else:
            self.write_dot(filename)

