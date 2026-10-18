import pytest

from pharmachain.api.byzantine_benchmark import (
    export_results,
    run_comparison,
    run_scenario,
)


@pytest.mark.parametrize(
    "mode",
    [
        "omit",
        "invalid_signature",
    ],
)
def test_without_faults(mode):
    result = run_scenario(
        mode=mode,
        faulty_nodes=0,
        rounds=4,
    )

    assert result.qc_count >= 1
    assert result.safe


def test_two_omitting_validators_prevent_qc():
    result = run_scenario(
        mode="omit",
        faulty_nodes=2,
        rounds=4,
    )

    assert result.qc_count == 0
    assert result.omitted_votes > 0


def test_invalid_signatures_are_rejected():
    result = run_scenario(
        mode="invalid_signature",
        faulty_nodes=1,
        rounds=4,
    )

    assert result.invalid_votes > 0
    assert result.safe


def test_comparison_has_three_scenarios():
    results = run_comparison(
        mode="omit",
        rounds=4,
    )

    assert len(results) == 3
    assert [r.faulty_nodes for r in results] == [0, 1, 2]


def test_export(tmp_path):
    results = run_comparison(
        mode="omit",
        rounds=4,
    )

    export_results(results, tmp_path)

    assert (tmp_path / "comparison.csv").exists()
    assert (tmp_path / "comparison.json").exists()


@pytest.mark.parametrize(
    "mode",
    [
        "unknown",
        "",
    ],
)
def test_invalid_mode(mode):
    with pytest.raises(ValueError):
        run_scenario(mode, faulty_nodes=1)


def test_invalid_fault_count():
    with pytest.raises(ValueError):
        run_scenario("omit", faulty_nodes=3)
