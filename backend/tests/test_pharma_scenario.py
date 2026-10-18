from dataclasses import replace

import pytest

from pharmachain.blockchain.chain import BlockchainError
from pharmachain.domain.models import TransactionType
from pharmachain.domain.transactions import Transaction
from pharmachain.simulation.pharma_scenario import (
    BATCH_ID,
    PharmaScenario,
)


@pytest.fixture
def scenario():
    return PharmaScenario.create()


def test_register_batch(scenario):
    scenario.confirm(scenario.register_batch())

    state = scenario.engine.blockchain.committed_state
    batch = state.batches[BATCH_ID]

    assert batch.medicine_name == "Amoxicillin 500 mg"
    assert batch.quantity == 100
    assert batch.custodian_id == "laboratory"


def test_full_traceability(scenario):
    scenario.confirm(scenario.register_batch())

    scenario.confirm(
        scenario.transfer(
            "laboratory",
            "distributor",
            nonce=2,
        )
    )

    scenario.confirm(
        scenario.transfer(
            "distributor",
            "hospital",
            nonce=1,
        )
    )

    assert scenario.custody() == "hospital"

    history = scenario.history()

    assert len(history) == 3
    assert [item["type"] for item in history] == [
        "register_batch",
        "transfer_batch",
        "transfer_batch",
    ]


def test_non_owner_cannot_transfer(scenario):
    scenario.confirm(scenario.register_batch())

    forged_transfer = scenario.transfer(
        "distributor",
        "hospital",
        nonce=1,
    )

    with pytest.raises(BlockchainError):
        scenario.engine.run_round([forged_transfer])

    assert scenario.custody() == "laboratory"


def test_modified_signed_transaction_rejected(scenario):
    original = scenario.register_batch()

    # Change the medicine after signing.
    tampered = replace(
        original,
        medicine_name="Different Medicine",
    )

    with pytest.raises(BlockchainError):
        scenario.engine.run_round([tampered])

    assert scenario.custody() is None


def test_replay_rejected(scenario):
    transaction = scenario.register_batch()
    scenario.confirm(transaction)

    with pytest.raises(BlockchainError):
        scenario.engine.run_round([transaction])

    assert scenario.custody() == "laboratory"


def test_hospital_cannot_register_batch(scenario):
    transaction = Transaction(
        tx_type=TransactionType.REGISTER_BATCH,
        sender_id="hospital",
        batch_id="LOT-UNAUTHORIZED",
        receiver_id=None,
        medicine_name="Amoxicillin",
        quantity=100,
        nonce=1,
    ).signed(scenario.private_keys["hospital"])

    with pytest.raises(BlockchainError):
        scenario.engine.run_round([transaction])


def test_proposal_is_not_immediately_committed(scenario):
    transaction = scenario.register_batch()

    result = scenario.engine.run_round([transaction])

    assert result.qc_formed
    assert scenario.custody() is None

    scenario.engine.run_round()
    scenario.engine.run_round()

    assert scenario.custody() == "laboratory"


def test_history_uses_only_committed_blocks(scenario):
    transaction = scenario.register_batch()

    scenario.engine.run_round([transaction])

    assert scenario.history() == []

    scenario.engine.run_round()
    scenario.engine.run_round()

    assert len(scenario.history()) == 1
