"""Byzantine vote fault experiments
for the educational HotStuff simulator.

Compatible with phase 21
(run_scenario/run_comparison/export_results) and
phase 22 (run_experiment/compare/to_csv).
Models faulty votes, not full BFT.
"""

from __future__ import annotations

import argparse
import csv
import io
import json
from dataclasses import asdict, dataclass, replace
from pathlib import Path

from pharmachain.consensus.distributed import DistributedHotStuff
from pharmachain.consensus.safety import audit_committed_safety
from pharmachain.domain.state import LedgerState

MODES = ("omit", "invalid_signature")
CSV_FIELDS = (
    "seed",
    "mode",
    "faulty_count",
    "rounds",
    "qc_rounds",
    "qc_rate",
    "max_committed_height",
    "invalid_votes",
    "safety_ok",
    "simulated_time",
)


@dataclass
class ByzantineResult:
    """Legacy phase-21 result contract."""

    mode: str
    faulty_nodes: int
    rounds: int
    qc_count: int
    qc_rate: float
    max_committed_height: int
    invalid_votes: int
    omitted_votes: int
    simulated_time: float
    safe: bool


def run_experiment(*, rounds: int = 12, seed: int = 42, faulty_count: int = 1, mode: str = "omit") -> dict:
    """Run one isolated four-validator experiment with injected faulty votes."""
    if type(rounds) is not int or not 1 <= rounds <= 100:
        raise ValueError("rounds must be between 1 and 100")
    if type(seed) is not int:
        raise ValueError("seed must be an integer")
    if type(faulty_count) is not int or faulty_count not in (0, 1, 2):
        raise ValueError("faulty_count must be 0, 1, or 2")
    if mode not in MODES:
        raise ValueError(f"mode must be one of {MODES}")

    sim = DistributedHotStuff(LedgerState({}), validator_count=4, seed=seed)
    faulty = [f"validator-{i}" for i in range(4 - faulty_count, 4)]

    for node_id in faulty:
        validator = sim.nodes[node_id].node.validator
        original_vote = validator.vote

        def adversarial_vote(view, block_hash, safe, *, original=original_vote, identity=node_id):
            if mode == "omit":
                sim._record("BYZANTINE_VOTE_OMITTED", node=identity, view=view)
                return None
            vote = original(view=view, block_hash=block_hash, safe=safe)
            if vote is None:
                return None
            sim._record("BYZANTINE_INVALID_SIGNATURE_SENT", node=identity, view=view)
            # Signatures are hexadecimal strings in pharmachain.consensus.messages.Vote.
            return replace(vote, signature="00" * 64)

        validator.vote = adversarial_vote

    details = []
    for _ in range(rounds):
        result = sim.run_round()
        details.append(
            {
                "view": result.view,
                "leader": result.leader,
                "votes": result.votes,
                "qc_formed": result.qc_formed,
                "max_committed_height": max(result.committed_heights.values(), default=0),
            }
        )

    audit = audit_committed_safety(sim)
    qc_rounds = sum(bool(item["qc_formed"]) for item in details)
    return {
        "seed": seed,
        "mode": mode,
        "faulty_count": faulty_count,
        "faulty_validators": faulty,
        "rounds": rounds,
        "qc_rounds": qc_rounds,
        "qc_rate": round(qc_rounds / rounds, 6),
        "max_committed_height": max((rt.node.committed_height for rt in sim.nodes.values()), default=0),
        "invalid_votes": sum(e["event"] == "INVALID_VOTE" for e in sim.events),
        "omitted_votes": sum(e["event"] == "BYZANTINE_VOTE_OMITTED" for e in sim.events),
        "safety_ok": audit["safe"],
        "safety": audit,
        "simulated_time": round(sim.network.time, 6),
        "round_details": details,
        "limitations": (
            "Controlled faulty votes only; proposer and transport logic are unchanged. "
            "This experiment is not a formal safety or liveness proof."
        ),
    }


def compare(*, rounds: int = 12, seed: int = 42, mode: str = "omit") -> dict:
    return {
        "title": "HotStuff: Byzantine vote fault comparison",
        "mode": mode,
        "seed": seed,
        "rounds": rounds,
        "scenarios": [run_experiment(rounds=rounds, seed=seed, mode=mode, faulty_count=n) for n in (0, 1, 2)],
    }


def to_csv(comparison: dict) -> str:
    stream = io.StringIO(newline="")
    writer = csv.DictWriter(stream, fieldnames=CSV_FIELDS, lineterminator="\n")
    writer.writeheader()
    for result in comparison["scenarios"]:
        writer.writerow({name: result[name] for name in CSV_FIELDS})
    return stream.getvalue()


def run_scenario(mode: str, faulty_nodes: int, rounds: int = 12, seed: int = 42) -> ByzantineResult:
    """Phase-21 compatibility adapter; uses the same simulation as phase 22."""
    result = run_experiment(rounds=rounds, seed=seed, faulty_count=faulty_nodes, mode=mode)
    return ByzantineResult(
        mode=result["mode"],
        faulty_nodes=result["faulty_count"],
        rounds=result["rounds"],
        qc_count=result["qc_rounds"],
        qc_rate=result["qc_rate"],
        max_committed_height=result["max_committed_height"],
        invalid_votes=result["invalid_votes"],
        omitted_votes=result["omitted_votes"],
        simulated_time=result["simulated_time"],
        safe=result["safety_ok"],
    )


def run_comparison(mode: str, rounds: int = 12, seed: int = 42) -> list[ByzantineResult]:
    return [run_scenario(mode, n, rounds, seed) for n in (0, 1, 2)]


def export_results(results: list[ByzantineResult] | list[dict], output_dir: str | Path) -> None:
    """Phase-21 CSV/JSON export; accepts result dataclasses or dictionaries."""
    output = Path(output_dir)
    output.mkdir(parents=True, exist_ok=True)
    rows = [asdict(item) if isinstance(item, ByzantineResult) else dict(item) for item in results]
    (output / "comparison.json").write_text(json.dumps(rows, indent=2), encoding="utf-8")
    with (output / "comparison.csv").open("w", newline="", encoding="utf-8") as stream:
        if rows:
            fields = list(dict.fromkeys(key for row in rows for key in row))
            writer = csv.DictWriter(stream, fieldnames=fields, extrasaction="ignore")
            writer.writeheader()
            writer.writerows(rows)


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--rounds", type=int, default=12)
    parser.add_argument("--seed", type=int, default=42)
    parser.add_argument("--mode", choices=MODES, default="omit")
    parser.add_argument("--out", type=Path, default=Path("results/byzantine"))
    args = parser.parse_args()
    comparison = compare(rounds=args.rounds, seed=args.seed, mode=args.mode)
    args.out.mkdir(parents=True, exist_ok=True)
    (args.out / "comparison.json").write_text(json.dumps(comparison, indent=2), encoding="utf-8")
    (args.out / "comparison.csv").write_text(to_csv(comparison), encoding="utf-8")
    for row in comparison["scenarios"]:
        print(
            f"f={row['faulty_count']} QC={row['qc_rounds']}/{row['rounds']} "
            f"committed={row['max_committed_height']} safe={row['safety_ok']}"
        )
    print(f"Saved to {args.out}")


if __name__ == "__main__":
    main()
