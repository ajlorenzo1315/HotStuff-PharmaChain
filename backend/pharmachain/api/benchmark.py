"""Reproducible fail-stop availability
experiments for educational HotStuff.

These scenarios disconnect validators;
they do NOT simulate arbitrary Byzantine behavior.
The simulator is in-memory,
so timings are simulated network time, not real throughput.
"""

from __future__ import annotations

from pharmachain.consensus.distributed import DistributedHotStuff
from pharmachain.consensus.safety import audit_committed_safety
from pharmachain.domain.state import LedgerState


def run_benchmark(rounds: int = 12, seed: int = 42) -> dict:
    if not isinstance(rounds, int) or isinstance(rounds, bool) or not 1 <= rounds <= 100:
        raise ValueError(
            "rounds must be an \
        integer between 1 and 100"
        )
    if not isinstance(seed, int) or isinstance(seed, bool):
        raise ValueError("seed must be an integer")

    scenarios = []
    for offline_count in (0, 1, 2):
        sim = DistributedHotStuff(LedgerState({}), validator_count=4, seed=seed)
        # Fixed choice makes runs reproducible and exercises rotating leaders.
        offline = [f"validator-{i}" for i in range(4 - offline_count, 4)]
        for node_id in offline:
            sim.network.disconnect(node_id)
        rounds_data = []
        for _ in range(rounds):
            start = sim.network.time
            result = sim.run_round()
            rounds_data.append(
                {
                    "view": result.view,
                    "leader": result.leader,
                    "votes": result.votes,
                    "qc_formed": result.qc_formed,
                    "elapsed_simulated": round(sim.network.time - start, 6),
                    "max_committed_height": max(result.committed_heights.values()),
                }
            )
        audit = audit_committed_safety(sim)
        qc_count = sum(r["qc_formed"] for r in rounds_data)
        committed_height = max(rt.node.committed_height for rt in sim.nodes.values())
        scenarios.append(
            {
                "id": f"offline_{offline_count}",
                "offline_count": offline_count,
                "offline": offline,
                "online_count": 4 - offline_count,
                "quorum": sim.quorum,
                "rounds": rounds,
                "qc_rounds": qc_count,
                "qc_rate": round(qc_count / rounds, 4),
                "max_committed_height": committed_height,
                "simulated_time": round(sim.network.time, 6),
                "safety": audit,
                "round_details": rounds_data,
            }
        )
    return {
        "title": "HotStuff: tolerancia a desconexiones",
        "seed": seed,
        "rounds_per_scenario": rounds,
        "scenarios": scenarios,
        "limitations": (
            "Disconnecting nodes is fail-stop, \
            not Byzantine behavior. "
            "QC rate and simulated time are \
            simulator metrics, not real TPS or latency. "
            "A finite experiment cannot\
            establish formal safety or liveness."
        ),
    }
