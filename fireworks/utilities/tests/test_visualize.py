import pytest

from fireworks import Firework, PyTask, Workflow
from fireworks.utilities.visualize import Digraph, plot_wf, wf_to_graph


@pytest.fixture()
def power_wf():
    fw1 = Firework(
        PyTask(func="math.pow", inputs=["base", "exponent"], outputs=["first power"]),
        name="pow(2, 3)",
        spec={"base": 2, "exponent": 3},
    )
    fw2 = Firework(
        PyTask(func="math.pow", inputs=["first power", "exponent"], outputs=["second power"]),
        name="pow(pow(2, 3), 4)",
        spec={"exponent": 4},
    )
    fw3 = Firework(PyTask(func="print", inputs=["second power"]), name="the third one")

    return Workflow([fw1, fw2, fw3], {fw1: [fw2], fw2: [fw3], fw3: []})


def test_wf_to_graph(power_wf) -> None:
    dag = wf_to_graph(power_wf)

    assert isinstance(dag, Digraph)

    dag = wf_to_graph(power_wf, wf_show_tasks=False)

    assert isinstance(dag, Digraph)


def test_plot_wf(power_wf) -> None:
    plot_wf(power_wf)

    plot_wf(power_wf, depth_factor=0.5, breadth_factor=1)

    plot_wf(power_wf, labels_on=True)
