"""Bounded block ancestry synchronization messages for the educational simulator."""

from __future__ import annotations

from dataclasses import dataclass

from pharmachain.blockchain.block import Block


@dataclass(frozen=True)
class BlockRequest:
    target_hash: str
    max_blocks: int = 64


@dataclass(frozen=True)
class BlockResponse:
    target_hash: str
    blocks: tuple[Block, ...]  # oldest ancestor first, target last


def ancestry(
    blocks: dict[str, Block], target_hash: str, limit: int = 64
) -> tuple[Block, ...]:
    """Return genesis-excluded ancestry; reject unknown or oversized paths."""
    if not 1 <= limit <= 256:
        raise ValueError("Invalid ancestry limit")
    result: list[Block] = []
    seen: set[str] = set()
    current = target_hash
    while current in blocks:
        if current in seen:
            raise ValueError("Cyclic ancestry")
        seen.add(current)
        block = blocks[current]
        if block.height == 0:
            return tuple(reversed(result))
        result.append(block)
        if len(result) > limit:
            raise ValueError("Ancestry exceeds limit")
        current = block.parent_hash
    raise ValueError("Missing ancestor")


def validate_response(
    response: BlockResponse, expected_hash: str, genesis_hash: str, max_blocks: int = 64
) -> bool:
    """Check structure only; caller must validate blocks against its local ledger."""
    blocks = response.blocks
    if response.target_hash != expected_hash or not 1 <= len(blocks) <= max_blocks:
        return False
    if blocks[-1].block_hash != expected_hash:
        return False
    previous = genesis_hash
    previous_view = 0
    for index, block in enumerate(blocks):
        if block.parent_hash != previous or block.height != index + 1:
            return False
        if block.view <= previous_view:
            return False
        previous, previous_view = block.block_hash, block.view
    return True
