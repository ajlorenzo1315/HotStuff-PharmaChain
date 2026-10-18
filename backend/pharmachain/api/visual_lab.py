"""Isolated, evidence-backed traces for the HotStuff teaching UI."""

from __future__ import annotations

from collections import Counter
from pathlib import Path
from typing import Any

from fastapi import APIRouter, HTTPException, Query
from fastapi.responses import FileResponse

from pharmachain.api.education import get_guide

router = APIRouter(prefix="/api/visual", tags=["Visual lab"])
_ASSETS = Path(__file__).resolve().parent / "static"

GUIDES = {
    "offline_leader": (
        "Líder desconectado",
        "Se desconecta el líder de la vista antes de proponer.",
        "Disponibilidad: puede bloquear la propuesta hasta un cambio de vista.",
        "TIMEOUT/TC y rotación de líder pueden restaurar el progreso; un QC requiere 3 votos.",
    ),
    "quorum_loss": (
        "Pérdida de cuórum",
        "Se desconectan dos de cuatro validadores.",
        "Disponibilidad: con solo dos votos honestos posibles no se alcanza el umbral de 3.",
        "Restaurar conectividad o recuperar validadores; no reducir arbitrariamente el cuórum.",
    ),
    "forged_qc": (
        "QC falsificado",
        "Se altera la firma de un voto contenido en un QC de sincronización.",
        "Integridad: aceptar el certificado sin verificar firmas permitiría confiar en evidencia falsa.",
        "Verificar firmas, identidad de votantes, bloque y umbral antes de importar certificados.",
    ),
    "duplicate_qc": (
        "Certificado duplicado",
        "Se repite un certificado en la respuesta de sincronización.",
        "Integridad del protocolo de sincronización: el receptor debe aplicar la política de validación de certificados.",
        "Validar estructura y evitar aceptar evidencia duplicada como si fuese nueva.",
    ),
    "unsolicited_sync": (
        "Sincronización no solicitada",
        "Un remitente diferente al par esperado envía una respuesta.",
        "Autenticidad y contexto: una respuesta fuera de la solicitud puede contaminar el estado local.",
        "Vincular cada respuesta a la solicitud pendiente y al emisor esperado.",
    ),
    "valid_sync": (
        "Sincronización legítima",
        "Un nodo recibe una respuesta válida a una petición de sincronización.",
        "Control positivo: confirma que el mecanismo no rechaza indiscriminadamente toda respuesta.",
        "Aceptar solo bloques y certificados verificados y actualizar el estado atómicamente.",
    ),
    "equivocation": (
        "Líder equívoco",
        "Un líder propone ramas diferentes en una misma vista.",
        "Seguridad: pueden aparecer forks; no deben aparecer commits honestos incompatibles dentro del modelo de fallos.",
        "Una firma por vista y reglas de voto/bloqueo impiden que un nodo honesto vote dos veces.",
    ),
    "omit": (
        "Omisión de votos",
        "Validadores maliciosos reciben propuestas pero no emiten votos.",
        "Disponibilidad: la ausencia de votos puede impedir formar QC.",
        "Cambios de vista y suficientes votantes honestos son necesarios para el progreso.",
    ),
    "invalid_signature": (
        "Firma de voto inválida",
        "Validadores envían votos alterados criptográficamente.",
        "Integridad: el líder no debe incluir votos inválidos en un QC.",
        "Verificar cada voto antes de contarlo para el cuórum.",
    ),
}


def _event_kind(event: dict[str, Any]) -> str:
    name = str(event.get("event", "")).upper()
    if "REJECT" in name or "INVALID" in name or "FORGED" in name:
        return "REJECT"
    if "TIMEOUT" in name or "NEW_VIEW" in name or name.startswith("TC_"):
        return "VIEW_CHANGE"
    if "COMMIT" in name:
        return "COMMIT"
    if "QC" in name or "CERTIFICATE" in name:
        return "QC"
    if "VOTE" in name:
        return "VOTE"
    if "PROPOS" in name or "BLOCK_CREATED" in name:
        return "PROPOSE"
    if "SYNC" in name or "RECOVER" in name:
        return "SYNC"
    return "OTHER"


EVENT_EXPLANATIONS = {
    "PROPOSE": "Se anuncia una propuesta. Todavía no existe una decisión de consenso.",
    "VOTE": "Se observa actividad de voto; un voto aislado no alcanza el cuórum.",
    "QC": "Se registra actividad de certificado; comprueba las firmas y el umbral antes de considerarlo válido.",
    "COMMIT": "El simulador registra una confirmación. En Chained HotStuff se necesita la regla de tres cadenas.",
    "VIEW_CHANGE": "Se observa un cambio de vista o timeout. Puede afectar al progreso, no implica por sí mismo pérdida de seguridad.",
    "REJECT": "Se registra un rechazo o dato inválido; consulta la evidencia para conocer el motivo exacto.",
    "SYNC": "Se observa sincronización de estado; su aceptación depende de las verificaciones del receptor.",
    "OTHER": "Evento del simulador sin clasificación específica. No se infiere una transmisión no registrada.",
}


def explain_event(event: dict[str, Any]) -> str:
    """Return a conservative explanation; never claim unobserved packet delivery."""
    return EVENT_EXPLANATIONS[_event_kind(event)]


def analyze_trace(events: list[dict[str, Any]]) -> dict[str, Any]:
    """Calculate event frequencies and recorded message coverage only."""
    kinds = Counter(e.get("type", "OTHER") for e in events)
    names = Counter(e.get("name", "UNKNOWN") for e in events)
    count = len(events)
    with_endpoints = sum(bool(e.get("source") and e.get("target") and e["source"] != e["target"]) for e in events)
    times = [e["time"] for e in events if isinstance(e.get("time"), int | float)]
    views = {e["view"] for e in events if isinstance(e.get("view"), int)}
    return {
        "recorded_events": count,
        "rejection_events": kinds.get("REJECT", 0),
        "vote_events": kinds.get("VOTE", 0),
        "qc_related_events": kinds.get("QC", 0),
        "commit_related_events": kinds.get("COMMIT", 0),
        "view_change_events": kinds.get("VIEW_CHANGE", 0),
        "event_type_diversity": len(kinds),
        "trace_limited_to_300": count == 300,
        "types": dict(sorted(kinds.items())),
        "top_events": dict(names.most_common(12)),
        "observed_views": len(views),
        "recorded_transmissions": with_endpoints,
        "transmission_coverage_pct": round(100 * with_endpoints / count, 2) if count else None,
        "observed_time_span": round(max(times) - min(times), 6) if len(times) >= 2 else None,
        "notes": {
            "recorded_events": "Número de entradas incluidas en esta traza (máximo 300); no es el número de paquetes de la red.",
            "recorded_transmissions": "Eventos con origen y destino explícitos; no implica que sean entregas verificadas.",
            "transmission_coverage_pct": "Porcentaje de eventos con origen y destino registrados; mide observabilidad, no rendimiento.",
            "observed_views": "Vistas distintas que aparecen en la traza disponible.",
            "observed_time_span": "Diferencia de marcas temporales del simulador; no es tiempo de reloj ni latencia real.",
        },
    }


def normalize_events(events: list[dict[str, Any]]) -> list[dict[str, Any]]:
    """Retain source event fields, but provide a stable, bounded timeline schema."""
    trace = []
    for index, event in enumerate(events[-300:]):
        trace.append(
            {
                "step": index + 1,
                "time": event.get("time"),
                "type": _event_kind(event),
                "name": str(event.get("event", "UNKNOWN")),
                "source": str(event.get("sender") or event.get("node") or event.get("validator") or ""),
                "target": str(event.get("recipient") or event.get("receiver") or ""),
                "view": event.get("view"),
                "evidence": event,
                "explanation": explain_event(event),
            }
        )
    return trace


def build_attack_trace(name: str, result: dict[str, Any]) -> dict[str, Any]:
    if name not in GUIDES:
        raise ValueError("Escenario desconocido")
    title, mechanism, impact, mitigation = GUIDES[name]
    events = normalize_events(result.get("events") or [])
    passed = result.get("passed")
    if passed is True:
        conclusion = "El resultado observado cumple el criterio del experimento. No constituye una prueba formal del protocolo."
    elif passed is False:
        conclusion = "El resultado observado NO cumple el criterio del experimento; revisar la traza y la implementación."
    else:
        conclusion = "Resultado sin criterio booleano de éxito; interpretar únicamente la evidencia disponible."
    return {
        "id": name,
        "title": title,
        "mechanism": mechanism,
        "impact": impact,
        "mitigation": mitigation,
        "expected": result.get("expected", ""),
        "observation": result.get("observation", ""),
        "passed": passed,
        "conclusion": conclusion,
        "events": events,
        "analysis": analyze_trace(events),
        "raw_summary": {k: v for k, v in result.items() if k != "events"},
        "limitations": "Experimento educativo aislado; los eventos proceden del simulador, no de una red blockchain real.",
    }


@router.get("/guide/{scenario}")
def scenario_guide(scenario: str):
    """Educational methodology for a scenario, separate from empirical traces."""
    try:
        return get_guide(scenario)
    except ValueError as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc


@router.get("/catalog")
def catalog():
    return {"scenarios": [{"id": k, "title": v[0], "mechanism": v[1], "impact": v[2]} for k, v in GUIDES.items()]}


@router.get("/attack/{scenario}")
def attack_trace(scenario: str):
    if scenario not in GUIDES:
        raise HTTPException(status_code=404, detail="Escenario desconocido")
    try:
        if scenario == "equivocation":
            from pharmachain.api.fork_experiment import run_fork_experiment

            result = run_fork_experiment()
            # Preserve full fork data for its dedicated graph, and show recorded events when available.
            result = {**result, "events": result.get("events", []), "passed": result.get("passed")}
        elif scenario in {"omit", "invalid_signature"}:
            raise HTTPException(status_code=422, detail="Utiliza /api/visual/byzantine para estos modos")
        else:
            from pharmachain.api.attacks import run_scenario

            result = run_scenario(scenario)
        return build_attack_trace(scenario, result)
    except HTTPException:
        raise
    except (ValueError, RuntimeError) as exc:
        raise HTTPException(status_code=409, detail=str(exc)) from exc


@router.get("/byzantine")
def byzantine_trace(mode: str = Query("omit"), rounds: int = Query(12, ge=1, le=100), seed: int = 42):
    if mode not in ("omit", "invalid_signature"):
        raise HTTPException(status_code=422, detail="Modo desconocido")
    from pharmachain.api.byzantine_benchmark import compare

    try:
        comparison = compare(mode=mode, rounds=rounds, seed=seed)
    except (ValueError, RuntimeError) as exc:
        raise HTTPException(status_code=409, detail=str(exc)) from exc
    title, mechanism, impact, mitigation = GUIDES[mode]
    scenarios = []
    for scenario in comparison["scenarios"]:
        details = scenario.get("round_details", [])
        rounds_trace = [
            {
                "step": i + 1,
                "time": None,
                "type": "QC" if item.get("qc_formed") else "VIEW_CHANGE",
                "name": "QC_FORMED" if item.get("qc_formed") else "ROUND_WITHOUT_QC",
                "source": str(item.get("leader", "")),
                "target": "",
                "view": item.get("view"),
                "evidence": item,
            }
            for i, item in enumerate(details)
        ]
        scenarios.append({**scenario, "events": rounds_trace, "analysis": analyze_trace(rounds_trace)})
    return {
        "id": mode,
        "title": title,
        "mechanism": mechanism,
        "impact": impact,
        "mitigation": mitigation,
        "scenarios": scenarios,
        "conclusion": "Compara los QC y alturas realmente observados. Con dos fallos se supera el límite teórico f=1; no se infiere seguridad formal.",
        "limitations": "Los pasos representan resultados por ronda; no se inventan mensajes internos no registrados.",
    }


@router.get("/assets/{filename}", include_in_schema=False)
def visual_asset(filename: str):
    if filename not in {"visual_lab.js", "visual_lab.css"}:
        raise HTTPException(status_code=404, detail="Recurso no encontrado")
    return FileResponse(_ASSETS / filename)


@router.get("/gif/{scenario}", include_in_schema=False)
def scenario_gif(scenario: str):
    """Conceptual GIF; never presented as an actual recorded network trace."""
    if scenario not in GUIDES:
        raise HTTPException(status_code=404, detail="Escenario desconocido")
    return FileResponse(_ASSETS / "gifs" / f"{scenario}.gif", media_type="image/gif")
