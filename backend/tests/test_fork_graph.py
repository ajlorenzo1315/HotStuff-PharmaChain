"""Contrato de datos de la visualización del experimento de bifurcación."""

from pharmachain.api.fork_experiment import run_fork_experiment


def test_fork_graph_has_real_parent_links():
    result = run_fork_experiment()
    blocks = result["graph"]["blocks"]
    assert len(blocks) == 4
    assert blocks[0]["parent"] is None
    assert blocks[1]["parent"] == blocks[0]["id"]
    assert blocks[2]["parent"] == blocks[1]["id"]
    assert blocks[3]["parent"] == blocks[0]["id"]
    assert len({b["id"] for b in blocks}) == 4


def test_fork_graph_voters_and_quorum():
    result = run_fork_experiment()
    graph = result["graph"]
    assert graph["quorum"] == 3
    assert len(graph["votes"]) == 4
    assert sum(not v["honest"] for v in graph["votes"]) == 1
    assert all(v["branch"] in {"A", "B", "—"} for v in graph["votes"])
