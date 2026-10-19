# Guía de experimentos reproducibles

## Preparación

Abrir `index.html`, seleccionar un escenario y usar **Siguiente evento** para
registrar la secuencia. **Reiniciar** antes de cambiar de experimento. Los
resultados siguientes son comportamientos esperados del modelo, no mediciones
de una red real.

| ID | Preparación | Acción | Resultado esperado | Interpretación |
|---|---|---|---|---|
| A | Entrega legítima | Avanzar hasta confirmar | Propuesta, validación, votos, QC, confirmación | Un QC inicial no implica commit |
| B | Líder silencioso | Iniciar primera vista | Timeout y nueva vista | Recuperación didáctica por rotación |
| C | Equivocación | Iniciar primera vista | Se modela detección y no se forma QC | Supuesto idealizado de detección |
| D | Falta de autorización | Ejecutar propuesta | Rechazo antes de votar | Regla de negocio, no prueba de BFT |
| E | Doble transferencia | Confirmar primera y continuar | Segundo envío por custodio antiguo rechazado | Evita conflicto de custodia en el modelo |
| F | Dos nodos inactivos | Avanzar varias vistas | Menos de 3 votos, sin QC | No hay liveness con más fallos de los tolerados |

## Evidencias recomendadas

Para cada experimento, guardar captura de: escenario seleccionado, eventos,
número de votos, QC y estado de custodia. Anotar versión o commit del
repositorio y navegador utilizado.

## Resultados cuantitativos

No publicar valores de latencia real, throughput o complejidad de mensajes
como resultados experimentales de la demo HTML: los eventos y tiempos son
simulados. Para experimentos de backend, definir infraestructura, semillas,
tamaño de red, configuración y procedimientos reproducibles antes de presentar
cifras.

## Interpretación visual

![Red y umbral de cuórum](images/01-red-quorum.svg)

Un fallo de líder puede desencadenar un cambio de vista. Una pérdida de
quórum impide avanzar; por sí sola no demuestra una violación de seguridad.
El laboratorio visual ilustra los eventos, pero no mide latencia de red real.
