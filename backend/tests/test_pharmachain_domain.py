import pytest

from pharmachain.domain.crypto import generate_keypair
from pharmachain.domain.models import (
    Organization,
    OrganizationRole,
    TransactionType,
)
from pharmachain.domain.state import LedgerState, ValidationError
from pharmachain.domain.transactions import Transaction


@pytest.fixture
def environment():
    manufacturer_private, manufacturer_public = generate_keypair()
    distributor_private, distributor_public = generate_keypair()

    organizations = {
        "manufacturer": Organization(
            "manufacturer",
            "Pharma Factory",
            OrganizationRole.MANUFACTURER,
            manufacturer_public,
        ),
        "distributor": Organization(
            "distributor",
            "Medical Logistics",
            OrganizationRole.DISTRIBUTOR,
            distributor_public,
        ),
    }

    return {
        "state": LedgerState(organizations),
        "manufacturer_private": manufacturer_private,
        "distributor_private": distributor_private,
    }


def register_transaction(private_key):
    return Transaction(
        tx_type=TransactionType.REGISTER_BATCH,
        sender_id="manufacturer",
        batch_id="LOT-2026-001",
        receiver_id=None,
        medicine_name="Amoxicillin",
        quantity=100,
        nonce=1,
    ).signed(private_key)


def test_register_batch(environment):
    state = environment["state"]

    tx = register_transaction(environment["manufacturer_private"])

    new_state = state.apply(tx)

    assert "LOT-2026-001" in new_state.batches
    assert new_state.batches["LOT-2026-001"].quantity == 100
    assert state.batches == {}


def test_transfer_batch(environment):
    state = environment["state"]

    state = state.apply(register_transaction(environment["manufacturer_private"]))

    transfer = Transaction(
        tx_type=TransactionType.TRANSFER_BATCH,
        sender_id="manufacturer",
        batch_id="LOT-2026-001",
        receiver_id="distributor",
        medicine_name=None,
        quantity=None,
        nonce=2,
    ).signed(environment["manufacturer_private"])

    new_state = state.apply(transfer)

    assert new_state.batches["LOT-2026-001"].custodian_id == "distributor"
    assert state.batches["LOT-2026-001"].custodian_id == "manufacturer"


def test_invalid_signature(environment):
    tx = register_transaction(environment["distributor_private"])

    with pytest.raises(ValidationError, match="Invalid signature"):
        environment["state"].apply(tx)


def test_duplicate_transaction(environment):
    tx = register_transaction(environment["manufacturer_private"])

    state = environment["state"].apply(tx)

    with pytest.raises(ValidationError, match="Duplicate transaction"):
        state.apply(tx)


def test_unauthorized_transfer(environment):
    state = environment["state"].apply(register_transaction(environment["manufacturer_private"]))

    tx = Transaction(
        tx_type=TransactionType.TRANSFER_BATCH,
        sender_id="distributor",
        batch_id="LOT-2026-001",
        receiver_id="manufacturer",
        medicine_name=None,
        quantity=None,
        nonce=1,
    ).signed(environment["distributor_private"])

    with pytest.raises(
        ValidationError,
        match="Sender is not the custodian",
    ):
        state.apply(tx)
