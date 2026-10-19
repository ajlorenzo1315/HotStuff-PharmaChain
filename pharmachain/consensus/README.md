# Consenso HotStuff

Módulo principal de consenso y coordinación de validadores.

| Archivo | Responsabilidad |
| --- | --- |
| `engine.py` | Motor educativo centralizado `HotStuffEngine` |
| `distributed.py` | Simulador `DistributedHotStuff` |
| `validator.py` | Identidades de validadores |
| `node.py` | Comportamiento de nodos |
| `messages.py` | Mensajes y certificados de quórum |
| `pacemaker.py` | Progreso y gestión de tiempos |
| `new_view.py` | Mensajes de nueva vista |
| `view_change.py` | Cambios de vista |
| `sync.py` | Sincronización |
| `safety.py` | Auditorías de seguridad |
| `quorum_audit.py` | Comprobaciones de quórum |

## Quórum

El motor centralizado exige `n = 3f + 1` y calcula `2f + 1` votos.
Con cuatro validadores: `f = 1` y el quórum es tres.

Un QC no equivale automáticamente a un bloque confirmado. El modelo
debe cumplir las reglas de votación, bloqueo y confirmación.

## Pruebas relevantes

```bash
python -m pytest tests/test_hotstuff.py tests/test_distributed.py
python -m pytest tests/test_safety.py tests/test_pacemaker.py
```

Lee [HotStuff](../../docs/hotstuff.md) y
[Chained HotStuff](../../docs/chained-hotstuff.md).
