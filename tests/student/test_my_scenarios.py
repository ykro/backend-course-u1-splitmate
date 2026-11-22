"""Tus tests propios (al menos 2).

Un buen test propio pasa con tu código y falla si siembras a propósito un error
plausible que los tests de la plantilla no atrapan: por ejemplo, que el PATCH
cambie created_at o mueva el gasto al final del listado. Compruébalo: mete el
error, corre `uv run pytest tests/student -v`, confirma que tu test falla y
deshaz el cambio con `git restore`. Reescribir un test de la plantilla no atrapa
nada nuevo.

Reglas: usa los fixtures de tests/conftest.py (client, create_trip,
add_expense), no crees conftest.py en esta carpeta y no uses la red.
"""

import pytest
from fastapi.testclient import TestClient


def test_my_scenario_1(client: TestClient) -> None:
    """Describe aquí qué error del reto atrapa este test y renómbralo."""
    pytest.fail("Escribe tu primer test propio")


def test_my_scenario_2(client: TestClient) -> None:
    """Describe aquí qué error del reto atrapa este test y renómbralo."""
    pytest.fail("Escribe tu segundo test propio")
