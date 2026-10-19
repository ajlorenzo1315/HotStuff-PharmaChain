"""Signed timeout messages and verifiable timeout certificates."""

from __future__ import annotations

from dataclasses import dataclass

from pharmachain.domain.crypto import sign_message, verify_signature


def timeout_payload(view: int) -> bytes:
    return f"HOTSTUFF_TIMEOUT_V1:{view}".encode()


@dataclass(frozen=True)
class SignedTimeout:
    validator_id: str
    view: int
    signature: str

    @classmethod
    def create(cls, validator_id: str, private_key: str, view: int):
        if view < 1:
            raise ValueError("View must be positive")
        return cls(validator_id, view, sign_message(private_key, timeout_payload(view)))

    def verify(self, public_keys: dict[str, str]) -> bool:
        key = public_keys.get(self.validator_id)
        return bool(key and self.view > 0 and verify_signature(key, timeout_payload(self.view), self.signature))


@dataclass(frozen=True)
class TimeoutCertificate:
    view: int
    notices: tuple[SignedTimeout, ...]

    def verify(self, public_keys: dict[str, str], quorum: int) -> bool:
        if self.view < 1 or len(self.notices) < quorum:
            return False
        signers = [notice.validator_id for notice in self.notices]
        return len(signers) == len(set(signers)) and all(notice.view == self.view and notice.verify(public_keys) for notice in self.notices)
