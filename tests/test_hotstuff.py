from pharmachain.consensus.engine import HotStuffEngine
from pharmachain.consensus.messages import (
    QuorumCertificate,
    Vote,
)
from pharmachain.domain.crypto import generate_keypair
from pharmachain.domain.models import (
    Organization,
    OrganizationRole,
    TransactionType,
)
from pharmachain.domain.state import LedgerState
from pharmachain.domain.transactions import Transaction


def create_environment():
    private_key, public_key = generate_keypair()

    organization = Organization(
        organization_id="manufacturer",
        name="Pharma Factory",
        role=OrganizationRole.MANUFACTURER,
        public_key=public_key,
    )

    engine = HotStuffEngine(LedgerState({"manufacturer": organization}))

    tx = Transaction(
        tx_type=TransactionType.REGISTER_BATCH,
        sender_id="manufacturer",
        batch_id="LOT-2026-001",
        receiver_id=None,
        medicine_name="Amoxicillin",
        quantity=100,
        nonce=1,
    ).signed(private_key)

    return engine, tx


def test_quorum_certificate():
    engine, _ = create_environment()

    result = engine.run_round()

    assert result.votes == 4
    assert result.qc_formed is True
    assert result.block_hash in engine.certificates


def test_one_inactive_validator():
    engine, _ = create_environment()

    engine.validators[3].active = False

    result = engine.run_round()

    assert result.votes == 3
    assert result.qc_formed is True


def test_two_inactive_validators():
    engine, _ = create_environment()

    engine.validators[2].active = False
    engine.validators[3].active = False

    result = engine.run_round()

    assert result.votes == 2
    assert result.qc_formed is False
    assert result.committed == ()


def test_three_chain_commit():
    engine, tx = create_environment()

    first = engine.run_round([tx])

    assert first.qc_formed
    assert engine.blockchain.committed_height == 0

    second = engine.run_round()

    assert second.qc_formed
    assert engine.blockchain.committed_height == 0

    third = engine.run_round()

    assert third.qc_formed
    assert engine.blockchain.committed_height == 1

    state = engine.blockchain.committed_state

    assert state.batches["LOT-2026-001"].quantity == 100
    assert state.batches["LOT-2026-001"].custodian_id == "manufacturer"


def test_duplicate_vote_rejected():
    engine, _ = create_environment()
    validator = engine.validators[0]

    first_vote = validator.vote(
        view=1,
        block_hash="abc",
        safe=True,
    )

    second_vote = validator.vote(
        view=1,
        block_hash="def",
        safe=True,
    )

    assert first_vote is not None
    assert second_vote is None


def test_forged_qc_rejected():
    engine, _ = create_environment()
    validator = engine.validators[0]

    vote = Vote.create(
        validator.validator_id,
        validator.private_key,
        1,
        "block-a",
    )

    forged = QuorumCertificate(
        view=1,
        block_hash="block-a",
        votes=(vote, vote, vote),
    )

    assert not forged.verify(
        engine.public_keys,
        engine.quorum,
    )


def test_silent_leader_changes_view():
    engine, _ = create_environment()

    engine.validators[0].active = False

    result = engine.run_round()

    assert result.qc_formed is False
    assert result.block_hash is None
    assert engine.view == 2

    next_result = engine.run_round()

    assert next_result.leader == "validator-1"
    assert next_result.qc_formed is True
