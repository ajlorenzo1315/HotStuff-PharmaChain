from pharmachain.consensus.distributed import DistributedHotStuff
from pharmachain.domain.state import LedgerState

sim = DistributedHotStuff(
    initial_state=LedgerState({}),
    validator_count=4,
)

# Generar varios bloques certificados.
for _ in range(4):
    result = sim.run_round()
    print(f"Vista {result.view}: QC={result.qc_formed}")

source = "validator-0"
recipient = "validator-2"

source_chain = sim.nodes[source].node.blockchain
target_hash = source_chain.committed_tip

print("\n=== SINCRONIZACIÓN ===")
print("Bloque objetivo:", target_hash)

# Esta solicitud solo tendrá efecto si el receptor
# todavía no posee el bloque.
sim.request_sync(
    recipient=recipient,
    source=source,
    target_hash=target_hash,
)

sim.network.run()

for event in sim.events:
    if event["event"] in {
        "BLOCK_REQUESTED",
        "BLOCK_UNAVAILABLE",
        "SYNC_COMPLETED",
        "SYNC_REJECTED",
    }:
        print(event)
