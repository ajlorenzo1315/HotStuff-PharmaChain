# Modelo de amenazas

![Red de cuatro validadores](images/01-red-quorum.svg)

## Activos

Integridad de la cadena confirmada, unicidad de la custodia, disponibilidad
del servicio, identidad de los validadores y evidencias de autorización.

## Adversarios y escenarios

| Amenaza | Efecto posible | Tratamiento en la demo | Límite |
|---|---|---|---|
| Líder bizantino silencioso | Retrasa el progreso | Timeout y cambio de vista | Temporizadores simulados |
| Equivocación | Propuestas incompatibles | Detección idealizada | No modela propagación real |
| Nodos inactivos | Pérdida de quórum | Dos inactivos impiden QC | Excede `f=1` |
| Transferencia fraudulenta | Custodia inválida | Validación de negocio | Firmas simbólicas |
| Doble transferencia | Registro contradictorio | Verificación de custodio | No es ataque de doble gasto monetario |
| Sybil | Identidades falsas | No implementado | Se asume conjunto cerrado de validadores |
| Eclipse / partición | Aislamiento de réplicas | No implementado | Sin transporte de red |
| Denegación de servicio | Degradación de disponibilidad | Parcialmente ilustrada | Sin tráfico real |

## Umbral de corrupción

Con cuatro validadores, un adversario bizantino está dentro del modelo
(`f=1`). Con dos réplicas inactivas, la demo no puede reunir tres votos; esto
muestra una limitación de progreso, **no una ruptura demostrada de safety**.

## Mitigaciones para una implementación real

Autenticación de nodos, firmas verificables, gestión de claves, control de
membresía, límites de recursos, monitorización, pruebas de partición y
auditoría independiente. Las garantías del consenso dependen de una
implementación correcta y de sus supuestos.
