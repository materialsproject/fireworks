""" A utility to validate and visualize workflows """

__author__ = "Ivan Kondov"
__email__ = "ivan.kondov@kit.edu"
__copyright__ = "Copyright 2017, Karlsruhe Institute of Technology"

from itertools import combinations

import igraph
from igraph import Graph
from monty.dev import requires

from fireworks import Workflow
from fireworks.features.fw_report import state_to_color

try:
    from graphviz import Digraph
except ImportError:
    graphviz = None

DF_TASKS = ["PyTask", "CommandLineTask", "ForeachTask", "JoinDictTask", "JoinListTask"]

DEFAULT_IGRAPH_VISUAL_STYLE = {
    "bbox": (1280, 800),
    "margin": [200, 100, 200, 100],
    "vertex_label_dist": 2,
}

# for graph visualization, code "roots" green (start), "leaves" red (end),
# any other blue
try:
    import matplotlib

    # only needed for color-coding with favorite named colors, not imported
    # in top level as matplotlib is no Fireworks requirement.

    DEFAULT_IGRAPH_VERTEX_COLOR_CODING = {
        "root": matplotlib.colors.cnames["forestgreen"],
        "leaf": matplotlib.colors.cnames["indianred"],
        "other": matplotlib.colors.cnames["lightsteelblue"],
    }
except ImportError:
    DEFAULT_IGRAPH_VERTEX_COLOR_CODING = {
        "root": "#228B22",
        "leaf": "#CD5C5C",
        "other": "#B0C4DE",
    }


class DAGFlow(Graph):
    """The purpose of this class is to help construction, validation and
    visualization of workflows."""

    def __init__(self, steps, links=None, nlinks=None, name=None, **kwargs):
        Graph.__init__(self, directed=True, graph_attrs={"name": name}, **kwargs)

        for step in steps:
            self._set_io_fields(step)
            self.add_vertex(**step)
        assert len(steps) < 2 or links or nlinks, "steps must be defined with links"
        if nlinks:
            self._add_ctrlflow_links(self._get_links(nlinks))
        elif links:
            self._add_ctrlflow_links(links)
        self._add_dataflow_links()

    @classmethod
    def from_fireworks(cls, fireworkflow):
        """Converts a fireworks workflow object into a new DAGFlow object"""
        wfd = fireworkflow.to_dict()
        if "name" in wfd:
            name = wfd["name"]
        fw_idx = {}
        steps = []
        for idx, fwk in enumerate(wfd["fws"]):
            fw_idx[str(fwk["fw_id"])] = idx
            step = {}
            step["name"] = fwk["name"]
            step["id"] = fwk["fw_id"]
            step["state"] = fwk["state"] if "state" in fwk else None
            steps.append(step)

        links = []
        for src in wfd["links"]:
            for trg in wfd["links"][src]:
                links.append((int(src), trg))

        for idx, fwk in enumerate(wfd["fws"]):
            step = steps[idx]
            step.update(fwk["spec"])
            tasks = fwk["spec"]["_tasks"]
            step["_tasks"] = [t for t in tasks if t["_fw_name"] in DF_TASKS]

            def task_input(task, spec):
                """extracts labels of available inputs from a task"""
                inps = []
                if "inputs" in task:
                    if "command_spec" in task:
                        # CommandLineTask
                        for inp in task["inputs"]:
                            assert inp in task["command_spec"], (idx, inp)
                            taskinp = task["command_spec"][inp]
                            if isinstance(taskinp, dict):
                                assert "source" in taskinp, (idx, inp)
                                src = taskinp["source"]
                                if isinstance(src, dict) or src in spec:
                                    inps.append(inp)
                            elif isinstance(taskinp, str) and taskinp in spec:
                                inps.append(taskinp)
                    else:
                        # PythonFunctionTask
                        for inp in task["inputs"]:
                            if inp in spec:
                                inps.append(inp)
                return inps

            step_data = []
            for task in step["_tasks"]:
                true_task = task["task"] if "task" in task else task
                step_data.extend(task_input(true_task, fwk["spec"]))
                if "outputs" in true_task:
                    assert isinstance(true_task["outputs"], list), "outputs must be a list in fw_id " + str(step["id"])
                if "inputs" in true_task:
                    assert isinstance(true_task["inputs"], list), "inputs must be a list in fw_id " + str(step["id"])
            step["data"] = list(set(step_data))

        return cls(steps=steps, links=links, name=name)

    def _get_links(self, nlinks):
        """Translates named links into links between step ids"""
        links = []
        for link in nlinks:
            source = [v["id"] for v in list(self.vs) if v["name"] == link[0]]
            target = [v["id"] for v in list(self.vs) if v["name"] == link[1]]
            links.append((source, target))
        return links

    def _get_ctrlflow_links(self):
        """Returns a list of unique tuples of link ids"""
        links = []
        for ilink in {link.tuple for link in list(self.es)}:
            source = self.vs[ilink[0]]["id"]
            target = self.vs[ilink[1]]["id"]
            links.append((source, target))
        return links

    def _add_ctrlflow_links(self, links):
        """Adds graph edges corresponding to control flow links"""
        for link in links:
            source = self._get_index(link[0])
            target = self._get_index(link[1])
            self.add_edge(source, target, **{"label": " "})

    def _add_dataflow_links(self, step_id=None, mode="both"):
        """Adds graph edges corresponding to data flow links"""
        if step_id:
            vidx = self._get_index(step_id)
            vertex = self.vs[vidx]
            if mode in ["out", "both"]:
                for entity in vertex["outputs"]:
                    for cidx in self._get_targets(vertex, entity):
                        self.add_edge(vidx, cidx, **{"label": entity})
            if mode in ["in", "both"]:
                for entity in vertex["inputs"]:
                    for pidx in self._get_sources(vertex, entity):
                        if pidx != vidx:
                            self.add_edge(pidx, vidx, **{"label": entity})
        else:
            for parent in list(self.vs):
                pidx = parent.index
                for entity in parent["outputs"]:
                    for cidx in self._get_targets(parent, entity):
                        self.add_edge(pidx, cidx, **{"label": entity})

    def _get_sources(self, step, entity):
        """Returns a list of steps that act as sources for the data entity
        in the specified step."""
        lst = []
        parents = set(self.predecessors(step))
        # data entity passed from parent steps
        for parent in parents:
            if entity in self.vs[parent]["outputs"]:
                if not self.vs[parent]["chunk"]:
                    lst.append(parent)

        # data entity in the same step
        cparents = [p for p in parents if self.vs[p]["state"] == "COMPLETED"]
        csrclist = [op for cp in cparents for op in self.vs[cp]["outputs"]]
        if entity in step["data"] and entity not in csrclist:
            lst.append(step.index)

        # data entity from a preceding task in the same step
        outp_found = False
        for task in step["_tasks"]:
            if "outputs" in task and entity in task["outputs"]:
                outp_found = True
            if "output" in task and entity == task["output"]:
                outp_found = True
            if outp_found and "inputs" in task and entity in task["inputs"]:
                lst.append(step.index)
                break

        return lst

    def _get_targets(self, step, entity):
        """Returns a list of IDs of all successor steps
        that are data targets for the specified step."""
        lst = []
        for child in set(self.successors(step)):
            if entity in self.vs[child]["inputs"]:
                lst.append(child)
        return lst

    @staticmethod
    def _set_io_fields(step):
        """Set io keys as step attributes"""
        for item in ["inputs", "outputs", "output"]:
            step[item] = []
            for task in step["_tasks"]:
                # test the case of meta-tasks
                true_task = task["task"] if "task" in task else task
                if item in true_task:
                    if isinstance(true_task[item], list):
                        step[item].extend(true_task[item])
                    else:
                        step[item].append(true_task[item])
        step["outputs"].extend(step["output"])

        # some tasks may share inputs
        step["inputs"] = list(set(step["inputs"]))

        # data chunks distributed over several sibling steps
        for task in step["_tasks"]:
            step["chunk"] = "chunk_number" in task

    def _get_steps(self):
        """Returns a list of dictionaries describing the steps"""
        steps = [vertex.attributes() for vertex in list(self.vs)]
        for step in steps:
            for item in ["inputs", "outputs"]:
                if item in step:
                    del item
        return steps

    def _get_index(self, step_id):
        """Returns the vertex index for a step with provided id"""
        for vertex in list(self.vs):
            if vertex["id"] == step_id:
                retval = vertex.index
                break
        return retval

    def _get_cycles(self):
        """Returns a partial list of cycles in case of erroneous workflow"""
        if self.is_dag():
            return []
        for deg in range(2, len(self.vs) + 1):
            lst = self.get_subisomorphisms_vf2(Graph.Ring(deg, directed=True))
            flatten = lambda l: [item for sublist in l for item in sublist]
            if flatten(lst):
                break
        cycs = [list(x) for x in {tuple(sorted(l)) for l in lst}]
        cycs = [[self.vs[ind]["id"] for ind in cycle] for cycle in cycs]
        return cycs

    def _get_roots(self):
        """Returns all roots (i.e. vertices without incoming edges)"""
        return [i for i, v in enumerate(self.degree(mode=igraph.IN)) if v == 0]

    def _get_leaves(self):
        """Returns all leaves (i.e. vertices without outgoing edges)"""
        return [i for i, v in enumerate(self.degree(mode=igraph.OUT)) if v == 0]

    def delete_ctrlflow_links(self):
        """Deletes graph edges corresponding to control flow links"""
        lst = [link.index for link in list(self.es) if link["label"] == " "]
        self.delete_edges(lst)

    def delete_dataflow_links(self):
        """Deletes graph edges corresponding to data flow links"""
        lst = [link.index for link in list(self.es) if link["label"] != " "]
        self.delete_edges(lst)

    def add_step_labels(self):
        """Labels the workflow steps (i.e. graph vertices)"""
        for vertex in list(self.vs):
            vertex["label"] = vertex["name"] + ", id: " + str(vertex["id"])

    def check(self):
        """Correctness check of the workflow"""
        try:
            assert self.is_dag(), "The workflow graph must be a DAG."
        except AssertionError as err:
            err.args = (err.args[0] + ": found cycles: " + repr(self._get_cycles()),)
            raise err
        assert self.is_connected(mode="weak"), "The workflow graph must be connected."
        assert len(self.vs["id"]) == len(set(self.vs["id"])), "Workflow steps must have unique IDs."
        self.check_dataflow()

    def check_dataflow(self):
        """Checks whether all inputs and outputs match"""

        # check for shared output data entities
        for vertex in list(self.vs):
            outputs = vertex["outputs"]
            assert len(outputs) == len(set(outputs)), (
                "Several tasks may not use the same name in outputs list.",
                [x for n, x in enumerate(outputs) if x in outputs[:n]],
            )
        # evaluate matching sources
        for vertex in list(self.vs):
            for entity in vertex["inputs"]:
                sources = self._get_sources(vertex, entity)
                assert len(sources) == 1, (
                    "Every input in inputs list must have exactly one source.",
                    "step",
                    vertex["name"],
                    "entity",
                    entity,
                    "sources",
                    sources,
                )

    def to_dict(self):
        """Returns a dictionary that can be passed to the constructor"""
        dct = {}
        dct["name"] = self["name"]
        dct["steps"] = self._get_steps()
        dct["links"] = self._get_ctrlflow_links()
        return dct

    def to_dot(self, filename="wf.dot", view="combined"):
        """Writes the workflow into a file in DOT format"""
        graph = DAGFlow(**self.to_dict())
        if view == "controlflow":
            graph.delete_dataflow_links()
        elif view == "dataflow":
            graph.delete_ctrlflow_links()
        elif view == "combined":
            dlinks = []
            for vertex1, vertex2 in combinations(graph.vs.indices, 2):
                clinks = list(set(graph.incident(vertex1, mode="ALL")) & set(graph.incident(vertex2, mode="ALL")))
                if len(clinks) > 1:
                    for link in clinks:
                        if graph.es[link]["label"] == " ":
                            dlinks.append(link)
            graph.delete_edges(dlinks)
        # remove non-string, non-numeric attributes because write_dot() warns
        for vertex in graph.vs:
            for key, val in vertex.attributes().items():
                if not isinstance(val, (str, int, float, complex)):
                    del vertex[key]
                if isinstance(val, bool):
                    del vertex[key]
        graph.write_dot(filename)


def plot_wf(wf, view="combined", labels=False, **kwargs):
    """Plot workflow DAG via igraph.plot.

    Args:
        wf (Workflow)
        view (str): same as in 'to_dot'. Default: 'combined'
        labels (bool): show a FW's name and id as labels in graph

    Other **kwargs can be any igraph plotting style keyword, overrides default.
    See https://igraph.org/python/doc/tutorial/tutorial.html for possible
    keywords. See `plot_wf` code for defaults.

    Returns:
        igraph.drawing.Plot
    """

    dagf = DAGFlow.from_fireworks(wf)
    if labels:
        dagf.add_step_labels()

    # copied from to_dot
    if view == "controlflow":
        dagf.delete_dataflow_links()
    elif view == "dataflow":
        dagf.delete_ctrlflow_links()
    elif view == "combined":
        dlinks = []
        for vertex1, vertex2 in combinations(dagf.vs.indices, 2):
            clinks = list(set(dagf.incident(vertex1, mode="ALL")) & set(dagf.incident(vertex2, mode="ALL")))
            if len(clinks) > 1:
                for link in clinks:
                    if dagf.es[link]["label"] == " ":
                        dlinks.append(link)
        dagf.delete_edges(dlinks)

    # remove non-string, non-numeric attributes because write_dot() warns
    for vertex in dagf.vs:
        for key, val in vertex.attributes().items():
            if not isinstance(val, (str, int, float, complex)):
                del vertex[key]
            if isinstance(val, bool):
                del vertex[key]

    # plotting defaults
    visual_style = DEFAULT_IGRAPH_VISUAL_STYLE.copy()

    # generic plotting defaults
    visual_style["layout"] = dagf.layout_kamada_kawai()

    # vertex defaults
    dagf_roots = dagf._get_roots()
    dagf_leaves = dagf._get_leaves()

    def color_coding(v):
        if v in dagf_roots:
            return DEFAULT_IGRAPH_VERTEX_COLOR_CODING["root"]
        elif v in dagf_leaves:
            return DEFAULT_IGRAPH_VERTEX_COLOR_CODING["leaf"]
        else:
            return DEFAULT_IGRAPH_VERTEX_COLOR_CODING["other"]

    visual_style["vertex_color"] = [color_coding(v) for v in range(dagf.vcount())]

    visual_style.update(kwargs)

    # special treatment
    if "layout" in kwargs and isinstance(kwargs["layout"], str):
        visual_style["layout"] = dagf.layout(kwargs["layout"])

    return igraph.plot(dagf, **visual_style)


@requires(
    graphviz,
    "graphviz package required for wf_to_graph.\n"
    "Follow the installation instructions here: https://github.com/xflr6/graphviz",
)
def wf_to_graph(wf: Workflow) -> "Digraph":
    """
    Renders a graph representation of a workflow or firework. Workflows are
    rendered as the control flow of the firework, while Fireworks are
    rendered as a sequence of Firetasks.

    Copied from https://git.io/JO6L8.

    Args:
        workflow (Workflow|Firework): workflow or Firework
            to be rendered.

    Returns:
        Digraph: the rendered workflow or firework graph
    """
    # Directed Acyclic Graph
    dag = Digraph(comment=wf.name, graph_attr={"rankdir": "LR"})
    dag.node_attr["shape"] = "box"
    if isinstance(wf, Workflow):
        for fw in wf:
            dag.node(str(fw.fw_id), label=fw.name, color=state_to_color[fw.state])

        for start, targets in wf.links.items():
            for target in targets:
                dag.edge(str(start), str(target))
    elif isinstance(wf, Firework):
        for n, ft in enumerate(wf.tasks):
            # Clean up names
            name = ft.fw_name.replace("{", "").replace("}", "")
            name = name.split(".")[-1]
            dag.node(str(n), label=name)
            if n >= 1:
                dag.edge(str(n - 1), str(n))
    else:
        raise ValueError("expected instance of Workflow or Firework")
    return dag
