"""Read-only committed-prefix safety audit for the teaching HotStuff simulator."""

from __future__ import annotations

from pharmachain.blockchain.block import Block


def committed_prefix(blocks: dict[str, Block], committed_tip: str) -> tuple[str, ...]:
    """Return genesis-to-tip hashes; fail closed on missing links or cycles."""
    path: list[str] = []
    seen: set[str] = set()
    current = committed_tip
    while True:
        if current in seen:
            raise ValueError("cycle in committed ancestry")
        seen.add(current)
        block = blocks.get(current)
        if block is None:
            raise ValueError("missing committed ancestor")
        path.append(current)
        if block.height == 0:
            if block.parent_hash != "0" * 64 or block.block_hash != Block.genesis().block_hash:
                raise ValueError("invalid genesis")
            return tuple(reversed(path))
        parent = blocks.get(block.parent_hash)
        if parent is None or parent.height != block.height - 1 or parent.view >= block.view:
            raise ValueError("invalid committed ancestry")
        current = block.parent_hash


def audit_committed_safety(sim) -> dict:
    """Check that every validator's committed history is a prefix of one chain.

    This is a snapshot invariant, not a formal proof of BFT safety.
    """
    histories: dict[str, tuple[str, ...]] = {}
    errors: list[str] = []
    for node_id, runtime in sim.nodes.items():
        chain = runtime.node.blockchain
        try:
            history = committed_prefix(chain.blocks, chain.committed_tip)
            recorded = tuple(chain.committed)
            if recorded != history:
                errors.append(f"{node_id}: committed list differs from ancestry")
            histories[node_id] = history
        except (ValueError, KeyError) as exc:
            errors.append(f"{node_id}: {exc}")
    ids = sorted(histories)
    conflicts: list[dict] = []
    for i, left_id in enumerate(ids):
        for right_id in ids[i + 1 :]:
            left, right = histories[left_id], histories[right_id]
            shared = min(len(left), len(right))
            if left[:shared] != right[:shared]:
                height = next(j for j in range(shared) if left[j] != right[j])
                conflicts.append({"nodes": [left_id, right_id], "height": height, "blocks": [left[height], right[height]]})
    return {
        "safe": not errors and not conflicts,
        "committed_heights": {nid: len(path) - 1 for nid, path in histories.items()},
        "conflicts": conflicts,
        "errors": errors,
    }


def demonstrate_conflict_detection() -> dict:
    """Deliberately inject incompatible *committed* histories in mock nodes.

    This bypasses consensus to verify that the auditor detects an unsafe state.
    It does NOT demonstrate that HotStuff can reach such a state.
    """
    from types import SimpleNamespace

    genesis = Block.genesis()
    a = Block(genesis.block_hash, 1, 1, "validator-0", ())
    b = Block(genesis.block_hash, 1, 1, "validator-1", ())

    def mock(block):
        chain = SimpleNamespace(
            blocks={genesis.block_hash: genesis, block.block_hash: block},
            committed_tip=block.block_hash,
            committed=[genesis.block_hash, block.block_hash],
        )
        return SimpleNamespace(node=SimpleNamespace(blockchain=chain))

    sim = SimpleNamespace(nodes={"validator-0": mock(a), "validator-1": mock(b)})
    result = audit_committed_safety(sim)
    return {
        "injected_conflict_detected": not result["safe"] and bool(result["conflicts"]),
        "warning": "Conflicto artificial inyectado; no es un ataque exitoso contra HotStuff.",
        "audit": result,
    }
