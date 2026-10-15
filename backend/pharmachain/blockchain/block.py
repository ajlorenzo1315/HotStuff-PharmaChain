import hashlib
import json

from dataclasses import dataclass
from typing import Any

from pharmachain.domain.transactions import Transaction


GENESIS_PARENT = "0" * 64


def canonical_json(data: Any) -> bytes:
    return json.dumps(
        data,
        sort_keys=True,
        separators=(",", ":"),
        ensure_ascii=False,
    ).encode("utf-8")


@dataclass(frozen=True)
class Block:
    parent_hash: str
    height: int
    view: int
    proposer_id: str
    transactions: tuple[Transaction, ...]

    def payload(self) -> dict:
        return {
            "parent_hash": self.parent_hash,
            "height": self.height,
            "view": self.view,
            "proposer_id": self.proposer_id,
            "transactions": [
                {
                    "payload": tx.payload().hex(),
                    "signature": tx.signature,
                }
                for tx in self.transactions
            ],
        }

    @property
    def block_hash(self) -> str:
        return hashlib.sha256(
            canonical_json(self.payload())
        ).hexdigest()

    @classmethod
    def genesis(cls) -> "Block":
        return cls(
            parent_hash=GENESIS_PARENT,
            height=0,
            view=0,
            proposer_id="GENESIS",
            transactions=(),
        )
