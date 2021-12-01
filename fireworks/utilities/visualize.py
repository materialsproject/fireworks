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
):
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

    keys = sorted(wf.links.keys(), reverse=True)
    n_root_nodes = len(wf.root_fw_ids)

    # set (x,y) coordinates for each node in the workflow links
    points_map = {}

    # root nodes
    for i, k in enumerate(wf.root_fw_ids):
        points_map.update({k: ((-0.5 * n_root_nodes + i) * breadth_factor, (keys[0] + 1) * depth_factor)})

    # the rest
    for k in keys:
        for i, j in enumerate(wf.links[k]):
            if not points_map.get(j, None):
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
def wf_to_graph(wf: Workflow) -> "Digraph":
    """
    Renders a graph representation of a workflow or firework. Workflows are
    rendered as the control flow of the firework, while Fireworks are
    rendered as a sequence of Firetasks.

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
