from collections import deque

from pharmachain.blockchain.chain import (
    Blockchain,
    BlockchainError,
)
from pharmachain.domain.state import LedgerState
from pharmachain.domain.transactions import Transaction
from pharmachain.engines.events import (
    ConsensusEvent,
    EventType,
)
from pharmachain.engines.interface import EngineCapabilities


class EducationalHotStuffAdapter:
    name = "educational-hotstuff"

    capabilities = EngineCapabilities(
        step_by_step=True,
        internal_votes=False,
        byzantine_faults=False,
        adaptive_pacemaker=False,
        real_network=False,
        smart_contracts=False,
    )

    def __init__(self, initial_state: LedgerState):
        self.initial_state = initial_state.clone()
        self.reset()

    def reset(self) -> None:
        self.blockchain = Blockchain(self.initial_state)
        self.pending = deque()
        self.events = []
        self.view = 1

    def _event(
        self,
        event_type: EventType,
        message: str,
        block_hash: str | None = None,
        **details,
    ) -> ConsensusEvent:
        event = ConsensusEvent(
            event_type=event_type,
            engine=self.name,
            view=self.view,
            block_hash=block_hash,
            validator_id=None,
            message=message,
            details=details,
        )
        self.events.append(event)
        return event

    def submit(self, tx: Transaction) -> str:
        # Validación preliminar sobre el estado confirmado.
        # No sustituye la validación al construir el bloque.
        self.blockchain.committed_state.apply(tx)

        self.pending.append(tx)

        self._event(
            EventType.TRANSACTION_RECEIVED,
            "Transaction received",
            transaction_id=tx.tx_id,
        )

        return tx.tx_id

    def step(self) -> list[ConsensusEvent]:
        if not self.pending:
            return []

        tx = self.pending.popleft()

        # Usamos el estado confirmado como base en esta etapa.
        parent_hash = self.blockchain.committed_tip

        block = self.blockchain.create_block(
            parent_hash=parent_hash,
            view=self.view,
            proposer_id="validator-0",
            transactions=[tx],
        )

        try:
            block_hash = self.blockchain.add_block(block)

        except BlockchainError as exc:
            return [
                self._event(
                    EventType.TRANSACTION_REJECTED,
                    str(exc),
                    transaction_id=tx.tx_id,
                )
            ]

        proposed = self._event(
            EventType.BLOCK_PROPOSED,
            "Leader proposed a new block",
            block_hash,
            transaction_id=tx.tx_id,
            height=block.height,
        )

        validated = self._event(
            EventType.BLOCK_VALIDATED,
            "Block passed application validation",
            block_hash,
        )

        self.view += 1

        return [proposed, validated]

    def snapshot(self) -> dict:
        state = self.blockchain.committed_state

        return {
            "engine": self.name,
            "view": self.view,
            "pending_transactions": len(self.pending),
            "known_blocks": len(self.blockchain.blocks),
            "committed_height": self.blockchain.committed_height,
            "batches": {
                batch_id: {
                    "medicine": batch.medicine_name,
                    "quantity": batch.quantity,
                    "custodian": batch.custodian_id,
                }
                for batch_id, batch in state.batches.items()
            },
            "capabilities": vars(self.capabilities),
        }
