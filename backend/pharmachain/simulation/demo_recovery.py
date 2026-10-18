from pharmachain.consensus.distributed import DistributedHotStuff
from pharmachain.domain.state import LedgerState

sim = DistributedHotStuff(
    initial_state=LedgerState({}),
    validator_count=4,
)

print("=== FALLO DE LA FARMACIA ===")

sim.network.disconnect("validator-2")

result = sim.run_round()

print("Vista:", result.view)
print("Votos:", result.votes)
print("QC formado:", result.qc_formed)

print("\n=== RECONEXIÓN ===")

success = sim.reconnect_and_sync(
    node_id="validator-2",
    source="validator-0",
)

print("Recuperación completada:", success)

print("\n=== ESTADO DE LOS VALIDADORES ===")

for node_id, runtime in sim.nodes.items():
    node = runtime.node
    print(
        node_id,
        "vista:",
        node.view,
        "bloques:",
        len(node.blockchain.blocks),
        "QC:",
        len(node.certificates),
        "altura confirmada:",
        node.committed_height,
    )

print("\n=== EVENTOS ===")

for event in sim.events:
    if event["event"] in {
        "RECOVERY_STARTED",
        "BLOCK_REQUESTED",
        "SYNC_COMPLETED",
        "NODE_RECOVERED",
        "SYNC_REJECTED",
    }:
        print(event)
