"""Controlled equivocation experiment
against a four-validator Chained HotStuff simulator.

The leader sends two different proposals in the same view. Both use real
PROPOSE/VOTE network messages; no committed state is injected or forged.
"""

from __future__ import annotations

from pharmachain.consensus.distributed import DistributedHotStuff, Proposal
from pharmachain.consensus.safety import audit_committed_safety
from pharmachain.domain.state import LedgerState


def run_fork_experiment() -> dict:
    sim = DistributedHotStuff(LedgerState({}), validator_count=4)
    first = sim.run_round()
    if not first.qc_formed or first.block_hash is None:
        raise RuntimeError("Preparation round did not produce a QC")

    view = sim.view
    leader_id = sim.leader_id(view)
    leader = sim.nodes[leader_id].node
    qc = leader.high_qc
    if qc is None or qc.block_hash != first.block_hash:
        raise RuntimeError("Leader has no verified QC for preparation block")

    # Equivocation: one valid leader sends different proposals for the SAME view.
    # A extends the certified parent; B extends genesis directly.
    branch_a = leader.blockchain.create_block(
        parent_hash=qc.block_hash,
        view=view,
        proposer_id=leader_id,
        transactions=[],
    )
    branch_b = leader.blockchain.create_block(
        parent_hash=sim.genesis_hash,
        view=view,
        proposer_id=leader_id,
        transactions=[],
    )
    assert branch_a.block_hash != branch_b.block_hash

    sim.nodes[leader_id].proposed[view] = branch_a.block_hash
    # Each honest validator receives only one branch; the Byzantine leader
    # equivocates. The simulation's honest leader handler will only tally A.
    for recipient in ("validator-0", "validator-1"):
        sim.network.send(leader_id, recipient, "PROPOSE", Proposal(branch_a, qc))
    for recipient in ("validator-2", "validator-3"):
        sim.network.send(leader_id, recipient, "PROPOSE", Proposal(branch_b, None))
    sim.network.run()

    votes_a = sim.nodes[leader_id].votes.get((view, branch_a.block_hash), {})
    votes_b = sim.nodes[leader_id].votes.get((view, branch_b.block_hash), {})
    created = [
        e for e in sim.events if e["event"] == "VOTE_CREATED" and e.get("view") == view
    ]
    votes_by_node: dict[str, set[str]] = {}
    for event in created:
        votes_by_node.setdefault(event["node"], set()).add(event["block"])
    no_double_vote = all(len(blocks) <= 1 for blocks in votes_by_node.values())
    qc_events = [
        e for e in sim.events if e["event"] == "QC_FORMED" and e.get("view") == view
    ]
    audit = audit_committed_safety(sim)
    passed = no_double_vote and not qc_events and audit["safe"]
    sim._record("FORK_EXPERIMENT_RESULT", view=view, passed=passed)

    return {
        "scenario": "equivocating_leader",
        "title": "Líder que propone dos ramas en la misma vista",
        "passed": passed,
        "view": view,
        "leader": leader_id,
        "branches": {
            "A": {"hash": branch_a.block_hash, "parent": branch_a.parent_hash},
            "B": {"hash": branch_b.block_hash, "parent": branch_b.parent_hash},
        },
        "votes_created": {
            node: sorted(blocks) for node, blocks in votes_by_node.items()
        },
        "votes_tallied_for_a": len(votes_a),
        "votes_tallied_for_b": len(votes_b),
        "double_vote_prevented": no_double_vote,
        "qc_formed_in_attack_view": bool(qc_events),
        "safety": audit,
        "events": sim.events[-120:],
        "limitations": (
            "This tests a single equivocating leader \
            and a particular delivery schedule; "
            "it is not an exhaustive safety proof. The leader's vote collector "
            "remains honest in this experiment."
        ),
    }
