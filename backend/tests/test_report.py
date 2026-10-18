"""Tests for report aggregation and exports, without requiring a live HTTP server."""

import csv
import io
import sys
from types import ModuleType

import pytest

from pharmachain.api.report import collect_report, report_csv, report_svg, save_report


def fake_benchmark(*, rounds, seed):
    return {
        "scenarios": [
            {
                "id": f"offline_{i}",
                "offline_count": i,
                "online_count": 4 - i,
                "qc_rounds": (rounds if i == 0 else rounds // 2 if i == 1 else 0),
                "max_committed_height": max(0, rounds - i * 3),
                "simulated_time": seed / 100,
                "safety": {"safe": True},
            }
            for i in range(3)
        ]
    }


@pytest.fixture(autouse=True)
def mock_benchmark(monkeypatch):
    module = ModuleType("pharmachain.api.benchmark")
    module.run_benchmark = fake_benchmark
    monkeypatch.setitem(sys.modules, "pharmachain.api.benchmark", module)


def test_aggregate_seeds_and_scenarios():
    report = collect_report(runs=3, rounds=12, start_seed=42)
    assert len(report["rows"]) == 9
    assert [s["mean_qc_rate"] for s in report["summary"]] == [1.0, 0.5, 0.0]
    assert all(s["all_safe"] for s in report["summary"])
    assert {r["seed"] for r in report["rows"]} == {42, 43, 44}


def test_csv_and_svg(tmp_path):
    report = collect_report(runs=2, rounds=8)
    records = list(csv.DictReader(io.StringIO(report_csv(report))))
    assert len(records) == 6
    assert records[0]["scenario"] == "offline_0"
    assert "<svg" in report_svg(report)
    paths = save_report(report, tmp_path / "report")
    assert all(path.is_file() for path in paths)


@pytest.mark.parametrize(
    "kwargs", [{"runs": 0}, {"runs": True}, {"runs": 101}, {"rounds": 0}, {"rounds": 101}, {"start_seed": 1.5}]
)
def test_invalid_parameters(kwargs):
    with pytest.raises(ValueError):
        collect_report(**kwargs)
