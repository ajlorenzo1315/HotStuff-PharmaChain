import hashlib
import json
from dataclasses import dataclass, replace

from .crypto import sign_message
from .models import TransactionType


@dataclass(frozen=True)
class Transaction:
    tx_type: TransactionType
    sender_id: str
    batch_id: str
    receiver_id: str | None
    medicine_name: str | None
    quantity: int | None
    nonce: int
    signature: str = ""

    def payload(self) -> bytes:
        data = {
            "tx_type": self.tx_type.value,
            "sender_id": self.sender_id,
            "batch_id": self.batch_id,
            "receiver_id": self.receiver_id,
            "medicine_name": self.medicine_name,
            "quantity": self.quantity,
            "nonce": self.nonce,
        }

        return json.dumps(
            data,
            sort_keys=True,
            separators=(",", ":"),
        ).encode("utf-8")

    @property
    def tx_id(self) -> str:
        return hashlib.sha256(self.payload() + bytes.fromhex(self.signature)).hexdigest()

    def signed(self, private_key_hex: str) -> "Transaction":
        signature = sign_message(
            private_key_hex,
            self.payload(),
        )

        return replace(self, signature=signature)
