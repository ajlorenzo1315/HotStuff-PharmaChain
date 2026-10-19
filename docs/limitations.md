# Alcance y limitaciones

## Lo que sí muestra la demo

Una visualización de propuestas, votos, QC, cambio de vista, regla de tres
cadenas y actualización diferida del estado de custodia. Seis escenarios
reproducibles mediante eventos simulados.

## Lo que no demuestra

- Nodos independientes ni transporte distribuido.
- Firmas criptográficas, agregación real o verificación de certificados.
- Resistencia formal a todas las estrategias bizantinas.
- Detección garantizada de equivocación en una red real.
- Seguridad ante Eclipse, Sybil, DDoS o particiones arbitrarias.
- Pruebas físicas de recepción de medicamentos.
- Rendimiento o escalabilidad de una implementación productiva.

FNV-1a se usa como identificador didáctico, no como hash seguro. Las
autorizaciones son etiquetas simbólicas. Las propiedades de HotStuff
estudiadas teóricamente no se trasladan automáticamente al simulador.

## Futuro trabajo

Réplicas independientes, mensajería con retrasos y pérdidas, Ed25519/SHA-256,
QC verificables, pacemaker configurable, pruebas de propiedades y experimentos
comparativos documentados.
