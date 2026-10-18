"""Regression tests for bounded HotStuff block ancestry transfer."""

from dataclasses import replace

from pharmachain.blockchain.block import Block
from pharmachain.consensus.sync import BlockResponse, ancestry, validate_response


def sample_chain():
    genesis = Block.genesis()
    b1 = Block(genesis.block_hash, 1, 1, "validator-0", ())
    b2 = Block(b1.block_hash, 2, 2, "validator-1", ())
    return genesis, b1, b2


def test_valid_ancestry():
    genesis, b1, b2 = sample_chain()
    path = ancestry({b.block_hash: b for b in (genesis, b1, b2)}, b2.block_hash)
    assert path == (b1, b2)
    assert validate_response(
        BlockResponse(b2.block_hash, path), b2.block_hash, genesis.block_hash
    )


def test_missing_parent_rejected():
    _, _, b2 = sample_chain()
    try:
        ancestry({b2.block_hash: b2}, b2.block_hash)
    except ValueError as exc:
        assert "Missing ancestor" in str(exc)
    else:
        raise AssertionError("Missing ancestor accepted")


def test_tampered_block_rejected():
    genesis, b1, b2 = sample_chain()
    altered = replace(b1, proposer_id="attacker")
    response = BlockResponse(b2.block_hash, (altered, b2))
    assert not validate_response(response, b2.block_hash, genesis.block_hash)


def test_wrong_target_rejected():
    genesis, b1, b2 = sample_chain()
    response = BlockResponse(b2.block_hash, (b1, b2))
    assert not validate_response(response, b1.block_hash, genesis.block_hash)


def test_size_limit():
    genesis, b1, b2 = sample_chain()
    try:
        ancestry({b.block_hash: b for b in (genesis, b1, b2)}, b2.block_hash, limit=1)
    except ValueError as exc:
        assert "limit" in str(exc)
    else:
        raise AssertionError("Oversized response accepted")
