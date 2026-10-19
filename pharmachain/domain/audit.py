from dataclasses import asdict, dataclass

from pharmachain.domain.state import LedgerState
from pharmachain.domain.transactions import Transaction


@dataclass(frozen=True)
class CustodyChange:
    transaction_id: str
    batch_id: str
    previous_custodian: str | None
    new_custodian: str | None
    changed: bool

    def to_dict(self) -> dict:
        return asdict(self)


def inspect_custody_change(
    before: LedgerState,
    after: LedgerState,
    tx: Transaction,
) -> CustodyChange:
    previous_batch = before.batches.get(tx.batch_id)
    new_batch = after.batches.get(tx.batch_id)

    previous = previous_batch.custodian_id if previous_batch is not None else None

    current = new_batch.custodian_id if new_batch is not None else None

    return CustodyChange(
        transaction_id=tx.tx_id,
        batch_id=tx.batch_id,
        previous_custodian=previous,
        new_custodian=current,
        changed=previous != current,
    )
