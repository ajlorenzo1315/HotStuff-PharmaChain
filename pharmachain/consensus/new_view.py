"""Authenticated NEW_VIEW messages and deterministic high-QC selection."""

from __future__ import annotations

import hashlib
import json
from dataclasses import dataclass

from pharmachain.consensus.messages import QuorumCertificate
from pharmachain.domain.crypto import sign_message, verify_signature


def qc_fingerprint(qc: QuorumCertificate | None) -> str:
    """Bind a NEW_VIEW signature to all QC fields and vote signatures."""
    if qc is None:
        return "GENESIS"
    data = {
        "view": qc.view,
        "block_hash": qc.block_hash,
        "votes": sorted((vote.validator_id, vote.view, vote.block_hash, vote.signature) for vote in qc.votes),
    }
    payload = json.dumps(data, sort_keys=True, separators=(",", ":")).encode()
    return hashlib.sha256(payload).hexdigest()


def new_view_payload(view: int, high_qc: QuorumCertificate | None) -> bytes:
    return f"HOTSTUFF_NEW_VIEW_V1:{view}:{qc_fingerprint(high_qc)}".encode()


@dataclass(frozen=True)
class NewView:
    validator_id: str
    view: int
    high_qc: QuorumCertificate | None
    signature: str

    @classmethod
    def create(
        cls,
        validator_id: str,
        private_key: str,
        view: int,
        high_qc: QuorumCertificate | None,
    ) -> NewView:
        if view < 1:
            raise ValueError("View must be positive")
        if high_qc is not None and high_qc.view >= view:
            raise ValueError("High QC must precede the new view")
        return cls(
            validator_id=validator_id,
            view=view,
            high_qc=high_qc,
            signature=sign_message(private_key, new_view_payload(view, high_qc)),
        )

    def verify(self, public_keys: dict[str, str], quorum: int) -> bool:
        key = public_keys.get(self.validator_id)
        if key is None or self.view < 1:
            return False
        if self.high_qc is not None:
            if self.high_qc.view >= self.view:
                return False
            if not self.high_qc.verify(public_keys, quorum):
                return False
        return verify_signature(
            key,
            new_view_payload(self.view, self.high_qc),
            self.signature,
        )


class NewViewCollector:
    """Collect distinct valid NEW_VIEW messages for one target view."""

    def __init__(self, view: int, public_keys: dict[str, str], quorum: int):
        if view < 1 or quorum < 1 or quorum > len(public_keys):
            raise ValueError("Invalid view or quorum")
        self.view = view
        self.public_keys = public_keys
        self.quorum = quorum
        self.messages: dict[str, NewView] = {}

    def add(self, message: NewView) -> bool:
        if message.view != self.view:
            return False
        if message.validator_id in self.messages:
            return False
        if not message.verify(self.public_keys, self.quorum):
            return False
        self.messages[message.validator_id] = message
        return True

    @property
    def ready(self) -> bool:
        return len(self.messages) >= self.quorum

    def highest_qc(self) -> QuorumCertificate | None:
        if not self.ready:
            raise RuntimeError("NEW_VIEW quorum not reached")
        qcs = [m.high_qc for m in self.messages.values() if m.high_qc is not None]
        if not qcs:
            return None
        return max(qcs, key=lambda qc: (qc.view, qc.block_hash))
