# Checklist de seguridad y calidad — SplitMate API (Unidad 1)

Marca cada casilla solo si la verificaste en tu código y escribe la evidencia (archivo y función, comando o test). Una casilla marcada sin evidencia no cuenta.

- [ ] **DTOs separados.** Los esquemas de entrada (`ExpenseCreate` y tu DTO del PATCH) usan `extra="forbid"` y ninguna ruta devuelve objetos internos sin `response_model`. Evidencia:
- [ ] **Dinero exacto.** Ningún monto pasa por `float` ni por `round()`; los saldos de un viaje suman exactamente `0`. Evidencia:
- [ ] **Validación en la frontera.** Montos mayores que 0, como máximo `100000.00` y 2 decimales; nombres normalizados; monedas permitidas; en el PATCH se rechazan `null`, cuerpo vacío y campos extra. Evidencia:
- [ ] **Dominio sin HTTP.** `app/store.py` no importa FastAPI y todos sus errores son subclases de `DomainError` con `error_code` estable. Evidencia:
- [ ] **Sin fugas entre viajes.** Un gasto solo se lee, modifica o borra a través de su propio viaje; el `id` de otro viaje responde `404 EXPENSE_NOT_FOUND`. Evidencia:
- [ ] **Errores 422 sin eco.** Las respuestas de validación devuelven `loc`, `msg` y `type`, nunca `input` ni `ctx`. Evidencia:
- [ ] **Consola segura.** Sin `innerHTML` con datos, sin manejadores inline, CSP con nonce en `/` y ninguna credencial en el código. Evidencia:
- [ ] **Sin estado compartido accidental.** Ningún parámetro por defecto mutable (`def f(x=[])`) y ninguna llamada bloqueante (`time.sleep`) dentro de `async def`. Evidencia:
- [ ] **Calidad.** `uv run ruff check .` y `uv run ruff format --check .` limpios, `uv run pytest -v` en verde y ningún test ni workflow de la plantilla modificado. Evidencia:
