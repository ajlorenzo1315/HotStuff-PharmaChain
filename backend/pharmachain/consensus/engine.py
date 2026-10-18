from collections.abc import Callable
from dataclasses import dataclass

from pharmachain.blockchain.chain import Blockchain
from pharmachain.consensus.messages import QuorumCertificate
from pharmachain.consensus.validator import Validator
from pharmachain.domain.state import LedgerState
from pharmachain.domain.transactions import Transaction


@dataclass
class RoundResult:
    view: int
    leader: str
    block_hash: str | None
    votes: int
    qc_formed: bool
    committed: tuple[str, ...]


EventCallback = Callable[[dict], None]


class HotStuffEngine:
    def __init__(
        self,
        initial_state: LedgerState,
        validator_count: int = 4,
        on_event: EventCallback | None = None,
    ):
        if validator_count < 4:
            raise ValueError("At least four validators required")

        if (validator_count - 1) % 3 != 0:
            raise ValueError("Use n = 3f + 1 validators")

        self.blockchain = Blockchain(initial_state)

        self.validators = [
            Validator.create(f"validator-{i}") for i in range(validator_count)
        ]

        self.f = (validator_count - 1) // 3
        self.quorum = 2 * self.f + 1

        self.public_keys = {
            validator.validator_id: validator.public_key
            for validator in self.validators
        }

        self.certificates: dict[str, QuorumCertificate] = {}

        self.high_qc: QuorumCertificate | None = None
        self.high_qc_hash = self.blockchain.genesis.block_hash

        self.view = 1
        self.on_event = on_event
        self.event_history: list[dict] = []

    def emit(
        self,
        event_type: str,
        **details: object,
    ) -> None:
        """Record a consensus event and notify the observer."""

        event = {
            "type": event_type,
            "view": self.view,
            **details,
        }

        self.event_history.append(event)

        if self.on_event is not None:
            self.on_event(event)

    def leader(self) -> Validator:
        index = (self.view - 1) % len(self.validators)
        return self.validators[index]

    def is_ancestor(
        self,
        ancestor_hash: str,
        descendant_hash: str,
    ) -> bool:
        current = descendant_hash

        while current in self.blockchain.blocks:
            if current == ancestor_hash:
                return True

            block = self.blockchain.blocks[current]

            if block.height == 0:
                break

            current = block.parent_hash

        return False

    def is_safe(
        self,
        validator: Validator,
        parent_hash: str,
    ) -> bool:
        if validator.locked_block_hash is None:
            return True

        # Primera regla: la propuesta extiende el bloqueo.
        if self.is_ancestor(
            validator.locked_block_hash,
            parent_hash,
        ):
            return True

        # Segunda regla: el QC del padre es más reciente
        # que el QC que estableció el bloqueo.
        parent_qc = self.certificates.get(parent_hash)

        if parent_qc is None:
            return False

        return parent_qc.view > validator.locked_view

    def _update_locks(self, block_hash: str) -> None:
        """Update validator locks when the parent has a QC."""

        block = self.blockchain.get_block(block_hash)

        parent_hash = block.parent_hash

        # Retrieve the certificate of the parent block.
        parent_qc = self.certificates.get(parent_hash)

        if parent_qc is None:
            return

        for validator in self.validators:
            if not validator.active:
                continue

            previous_view = validator.locked_view

            validator.update_lock(
                parent_hash,
                parent_qc.view,
            )

            if validator.locked_view > previous_view:
                self.emit(
                    "LOCK_UPDATED",
                    validator=validator.validator_id,
                    block_hash=validator.locked_block_hash,
                    locked_view=validator.locked_view,
                )

    def _try_commit(self, block_hash: str) -> tuple[str, ...]:
        """
        Regla de commit de tres cadenas certificadas.
        """
        b3 = self.blockchain.get_block(block_hash)

        if b3.height < 3:
            return ()

        b2_hash = b3.parent_hash
        b2 = self.blockchain.get_block(b2_hash)

        b1_hash = b2.parent_hash
        b1 = self.blockchain.get_block(b1_hash)

        if not all(
            block_id in self.certificates for block_id in (b1_hash, b2_hash, block_hash)
        ):
            return ()

        # Exigimos vistas consecutivas para esta
        # implementación inicial.
        if not (b2.view == b1.view + 1 and b3.view == b2.view + 1):
            return ()

        if self.blockchain.is_committed(b1_hash):
            return ()

        committed = self.blockchain.commit(b1_hash)

        return tuple(committed)

    def run_round(
        self,
        transactions: list[Transaction] | None = None,
    ) -> RoundResult:
        transactions = transactions or []

        current_view = self.view
        leader = self.leader()

        self.emit(
            "NEW_VIEW",
            leader=leader.validator_id,
            quorum=self.quorum,
            validator_count=len(self.validators),
        )

        if not leader.active:
            self.view += 1
            return RoundResult(
                current_view,
                leader.validator_id,
                None,
                0,
                False,
                (),
            )

        parent_hash = self.high_qc_hash

        block = self.blockchain.create_block(
            parent_hash=parent_hash,
            view=current_view,
            proposer_id=leader.validator_id,
            transactions=transactions,
        )

        block_hash = self.blockchain.add_block(block)

        self.emit(
            "BLOCK_PROPOSED",
            leader=leader.validator_id,
            block_hash=block_hash,
            parent_hash=parent_hash,
            height=block.height,
            transaction_count=len(block.transactions),
        )

        votes = []

        for validator in self.validators:
            safe = self.is_safe(
                validator,
                parent_hash,
            )

            self.emit(
                "VALIDATE_PROPOSAL",
                validator=validator.validator_id,
                block_hash=block_hash,
                safe=safe,
                active=validator.active,
            )

            vote = validator.vote(
                view=current_view,
                block_hash=block_hash,
                safe=safe,
            )

            if vote is not None:
                votes.append(vote)

                self.emit(
                    "VOTE_CAST",
                    validator=validator.validator_id,
                    block_hash=block_hash,
                    signature=vote.signature,
                    votes_received=len(votes),
                    quorum=self.quorum,
                )

            else:
                if not validator.active:
                    reason = "VALIDATOR_OFFLINE"
                elif current_view in validator.voted_views:
                    reason = "ALREADY_VOTED"
                elif not safe:
                    reason = "UNSAFE_PROPOSAL"
                else:
                    reason = "VOTE_NOT_PRODUCED"

                self.emit(
                    "VOTE_REJECTED",
                    validator=validator.validator_id,
                    block_hash=block_hash,
                    reason=reason,
                )

        qc_formed = False
        committed = ()

        if len(votes) >= self.quorum:
            qc = QuorumCertificate(
                view=current_view,
                block_hash=block_hash,
                votes=tuple(votes),
            )

            if qc.verify(self.public_keys, self.quorum):
                self.certificates[block_hash] = qc
                self.high_qc = qc
                self.high_qc_hash = block_hash

                qc_formed = True

                self.emit(
                    "QC_FORMED",
                    block_hash=block_hash,
                    votes=len(qc.votes),
                    quorum=self.quorum,
                    validators=[vote.validator_id for vote in qc.votes],
                )

                # Actualizar bloqueos solamente
                # a partir de certificados válidos.
                self._update_locks(block_hash)

                # Comprobar la regla de commit.
                committed = self._try_commit(block_hash)

                for committed_hash in committed:
                    committed_block = self.blockchain.get_block(committed_hash)

                    self.emit(
                        "BLOCK_COMMITTED",
                        block_hash=committed_hash,
                        height=committed_block.height,
                        committed_height=(self.blockchain.committed_height),
                    )

        if not qc_formed:
            self.emit(
                "QUORUM_NOT_REACHED",
                block_hash=block_hash,
                votes=len(votes),
                quorum=self.quorum,
            )

        self.view += 1

        return RoundResult(
            view=current_view,
            leader=leader.validator_id,
            block_hash=block_hash,
            votes=len(votes),
            qc_formed=qc_formed,
            committed=committed,
        )
