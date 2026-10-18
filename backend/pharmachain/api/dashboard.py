"""Dashboard local para la simulación distribuida de PharmaChain.

Ejecutar desde backend/: uvicorn pharmachain.api.dashboard:app --reload --port 8001
"""

from __future__ import annotations

from pathlib import Path
from threading import RLock

from fastapi import FastAPI, HTTPException
from fastapi.responses import FileResponse
from pydantic import BaseModel

from pharmachain.api.attacks import SCENARIOS, run_scenario
from pharmachain.consensus.distributed import DistributedHotStuff
from pharmachain.consensus.safety import (
    audit_committed_safety,
    demonstrate_conflict_detection,
)
from pharmachain.domain.state import LedgerState

app = FastAPI(title="PharmaChain · Distributed HotStuff Dashboard")
_lock = RLock()
_sim: DistributedHotStuff | None = None
_STATIC = Path(__file__).resolve().parent / "static" / "index.html"


class NodeAction(BaseModel):
    node_id: str


def _simulator() -> DistributedHotStuff:
    global _sim
    if _sim is None:
        _sim = DistributedHotStuff(LedgerState({}), validator_count=4)
    return _sim


def _validate_node(sim: DistributedHotStuff, node_id: str) -> None:
    if node_id not in sim.nodes:
        raise HTTPException(status_code=404, detail="Validador desconocido")


def _snapshot(sim: DistributedHotStuff) -> dict:
    nodes = []
    for node_id, runtime in sim.nodes.items():
        node = runtime.node
        nodes.append(
            {
                "id": node_id,
                "online": node_id not in sim.network.offline,
                "view": node.view,
                "height": node.committed_height,
                "blocks": len(node.blockchain.blocks),
                "certificates": len(node.certificates),
                "recovering": runtime.recovering,
            }
        )
    return {
        "view": sim.view,
        "leader": sim.leader_id(sim.view),
        "quorum": sim.quorum,
        "nodes": nodes,
        "events": sim.events[-150:],
    }


@app.get("/")
def home():
    return FileResponse(_STATIC)


@app.get("/api/simulation")
def status():
    with _lock:
        return _snapshot(_simulator())


@app.post("/api/simulation/reset")
def reset():
    global _sim
    with _lock:
        _sim = DistributedHotStuff(LedgerState({}), validator_count=4)
        return _snapshot(_sim)


@app.post("/api/simulation/round")
def round_step():
    with _lock:
        sim = _simulator()
        result = sim.run_round()
        return {
            "round": {
                "view": result.view,
                "leader": result.leader,
                "votes": result.votes,
                "qc_formed": result.qc_formed,
                "committed_heights": result.committed_heights,
            },
            "state": _snapshot(sim),
        }


@app.post("/api/simulation/disconnect")
def disconnect(action: NodeAction):
    with _lock:
        sim = _simulator()
        _validate_node(sim, action.node_id)
        sim.network.disconnect(action.node_id)
        sim._record("NODE_DISCONNECTED", node=action.node_id)
        return _snapshot(sim)


@app.post("/api/simulation/reconnect")
def reconnect(action: NodeAction):
    with _lock:
        sim = _simulator()
        _validate_node(sim, action.node_id)
        sim.network.reconnect(action.node_id)
        sim._record("NODE_RECONNECTED", node=action.node_id)
        return _snapshot(sim)


@app.post("/api/simulation/recover")
def recover(action: NodeAction):
    with _lock:
        sim = _simulator()
        _validate_node(sim, action.node_id)
        try:
            completed = sim.reconnect_and_sync(action.node_id)
        except (ValueError, RuntimeError) as exc:
            raise HTTPException(status_code=409, detail=str(exc)) from exc
        return {"completed": completed, "state": _snapshot(sim)}


@app.get("/api/attacks")
def attack_catalog():
    return {
        "scenarios": [{"id": key, "title": title} for key, title in SCENARIOS.items()]
    }


@app.post("/api/attacks/{scenario}")
def attack_run(scenario: str):
    if scenario not in SCENARIOS:
        raise HTTPException(status_code=404, detail="Escenario desconocido")
    with _lock:
        try:
            return run_scenario(scenario)
        except RuntimeError as exc:
            raise HTTPException(status_code=409, detail=str(exc)) from exc


@app.get("/api/safety")
def safety_status():
    with _lock:
        return audit_committed_safety(_simulator())


@app.post("/api/safety/injected-conflict")
def safety_injected_conflict():
    return demonstrate_conflict_detection()


@app.post("/api/safety/equivocation")
def safety_equivocation():
    """Run an isolated Byzantine-leader fork experiment."""
    from pharmachain.api.fork_experiment import run_fork_experiment

    try:
        return run_fork_experiment()
    except RuntimeError as exc:
        raise HTTPException(status_code=409, detail=str(exc)) from exc
