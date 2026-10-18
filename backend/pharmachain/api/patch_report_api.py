"""Patch existing dashboard report routes in place without replacing other endpoints.

Usage: python3 patch_report_api.py backend/pharmachain/api/dashboard.py
"""

import sys
from pathlib import Path

if len(sys.argv) != 2:
    raise SystemExit("Uso: python3 patch_report_api.py backend/pharmachain/api/dashboard.py")
path = Path(sys.argv[1])
source = path.read_text(encoding="utf-8")
if "def benchmark_report(" not in source or "def benchmark_report_csv(" not in source:
    raise SystemExit("No se encuentran los endpoints de informe; no se modifica el archivo.")
if "REPORT_DIAGNOSTIC_HANDLER" in source:
    raise SystemExit("El parche ya está instalado.")
source = source.replace("from pathlib import Path", "from pathlib import Path\nimport logging", 1)
source = source.replace("app = FastAPI(", 'report_logger = logging.getLogger("pharmachain.benchmark")\n\napp = FastAPI(', 1)
# add a non-destructive exception branch after the ValueError branch of each report endpoint
for name in ("benchmark_report", "benchmark_report_csv"):
    start = source.index("def " + name + "(")
    end = source.find("\n@app.", start + 4)
    if end == -1:
        end = len(source)
    block = source[start:end]
    if "except ValueError as exc:" not in block:
        raise SystemExit(f"No se encuentra el manejador ValueError en {name}.")
    old = "except ValueError as exc:\n        raise HTTPException(status_code=422, detail=str(exc)) from exc"
    new = """except ValueError as exc:
        raise HTTPException(status_code=422, detail=str(exc)) from exc
    except Exception as exc:  # REPORT_DIAGNOSTIC_HANDLER
        report_logger.exception("Fallo al ejecutar informe multiejecución")
        raise HTTPException(
            status_code=503,
            detail=("No se pudo ejecutar el benchmark. "
                    f"{type(exc).__name__}: {exc}. "
                    "Consulta el traceback de Uvicorn para identificar la causa."),
        ) from exc"""
    if old not in block:
        raise SystemExit(f"Formato no reconocido en {name}.")
    source = source[:start] + block.replace(old, new, 1) + source[end:]
backup = path.with_suffix(".py.before_report_patch")
backup.write_text(path.read_text(encoding="utf-8"), encoding="utf-8")
path.write_text(source, encoding="utf-8")
print("Parche aplicado; copia de seguridad:", backup)
