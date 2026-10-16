from pharmachain.domain.state import LedgerState
from pharmachain.engines.events import EventType
from pharmachain.simulation.simulation import Simulation


def test_three_views_commit():
    sim = Simulation(LedgerState({}))

    for _ in range(3):
        sim.step()

    assert any(event.event_type == EventType.BLOCK_COMMITTED for event in sim.events)

    assert sim.engine.blockchain.committed_height == 1


def test_inactive_leader_timeout():
    sim = Simulation(LedgerState({}))

    sim.set_active("validator-0", False)

    events = sim.step()

    assert any(event.event_type == EventType.TIMEOUT for event in events)

    assert sim.snapshot()["view"] == 2


def test_quorum_failure():
    sim = Simulation(LedgerState({}))

    sim.set_active("validator-2", False)
    sim.set_active("validator-3", False)

    events = sim.step()

    assert not any(event.event_type == EventType.QC_FORMED for event in events)

    assert any(event.event_type == EventType.TIMEOUT for event in events)


def test_reset():
    sim = Simulation(LedgerState({}))

    sim.step()
    sim.reset()

    assert sim.snapshot()["view"] == 1
    assert sim.events == []
