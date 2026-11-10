"""Tests PÚBLICOS del reto autónomo: PATCH /api/v1/trips/{trip_id}/expenses/{expense_id}.

Son una muestra. El contrato completo de la guía del reto tiene otros datos y más
casos borde, así que impleméntalo completo, no solo lo que estos tests
revisan.
"""

from collections.abc import Callable
from typing import Any

from fastapi.testclient import TestClient

Trip = dict[str, Any]
MakeTrip = Callable[..., Trip]
AddExpense = Callable[..., dict[str, Any]]


def _url(trip_id: str, expense_id: str) -> str:
    return f"/api/v1/trips/{trip_id}/expenses/{expense_id}"


def test_patch_amount_only_changes_amount_and_shares_and_keeps_the_rest(
    client: TestClient, create_trip: MakeTrip, add_expense: AddExpense
) -> None:
    trip = create_trip()
    original = add_expense(trip, description="Hotel en Flores", amount="90.00", category="lodging")

    response = client.patch(_url(trip["id"], original["id"]), json={"amount": "100.00"})

    assert response.status_code == 200
    data = response.json()
    assert data["amount"] == "100.00"
    assert data["shares"] == {"Ana": "33.34", "Luis": "33.33", "Sofía": "33.33"}
    for unchanged in ("id", "trip_id", "description", "category", "paid_by", "created_at"):
        assert data[unchanged] == original[unchanged]
    assert data["updated_at"] is not None
    assert client.get(f"/api/v1/trips/{trip['id']}").json()["total_spent"] == "100.00"


def test_patch_payer_recalculates_settlements(
    client: TestClient, create_trip: MakeTrip, add_expense: AddExpense
) -> None:
    trip = create_trip(currency="USD")
    expense = add_expense(trip, amount="30.00", paid_by="Ana")

    response = client.patch(_url(trip["id"], expense["id"]), json={"paid_by": " luis "})

    assert response.status_code == 200
    assert response.json()["paid_by"] == "Luis"
    summary = client.get(f"/api/v1/trips/{trip['id']}/settlements").json()
    assert summary["net_balances"] == {"Ana": "-10.00", "Luis": "20.00", "Sofía": "-10.00"}


def test_patch_distinguishes_unknown_trip_from_unknown_expense(
    client: TestClient, create_trip: MakeTrip, add_expense: AddExpense
) -> None:
    trip = create_trip()
    expense = add_expense(trip)

    unknown_trip = client.patch(_url("trip-no-existe", expense["id"]), json={"amount": "5.00"})
    unknown_expense = client.patch(_url(trip["id"], "exp-no-existe"), json={"amount": "5.00"})

    assert unknown_trip.status_code == 404
    assert unknown_trip.json()["error_code"] == "TRIP_NOT_FOUND"
    assert unknown_expense.status_code == 404
    assert unknown_expense.json()["error_code"] == "EXPENSE_NOT_FOUND"


def test_patch_rejects_empty_body_and_unknown_fields_with_422(
    client: TestClient, create_trip: MakeTrip, add_expense: AddExpense
) -> None:
    trip = create_trip()
    expense = add_expense(trip)

    empty = client.patch(_url(trip["id"], expense["id"]), json={})
    unknown = client.patch(_url(trip["id"], expense["id"]), json={"created_at": "2020-01-01"})

    assert empty.status_code == 422
    assert empty.json()["error_code"] == "VALIDATION_ERROR"
    assert unknown.status_code == 422
    assert unknown.json()["error_code"] == "VALIDATION_ERROR"


def test_patch_with_payer_outside_trip_returns_400_and_keeps_expense_unchanged(
    client: TestClient, create_trip: MakeTrip, add_expense: AddExpense
) -> None:
    trip = create_trip()
    expense = add_expense(trip, amount="60.00")

    response = client.patch(
        _url(trip["id"], expense["id"]), json={"amount": "75.00", "paid_by": "Intruso"}
    )

    assert response.status_code == 400
    assert response.json()["error_code"] == "INVALID_PARTICIPANT"
    stored = client.get(f"/api/v1/trips/{trip['id']}/expenses").json()
    assert stored == [expense]
