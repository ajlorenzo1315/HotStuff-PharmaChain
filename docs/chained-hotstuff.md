# Chained HotStuff: confirmación por tres cadenas

![Regla de tres cadenas](images/03-chained-commit.svg)

Chained HotStuff encadena propuestas y certificados entre vistas consecutivas
para solapar las fases de consenso. No debe confundirse «obtener un QC» con
«confirmar definitivamente el bloque».

## Ejemplo

```text
B1  <- B2  <- B3  <- B4
      QC1    QC2    QC3
```

En la presentación simplificada, cuando se forma una cadena directa de tres
bloques certificados según la regla aplicable, el ancestro correspondiente
puede confirmarse. La implementación precisa debe verificar la relación
padre-hijo, la justificación y las vistas requeridas por la variante
estudiada; no basta con contar tres QC cualesquiera.

## Flujo didáctico

1. Un líder propone un bloque extendiendo una rama justificada.
2. Las réplicas honestas validan propuesta y reglas de bloqueo.
3. Con `2f+1` votos se forma un QC.
4. Una propuesta posterior extiende la rama certificada.
5. La cadena de certificados satisface la regla de commit y permite aplicar al
estado de negocio los bloques confirmados.

## Ventaja frente a la presentación por fases separadas

La variante encadenada solapa el trabajo de varias vistas y permite
procesamiento en pipeline. Su coste conceptual es que un bloque puede estar
propuesto o certificado sin estar confirmado.

## En PharmaChain

El simulador visual presenta bloques, QC y estado confirmado por separado. El
cambio de custodio solo se refleja al confirmar, evitando equiparar propuesta
con entrega definitiva.
