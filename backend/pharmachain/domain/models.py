from dataclasses import dataclass
from enum import Enum


class OrganizationRole(str, Enum):
    MANUFACTURER = "manufacturer"
    DISTRIBUTOR = "distributor"
    HOSPITAL = "hospital"
    REGULATOR = "regulator"


class TransactionType(str, Enum):
    REGISTER_BATCH = "register_batch"
    TRANSFER_BATCH = "transfer_batch"


@dataclass(frozen=True)
class Organization:
    organization_id: str
    name: str
    role: OrganizationRole
    public_key: str


@dataclass(frozen=True)
class MedicineBatch:
    batch_id: str
    medicine_name: str
    quantity: int
    manufacturer_id: str
    custodian_id: str
