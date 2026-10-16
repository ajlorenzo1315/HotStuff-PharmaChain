"""Tests for the existing HotStuff validator."""

from pharmachain.consensus.validator import Validator


def test_validator_votes_once_per_view():
    validator = Validator.create("validator-test")

    first_vote = validator.vote(
        1,
        "block-a",
        safe=True,
    )

    second_vote = validator.vote(
        1,
        "block-b",
        safe=True,
    )

    assert first_vote is not None
    assert second_vote is None


def test_validator_rejects_unsafe_proposal():
    validator = Validator.create("validator-test")

    vote = validator.vote(
        1,
        "block-a",
        safe=False,
    )

    assert vote is None
    assert validator.voted_views == set()


def test_validator_lock_never_moves_backwards():
    validator = Validator.create("validator-test")

    validator.update_lock("block-b", 2)
    validator.update_lock("block-a", 1)

    assert validator.locked_block_hash == "block-b"
    assert validator.locked_view == 2
