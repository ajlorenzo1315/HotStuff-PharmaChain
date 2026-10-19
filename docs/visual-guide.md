# Guía visual de HotStuff

[Volver al índice](README.md)

## 1. Validadores y cuórum

![Validadores](images/01-red-quorum.svg)

Con cuatro validadores, el modelo admite un fallo bizantino (`f = 1`).
Para formar un certificado de cuórum (QC) se requieren tres votos válidos.
Si dos validadores no participan, no se alcanza el cuórum.

## 2. Propuesta, voto y QC

![Secuencia de mensajes](images/02-flujo-hotstuff.svg)

El líder propone un bloque. Los validadores verifican la propuesta
y votan si las reglas de seguridad lo permiten. La agregación de
`2f + 1` votos produce un QC. **Un QC no es un commit inmediato**.

## 3. Confirmación en Chained HotStuff

![Tres cadenas](images/03-chained-commit.svg)

La regla de tres cadenas se aplica a bloques consecutivos y certificados
según las reglas del protocolo. El bloque más antiguo de esa secuencia
puede confirmarse. Un bloque propuesto o certificado puede seguir
sin estar confirmado.

## 4. Arquitectura del laboratorio

![Arquitectura](images/04-arquitectura.svg)

El código separa API, dominio farmacéutico, cadena, consenso, motores
y simulaciones. Los diagramas explican conceptos y responsabilidades,
no son trazas capturadas de una ejecución real.

## 5. Cómo demostrarlo en una exposición

1. Presenta una transferencia de custodia farmacéutica.
2. Identifica líder, validadores y cuórum.
3. Explica la diferencia entre QC y commit.
4. Provoca un líder inactivo y observa el cambio de vista.
5. Desactiva dos validadores y explica la pérdida de progreso.
6. Distingue las garantías teóricas de los resultados de la demo.
