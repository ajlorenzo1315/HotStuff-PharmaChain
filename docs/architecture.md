# Arquitectura del laboratorio

![Arquitectura del proyecto](images/04-arquitectura.svg)

## Componentes

1. `index.html`: demostración independiente en el navegador.
2. `pharmachain/api/main.py`: API local basada en `PharmaService`.
3. `pharmachain/api/dashboard.py`: API y panel distribuido.
4. `domain/`: organizaciones, lotes, transacciones y estado.
5. `blockchain/`: bloques y cadena de bloques confirmados.
6. `consensus/`: motor educativo y simulador distribuido.
7. `simulation/`: escenarios, red y pruebas de fallos.
8. `engines/`: abstracciones para comparar motores.

## Flujos

La API de lotes construye transacciones desde peticiones HTTP.
`PharmaService` mantiene un `HotStuffEngine` en memoria.
El dashboard utiliza `DistributedHotStuff` y otras herramientas.
No son necesariamente el mismo proceso ni comparten estado.

## Límites

No confundas simulación de nodos con despliegue de procesos
independientes ni certificados simulados con pruebas de seguridad
criptográfica en un entorno adversarial real.
