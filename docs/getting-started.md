# Instalación y ejecución

## 1. Entorno Python

```bash
python3 -m venv .venv
source .venv/bin/activate
python -m pip install -e '.[dev]'
```

## 2. API local

```bash
python -m uvicorn pharmachain.api.main:app --port 8001
```

Abre <http://127.0.0.1:8001/docs>.

## 3. Dashboard

En otra terminal:

```bash
python -m uvicorn pharmachain.api.dashboard:app --port 8002
```

Abre <http://127.0.0.1:8002/>.

## 4. Demo HTML

```bash
python -m http.server 8000
```

Abre <http://127.0.0.1:8000/index.html>.

## 5. Comprobar

```bash
python -m pytest
pre-commit run --all-files
```

## Docker y Relab

El `compose.yaml` del archivo recibido apunta a una ruta bajo
`backend/` que no coincide con el árbol principal extraído.
No ejecutes `docker compose up` sin corregir primero el Dockerfile
referenciado y verificar las dependencias externas.
