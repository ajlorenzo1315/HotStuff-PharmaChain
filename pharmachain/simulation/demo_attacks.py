"""Run reproducible fault scenarios; write JSON for a future dashboard."""

from __future__ import annotations

import argparse
import json
from pathlib import Path

from pharmachain.consensus.distributed import DistributedHotStuff
from pharmachain.domain.state import LedgerState

SCENARIOS = {
    "normal": (),
    "one_offline": ("validator-3",),
    "two_offline": ("validator-2", "validator-3"),
    "leader_offline": ("validator-0",),
}


def run_scenario(name: str, rounds: int = 1) -> dict:
    if name not in SCENARIOS:
        raise ValueError(f"Unknown scenario: {name}")
    if rounds < 1:
        raise ValueError("rounds must be positive")

    sim = DistributedHotStuff(LedgerState({}), validator_count=4, seed=42)
    for node_id in SCENARIOS[name]:
        sim.network.disconnect(node_id)

    outcomes = []
    for _ in range(rounds):
        result = sim.run_round()
        outcomes.append(
            {
                "view": result.view,
                "leader": result.leader,
                "votes": result.votes,
                "qc_formed": result.qc_formed,
                "committed_heights": result.committed_heights,
            }
        )

    return {
        "scenario": name,
        "offline": list(SCENARIOS[name]),
        "validators": 4,
        "quorum": sim.quorum,
        "rounds": outcomes,
        "events": sim.events,
        "network_events": [
            {
                "time": event.at,
                "action": event.action,
                "sender": event.sender,
                "recipient": event.recipient,
                "kind": event.kind,
            }
            for event in sim.network.events
        ],
    }


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--scenario", choices=SCENARIOS, default="one_offline")
    parser.add_argument("--rounds", type=int, default=1)
    parser.add_argument("--output", type=Path)
    args = parser.parse_args()

    report = run_scenario(args.scenario, args.rounds)
    for result in report["rounds"]:
        print(f"View {result['view']} | leader={result['leader']} | votes={result['votes']}/3 | QC={'YES' if result['qc_formed'] else 'NO'}")
    print("Committed heights:", report["rounds"][-1]["committed_heights"])

    if args.output:
        args.output.parent.mkdir(parents=True, exist_ok=True)
        args.output.write_text(json.dumps(report, indent=2), encoding="utf-8")
        print("Report:", args.output)


if __name__ == "__main__":
    main()
