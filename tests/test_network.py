from pharmachain.simulation.network import SimulatedNetwork


def setup_net(**kwargs):
    net = SimulatedNetwork(**kwargs)
    inbox = {node: [] for node in ("v0", "v1", "v2", "v3")}
    for node in inbox:
        net.register(node, inbox[node].append)
    return net, inbox


def test_delayed_delivery():
    net, inbox = setup_net(latency=2)
    net.send("v0", "v1", "PROPOSE", "block")
    net.run(until=1)
    assert not inbox["v1"]
    net.run(until=2)
    assert inbox["v1"][0].payload == "block"


def test_partition_and_heal():
    net, inbox = setup_net()
    net.partition([{"v0", "v1"}, {"v2", "v3"}])
    net.send("v0", "v2", "VOTE", "vote")
    net.run()
    assert not inbox["v2"]
    net.heal()
    net.send("v0", "v2", "VOTE", "vote")
    net.run()
    assert len(inbox["v2"]) == 1


def test_disconnect_after_send_drops_on_delivery():
    net, inbox = setup_net()
    net.send("v0", "v1", "QC", "qc")
    net.disconnect("v1")
    net.run()
    assert not inbox["v1"]


def test_total_loss():
    net, inbox = setup_net(loss_rate=1)
    net.broadcast("v0", "PROPOSE", "block")
    net.run()
    assert all(not messages for messages in inbox.values())


def test_duplicates_are_delivered_separately():
    net, inbox = setup_net()
    net.send("v0", "v1", "VOTE", "vote", copies=2)
    net.run()
    assert len(inbox["v1"]) == 2
    assert inbox["v1"][0].message_id != inbox["v1"][1].message_id


def test_invalid_parameters():
    import pytest

    with pytest.raises(ValueError):
        SimulatedNetwork(loss_rate=1.2)
    net, _ = setup_net()
    with pytest.raises(ValueError):
        net.partition([{"v0", "v1"}, {"v1", "v2"}])
