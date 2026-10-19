from types import SimpleNamespace

from pharmachain.blockchain.block import Block
from pharmachain.consensus.safety import (
    audit_committed_safety,
    committed_prefix,
    demonstrate_conflict_detection,
)


def fake_node(blocks, tip, committed):
    chain = SimpleNamespace(blocks=blocks, committed_tip=tip, committed=committed)
    return SimpleNamespace(node=SimpleNamespace(blockchain=chain))


def test_genesis_only_is_safe():
    genesis = Block.genesis()
    sim = SimpleNamespace(nodes={"a": fake_node({genesis.block_hash: genesis}, genesis.block_hash, [genesis.block_hash])})
    assert audit_committed_safety(sim)["safe"]


def test_committed_prefixes_at_different_heights_are_safe():
    g = Block.genesis()
    a = Block(g.block_hash, 1, 1, "validator-0", ())
    b = Block(a.block_hash, 2, 2, "validator-1", ())
    blocks = {x.block_hash: x for x in (g, a, b)}
    sim = SimpleNamespace(
        nodes={
            "a": fake_node(blocks, a.block_hash, [g.block_hash, a.block_hash]),
            "b": fake_node(blocks, b.block_hash, [g.block_hash, a.block_hash, b.block_hash]),
        }
    )
    assert audit_committed_safety(sim)["safe"]


def test_conflicting_commits_are_detected():
    result = demonstrate_conflict_detection()
    assert result["injected_conflict_detected"]
    assert result["audit"]["conflicts"][0]["height"] == 1


def test_broken_ancestry_is_rejected():
    g = Block.genesis()
    b = Block("f" * 64, 1, 1, "validator-0", ())
    try:
        committed_prefix({g.block_hash: g, b.block_hash: b}, b.block_hash)
    except ValueError as exc:
        assert "ancestry" in str(exc)
    else:
        raise AssertionError("missing parent was accepted")


def test_mismatched_committed_list_is_detected():
    g = Block.genesis()
    b = Block(g.block_hash, 1, 1, "validator-0", ())
    sim = SimpleNamespace(nodes={"a": fake_node({g.block_hash: g, b.block_hash: b}, b.block_hash, [g.block_hash])})
    assert not audit_committed_safety(sim)["safe"]
