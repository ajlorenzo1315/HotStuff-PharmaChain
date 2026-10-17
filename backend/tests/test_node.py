from pharmachain.consensus.node import HotStuffNode
from pharmachain.consensus.validator import Validator
from pharmachain.domain.state import LedgerState


def test_nodes_have_independent_blockchains():
    state = LedgerState({})

    node_a = HotStuffNode.create(Validator.create("validator-0"), state)
    node_b = HotStuffNode.create(Validator.create("validator-1"), state)

    assert node_a.blockchain is not node_b.blockchain
    assert node_a.view == node_b.view == 1

    node_a.view = 5

    assert node_b.view == 1
