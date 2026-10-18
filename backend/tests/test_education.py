import pytest

from pharmachain.api.education import GUIDED_SCENARIOS, get_guide
from pharmachain.api.visual_lab import analyze_trace


def test_all_nine_guides():
    assert len(GUIDED_SCENARIOS) == 9
    for scenario in GUIDED_SCENARIOS:
        guide = get_guide(scenario)
        assert len(guide["steps"]) >= 5
        assert guide["objective"] and guide["expected"] and guide["evidence"]


def test_unknown_guide():
    with pytest.raises(ValueError):
        get_guide("missing")


def test_extended_trace_metrics():
    events = [
        {"type": "VOTE", "name": "VOTE_RECEIVED", "source": "validator-1", "target": "validator-0", "view": 1, "time": 1.0},
        {"type": "REJECT", "name": "INVALID_VOTE", "source": "validator-2", "target": "validator-0", "view": 1, "time": 2.0},
        {"type": "QC", "name": "QC_FORMED", "view": 1, "time": 3.0},
    ]
    metrics = analyze_trace(events)
    assert metrics["recorded_events"] == 3
    assert metrics["vote_events"] == 1
    assert metrics["rejection_events"] == 1
    assert metrics["qc_related_events"] == 1
    assert metrics["event_type_diversity"] == 3
    assert metrics["trace_limited_to_300"] is False
