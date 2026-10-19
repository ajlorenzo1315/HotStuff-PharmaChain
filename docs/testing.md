# Estrategia de pruebas

## Pruebas manuales de la demo HTML

- [ ] A: los primeros QC no actualizan prematuramente el custodio.
- [ ] A: tras commit, el custodio cambia una sola vez.
- [ ] B: se observa timeout y cambio de vista.
- [ ] C: la equivocación no genera QC en el modelo.
- [ ] D: una autorización ausente impide validar.
- [ ] E: la segunda transferencia desde el custodio anterior se rechaza.
- [ ] F: con dos inactivos no se alcanza el quórum.
- [ ] Reiniciar restaura la custodia y los contadores.

## Pruebas automatizadas propuestas

Las siguientes son recomendaciones, **no pruebas afirmadas como existentes**:

1. Invariantes de seguridad: ausencia de commits incompatibles, voto único por
vista, aplicación única de transacciones.
2. Propiedades de progreso bajo sincronía eventual y hasta `f` fallos.
3. Tests de validación de lotes, cantidades, custodios y autorizaciones.
4. Tests de integración API y de Docker, si esos componentes están realmente
implementados.
5. Repetición con semillas y comparación de métricas bajo condiciones
controladas.

## Evidencia

Registrar commit, versión de Python y herramientas, comandos exactos,
configuración, salida de tests y explicación de fallos. No declarar cobertura,
tiempos o resultados hasta ejecutarlos.
