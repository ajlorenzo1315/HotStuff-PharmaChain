"""Local pharmaceutical demo backed by HotStuffEngine."""

from __future__ import annotations

from pharmachain.consensus.engine import HotStuffEngine
from pharmachain.domain.crypto import generate_keypair
from pharmachain.domain.models import (
    Organization,
    OrganizationRole,
    TransactionType,
)
from pharmachain.domain.state import LedgerState
from pharmachain.domain.transactions import Transaction


class PharmaService:
    def __init__(self) -> None:
        roles = {
            "laboratory": OrganizationRole.MANUFACTURER,
            "distributor": OrganizationRole.DISTRIBUTOR,
            "hospital": OrganizationRole.HOSPITAL,
            "regulator": OrganizationRole.REGULATOR,
        }

        self.private_keys: dict[str, str] = {}
        organizations: dict[str, Organization] = {}

        for org_id, role in roles.items():
            private_key, public_key = generate_keypair()
            self.private_keys[org_id] = private_key

            organizations[org_id] = Organization(
                organization_id=org_id,
                name=org_id.title(),
                role=role,
                public_key=public_key,
            )

        self.engine = HotStuffEngine(
            initial_state=LedgerState(organizations),
            validator_count=4,
        )

    def status(self) -> dict:
        engine = self.engine
        return {
            "view": engine.view,
            "leader": engine.leader().validator_id,
            "validators": len(engine.validators),
            "quorum": engine.quorum,
            "committed_height": engine.blockchain.committed_height,
            "certificates": len(engine.certificates),
            "mode": "centralized-educational",
        }

    def batches(self) -> list[dict]:
        state = self.engine.blockchain.committed_state

        return [
            {
                "batch_id": batch.batch_id,
                "medicine_name": batch.medicine_name,
                "quantity": batch.quantity,
                "manufacturer_id": batch.manufacturer_id,
                "custodian_id": batch.custodian_id,
            }
            for batch in state.batches.values()
        ]

    def blocks(self) -> list[dict]:
        chain = self.engine.blockchain
        result = []

        for block_hash in chain.committed:
            block = chain.get_block(block_hash)

            result.append(
                {
                    "hash": block_hash,
                    "height": block.height,
                    "view": block.view,
                    "proposer": block.proposer_id,
                    "parent_hash": block.parent_hash,
                    "transactions": [
                        {
                            "tx_id": tx.tx_id,
                            "type": tx.tx_type.value,
                            "batch_id": tx.batch_id,
                            "sender": tx.sender_id,
                            "receiver": tx.receiver_id,
                        }
                        for tx in block.transactions
                    ],
                }
            )

        return result

    def events(self) -> list[dict]:
        return list(getattr(self.engine, "event_history", []))

    def _next_nonce(self, sender_id: str) -> int:
        state = self.engine.blockchain.committed_state
        return state.nonces.get(sender_id, 0) + 1

    def _commit_transaction(
        self,
        tx: Transaction,
    ) -> dict:
        engine = self.engine

        # Prevalidate before adding the proposal to the chain.
        engine.blockchain.committed_state.apply(tx)

        first = engine.run_round([tx])

        if not first.qc_formed or first.block_hash is None:
            raise RuntimeError("No QC for transaction block")

        # In this educational engine, three certified
        # consecutive blocks trigger the commit rule.
        for _ in range(2):
            result = engine.run_round()

            if not result.qc_formed:
                raise RuntimeError("Consensus did not reach quorum")

        if not engine.blockchain.is_committed(first.block_hash):
            raise RuntimeError("Transaction block not committed")

        return {
            "tx_id": tx.tx_id,
            "block_hash": first.block_hash,
            "committed": True,
            "committed_height": (engine.blockchain.committed_height),
        }

    def register_batch(
        self,
        batch_id: str,
        medicine_name: str,
        quantity: int,
    ) -> dict:
        tx = Transaction(
            tx_type=TransactionType.REGISTER_BATCH,
            sender_id="laboratory",
            batch_id=batch_id,
            receiver_id=None,
            medicine_name=medicine_name,
            quantity=quantity,
            nonce=self._next_nonce("laboratory"),
        ).signed(self.private_keys["laboratory"])

        return self._commit_transaction(tx)

    def transfer_batch(
        self,
        batch_id: str,
        sender_id: str,
        receiver_id: str,
    ) -> dict:
        if sender_id not in self.private_keys:
            raise ValueError("Unknown demo sender")

        tx = Transaction(
            tx_type=TransactionType.TRANSFER_BATCH,
            sender_id=sender_id,
            batch_id=batch_id,
            receiver_id=receiver_id,
            medicine_name=None,
            quantity=None,
            nonce=self._next_nonce(sender_id),
        ).signed(self.private_keys[sender_id])

        return self._commit_transaction(tx)
