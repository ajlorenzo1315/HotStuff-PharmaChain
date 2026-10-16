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


class HotStuffEngine:
    def __init__(
        self,
        initial_state: LedgerState,
        validator_count: int = 4,
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
        """
        En esta versión, los validadores actualizan su
        bloqueo al observar la cadena certificada.
        """
        block = self.blockchain.get_block(block_hash)

        parent_hash = block.parent_hash
        parent_qc = self.certificates.get(parent_hash)

        if parent_qc is None:
            return

        # Solo se actualiza si el padre está certificado.
        for validator in self.validators:
            if validator.active:
                validator.update_lock(
                    parent_hash,
                    parent_qc.view,
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

        votes = []

        for validator in self.validators:
            safe = self.is_safe(
                validator,
                parent_hash,
            )

            vote = validator.vote(
                view=current_view,
                block_hash=block_hash,
                safe=safe,
            )

            if vote is not None:
                votes.append(vote)

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

                self._update_locks(block_hash)
                committed = self._try_commit(block_hash)

        self.view += 1

        return RoundResult(
            view=current_view,
            leader=leader.validator_id,
            block_hash=block_hash,
            votes=len(votes),
            qc_formed=qc_formed,
            committed=committed,
        )
