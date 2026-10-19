# Fundamentos de HotStuff BFT

![Propuesta y certificado de cuórum](images/02-flujo-hotstuff.svg)

HotStuff es un protocolo de consenso bizantino basado en líderes, certificados
de quórum y reglas de votación seguras. Fue diseñado para reducir los costes
de comunicación asociados a los cambios de líder y ofrecer *responsiveness*
optimista tras alcanzar sincronía suficiente.

## Modelo de fallos

En el modelo clásico, `n >= 3f + 1` réplicas permiten tolerar hasta `f`
réplicas bizantinas. Un QC requiere `2f + 1` votos distintos válidos. En el
laboratorio: `n=4`, `f=1`, QC de 3 votos. Dos quórums de tamaño 3 sobre 4 se
intersecan en al menos 2 réplicas, de las cuales al menos una es honesta si
hay como máximo una bizantina.

## Conceptos

- **View:** ronda lógica con un líder asignado.
- **Proposal:** bloque candidato y justificación.
- **Vote:** apoyo de una réplica a una propuesta que cumple sus reglas
  de seguridad.
- **QC:** prueba agregada de suficientes votos; requiere verificación
  criptográfica en sistemas reales.
- **HighQC:** QC de mayor vista conocido, que justifica propuestas
  posteriores.
- **Lock:** restricción de voto sobre ramas conflictivas, con reglas
  seguras de desbloqueo.
- **Pacemaker:** mecanismo de progreso y cambio de vista ante retrasos o fallos.

## Safety y liveness

**Safety:** no confirmar dos historias incompatibles bajo el límite de fallos
y los supuestos del protocolo. **Liveness:** el sistema puede progresar cuando
la red llega a ser suficientemente síncrona y hay líderes honestos; no implica
progreso durante particiones arbitrarias.

## Diferencia entre consenso y reglas de negocio

HotStuff ordena decisiones compartidas. Una validación como «el emisor debe
ser el custodio» pertenece a la máquina de estados de la aplicación. Ambas
capas son necesarias y deben evaluarse separadamente.

Consulta también [Chained HotStuff](chained-hotstuff.md) y [la referencia
académica](references.md).
