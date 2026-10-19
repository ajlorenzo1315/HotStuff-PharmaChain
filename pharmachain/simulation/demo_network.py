from pharmachain.simulation.network import SimulatedNetwork

network = SimulatedNetwork(latency=0.5, seed=42)

for i in range(4):
    node_id = f"validator-{i}"

    def receive(message, node=node_id):
        print(f"[{network.time:.1f}s] {node} recibe {message.kind} de {message.sender}")

    network.register(node_id, receive)

# Dos grupos aislados
network.partition(
    [
        {"validator-0", "validator-1"},
        {"validator-2", "validator-3"},
    ]
)

network.broadcast(
    "validator-0",
    "PROPOSE",
    {"view": 1, "block": "B1"},
)

network.run()

print("\nEventos:")
for event in network.events:
    print(event.action, event.sender, "->", event.recipient)

print("\nRestaurando conexiones...")
network.heal()

network.broadcast(
    "validator-0",
    "PROPOSE",
    {"view": 2, "block": "B2"},
)

network.run()
