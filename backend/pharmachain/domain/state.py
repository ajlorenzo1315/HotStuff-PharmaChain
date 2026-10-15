
from dataclasses import dataclass, field, replace

from .crypto import verify_signature
from .models import (
    MedicineBatch,
    Organization,
    OrganizationRole,
    TransactionType,
)
from .transactions import Transaction


class ValidationError(Exception):
    pass


@dataclass
class LedgerState:
    organizations: dict[str, Organization]
    batches: dict[str, MedicineBatch] = field(default_factory=dict)
    nonces: dict[str, int] = field(default_factory=dict)
    processed_transactions: set[str] = field(default_factory=set)

    def clone(self) -> "LedgerState":
        return LedgerState(
            organizations=self.organizations.copy(),
            batches=self.batches.copy(),
            nonces=self.nonces.copy(),
            processed_transactions=self.processed_transactions.copy(),
        )

    def apply(self, tx: Transaction) -> "LedgerState":
        new_state = self.clone()
        new_state._validate_and_apply(tx)
        # Un lider puede proponer un bloque que posteriormente sea rechazado. 
        # Por eso validar una transacción no debe modificar inmediatamente el estado confirmado.
        return new_state

    def _validate_and_apply(self, tx: Transaction) -> None:
        sender = self.organizations.get(tx.sender_id)

        if sender is None:
            raise ValidationError("Unknown sender")

        if not verify_signature(
            sender.public_key,
            tx.payload(),
            tx.signature,
        ):
            raise ValidationError("Invalid signature")

        if tx.tx_id in self.processed_transactions:
            raise ValidationError("Duplicate transaction")

        expected_nonce = self.nonces.get(tx.sender_id, 0) + 1

        if tx.nonce != expected_nonce:
            raise ValidationError("Invalid nonce")

        if tx.tx_type == TransactionType.REGISTER_BATCH:
            self._register_batch(tx, sender)

        elif tx.tx_type == TransactionType.TRANSFER_BATCH:
            self._transfer_batch(tx)

        else:
            raise ValidationError("Unsupported transaction type")

        self.nonces[tx.sender_id] = tx.nonce
        self.processed_transactions.add(tx.tx_id)

    def _register_batch(
        self,
        tx: Transaction,
        sender: Organization,
    ) -> None:
        if sender.role != OrganizationRole.MANUFACTURER:
            raise ValidationError("Only manufacturers can register batches")

        if tx.batch_id in self.batches:
            raise ValidationError("Batch already exists")

        if not tx.medicine_name:
            raise ValidationError("Medicine name is required")

        if tx.quantity is None or tx.quantity <= 0:
            raise ValidationError("Invalid quantity")

        if tx.receiver_id is not None:
            raise ValidationError("Registration cannot specify receiver")

        self.batches[tx.batch_id] = MedicineBatch(
            batch_id=tx.batch_id,
            medicine_name=tx.medicine_name,
            quantity=tx.quantity,
            manufacturer_id=tx.sender_id,
            custodian_id=tx.sender_id,
        )

    def _transfer_batch(self, tx: Transaction) -> None:
        batch = self.batches.get(tx.batch_id)

        if batch is None:
            raise ValidationError("Batch does not exist")

        if batch.custodian_id != tx.sender_id:
            raise ValidationError("Sender is not the custodian")

        if tx.receiver_id not in self.organizations:
            raise ValidationError("Unknown receiver")

        if tx.receiver_id == tx.sender_id:
            raise ValidationError("Self-transfer not allowed")

        if tx.medicine_name is not None or tx.quantity is not None:
            raise ValidationError("Transfer must not redefine batch")

        self.batches[tx.batch_id] = replace(
            batch,
            custodian_id=tx.receiver_id,
        )
