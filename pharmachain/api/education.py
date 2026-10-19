"""Teaching guides for the nine HotStuff demonstrations.

These steps describe experiment methodology, not invented runtime events.
"""

from __future__ import annotations

GUIDED_SCENARIOS = {
    "offline_leader": {
        "title": "Fallo del líder y recuperación",
        "category": "Disponibilidad",
        "objective": "Comprobar cómo se gestiona una vista cuyo líder no puede proponer.",
        "steps": [
            "Identificar al líder de la vista",
            "Desconectar al líder antes de la propuesta",
            "Observar ausencia de propuesta y eventos TIMEOUT",
            "Buscar certificado de timeout y siguiente líder",
            "Verificar si vuelve a formarse un QC",
        ],
        "expected": "El progreso puede detenerse temporalmente; el cambio de vista intenta recuperarlo.",
        "evidence": "TIMEOUT/TC o eventos equivalentes y formación posterior de QC.",
    },
    "quorum_loss": {
        "title": "Pérdida de cuórum",
        "category": "Disponibilidad",
        "objective": "Determinar si dos nodos restantes pueden certificar un bloque.",
        "steps": [
            "Partir de n=4 y umbral q=3",
            "Desconectar dos validadores",
            "Intentar proponer y reunir votos",
            "Comprobar número de votos y QC",
            "Restablecer conectividad y comparar",
        ],
        "expected": "Con solo dos votos disponibles no se alcanza q=3.",
        "evidence": "Votos válidos, QC formado o ausente, reconexión.",
    },
    "forged_qc": {
        "title": "Falsificación de certificado",
        "category": "Integridad criptográfica",
        "objective": "Verificar que el receptor no acepta pruebas de cuórum adulteradas.",
        "steps": [
            "Construir un certificado legítimo",
            "Modificar la firma de un voto",
            "Presentar el certificado manipulado",
            "Observar verificación y rechazo",
            "Comprobar que el estado no se altera",
        ],
        "expected": "Un QC con firma inválida debe rechazarse.",
        "evidence": "Evento de rechazo y estado antes/después.",
    },
    "duplicate_qc": {
        "title": "Repetición de certificados",
        "category": "Validación de datos",
        "objective": "Comprobar cómo se tratan certificados repetidos.",
        "steps": [
            "Obtener un QC válido",
            "Incluirlo repetido en una respuesta de sincronización",
            "Enviar la respuesta",
            "Observar aceptación o rechazo según la política",
            "Comprobar ausencia de votos contados dos veces",
        ],
        "expected": "La repetición no debe contar como evidencia adicional independiente.",
        "evidence": "Registro de validación y efectos en estado.",
    },
    "unsolicited_sync": {
        "title": "Respuesta de sincronización no solicitada",
        "category": "Autenticidad de mensajes",
        "objective": "Comprobar la asociación entre respuesta, petición y remitente.",
        "steps": [
            "Registrar una petición pendiente a un nodo concreto",
            "Preparar una respuesta desde otro emisor",
            "Entregar la respuesta no esperada",
            "Verificar el rechazo por contexto",
            "Comprobar integridad del estado local",
        ],
        "expected": "La respuesta no autorizada no debe incorporarse.",
        "evidence": "Remitente esperado, rechazo y estado posterior.",
    },
    "valid_sync": {
        "title": "Sincronización legítima",
        "category": "Control positivo",
        "objective": "Comprobar que la validación permite recuperar un nodo atrasado.",
        "steps": [
            "Desconectar un nodo",
            "Generar nuevos bloques certificados",
            "Reconectar el nodo",
            "Solicitar y verificar la cadena de ancestros",
            "Comparar alturas y certificados",
        ],
        "expected": "El nodo debe recuperar datos válidos sin saltarse verificaciones.",
        "evidence": "SYNC_COMPLETED y altura de cadena actualizada.",
    },
    "equivocation": {
        "title": "Equivocación del líder y bifurcación",
        "category": "Safety",
        "objective": "Examinar propuestas incompatibles emitidas en una misma vista.",
        "steps": [
            "Seleccionar un líder adversario",
            "Construir dos propuestas incompatibles",
            "Distribuirlas a grupos diferentes",
            "Registrar los votos por validador",
            "Comprobar QC y commits incompatibles",
        ],
        "expected": "Pueden existir ramas, pero no commits honestos incompatibles bajo las hipótesis del protocolo.",
        "evidence": "Propuestas, votos, QC y auditoría de safety.",
    },
    "omit": {
        "title": "Omisión de votos bizantinos",
        "category": "Liveness",
        "objective": "Comparar progreso con 0, 1 y 2 validadores que omiten votos.",
        "steps": [
            "Ejecutar el escenario sin fallos",
            "Inyectar omisión en un validador",
            "Repetir con dos validadores",
            "Comparar QC por ronda y alturas",
            "Interpretar el límite f=1",
        ],
        "expected": "Con dos votos honestos no hay cuórum garantizado; la ausencia de QC afecta al progreso.",
        "evidence": "qc_rounds, qc_rate, omitted_votes y alturas.",
    },
    "invalid_signature": {
        "title": "Votos con firma inválida",
        "category": "Integridad y liveness",
        "objective": "Verificar que votos manipulados no se cuentan para el QC.",
        "steps": [
            "Ejecutar línea base",
            "Alterar las firmas de uno o dos validadores",
            "Enviar votos al líder",
            "Observar rechazo de votos inválidos",
            "Comparar QC y altura confirmada",
        ],
        "expected": "Un voto inválido no debe aportar al cuórum.",
        "evidence": "INVALID_VOTE, QC por ronda y auditoría.",
    },
}


def get_guide(scenario: str) -> dict:
    if scenario not in GUIDED_SCENARIOS:
        raise ValueError("Unknown demonstration")
    return {
        "id": scenario,
        **GUIDED_SCENARIOS[scenario],
        "disclaimer": "Methodological steps are explanatory, not recorded network events.",
    }
