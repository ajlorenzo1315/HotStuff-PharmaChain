from pharmachain.consensus.distributed import DistributedHotStuff
from pharmachain.domain.state import LedgerState


def make_engine():
    return DistributedHotStuff(
        initial_state=LedgerState({}),
        validator_count=4,
        latency=0.1,
        seed=42,
    )


def test_four_validators():
    engine = make_engine()

    assert len(engine.nodes) == 4
    assert engine.quorum == 3
    assert engine.f == 1


def test_first_round_forms_qc():
    engine = make_engine()

    result = engine.run_round()

    assert result.view == 1
    assert result.leader == "validator-0"
    assert result.votes == 4
    assert result.qc_formed


def test_leader_rotation():
    engine = make_engine()

    results = [engine.run_round() for _ in range(4)]

    assert [r.leader for r in results] == [
        "validator-0",
        "validator-1",
        "validator-2",
        "validator-3",
    ]


def test_three_chain_commit():
    engine = make_engine()

    for _ in range(3):
        engine.run_round()

    heights = [runtime.node.committed_height for runtime in engine.nodes.values()]

    assert heights == [1, 1, 1, 1]


def test_one_disconnected_validator():
    engine = make_engine()

    engine.network.disconnect("validator-3")

    result = engine.run_round()

    assert result.votes == 3
    assert result.qc_formed


def test_two_disconnected_validators():
    engine = make_engine()

    engine.network.disconnect("validator-2")
    engine.network.disconnect("validator-3")

    result = engine.run_round()

    assert result.votes == 2
    assert not result.qc_formed


def test_votes_are_unique():
    engine = make_engine()

    result = engine.run_round()

    leader = engine.nodes[result.leader]
    key = (result.view, result.block_hash)
    collected = leader.votes[key]

    assert len(collected) == 4
    assert len(set(collected)) == 4


def test_qc_signatures():
    engine = make_engine()
    result = engine.run_round()

    leader = engine.nodes[result.leader].node
    qc = leader.certificates[result.block_hash]

    assert qc.verify(engine.public_keys, engine.quorum)


def test_committed_chains_agree():
    engine = make_engine()

    for _ in range(6):
        engine.run_round()

    chains = [runtime.node.blockchain.committed for runtime in engine.nodes.values()]

    assert all(chain == chains[0] for chain in chains)
