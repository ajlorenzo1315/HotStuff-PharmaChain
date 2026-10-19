from pharmachain.domain.crypto import generate_keypair
from pharmachain.domain.models import (
    Organization,
    OrganizationRole,
    TransactionType,
)
from pharmachain.domain.state import LedgerState
from pharmachain.domain.transactions import Transaction
from pharmachain.engines.educational.adapter import (
    EducationalHotStuffAdapter,
)
from pharmachain.engines.events import EventType


def test_transaction_reaches_block_tree():
    private_key, public_key = generate_keypair()

    manufacturer = Organization(
        organization_id="manufacturer",
        name="Pharma Factory",
        role=OrganizationRole.MANUFACTURER,
        public_key=public_key,
    )

    initial_state = LedgerState(
        {
            "manufacturer": manufacturer,
        }
    )

    engine = EducationalHotStuffAdapter(initial_state)

    tx = Transaction(
        tx_type=TransactionType.REGISTER_BATCH,
        sender_id="manufacturer",
        batch_id="LOT-2026-001",
        receiver_id=None,
        medicine_name="Amoxicillin",
        quantity=100,
        nonce=1,
    ).signed(private_key)

    transaction_id = engine.submit(tx)

    assert transaction_id == tx.tx_id
    assert engine.snapshot()["pending_transactions"] == 1

    events = engine.step()

    assert [event.event_type for event in events] == [
        EventType.BLOCK_PROPOSED,
        EventType.BLOCK_VALIDATED,
    ]

    assert engine.snapshot()["known_blocks"] == 2

    # El bloque todavia NO está confirmado.
    assert engine.snapshot()["committed_height"] == 0
    assert engine.snapshot()["batches"] == {}

    # Sin embargo, el estado provisional si contiene el lote.
    proposed_hash = events[0].block_hash

    provisional_state = engine.blockchain.get_state(proposed_hash)

    assert "LOT-2026-001" in provisional_state.batches


def test_reset_clears_simulation():
    engine = EducationalHotStuffAdapter(LedgerState({}))

    engine.reset()

    assert engine.snapshot()["view"] == 1
    assert engine.snapshot()["known_blocks"] == 1
    assert engine.snapshot()["pending_transactions"] == 0
