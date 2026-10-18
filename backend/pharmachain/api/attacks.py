"""Controlled adversarial scenarios for the local HotStuff teaching dashboard.

These simulations are independent from the interactive dashboard state.
"""

from __future__ import annotations

from dataclasses import replace
from types import SimpleNamespace

from pharmachain.consensus.distributed import DistributedHotStuff
from pharmachain.consensus.sync import BlockResponse, ancestry
from pharmachain.domain.state import LedgerState

SCENARIOS = {
    "offline_leader": "Líder desconectado",
    "quorum_loss": "Pérdida del cuórum",
    "forged_qc": "QC con firma falsificada",
    "duplicate_qc": "QC duplicado",
    "unsolicited_sync": "Respuesta de sincronización no solicitada",
    "valid_sync": "Sincronización legítima (control)",
}


def _sync_fixture():
    sim = DistributedHotStuff(LedgerState({}), validator_count=4)
    target_node = "validator-2"
    source = "validator-0"
    sim.network.disconnect(target_node)
    result = sim.run_round()
    if not result.qc_formed or result.block_hash is None:
        raise RuntimeError("La ronda de preparación no produjo un QC")
    sim.network.reconnect(target_node)
    source_node = sim.nodes[source].node
    blocks = ancestry(source_node.blockchain.blocks, result.block_hash)
    certificates = tuple(
        source_node.certificates[block.block_hash]
        for block in blocks
        if block.block_hash in source_node.certificates
    )
    if not certificates:
        raise RuntimeError("La preparación no produjo certificados")
    sim.request_sync(target_node, source, result.block_hash)
    response = BlockResponse(result.block_hash, blocks, certificates)
    return sim, source, target_node, response


def run_scenario(name: str) -> dict:
    if name not in SCENARIOS:
        raise ValueError(f"Escenario desconocido: {name}")
    if name in {"offline_leader", "quorum_loss"}:
        sim = DistributedHotStuff(LedgerState({}), validator_count=4)
        offline = (
            ["validator-0"]
            if name == "offline_leader"
            else ["validator-1", "validator-2"]
        )
        for node_id in offline:
            sim.network.disconnect(node_id)
            sim._record("ATTACK_NODE_OFFLINE", node=node_id)
        result = sim.run_round()
        passed = not result.qc_formed
        observation = (
            f"Vista {result.view}: {result.votes} votos; QC formado: {result.qc_formed}"
        )
        expected = "No se forma QC en esta ronda sin el líder/cuórum requerido"
    else:
        sim, source, recipient, response = _sync_fixture()
        if name == "forged_qc":
            qc = response.certificates[0]
            vote = replace(qc.votes[0], signature="00" * 64)
            forged = replace(qc, votes=(vote, *qc.votes[1:]))
            response = replace(response, certificates=(forged,))
        elif name == "duplicate_qc":
            response = replace(response, certificates=(response.certificates[0],) * 2)
        elif name == "unsolicited_sync":
            source = "validator-3"
        # Direct delivery allows us to isolate the injected response from the
        # genuine response already queued by request_sync().
        sim._on_block_response(
            recipient, SimpleNamespace(sender=source, payload=response)
        )
        node = sim.nodes[recipient].node
        accepted = response.target_hash in node.blockchain.blocks
        certified = response.target_hash in node.certificates
        rejected = any(e["event"] == "SYNC_REJECTED" for e in sim.events)
        if name == "valid_sync":
            passed = accepted and certified and not rejected
            expected = "Se aceptan el bloque y su QC legítimos"
        else:
            passed = rejected and not accepted and not certified
            expected = "Se rechaza el mensaje sin modificar la cadena local"
        observation = f"Bloque incorporado: {accepted}; \
            QC incorporado: {certified}; rechazo registrado: {rejected}"
    sim._record("ATTACK_SCENARIO_RESULT", scenario=name, passed=passed)
    return {
        "scenario": name,
        "title": SCENARIOS[name],
        "passed": passed,
        "expected": expected,
        "observation": observation,
        "events": sim.events[-100:],
    }
