from pharmachain.consensus.node import HotStuffNode
from pharmachain.consensus.validator import Validator
from pharmachain.domain.state import LedgerState


def create_nodes():
    validators = [Validator.create(f"validator-{i}") for i in range(4)]

    public_keys = {v.validator_id: v.public_key for v in validators}

    return [
        HotStuffNode.create(
            validator=v,
            initial_state=LedgerState({}),
            public_keys=public_keys,
            quorum=3,
        )
        for v in validators
    ]


def test_independent_blockchains():
    nodes = create_nodes()

    assert nodes[0].blockchain is not nodes[1].blockchain

    nodes[0].view = 5

    assert nodes[1].view == 1


def test_independent_blocks():
    nodes = create_nodes()
    leader = nodes[0]

    genesis_hash = leader.blockchain.genesis.block_hash

    block = leader.blockchain.create_block(
        parent_hash=genesis_hash,
        view=1,
        proposer_id=leader.node_id,
        transactions=[],
    )

    assert leader.receive_block(block)
    assert block.block_hash in leader.blockchain.blocks

    assert block.block_hash not in nodes[1].blockchain.blocks


def test_receive_block():
    nodes = create_nodes()
    leader = nodes[0]
    follower = nodes[1]

    block = leader.blockchain.create_block(
        parent_hash=leader.blockchain.genesis.block_hash,
        view=1,
        proposer_id=leader.node_id,
        transactions=[],
    )

    assert follower.receive_block(block)
    assert block.block_hash in follower.blockchain.blocks


def test_unknown_parent_rejected():
    nodes = create_nodes()
    leader = nodes[0]

    block = leader.blockchain.create_block(
        parent_hash=leader.blockchain.genesis.block_hash,
        view=1,
        proposer_id=leader.node_id,
        transactions=[],
    )

    child = leader.blockchain.create_block(
        parent_hash=leader.blockchain.add_block(block),
        view=2,
        proposer_id=leader.node_id,
        transactions=[],
    )

    # El nodo 1 no conoce el bloque padre.
    assert not nodes[1].receive_block(child)


def test_invalid_qc_rejected():
    nodes = create_nodes()

    from pharmachain.consensus.messages import QuorumCertificate

    fake_qc = QuorumCertificate(
        view=1,
        block_hash="fake",
        votes=(),
    )

    assert not nodes[0].receive_qc(fake_qc)
