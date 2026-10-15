# HotStuff PharmaChain

Demo local, autocontenida y en español para presentar HotStuff BFT aplicado a la trazabilidad farmacéutica.

## Ejecución

Abre `index.html` en Chrome, Edge o Firefox. No necesita conexión, paquetes ni servidor. Opcionalmente: `python -m http.server 8000` y abre `http://localhost:8000`.

## Guion de demostración

1. **A — Entrega legítima**: pulsa «Siguiente evento». Observa PROPOSE, VALIDATE, VOTE, QC y la confirmación diferida por la regla de tres cadenas. Los primeros QC no transfieren todavía la custodia.
2. **B — Líder silencioso**: el primer líder no propone. Observa TIMEOUT, NEW-VIEW y la recuperación con otro líder.
3. **C — Equivocación**: el primer líder envía dos propuestas distintas. El modelo simplificado simula que se detectan y no se forma QC; después continúa con otro líder.
4. **D — Transferencia sin autorización**: el emisor no aporta ambas autorizaciones simbólicas. La validación de negocio rechaza la propuesta.
5. **E — Doble transferencia**: tras confirmarse la primera transferencia, el fabricante intenta enviar el mismo lote al hospital. La propuesta se rechaza porque el custodio confirmado ya es el distribuidor.
6. **F — Dos nodos inactivos**: solo hay dos votos disponibles; no se forma QC y la red no progresa.

## Modelo

- 4 validadores identificados, tolerancia `f=1`, quórum `2f+1=3`.
- Vistas y líder rotativo, propuestas, votos, QC, timeout y tres cadenas consecutivas.
- Una máquina de estados de custodia, con lote, cantidad, propietario y autorizaciones simbólicas.
- Cadena local de bloques con hashes didácticos FNV-1a (NO criptográficos).
- Los bloques con QC no se aplican al estado de negocio hasta que son confirmados.

## Limitaciones académicas (declararlas durante la presentación)

**No es una implementación de referencia de HotStuff**: no hay nodos aislados en procesos, transporte de red real, firmas digitales, certificados criptográficamente verificables, ni pacemaker adaptativo. El estado de consenso está centralizado en un simulador de eventos discretos. Los votos, locks y equivocaciones están idealizados. El caso C asume detección de equivocación; no demuestra que todos los nodos honestos siempre detecten un ataque real. Los hashes son identificadores ilustrativos y no ofrecen resistencia criptográfica. Las firmas de custodia son etiquetas simbólicas. Tampoco verifica entregas físicas: para eso hacen falta pruebas externas. No usar con datos sanitarios reales ni para producción.

## Extensiones recomendadas

- Estado independiente por réplica y simulación de mensajes con latencia y pérdida.
- Firmas Ed25519, verificación de QC y hash SHA-256.
- Pacemaker adaptativo frente a fijo con métricas reproducibles.
- Escenario de doble gasto con dos transacciones incompatibles y trazas comparadas.
- Pruebas de safety, liveness bajo sincronía eventual y reproducibilidad con semillas.

## Fuentes de estudio

- Yin et al., *HotStuff: BFT Consensus with Linearity and Responsiveness*, PODC 2019. https://arxiv.org/abs/1803.05069
- https://github.com/boriscu/Adaptive-Pacemaker-HotStuff
- https://github.com/harmanhanjra/bft-consensus-simulator

Código de demostración creado para fines educativos; no incorpora ni copia código de los repositorios citados.
