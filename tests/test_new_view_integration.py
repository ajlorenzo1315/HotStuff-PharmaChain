"""Integration checks for authenticated NEW_VIEW delivery."""

from pharmachain.consensus.distributed import DistributedHotStuff
from pharmachain.consensus.new_view import NewView
from pharmachain.domain.state import LedgerState
from pharmachain.simulation.network import Envelope


def make_sim():
    return DistributedHotStuff(LedgerState({}), validator_count=4)


def test_normal_round_delivers_new_view_quorum():
    sim = make_sim()
    assert sim.run_round().qc_formed
    collector = sim.nodes["validator-1"].new_views[2]
    assert collector.ready
    assert len(collector.messages) == 4
    assert collector.highest_qc() is not None
    assert sim.run_round().qc_formed


def test_offline_leader_recovers_with_new_view():
    sim = make_sim()
    sim.network.disconnect("validator-0")
    assert not sim.run_round().qc_formed
    assert sim.view == 2
    collector = sim.nodes["validator-1"].new_views[2]
    assert collector.ready
    assert len(collector.messages) == 3
    assert sim.run_round().qc_formed


def test_spoofed_sender_rejected():
    sim = make_sim()
    validator = sim.nodes["validator-2"].node.validator
    msg = NewView.create("validator-2", validator.private_key, 2, None)
    # Call handler directly with a mismatched transport sender.
    sim._on_new_view(
        "validator-1",
        Envelope(
            sender="validator-3",
            recipient="validator-1",
            kind="NEW_VIEW",
            payload=msg,
            message_id=999,
        ),
    )
    assert 2 not in sim.nodes["validator-1"].new_views
