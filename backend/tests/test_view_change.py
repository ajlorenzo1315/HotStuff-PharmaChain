"""Signed timeout and view-change tests."""

from dataclasses import replace

from pharmachain.consensus.distributed import DistributedHotStuff
from pharmachain.consensus.view_change import SignedTimeout, TimeoutCertificate
from pharmachain.domain.state import LedgerState


def make():
    return DistributedHotStuff(LedgerState({}), validator_count=4)


def test_signed_timeout_and_tampering():
    sim = make()
    v = sim.nodes["validator-0"].node.validator
    notice = SignedTimeout.create(v.validator_id, v.private_key, 1)
    assert notice.verify(sim.public_keys)
    assert not replace(notice, view=2).verify(sim.public_keys)
    assert not replace(notice, signature="00").verify(sim.public_keys)


def test_tc_rejects_duplicate_signers():
    sim = make()
    v = sim.nodes["validator-0"].node.validator
    notice = SignedTimeout.create(v.validator_id, v.private_key, 1)
    assert not TimeoutCertificate(1, (notice, notice, notice)).verify(
        sim.public_keys, 3
    )


def test_offline_leader_triggers_signed_view_change():
    sim = make()
    sim.network.disconnect("validator-0")
    first = sim.run_round()
    assert not first.qc_formed
    assert sim.view == 2
    assert sim.nodes["validator-0"].node.view == 1
    assert all(sim.nodes[f"validator-{i}"].node.view == 2 for i in (1, 2, 3))
    assert any(e["event"] == "TC_FORMED" for e in sim.events)
    second = sim.run_round()
    assert second.leader == "validator-1"
    assert second.qc_formed
    assert second.votes == 3


def test_two_offline_no_tc():
    sim = make()
    sim.network.disconnect("validator-0")
    sim.network.disconnect("validator-2")
    result = sim.run_round()
    assert not result.qc_formed
    assert sim.view == 1
    assert not any(e["event"] == "TC_FORMED" for e in sim.events)


def test_ideal_network_still_commits():
    sim = make()
    for _ in range(3):
        assert sim.run_round().qc_formed
    assert all(r.node.committed_height == 1 for r in sim.nodes.values())
