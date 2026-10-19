# Blockchain

- `block.py`: representación de bloques y sus identificadores.
- `chain.py`: mantenimiento de bloques, relaciones y estado confirmado.

El módulo almacena los resultados del consenso educativo. Un bloque
propuesto no debe interpretarse como definitivamente confirmado.

## Verificación

```bash
python -m pytest tests/test_blockchain.py -v
```

Revisa también los tests de integración del motor de consenso.
