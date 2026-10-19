"""Tests for phase 19 availability comparison."""

import pytest

from pharmachain.api.benchmark import run_benchmark


def test_three_isolated_scenarios():
    result = run_benchmark(rounds=8)
    assert [x["offline_count"] for x in result["scenarios"]] == [0, 1, 2]
    assert all(x["quorum"] == 3 for x in result["scenarios"])
    assert all(len(x["round_details"]) == 8 for x in result["scenarios"])


def test_no_qc_with_only_two_online():
    result = run_benchmark(rounds=8)
    scenario = result["scenarios"][2]
    assert scenario["qc_rounds"] == 0
    assert scenario["max_committed_height"] == 0


def test_deterministic_seed():
    first = run_benchmark(rounds=5, seed=123)
    second = run_benchmark(rounds=5, seed=123)
    assert first["scenarios"] == second["scenarios"]


@pytest.mark.parametrize("rounds", [0, 101, True, 1.5])
def test_reject_bad_round_counts(rounds):
    with pytest.raises(ValueError):
        run_benchmark(rounds=rounds)
