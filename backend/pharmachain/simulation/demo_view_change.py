from pharmachain.consensus.distributed import DistributedHotStuff
from pharmachain.domain.state import LedgerState

sim = DistributedHotStuff(
    initial_state=LedgerState({}),
    validator_count=4,
)

print("=== PHARMACHAIN: FALLO DEL LABORATORIO ===")

sim.network.disconnect("validator-0")

first = sim.run_round()

print("\nPrimera ronda:")
print("Líder:", first.leader)
print("QC formado:", first.qc_formed)

print("\nVistas de los validadores:")
for node_id, runtime in sim.nodes.items():
    print(node_id, "->", runtime.node.view)

print("\nSegunda ronda:")
second = sim.run_round()

print("Líder:", second.leader)
print("Votos:", second.votes)
print("QC formado:", second.qc_formed)

print("\nEventos de recuperación:")
for event in sim.events:
    if event["event"] in {
        "TIMEOUT_SENT",
        "TC_FORMED",
        "VIEW_CHANGED",
        "QC_FORMED",
    }:
        print(event)
