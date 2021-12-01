from fireworks import Firework, PyTask, Workflow
from fireworks.utilities.visualize import Digraph, wf_to_graph


def test_wf_to_graph():

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

    wf = Workflow([fw1, fw2, fw3], {fw1: [fw2], fw2: [fw3], fw3: []})

    dag = wf_to_graph(wf)

    assert isinstance(dag, Digraph)
