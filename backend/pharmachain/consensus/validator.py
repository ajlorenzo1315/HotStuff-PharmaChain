from dataclasses import dataclass, field

from pharmachain.consensus.messages import Vote
from pharmachain.domain.crypto import generate_keypair


@dataclass
class Validator:
    validator_id: str
    private_key: str
    public_key: str
    active: bool = True
    voted_views: set[int] = field(default_factory=set)
    locked_block_hash: str | None = None
    locked_view: int = 0

    @classmethod
    def create(cls, validator_id: str) -> "Validator":
        private_key, public_key = generate_keypair()

        return cls(
            validator_id=validator_id,
            private_key=private_key,
            public_key=public_key,
        )

    def vote(
        self,
        view: int,
        block_hash: str,
        safe: bool,
    ) -> Vote | None:
        if not self.active:
            return None

        if view in self.voted_views:
            return None

        if not safe:
            return None

        vote = Vote.create(
            validator_id=self.validator_id,
            private_key=self.private_key,
            view=view,
            block_hash=block_hash,
        )

        self.voted_views.add(view)

        return vote

    def update_lock(
        self,
        block_hash: str,
        view: int,
    ) -> None:
        if view > self.locked_view:
            self.locked_block_hash = block_hash
            self.locked_view = view
