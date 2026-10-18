import pytest

from pharmachain.simulation.scenarios import simulate


def test_normal_three_chain_commit():
    data = simulate("normal", rounds=3)
    assert all(row["qc_formed"] for row in data["rounds"])
    assert data["final_committed_height"] == 1


def test_one_offline_still_reaches_quorum():
    data = simulate("one_offline", rounds=3)
    assert all(row["votes"] == 3 for row in data["rounds"])
    assert data["final_committed_height"] == 1


def test_two_offline_no_quorum():
    data = simulate("two_offline", rounds=6)
    assert all(not row["qc_formed"] for row in data["rounds"])
    assert data["final_committed_height"] == 0


def test_silent_leader_causes_view_change():
    data = simulate("silent_leader", rounds=2)
    assert data["rounds"][0]["event"] == "leader_timeout"
    assert data["rounds"][1]["qc_formed"]


def test_recovery_after_network_restored():
    data = simulate("recovery", rounds=5)
    assert not data["rounds"][0]["qc_formed"]
    assert not data["rounds"][1]["qc_formed"]
    assert all(row["qc_formed"] for row in data["rounds"][2:])


def test_invalid_rounds():
    with pytest.raises(ValueError):
        simulate(rounds=0)
