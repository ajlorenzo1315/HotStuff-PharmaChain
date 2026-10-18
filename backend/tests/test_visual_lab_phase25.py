"""Phase 25: ensure analysis is conservative and reproducible."""

from pharmachain.api.visual_lab import analyze_trace, build_attack_trace, normalize_events


def test_metrics_from_actual_events():
    events = normalize_events(
        [
            {"event": "VOTE_CREATED", "node": "validator-1", "view": 2, "time": 1},
            {"event": "QC_FORMED", "sender": "validator-0", "recipient": "validator-2", "view": 2, "time": 2.5},
            {"event": "INVALID_VOTE", "node": "validator-3", "view": 3, "time": 3},
        ]
    )
    metrics = analyze_trace(events)
    assert metrics["recorded_events"] == 3
    assert metrics["recorded_transmissions"] == 1
    assert metrics["observed_views"] == 2
    assert metrics["observed_time_span"] == 2
    assert metrics["types"] == {"QC": 1, "REJECT": 1, "VOTE": 1}
    assert events[0]["explanation"]


def test_empty_trace_has_no_invented_metrics():
    metrics = analyze_trace([])
    assert metrics["recorded_events"] == 0
    assert metrics["transmission_coverage_pct"] is None
    assert metrics["observed_time_span"] is None


def test_attack_trace_contains_analysis():
    trace = build_attack_trace("forged_qc", {"passed": True, "events": [{"event": "INVALID_QC"}]})
    assert trace["analysis"]["recorded_events"] == 1
    assert trace["events"][0]["type"] == "REJECT"
