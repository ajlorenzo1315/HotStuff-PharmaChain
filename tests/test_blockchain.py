import pytest

from pharmachain.blockchain.chain import (
    Blockchain,
    BlockchainError,
)
from pharmachain.domain.crypto import generate_keypair
from pharmachain.domain.models import (
    Organization,
    OrganizationRole,
    TransactionType,
)
from pharmachain.domain.state import LedgerState
from pharmachain.domain.transactions import Transaction


@pytest.fixture
def environment():
    private_key, public_key = generate_keypair()

    organizations = {
        "manufacturer": Organization(
            "manufacturer",
            "Pharma Factory",
            OrganizationRole.MANUFACTURER,
            public_key,
        )
    }

    blockchain = Blockchain(LedgerState(organizations))

    return blockchain, private_key


def make_registration(private_key):
    return Transaction(
        tx_type=TransactionType.REGISTER_BATCH,
        sender_id="manufacturer",
        batch_id="LOT-2026-001",
        receiver_id=None,
        medicine_name="Amoxicillin",
        quantity=100,
        nonce=1,
    ).signed(private_key)


def test_genesis(environment):
    blockchain, _ = environment

    assert blockchain.committed_height == 0
    assert len(blockchain.committed) == 1
    assert blockchain.committed_state.batches == {}


def test_add_valid_block(environment):
    blockchain, private_key = environment

    tx = make_registration(private_key)

    block = blockchain.create_block(
        parent_hash=blockchain.genesis.block_hash,
        view=1,
        proposer_id="validator-0",
        transactions=[tx],
    )

    block_hash = blockchain.add_block(block)

    assert block_hash in blockchain.blocks
    assert blockchain.committed_height == 0

    assert "LOT-2026-001" in blockchain.get_state(block_hash).batches

    assert blockchain.committed_state.batches == {}


def test_commit_block(environment):
    blockchain, private_key = environment

    block = blockchain.create_block(
        blockchain.genesis.block_hash,
        1,
        "validator-0",
        [make_registration(private_key)],
    )

    block_hash = blockchain.add_block(block)

    blockchain.commit(block_hash)

    assert blockchain.committed_height == 1
    assert "LOT-2026-001" in blockchain.committed_state.batches


def test_invalid_transaction_rejected(environment):
    blockchain, private_key = environment

    invalid_tx = Transaction(
        tx_type=TransactionType.TRANSFER_BATCH,
        sender_id="manufacturer",
        batch_id="UNKNOWN",
        receiver_id="manufacturer",
        medicine_name=None,
        quantity=None,
        nonce=1,
    ).signed(private_key)

    block = blockchain.create_block(
        blockchain.genesis.block_hash,
        1,
        "validator-0",
        [invalid_tx],
    )

    with pytest.raises(
        BlockchainError,
        match="Invalid block transaction",
    ):
        blockchain.add_block(block)


def test_conflicting_branches(environment):
    blockchain, private_key = environment
    genesis_hash = blockchain.genesis.block_hash

    first = blockchain.create_block(
        genesis_hash,
        1,
        "validator-0",
        [make_registration(private_key)],
    )

    second = blockchain.create_block(
        genesis_hash,
        1,
        "validator-1",
        [],
    )

    first_hash = blockchain.add_block(first)
    second_hash = blockchain.add_block(second)

    assert first_hash != second_hash
    assert blockchain.committed_height == 0

    blockchain.commit(first_hash)

    with pytest.raises(
        BlockchainError,
        match="Target does not extend committed chain",
    ):
        blockchain.commit(second_hash)


def test_invalid_height(environment):
    blockchain, _ = environment

    from pharmachain.blockchain.block import Block

    invalid = Block(
        parent_hash=blockchain.genesis.block_hash,
        height=99,
        view=1,
        proposer_id="validator-0",
        transactions=(),
    )

    with pytest.raises(
        BlockchainError,
        match="Invalid block height",
    ):
        blockchain.add_block(invalid)
