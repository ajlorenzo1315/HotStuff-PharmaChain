from dataclasses import replace

import pytest

from pharmachain.consensus.messages import QuorumCertificate, Vote
from pharmachain.consensus.new_view import NewView, NewViewCollector
from pharmachain.domain.crypto import generate_keypair


def validators():
    pairs = {f"validator-{i}": generate_keypair() for i in range(4)}
    private = {name: pair[0] for name, pair in pairs.items()}
    public = {name: pair[1] for name, pair in pairs.items()}
    return private, public


def qc_for(private, view, block_hash):
    votes = tuple(
        Vote.create(name, private[name], view, block_hash) for name in list(private)[:3]
    )
    return QuorumCertificate(view, block_hash, votes)


def test_valid_signed_new_view():
    private, public = validators()
    qc = qc_for(private, 1, "block-1")
    msg = NewView.create("validator-0", private["validator-0"], 2, qc)
    assert msg.verify(public, 3)


def test_tampered_view_and_qc_are_rejected():
    private, public = validators()
    qc = qc_for(private, 1, "block-1")
    msg = NewView.create("validator-0", private["validator-0"], 3, qc)
    assert not replace(msg, view=4).verify(public, 3)
    assert not replace(msg, high_qc=qc_for(private, 2, "block-2")).verify(public, 3)


def test_invalid_qc_is_rejected():
    private, public = validators()
    bad_qc = QuorumCertificate(
        1, "block", (Vote.create("validator-0", private["validator-0"], 1, "block"),)
    )
    msg = NewView.create("validator-0", private["validator-0"], 2, bad_qc)
    assert not msg.verify(public, 3)


def test_collector_requires_three_distinct_validators():
    private, public = validators()
    collector = NewViewCollector(2, public, 3)
    for name in list(private)[:2]:
        assert collector.add(NewView.create(name, private[name], 2, None))
    assert not collector.ready
    duplicate = NewView.create("validator-0", private["validator-0"], 2, None)
    assert not collector.add(duplicate)
    with pytest.raises(RuntimeError):
        collector.highest_qc()
    assert collector.add(NewView.create("validator-2", private["validator-2"], 2, None))
    assert collector.ready
    assert collector.highest_qc() is None


def test_highest_qc_selected():
    private, public = validators()
    collector = NewViewCollector(4, public, 3)
    qcs = [qc_for(private, 1, "a"), qc_for(private, 2, "b"), qc_for(private, 3, "c")]
    for name, qc in zip(list(private)[:3], qcs, strict=False):
        assert collector.add(NewView.create(name, private[name], 4, qc))
    assert collector.highest_qc() == qcs[-1]


def test_old_view_rejected():
    private, public = validators()
    collector = NewViewCollector(3, public, 3)
    msg = NewView.create("validator-0", private["validator-0"], 2, None)
    assert not collector.add(msg)
