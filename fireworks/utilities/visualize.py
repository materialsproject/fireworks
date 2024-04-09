from __future__ import annotations

from typing import Any

from monty.dev import requires

from fireworks import Firework, Workflow
from fireworks.features.fw_report import state_to_color

try:
    from graphviz import Digraph
except ImportError:
    Digraph = None


def plot_wf(
    wf,
    depth_factor=1.0,
    breadth_factor=2.0,
    labels_on=True,
    numerical_label=False,
    text_loc_factor=1.0,
    save_as=None,
    style="rD--",
    markersize=10,
    markerfacecolor="blue",
    fontsize=12,
) -> None:
    """
    Generate a visual representation of the workflow. Useful for checking whether the firework
    connections are in order before launching the workflow.

    Args:
        wf (Workflow): workflow object.
        depth_factor (float): adjust this to stretch the plot in y direction.
        breadth_factor (float): adjust this to stretch the plot in x direction.
        labels_on (bool): whether to label the nodes or not. The default is to label the nodes
            using the firework names.
        numerical_label (bool): set this to label the nodes using the firework ids.
        text_loc_factor (float): adjust the label location.
        save_as (str): save the figure to the given name.
        style (str): marker style.
        markersize (int): marker size.
        markerfacecolor (str): marker face color.
        fontsize (int): font size for the node label.
    """
    try:
        import matplotlib.pyplot as plt
    except ImportError:
        raise SystemExit("Install matplotlib. Exiting.")

    keys = sorted(wf.links, reverse=True)
    n_root_nodes = len(wf.root_fw_ids)

    # set (x,y) coordinates for each node in the workflow links
    points_map = {}

    # root nodes
    for i, k in enumerate(wf.root_fw_ids):
        points_map.update({k: ((-0.5 * n_root_nodes + i) * breadth_factor, (keys[0] + 1) * depth_factor)})

    # the rest
    for k in keys:
        for i, j in enumerate(wf.links[k]):
            if not points_map.get(j):
                points_map[j] = ((i - len(wf.links[k]) / 2.0) * breadth_factor, k * depth_factor)

    # connect the dots
    for k in keys:
        for i in wf.links[k]:
            plt.plot(
                [points_map[k][0], points_map[i][0]],
                [points_map[k][1], points_map[i][1]],
                style,
                markersize=markersize,
                markerfacecolor=markerfacecolor,
            )
            if labels_on:
                label1 = wf.id_fw[k].name
                label2 = wf.id_fw[i].name
                if numerical_label:
                    label1 = str(k)
                    label2 = str(i)
                plt.text(
                    points_map[k][0] * text_loc_factor, points_map[k][1] * text_loc_factor, label1, fontsize=fontsize
                )
                plt.text(
                    points_map[i][0] * text_loc_factor, points_map[i][1] * text_loc_factor, label2, fontsize=fontsize
                )

    plt.axis("scaled")
    plt.axis("off")

    if save_as:
        plt.savefig(save_as)


@requires(
    Digraph is not None,
    "graphviz package required for wf_to_graph.\n"
    "Follow the installation instructions here: https://github.com/xflr6/graphviz",
)
def wf_to_graph(wf: Workflow, dag_kwargs: dict[str, Any] | None = None, wf_show_tasks: bool = True) -> Digraph:
    """Renders a graph representation of a workflow or firework. Workflows are rendered as the
    control flow of the firework, while Fireworks are rendered as a sequence of Firetasks.

    Copied from https://git.io/JO6L8.

    Args:
        workflow (Workflow | Firework): Workflow or Firework to be rendered.
        dag_kwargs (dict[str, Any]): Arguments passed to Digraph.attr(). Defaults to {}.
        wf_show_tasks (bool): When rendering a Workflow, whether to show each Firetask in the graph. Defaults to False.

    Returns:
        Digraph: The Workflow or Firework directed acyclic graph.
    """
    dag_kwargs = dag_kwargs or {}
    if not isinstance(wf, (Workflow, Firework)):
        raise ValueError(f"expected instance of Workflow or Firework, got {wf}")

    if isinstance(wf, Workflow) and not wf_show_tasks:
        # if we're rendering a Workflow and not showing tasks, we render the graph from left to right
        # by default
        dag_kwargs["rankdir"] = dag_kwargs.get("rankdir", "LR")

    # Directed Acyclic Graph
    dag = Digraph(comment=wf.name)
    dag.attr(**dag_kwargs)
    dag.node_attr.update(shape="box")

    dag.graph_attr["fontname"] = "helvetica"
    dag.node_attr["fontname"] = "helvetica"
    dag.edge_attr["fontname"] = "helvetica"

    if isinstance(wf, Workflow):
        for fw in wf:
            color = state_to_color[fw.state]
            dag.node(name=str(fw.fw_id), label=fw.name, color=color, fontname="helvetica")

            if not wf_show_tasks:
                continue

            subgraph = Digraph(name=f"tasks_{fw.fw_id}")
            subgraph.attr(color=color)

            for idx, task in enumerate(fw.tasks):
                # Clean up names
                name = task.fw_name.replace("{", "").replace("}", "")
                name = name.split(".")[-1]
                node_id = f"{fw.fw_id}-{idx}"
                subgraph.node(name=node_id, label=name, style="dashed")
                if idx == 0:
                    subgraph.edge(str(fw.fw_id), node_id)
                else:
                    subgraph.edge(f"{fw.fw_id}-{idx - 1}", node_id)

            dag.subgraph(subgraph)

        for start, targets in wf.links.items():
            for target in targets:
                dag.edge(str(start), str(target))

    elif isinstance(wf, Firework):
        for idx, task in enumerate(wf.tasks):
            # Clean up names
            name = task.fw_name.replace("{", "").replace("}", "")
            name = name.split(".")[-1]
            dag.node(str(idx), label=name)
            if idx >= 1:
                dag.edge(str(idx - 1), str(idx))

    return dag


if __name__ == "__main__":
    import atomate.vasp.workflows as wf_mod
    from pymatgen.core import Lattice, Structure

    struct = Structure(Lattice.cubic(3), ["S"], [[0, 0, 0]])
    wf = wf_mod.wf_bandstructure_hse(struct)

    for item in dir(wf_mod):
        if item.startswith("wf_"):
            try:
                wf = getattr(wf_mod, item)(struct)
            except TypeError:
                continue
            dag = wf_to_graph(wf)
            # add wf name as plot title above the graph
            dag.attr(label=item, fontsize="20", labelloc="t")
            dag.view()
            # dag.format = "png"  # default format is PDF
            # dag.render(f"docs_rst/_static/wf_graphs/{item}")
