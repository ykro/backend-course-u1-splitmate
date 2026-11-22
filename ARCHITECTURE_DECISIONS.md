# Decisiones de arquitectura — SplitMate API (Unidad 1)

Responde con tus palabras y con ejemplos de tu propio código. Una respuesta genérica, que podría aplicar a cualquier proyecto, no muestra tus decisiones. Extensión sugerida: de 3 a 8 líneas por pregunta.

## 1. Dinero exacto

¿Por qué SplitMate usa `Decimal` y no `float` para los montos, y por qué el dinero viaja en JSON como texto (`"150.00"`)? Usa un ejemplo numérico concreto del proyecto.

**Tu respuesta:**

> 

## 2. PATCH parcial

¿Cómo distingue tu implementación un campo que el cliente no envió de uno que envió con `null`? ¿Por qué el DTO del PATCH es una clase distinta de `ExpenseCreate`?

**Tu respuesta:**

> 

## 3. Atomicidad y errores 404

¿Cómo garantiza tu código que un PATCH rechazado no deja el gasto modificado a medias? ¿Por qué el `id` de un gasto de otro viaje debe responder `404 EXPENSE_NOT_FOUND`?

**Tu respuesta:**

> 

## 4. Tus tests propios

Para cada test de `tests/student/test_my_scenarios.py`: ¿qué error plausible del reto atrapa? Describe un cambio concreto en `app/` que lo haría fallar.

**Tu respuesta:**

> 

## 5. Tu regla en AGENTS.md

Copia la regla que agregaste a `AGENTS.md`. Describe qué generó el asistente de IA antes de tener esa regla y qué cambió después (si no usaste asistente, explica qué error evitaría la regla).

**Tu respuesta:**

> 

## 6. Declaración de uso de IA

Completa con honestidad: declarar cómo usaste la IA es parte del ejercicio.

- Herramientas usadas (o "ninguna"):
- Partes del trabajo en las que las usaste:
- Algo que el asistente propuso y aceptaste después de verificarlo:
- Algo que el asistente propuso y corregiste o rechazaste, y por qué:
