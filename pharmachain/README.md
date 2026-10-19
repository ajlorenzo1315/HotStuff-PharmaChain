# Paquete `pharmachain`

Código Python del laboratorio. Las carpetas separan lógica de negocio,
almacenamiento, consenso, presentación y experimentación.

| Carpeta | Responsabilidad |
| --- | --- |
| `api/` | Servicios HTTP, dashboard y escenarios de ataque |
| `blockchain/` | Estructuras de bloques y cadena |
| `consensus/` | Vistas, líderes, QC, seguridad y recuperación |
| `domain/` | Lotes, organizaciones, transacciones y firmas |
| `simulation/` | Red simulada, escenarios y demostraciones |

## Flujo conceptual

1. Una solicitud llega a la API o al simulador.
2. El dominio comprueba reglas y representa la transacción.
3. El motor de consenso procesa propuestas, votos y certificados.
4. La blockchain refleja los bloques que el modelo confirma.
5. La API y los escenarios muestran eventos y estado resultante.

No todos los puntos de entrada comparten la misma instancia de motor.
Consulta [arquitectura](../docs/architecture.md).
