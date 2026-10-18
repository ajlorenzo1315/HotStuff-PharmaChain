"""Integration tests for genuine network-message equivocation scenario."""

from pharmachain.api.fork_experiment import run_fork_experiment


def test_fork_safety_and_no_double_votes():
    result = run_fork_experiment()
    assert result["passed"], result
    assert result["double_vote_prevented"]
    assert result["safety"]["safe"]
    assert not result["qc_formed_in_attack_view"]


def test_fork_branches_are_distinct():
    result = run_fork_experiment()
    assert result["branches"]["A"]["hash"] != result["branches"]["B"]["hash"]
    assert result["branches"]["A"]["parent"] != result["branches"]["B"]["parent"]


def test_attack_uses_actual_vote_messages():
    result = run_fork_experiment()
    assert any(
        event["event"] == "VOTE_CREATED" and event.get("view") == result["view"]
        for event in result["events"]
    )
