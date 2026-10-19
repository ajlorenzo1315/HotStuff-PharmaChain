# Plan de reorganización sin romper el proyecto

## Conservar

- `pharmachain/` y sus seis módulos principales.
- `tests/` como suite principal de Pytest.
- `docs/` como documentación pública.
- `index.html` mientras siga siendo la demo autónoma.

## Revisar antes de mover

1. `test/` y `tests/`: unificar solo tras ejecutar ambos conjuntos.
2. `docs_1/`: revisar las notas numeradas y migrar su contenido útil.
3. `backend/` frente a `protocols/`: hay rutas históricas divergentes.
4. `.gitmodules`: el submódulo declara una ruta bajo `backend/`.
5. `compose.yaml`: referencia un Dockerfile bajo `backend/`.
6. `demo.py`: comprobar que coincida con los puntos de entrada Docker.
7. `pharmachain/api/static/index.html.bak`: copia de respaldo.
8. `backend.rar`, `backend.tar` y entornos virtuales: artefactos locales.
9. `results/`: separar ejemplos versionados de resultados generados.

## Comprobaciones seguras

```bash
git checkout -b chore/reorganize-project
python -m pytest
python -m pytest test/ -v
git submodule status
cat .gitmodules
grep -R 'backend/protocols' -n compose.yaml Dockerfile .gitmodules
```

Antes de borrar o mover algo, busca referencias a sus rutas en
scripts, imports, tests y archivos de configuración.

## Estructura objetivo

```text
HotStuff-PharmaChain/
  README.md
  pyproject.toml
  Dockerfile
  compose.yaml
  index.html
  pharmachain/
    api/
    blockchain/
    consensus/
    domain/
    engines/
    simulation/
  tests/
  docs/
  protocols/
    README.md
    relab/
  scripts/                 # Solo si se necesitan scripts
  .github/workflows/       # Solo si se configura CI
```

## Calidad Markdown

El hook markdownlint comprueba longitud máxima de 80 caracteres.
Todos los nuevos párrafos de esta entrega están partidos para facilitar
su mantenimiento. En tablas, abrevia el texto de cada celda.

```bash
pre-commit run markdownlint --all-files
```

## Árbol documental recomendado

```text
README.md
docs/
  README.md
  visual-guide.md
  glossary.md
  images/
  architecture.md
  hotstuff.md
  chained-hotstuff.md
  experiments.md
  threat-model.md
  testing.md
  getting-started.md
  limitations.md
  references.md
pharmachain/
  README.md
  api/README.md
  blockchain/README.md
  consensus/README.md
  domain/README.md
  engines/README.md
  simulation/README.md
tests/README.md
protocols/README.md
```

No muevas código Python ni submódulos sin revisar imports, pruebas,
`compose.yaml` y `.gitmodules`. Mantén `test/` y `tests/` intactos hasta
confirmar que sus pruebas se descubren correctamente.
