"""Adversarial regression tests for BLOCK_RESPONSE handling."""

from dataclasses import replace
from types import SimpleNamespace

from pharmachain.consensus.distributed import DistributedHotStuff
from pharmachain.consensus.sync import BlockResponse, ancestry
from pharmachain.domain.state import LedgerState


def setup_missing_block():
    sim = DistributedHotStuff(LedgerState({}), validator_count=4)
    sim.network.disconnect("validator-2")
    result = sim.run_round()
    assert result.qc_formed
    sim.network.reconnect("validator-2")
    sender = "validator-0"
    target = result.block_hash
    sim.request_sync("validator-2", sender, target)
    source_node = sim.nodes[sender].node
    blocks = ancestry(source_node.blockchain.blocks, target)
    qcs = tuple(
        source_node.certificates[b.block_hash]
        for b in blocks
        if b.block_hash in source_node.certificates
    )
    assert qcs
    return sim, sender, BlockResponse(target, blocks, qcs)


def deliver(sim, sender, response):
    sim._on_block_response(
        "validator-2", SimpleNamespace(sender=sender, payload=response)
    )


def assert_rejected_without_mutation(sim, target):
    node = sim.nodes["validator-2"].node
    assert target not in node.blockchain.blocks
    assert target not in node.certificates
    assert any(event["event"] == "SYNC_REJECTED" for event in sim.events)


def test_reject_tampered_block_without_mutation():
    sim, sender, response = setup_missing_block()
    bad = replace(response.blocks[-1], proposer_id="validator-3")
    deliver(sim, sender, replace(response, blocks=(*response.blocks[:-1], bad)))
    assert_rejected_without_mutation(sim, response.target_hash)


def test_reject_forged_qc_without_mutation():
    sim, sender, response = setup_missing_block()
    qc = response.certificates[0]
    forged_vote = replace(qc.votes[0], signature="00" * 64)
    forged_qc = replace(qc, votes=(forged_vote, *qc.votes[1:]))
    deliver(sim, sender, replace(response, certificates=(forged_qc,)))
    assert_rejected_without_mutation(sim, response.target_hash)


def test_reject_duplicate_qc_without_mutation():
    sim, sender, response = setup_missing_block()
    deliver(
        sim, sender, replace(response, certificates=(response.certificates[0],) * 2)
    )
    assert_rejected_without_mutation(sim, response.target_hash)


def test_reject_unsolicited_response():
    sim, sender, response = setup_missing_block()
    deliver(sim, "validator-3", response)
    assert_rejected_without_mutation(sim, response.target_hash)


def test_valid_response_is_accepted():
    sim, sender, response = setup_missing_block()
    deliver(sim, sender, response)
    node = sim.nodes["validator-2"].node
    assert response.target_hash in node.blockchain.blocks
    assert response.target_hash in node.certificates
    assert any(event["event"] == "SYNC_COMPLETED" for event in sim.events)
