from pharmachain.consensus.engine import HotStuffEngine
from pharmachain.domain.state import LedgerState


def make_engine():
    return HotStuffEngine(
        initial_state=LedgerState({}),
        validator_count=4,
    )


def test_quorum_not_reached_does_not_crash():
    engine = make_engine()

    engine.validators[2].active = False
    engine.validators[3].active = False

    result = engine.run_round()

    assert result.votes == 2
    assert not result.qc_formed
    assert result.committed == ()

    assert any(event["type"] == "QUORUM_NOT_REACHED" for event in engine.event_history)


def test_one_offline_validator_still_forms_qc():
    engine = make_engine()

    engine.validators[3].active = False

    result = engine.run_round()

    assert result.votes == 3
    assert result.qc_formed


def test_no_lock_without_parent_qc():
    engine = make_engine()

    result = engine.run_round()

    assert result.qc_formed

    # El primer bloque tiene como padre al génesis.
    # No existe un QC del génesis en este modelo.
    assert all(validator.locked_view == 0 for validator in engine.validators)


def test_three_successful_rounds_commit():
    engine = make_engine()

    results = [engine.run_round() for _ in range(3)]

    assert all(result.qc_formed for result in results)
    assert engine.blockchain.committed_height == 1

    assert any(event["type"] == "BLOCK_COMMITTED" for event in engine.event_history)


def test_events_are_recorded():
    engine = make_engine()

    engine.run_round()

    event_types = {event["type"] for event in engine.event_history}

    assert "NEW_VIEW" in event_types
    assert "BLOCK_PROPOSED" in event_types
    assert "VOTE_CAST" in event_types
    assert "QC_FORMED" in event_types
