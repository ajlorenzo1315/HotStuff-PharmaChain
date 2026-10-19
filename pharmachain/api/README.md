# API y dashboard

La carpeta contiene dos aplicaciones FastAPI diferenciadas:

- `main.py`: API local de lotes y operaciones farmacéuticas.
- `dashboard.py`: dashboard del simulador distribuido.

`service.py` implementa el servicio local de trazabilidad.
`attacks.py`, `benchmark.py`, `byzantine_benchmark.py`,
`fork_experiment.py`, `education.py` y `visual_lab.py` proporcionan
funciones experimentales o educativas.
`static/` contiene HTML, JavaScript, CSS y GIFs.

## Iniciar la API de lotes

```bash
python -m uvicorn pharmachain.api.main:app --port 8001
```

### Rutas comprobadas en `main.py`

| Método | Ruta | Función |
| --- | --- | --- |
| GET | `/api/status` | Estado del motor |
| GET | `/api/batches` | Lotes confirmados |
| GET | `/api/blocks` | Bloques confirmados |
| GET | `/api/events` | Eventos de consenso |
| POST | `/api/demo/register` | Registrar lote |
| POST | `/api/demo/transfer` | Transferir custodia |

### Registrar un lote

```bash
curl -X POST http://127.0.0.1:8001/api/demo/register \
  -H 'Content-Type: application/json' \
  -d '{"batch_id":"L-001","medicine_name":"Ejemplo","quantity":10}'
```

### Transferir custodia

```bash
curl -X POST http://127.0.0.1:8001/api/demo/transfer \
  -H 'Content-Type: application/json' \
  -d '{"batch_id":"L-001","sender_id":"laboratory",\
"receiver_id":"distributor"}'
```

## Iniciar el dashboard

```bash
python -m uvicorn pharmachain.api.dashboard:app --port 8002
```

Abre <http://127.0.0.1:8002/> o la documentación OpenAPI.

## Advertencias

Las claves y el estado del servicio local se crean en memoria.
No se debe exponer esta API como servicio público sin controles
adicionales de autenticación, autorización y persistencia.
