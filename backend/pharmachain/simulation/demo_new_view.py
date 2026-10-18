from pharmachain.consensus.distributed import DistributedHotStuff
from pharmachain.domain.state import LedgerState

sim = DistributedHotStuff(
    initial_state=LedgerState({}),
    validator_count=4,
)

# El primer líder deja de responder.
sim.network.disconnect("validator-0")

for _ in range(3):
    result = sim.run_round()
    print(
        f"Vista={result.view}, "
        f"Líder={result.leader}, "
        f"Votos={result.votes}, "
        f"QC={result.qc_formed}"
    )

print("\n=== EVENTOS DE CAMBIO DE VISTA ===")

interesting = {
    "TIMEOUT_SENT",
    "TC_FORMED",
    "VIEW_CHANGED",
    "NEW_VIEW_SENT",
    "NEW_VIEW_ACCEPTED",
    "NEW_VIEW_QUORUM",
    "SYNC_REQUIRED",
    "QC_FORMED",
}

for event in sim.events:
    if event["event"] in interesting:
        print(event)
