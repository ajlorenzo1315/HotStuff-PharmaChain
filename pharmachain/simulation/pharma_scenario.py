"""Pharmaceutical traceability demonstration using HotStuff."""

from dataclasses import dataclass

from pharmachain.consensus.engine import HotStuffEngine
from pharmachain.domain.crypto import generate_keypair
from pharmachain.domain.models import (
    Organization,
    OrganizationRole,
    TransactionType,
)
from pharmachain.domain.state import LedgerState
from pharmachain.domain.transactions import Transaction

BATCH_ID = "LOT-2026-001"


@dataclass
class PharmaScenario:
    engine: HotStuffEngine
    private_keys: dict[str, str]

    @classmethod
    def create(cls) -> "PharmaScenario":
        definitions = {
            "laboratory": (
                "PharmaLab",
                OrganizationRole.MANUFACTURER,
            ),
            "distributor": (
                "Medical Logistics",
                OrganizationRole.DISTRIBUTOR,
            ),
            "hospital": (
                "Central Hospital",
                OrganizationRole.HOSPITAL,
            ),
            "regulator": (
                "Medicine Regulator",
                OrganizationRole.REGULATOR,
            ),
        }

        organizations = {}
        private_keys = {}

        for org_id, (name, role) in definitions.items():
            private_key, public_key = generate_keypair()

            private_keys[org_id] = private_key
            organizations[org_id] = Organization(
                organization_id=org_id,
                name=name,
                role=role,
                public_key=public_key,
            )

        return cls(
            engine=HotStuffEngine(
                LedgerState(organizations),
                validator_count=4,
            ),
            private_keys=private_keys,
        )

    def register_batch(self) -> Transaction:
        return Transaction(
            tx_type=TransactionType.REGISTER_BATCH,
            sender_id="laboratory",
            batch_id=BATCH_ID,
            receiver_id=None,
            medicine_name="Amoxicillin 500 mg",
            quantity=100,
            nonce=1,
        ).signed(self.private_keys["laboratory"])

    def transfer(
        self,
        sender: str,
        receiver: str,
        nonce: int,
    ) -> Transaction:
        return Transaction(
            tx_type=TransactionType.TRANSFER_BATCH,
            sender_id=sender,
            batch_id=BATCH_ID,
            receiver_id=receiver,
            medicine_name=None,
            quantity=None,
            nonce=nonce,
        ).signed(self.private_keys[sender])

    def confirm(
        self,
        tx: Transaction,
    ) -> None:
        """Run three successful rounds to commit a new block.

        This helper assumes an ideal network and the existing
        educational HotStuff engine.
        """
        result = self.engine.run_round([tx])

        if not result.qc_formed:
            raise RuntimeError("Transaction block was not certified")

        target_hash = result.block_hash

        for _ in range(2):
            result = self.engine.run_round()

            if not result.qc_formed:
                raise RuntimeError("Follow-up round failed")

        if not self.engine.blockchain.is_committed(target_hash):
            raise RuntimeError("Transaction was not committed")

    def custody(self) -> str | None:
        state = self.engine.blockchain.committed_state
        batch = state.batches.get(BATCH_ID)

        return batch.custodian_id if batch else None

    def history(self) -> list[dict]:
        chain = self.engine.blockchain
        result = []

        for block_hash in chain.committed[1:]:
            block = chain.get_block(block_hash)

            for tx in block.transactions:
                result.append(
                    {
                        "view": block.view,
                        "block_hash": block_hash,
                        "tx_id": tx.tx_id,
                        "type": tx.tx_type.value,
                        "sender": tx.sender_id,
                        "receiver": tx.receiver_id,
                        "batch_id": tx.batch_id,
                    }
                )

        return result


def main() -> None:
    scenario = PharmaScenario.create()

    print("=== PHARMACHAIN TRACEABILITY ===")

    print("\n1. Manufacturer registers medicine")
    scenario.confirm(scenario.register_batch())
    print("Custodian:", scenario.custody())

    print("\n2. Manufacturer transfers to distributor")
    scenario.confirm(
        scenario.transfer(
            "laboratory",
            "distributor",
            nonce=2,
        )
    )
    print("Custodian:", scenario.custody())

    print("\n3. Distributor transfers to hospital")
    scenario.confirm(
        scenario.transfer(
            "distributor",
            "hospital",
            nonce=1,
        )
    )
    print("Custodian:", scenario.custody())

    print("\n=== VERIFIED HISTORY ===")

    for item in scenario.history():
        print(f"View {item['view']}: {item['type']} | {item['sender']} -> {item['receiver']} | {item['batch_id']}")

    print("\nCommitted height:", scenario.engine.blockchain.committed_height)


if __name__ == "__main__":
    main()
