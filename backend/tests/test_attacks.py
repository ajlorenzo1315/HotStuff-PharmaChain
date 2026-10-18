"""Adversarial regression tests for the distributed HotStuff simulator."""

from dataclasses import replace

from pharmachain.consensus.distributed import DistributedHotStuff
from pharmachain.domain.state import LedgerState


def make_simulator() -> DistributedHotStuff:
    return DistributedHotStuff(LedgerState({}), validator_count=4, seed=42)


def test_normal_network_forms_qc_and_commits():
    sim = make_simulator()
    rounds = [sim.run_round() for _ in range(3)]
    assert all(r.qc_formed for r in rounds)
    assert all(r.votes == 4 for r in rounds)
    assert all(height == 1 for height in rounds[-1].committed_heights.values())


def test_one_offline_follower_still_reaches_quorum():
    sim = make_simulator()
    sim.network.disconnect("validator-3")
    result = sim.run_round()  # validator-0 is the first leader
    assert result.qc_formed
    assert result.votes == 3
    assert sim.nodes["validator-3"].node.committed_height == 0


def test_two_offline_followers_prevent_quorum():
    sim = make_simulator()
    sim.network.disconnect("validator-2")
    sim.network.disconnect("validator-3")
    result = sim.run_round()
    assert not result.qc_formed
    assert result.votes == 2
    assert all(node.node.committed_height == 0 for node in sim.nodes.values())


def test_offline_leader_cannot_propose():
    sim = make_simulator()
    sim.network.disconnect("validator-0")
    result = sim.run_round()
    assert result.block_hash is None
    assert not result.qc_formed


def test_duplicate_vote_does_not_increase_quorum():
    sim = make_simulator()
    sim.network.disconnect("validator-2")
    sim.network.disconnect("validator-3")
    result = sim.run_round()
    assert result.block_hash is not None
    leader = sim.nodes["validator-0"]
    key = (result.view, result.block_hash)
    before = len(leader.votes[key])
    vote = leader.votes[key]["validator-1"]
    sim.network.send("validator-1", "validator-0", "VOTE", vote, copies=3)
    sim.network.run()
    assert len(leader.votes[key]) == before == 2
    assert key not in leader.formed_qcs
    assert any(e["event"] == "DUPLICATE_VOTE" for e in sim.events)


def test_tampered_signature_is_rejected():
    sim = make_simulator()
    sim.network.disconnect("validator-2")
    sim.network.disconnect("validator-3")
    result = sim.run_round()
    assert result.block_hash is not None
    leader = sim.nodes["validator-0"]
    key = (result.view, result.block_hash)
    legitimate = leader.votes[key]["validator-1"]
    invalid = replace(legitimate, signature="00")
    before = len(leader.votes[key])
    sim.network.send("validator-1", "validator-0", "VOTE", invalid)
    sim.network.run()
    assert len(leader.votes[key]) == before
    assert any(e["event"] == "INVALID_VOTE" for e in sim.events)


def test_no_conflicting_commits_in_ideal_network():
    sim = make_simulator()
    for _ in range(6):
        sim.run_round()
    committed = [tuple(runtime.node.blockchain.committed) for runtime in sim.nodes.values()]
    assert all(chain == committed[0] for chain in committed)
    assert len(committed[0]) > 1
