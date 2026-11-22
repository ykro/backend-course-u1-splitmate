# AGENTS.md — Reglas para asistentes de IA en SplitMate API (Unidad 1)

Este archivo le da contexto permanente a cualquier asistente de código que trabaje en el repositorio. Es una base: como parte del reto debes ampliarlo con al menos una regla propia (ver `ARCHITECTURE_DECISIONS.md`, pregunta 5).

## 1. Entorno y comandos

- Usa solo `uv`: `uv sync`, `uv run pytest -v`, `uv run ruff check .`, `uv run ruff format .`, `uv run uvicorn app.main:app --reload`.
- Prohibido `pip install` global o entornos creados a mano.
- Python 3.13. No agregues dependencias sin que la persona lo pida.

## 2. Capas

- `app/main.py` es la capa HTTP: rutas, `Depends(get_store)` y traducción de errores. Sin lógica de negocio.
- `app/schemas.py` define los DTOs de Pydantic v2. Entrada y salida usan clases distintas (`ExpenseCreate` frente a `ExpenseResponse`). Los DTOs de entrada usan `extra="forbid"`.
- `app/store.py` contiene el dominio en `InMemorySplitMateStore`. No importa nada de FastAPI ni `HTTPException`: lanza subclases de `DomainError` con su `status_code` y `error_code`.
- `app/money.py` concentra la aritmética de dinero.

## 3. Dinero

- Todo monto es `Decimal` con 2 decimales. Prohibido `float` para dinero, prohibido `round()` sobre montos y prohibido comparar con tolerancias como `0.009`.
- El reparto entre personas usa `split_evenly`: los centavos sobrantes van a los primeros nombres en orden alfabético y la suma de cuotas es exacta.
- En JSON el dinero sale como texto con 2 decimales (`"150.00"`).

## 4. Pruebas

- No modifiques `tests/conftest.py`, `tests/test_demo.py`, `tests/test_workshop.py`, `tests/test_challenge.py` ni `.github/workflows/ci.yml`.
- Los tests propios viven en `tests/student/`, usan los fixtures de `tests/conftest.py` y no acceden a la red ni a archivos.
- Ningún código de `app/` puede detectar si corre bajo pytest.

## 5. Seguridad de la consola

- En `app/ui.py` todo dato se pinta con `textContent`; nunca `innerHTML` con datos del servidor o del usuario, ni manejadores `onclick` en el HTML.
- No pongas credenciales, tokens ni contraseñas en el código ni en la consola.

## 6. Reglas propias del alumno

(Agrega aquí tus reglas y explica su efecto en `ARCHITECTURE_DECISIONS.md`.)
