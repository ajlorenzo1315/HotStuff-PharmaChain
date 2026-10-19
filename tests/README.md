# Pruebas automatizadas

La suite principal está en `tests/` y es la ruta configurada en
`pyproject.toml` mediante `testpaths = ["tests"]`.

## Ejecutar

```bash
python -m pip install -e '.[dev]'
python -m pytest -v
python -m pytest --cov=pharmachain --cov-report=term-missing
```

## Cobertura funcional

Los archivos `test_hotstuff.py`, `test_safety.py`,
`test_distributed.py`, `test_new_view.py` y `test_pacemaker.py`
cubren aspectos del consenso. `test_blockchain.py` y
`test_pharmachain_domain.py` cubren bloques y negocio.

Otros tests ejercitan la API, ataques, benchmarks, sincronización,
red simulada, dashboard y laboratorio visual.

Existe además un directorio `test/` con pruebas separadas. No lo
elimines sin ejecutar primero esas pruebas y decidir si deben migrarse.

```bash
python -m pytest test/ -v
```

Los resultados dependen del entorno. No se presupone que toda la suite
pase sin errores.
