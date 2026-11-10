# SplitMate API

API REST para dividir los gastos de un viaje en grupo y calcular quién le paga a quién.

## Unidad 1

Plantilla de la Unidad 1 del curso.

## Requisitos

- [uv](https://docs.astral.sh/uv/), que instala Python 3.13 y las dependencias exactas de `uv.lock`.

## Instalar y correr

```bash
uv sync
SEED_DEMO_DATA=true uv run uvicorn app.main:app --reload   # arranca con un viaje de ejemplo

```

La consola queda en http://127.0.0.1:8000 y Swagger en `/docs`.

## Tests

```bash
uv run pytest -v                  # solo los tests
uv run ruff check . && uv run ruff format --check . && uv run pytest -v   # chequeo completo
```

El archivo `AGENTS.md` trae las reglas para el asistente de IA.

El enunciado del reto, la rúbrica y la guía paso a paso están en el curso.
