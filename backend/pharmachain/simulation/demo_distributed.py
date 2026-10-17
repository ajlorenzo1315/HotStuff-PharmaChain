from pharmachain.consensus.distributed import DistributedHotStuff
from pharmachain.domain.state import LedgerState


def show_result(result):
    print(f"\nVIEW {result.view}")
    print(f"  Leader: {result.leader}")
    print(f"  Votes: {result.votes}")
    print(f"  QC formed: {result.qc_formed}")

    for node_id, height in result.committed_heights.items():
        print(f"  {node_id}: committed height {height}")


def main():
    engine = DistributedHotStuff(
        initial_state=LedgerState({}),
        validator_count=4,
        latency=0.1,
        seed=42,
    )

    print("=== HOTSTUFF DISTRIBUTED DEMO ===")
    print("Validators: 4")
    print("Byzantine tolerance: 1")
    print("Quorum: 3")

    for _ in range(6):
        result = engine.run_round()
        show_result(result)

    print("\n=== CONSENSUS EVENTS ===")

    for event in engine.events:
        print(
            f"[{event['time']:.2f}s] "
            f"{event['event']} "
            f"{event.get('node', '')} "
            f"view={event.get('view', '-')}"
        )

    print("\n=== FINAL SUMMARY ===")

    for node_id, runtime in engine.nodes.items():
        node = runtime.node

        print(
            f"{node_id}: "
            f"height={node.committed_height}, "
            f"QC={node.high_qc.view if node.high_qc else 0}"
        )


if __name__ == "__main__":
    main()
