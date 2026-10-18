"""Integration checks for reconnecting a lagging HotStuff validator."""

from pharmachain.consensus.distributed import DistributedHotStuff
from pharmachain.domain.state import LedgerState


def test_rejoin_fetches_missing_block_and_qc():
    sim = DistributedHotStuff(LedgerState({}), validator_count=4)
    sim.network.disconnect("validator-2")

    first = sim.run_round()
    assert first.qc_formed
    assert first.votes == 3
    assert first.block_hash not in sim.nodes["validator-2"].node.blockchain.blocks

    assert sim.reconnect_and_sync("validator-2", source="validator-0")
    recovered = sim.nodes["validator-2"].node
    assert first.block_hash in recovered.blockchain.blocks
    assert first.block_hash in recovered.certificates
    assert recovered.view >= sim.view
    assert any(e["event"] == "NODE_RECOVERED" for e in sim.events)


def test_rejoin_rejects_offline_source():
    sim = DistributedHotStuff(LedgerState({}), validator_count=4)
    sim.network.disconnect("validator-0")
    try:
        sim.reconnect_and_sync("validator-2", source="validator-0")
    except ValueError as exc:
        assert "online" in str(exc)
    else:
        raise AssertionError("An offline sync source was accepted")


def test_no_recovery_from_uncertified_peer():
    sim = DistributedHotStuff(LedgerState({}), validator_count=4)
    assert not sim.reconnect_and_sync("validator-2", source="validator-0")
