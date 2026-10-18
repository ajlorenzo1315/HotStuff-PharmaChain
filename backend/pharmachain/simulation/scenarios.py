"""Reproducible teaching scenarios for the existing centralized HotStuff engine.

This is an instrumented model, NOT a distributed network or a formal safety proof.
"""

from __future__ import annotations

import argparse
import json
from dataclasses import asdict

from pharmachain.consensus.engine import HotStuffEngine
from pharmachain.domain.state import LedgerState

SCENARIOS = ("normal", "one_offline", "two_offline", "silent_leader", "recovery")


def simulate(scenario: str = "normal", rounds: int = 6, nodes: int = 4) -> dict:
    if scenario not in SCENARIOS:
        raise ValueError(f"Unknown scenario: {scenario}")
    if rounds < 1:
        raise ValueError("rounds must be positive")
    engine = HotStuffEngine(LedgerState({}), validator_count=nodes)
    timeline = []
    for step in range(rounds):
        # Failures are injected BEFORE the round, to keep the experiment reproducible.
        for v in engine.validators:
            v.active = True
        if scenario == "one_offline":
            engine.validators[-1].active = False
        elif scenario == "two_offline":
            engine.validators[-1].active = False
            engine.validators[-2].active = False
        elif scenario == "silent_leader" and step == 0:
            engine.validators[0].active = False
        elif scenario == "recovery" and step < 2:
            engine.validators[-1].active = False
            engine.validators[-2].active = False
        leader = engine.leader().validator_id
        active = [v.validator_id for v in engine.validators if v.active]
        result = engine.run_round()
        timeline.append(
            {
                **asdict(result),
                "active_validators": active,
                "quorum_required": engine.quorum,
                "event": "qc_formed"
                if result.qc_formed
                else (
                    "leader_timeout"
                    if result.block_hash is None
                    else "insufficient_votes"
                ),
                "committed_height": engine.blockchain.committed_height,
                "high_qc_hash": engine.high_qc_hash,
                "locks": {
                    v.validator_id: {
                        "view": v.locked_view,
                        "block": v.locked_block_hash,
                    }
                    for v in engine.validators
                },
                "explanation": (
                    f"View {result.view}: leader {leader}; \
                    {result.votes}/{engine.quorum} votes. "
                    + ("QC certified." if result.qc_formed else "No QC formed.")
                    + (
                        f" Committed: {len(result.committed)} block(s)."
                        if result.committed
                        else " No new commits."
                    )
                ),
            }
        )
    return {
        "model": "centralized educational chained HotStuff (3-chain commit)",
        "limitations": [
            "Shared global block store and certificates;\
            no real message delivery.",
            "Offline validators and silent leader only; \
            no Byzantine equivocation simulation.",
            "Not a proof of HotStuff safety or liveness under adversarial scheduling.",
        ],
        "scenario": scenario,
        "validators": nodes,
        "f": engine.f,
        "quorum": engine.quorum,
        "rounds": timeline,
        "final_committed_height": engine.blockchain.committed_height,
    }


def main() -> None:
    parser = argparse.ArgumentParser(
        description="Explain HotStuff consensus round by round"
    )
    parser.add_argument("--scenario", choices=SCENARIOS, default="normal")
    parser.add_argument("--rounds", type=int, default=6)
    parser.add_argument("--nodes", type=int, default=4)
    parser.add_argument("--json", action="store_true")
    args = parser.parse_args()
    data = simulate(args.scenario, args.rounds, args.nodes)
    if args.json:
        print(json.dumps(data, indent=2))
    else:
        print(
            f"Scenario: {data['scenario']} | n={data['validators']} | \
            f={data['f']} | quorum={data['quorum']}"
        )
        for row in data["rounds"]:
            print(row["explanation"])
            print(
                f"  Event={row['event']} active={row['active_validators']} \
                committed_height={row['committed_height']}"
            )
        print(f"Final committed height: {data['final_committed_height']}")


if __name__ == "__main__":
    main()
