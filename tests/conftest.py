"""Fixtures oficiales de SplitMate API.

Herméticos: cada test recibe un almacén en memoria nuevo, no se crean
archivos .db y cualquier intento de abrir una conexión de red falla.
No modifiques este archivo: es parte de la suite oficial.
"""

import socket
from collections.abc import Callable, Generator
from typing import Any

import pytest
from fastapi.testclient import TestClient

from app.main import app
from app.store import InMemorySplitMateStore, get_store

DEFAULT_PEOPLE = ["Ana", "Luis", "Sofía"]


@pytest.fixture(autouse=True)
def _no_network(monkeypatch: pytest.MonkeyPatch) -> None:
    def blocked(*_args: Any, **_kwargs: Any) -> None:
        raise RuntimeError("Los tests de SplitMate no deben usar la red")

    monkeypatch.setattr(socket.socket, "connect", blocked)
    monkeypatch.setattr(socket.socket, "connect_ex", blocked)
    monkeypatch.setattr(socket, "create_connection", blocked)


@pytest.fixture()
def client() -> Generator[TestClient]:
    """TestClient con un InMemorySplitMateStore limpio para este test."""
    fresh_store = InMemorySplitMateStore()
    app.dependency_overrides[get_store] = lambda: fresh_store
    with TestClient(app) as test_client:
        yield test_client
    app.dependency_overrides.clear()


@pytest.fixture()
def create_trip(client: TestClient) -> Callable[..., dict[str, Any]]:
    """Crea un viaje por HTTP y devuelve el JSON de la respuesta 201."""

    def _create(
        name: str = "Viaje de prueba",
        currency: str = "GTQ",
        participants: list[str] | None = None,
    ) -> dict[str, Any]:
        body = {
            "name": name,
            "default_currency": currency,
            "participants": participants or DEFAULT_PEOPLE,
        }
        response = client.post("/api/v1/trips", json=body)
        assert response.status_code == 201, response.text
        return response.json()

    return _create


@pytest.fixture()
def add_expense(client: TestClient) -> Callable[..., dict[str, Any]]:
    """Registra un gasto por HTTP y devuelve el JSON de la respuesta 201."""

    def _add(trip: dict[str, Any], **fields: Any) -> dict[str, Any]:
        body = {
            "description": "Gasto de prueba",
            "amount": "90.00",
            "currency": trip["default_currency"],
            "category": "other",
            "paid_by": trip["participants"][0],
            "split_among": trip["participants"],
        }
        body.update(fields)
        response = client.post(f"/api/v1/trips/{trip['id']}/expenses", json=body)
        assert response.status_code == 201, response.text
        return response.json()

    return _add
