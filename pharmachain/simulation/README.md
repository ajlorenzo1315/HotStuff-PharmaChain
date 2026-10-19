# Simulación y demostraciones

| Archivo | Propósito |
| --- | --- |
| `network.py` | Entrega de mensajes en la red simulada |
| `simulation.py` | Coordinación de la simulación |
| `scenarios.py` | Escenarios predefinidos |
| `pharma_scenario.py` | Caso farmacéutico |
| `verify_custody.py` | Verificación del estado de custodia |
| `demo_attacks.py` | Demostración de ataques |
| `demo_distributed.py` | Demostración distribuida |
| `demo_network.py` | Demostración de red |
| `demo_new_view.py` | Nueva vista |
| `demo_pacemaker.py` | Temporizadores y progreso |
| `demo_recovery.py` | Recuperación |
| `demo_sync.py` | Sincronización |
| `demo_view_change.py` | Cambio de vista |

## Ejecución de una demo

```bash
python -m pharmachain.simulation.demo_attacks
python -m pharmachain.simulation.demo_distributed
```

Los scripts pueden imprimir eventos sin iniciar un servidor web.
Para comparar resultados, anota configuración, versión y semillas.

Consulta [experimentos](../../docs/experiments.md).
