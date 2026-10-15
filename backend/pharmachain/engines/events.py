from dataclasses import dataclass, field
from enum import Enum
from typing import Any


class EventType(str, Enum):
    TRANSACTION_RECEIVED = "transaction_received"
    TRANSACTION_REJECTED = "transaction_rejected"
    BLOCK_PROPOSED = "block_proposed"
    BLOCK_VALIDATED = "block_validated"
    VOTE_CAST = "vote_cast"
    QC_FORMED = "qc_formed"
    VIEW_CHANGED = "view_changed"
    BLOCK_COMMITTED = "block_committed"
    TIMEOUT = "timeout"
    ERROR = "error"


@dataclass(frozen=True)
class ConsensusEvent:
    event_type: EventType
    engine: str
    view: int | None
    block_hash: str | None
    validator_id: str | None
    message: str
    details: dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> dict:
        return {
            "type": self.event_type.value,
            "engine": self.engine,
            "view": self.view,
            "block_hash": self.block_hash,
            "validator_id": self.validator_id,
            "message": self.message,
            "details": self.details,
        }
