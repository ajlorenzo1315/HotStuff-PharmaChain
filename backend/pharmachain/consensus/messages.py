from dataclasses import dataclass

from pharmachain.domain.crypto import (
    sign_message,
    verify_signature,
)


def vote_payload(view: int, block_hash: str) -> bytes:
    return f"HOTSTUFF_VOTE_V1:{view}:{block_hash}".encode()


@dataclass(frozen=True)
class Vote:
    validator_id: str
    view: int
    block_hash: str
    signature: str

    @classmethod
    def create(
        cls,
        validator_id: str,
        private_key: str,
        view: int,
        block_hash: str,
    ) -> "Vote":
        signature = sign_message(
            private_key,
            vote_payload(view, block_hash),
        )
        return cls(
            validator_id,
            view,
            block_hash,
            signature,
        )

    def verify(self, public_key: str) -> bool:
        return verify_signature(
            public_key,
            vote_payload(self.view, self.block_hash),
            self.signature,
        )


@dataclass(frozen=True)
class QuorumCertificate:
    view: int
    block_hash: str
    votes: tuple[Vote, ...]

    def verify(
        self,
        public_keys: dict[str, str],
        quorum: int,
    ) -> bool:
        if len(self.votes) < quorum:
            return False

        seen = set()

        for vote in self.votes:
            if vote.validator_id in seen:
                return False

            seen.add(vote.validator_id)

            if vote.view != self.view:
                return False

            if vote.block_hash != self.block_hash:
                return False

            public_key = public_keys.get(vote.validator_id)

            if public_key is None:
                return False

            if not vote.verify(public_key):
                return False

        return True
