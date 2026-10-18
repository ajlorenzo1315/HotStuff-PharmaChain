from pharmachain.consensus.engine import HotStuffEngine
from pharmachain.domain.state import LedgerState


def test_events_are_generated():
    engine = HotStuffEngine(LedgerState({}))

    result = engine.run_round()

    event_types = [event["type"] for event in engine.event_history]

    assert result.qc_formed

    assert "NEW_VIEW" in event_types
    assert "BLOCK_PROPOSED" in event_types
    assert "VOTE_CAST" in event_types
    assert "QC_FORMED" in event_types


def test_three_chain_emits_commit():
    engine = HotStuffEngine(LedgerState({}))

    for _ in range(3):
        engine.run_round()

    commits = [
        event for event in engine.event_history if event["type"] == "BLOCK_COMMITTED"
    ]

    assert len(commits) == 1
    assert engine.blockchain.committed_height == 1


def test_inactive_leader_emits_timeout():
    engine = HotStuffEngine(LedgerState({}))

    engine.validators[0].active = False

    engine.run_round()

    assert any(event["type"] == "TIMEOUT" for event in engine.event_history)


def test_callback_receives_events():
    received = []

    engine = HotStuffEngine(
        LedgerState({}),
        on_event=received.append,
    )

    engine.run_round()

    assert received == engine.event_history


def test_no_quorum_event():
    engine = HotStuffEngine(LedgerState({}))

    engine.validators[2].active = False
    engine.validators[3].active = False

    engine.run_round()

    assert any(event["type"] == "QUORUM_NOT_REACHED" for event in engine.event_history)
