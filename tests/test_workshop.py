"""Tests del taller guiado: split_evenly, add_expense y calculate_settlements.

En el starter fallan; pasan a verde al completar el codelab.
"""

from collections.abc import Callable
from decimal import Decimal
from typing import Any

import pytest
from fastapi.testclient import TestClient

Trip = dict[str, Any]
MakeTrip = Callable[..., Trip]
AddExpense = Callable[..., dict[str, Any]]


def test_add_expense_returns_201_with_normalized_fields_and_money_as_text(
    client: TestClient, create_trip: MakeTrip
) -> None:
    trip = create_trip(name="Antigua Weekend")

    response = client.post(
        f"/api/v1/trips/{trip['id']}/expenses",
        json={
            "description": "  Cena   en el centro ",
            "amount": 300,
            "currency": "gtq",
            "category": "food",
            "paid_by": " ana ",
            "split_among": ["ana", "LUIS", "Sofía"],
        },
    )

    assert response.status_code == 201
    data = response.json()
    assert data["description"] == "Cena en el centro"
    assert data["amount"] == "300.00"
    assert data["currency"] == "GTQ"
    assert data["paid_by"] == "Ana"
    assert data["split_among"] == ["Ana", "Luis", "Sofía"]
    assert data["shares"] == {"Ana": "100.00", "Luis": "100.00", "Sofía": "100.00"}
    assert data["updated_at"] is None
    trip_after = client.get(f"/api/v1/trips/{trip['id']}").json()
    assert trip_after["expense_count"] == 1
    assert trip_after["total_spent"] == "300.00"


def test_add_expense_accepts_amount_as_text_and_pads_two_decimals(
    create_trip: MakeTrip, add_expense: AddExpense
) -> None:
    trip = create_trip()

    expense = add_expense(trip, amount="45.5")

    assert expense["amount"] == "45.50"


@pytest.mark.parametrize(
    "amount",
    [-25, 0, "0.004", "12.345", "doce", "100000.01"],
    ids=["negativo", "cero", "tres-decimales-chico", "tres-decimales", "texto", "sobre-limite"],
)
def test_add_expense_rejects_invalid_amount_with_422(
    client: TestClient, create_trip: MakeTrip, add_expense: AddExpense, amount: Any
) -> None:
    trip = create_trip()
    add_expense(trip, description="Gasto válido previo")

    response = client.post(
        f"/api/v1/trips/{trip['id']}/expenses",
        json={
            "description": "Lancha privada",
            "amount": amount,
            "currency": "GTQ",
            "paid_by": "Ana",
            "split_among": ["Ana", "Luis"],
        },
    )

    assert response.status_code == 422
    body = response.json()
    assert body["error_code"] == "VALIDATION_ERROR"
    assert body["detail"][0]["loc"] == ["body", "amount"]
    assert client.get(f"/api/v1/trips/{trip['id']}").json()["expense_count"] == 1


def test_add_expense_rejects_extra_fields_to_prevent_mass_assignment(
    client: TestClient, create_trip: MakeTrip, add_expense: AddExpense
) -> None:
    trip = create_trip()
    add_expense(trip, description="Gasto válido previo")

    response = client.post(
        f"/api/v1/trips/{trip['id']}/expenses",
        json={
            "id": "exp-falso",
            "description": "Hotel",
            "amount": "100.00",
            "currency": "GTQ",
            "paid_by": "Ana",
            "split_among": ["Ana"],
        },
    )

    assert response.status_code == 422
    assert response.json()["detail"][0]["type"] == "extra_forbidden"
    listed = client.get(f"/api/v1/trips/{trip['id']}/expenses").json()
    assert [e["description"] for e in listed] == ["Gasto válido previo"]


def test_add_expense_with_payer_or_beneficiary_outside_trip_returns_400(
    client: TestClient, create_trip: MakeTrip
) -> None:
    trip = create_trip(currency="USD", participants=["Ana", "Luis"])
    url = f"/api/v1/trips/{trip['id']}/expenses"
    base = {"description": "Hotel vista al lago", "amount": "120.00", "currency": "USD"}

    outsider_payer = client.post(
        url, json={**base, "paid_by": "Intruso", "split_among": ["Ana", "Luis"]}
    )
    outsider_beneficiary = client.post(
        url, json={**base, "paid_by": "Ana", "split_among": ["Ana", "Marta"]}
    )

    assert outsider_payer.status_code == 400
    assert outsider_payer.json()["error_code"] == "INVALID_PARTICIPANT"
    assert outsider_beneficiary.status_code == 400
    assert outsider_beneficiary.json()["error_code"] == "INVALID_PARTICIPANT"
    assert client.get(f"/api/v1/trips/{trip['id']}").json()["expense_count"] == 0


def test_add_expense_with_currency_different_from_trip_returns_400(
    client: TestClient, create_trip: MakeTrip
) -> None:
    trip = create_trip(currency="GTQ")

    response = client.post(
        f"/api/v1/trips/{trip['id']}/expenses",
        json={
            "description": "Café de especialidad",
            "amount": "45.00",
            "currency": "EUR",
            "paid_by": "Ana",
            "split_among": ["Ana", "Luis"],
        },
    )

    assert response.status_code == 400
    assert response.json()["error_code"] == "CURRENCY_MISMATCH"


def test_add_expense_to_unknown_trip_returns_404(client: TestClient) -> None:
    response = client.post(
        "/api/v1/trips/trip-no-existe/expenses",
        json={
            "description": "Gasto huérfano",
            "amount": "10.00",
            "currency": "USD",
            "paid_by": "Ana",
            "split_among": ["Ana"],
        },
    )

    assert response.status_code == 404
    assert response.json()["error_code"] == "TRIP_NOT_FOUND"


def test_split_gives_residual_cent_to_first_name_in_alphabetical_order(
    create_trip: MakeTrip, add_expense: AddExpense
) -> None:
    trip = create_trip()

    expense = add_expense(trip, amount="10.00", split_among=["Sofía", "Luis", "Ana"])

    assert expense["shares"] == {"Ana": "3.34", "Luis": "3.33", "Sofía": "3.33"}


def test_split_alphabetical_order_ignores_accents_and_puts_enie_after_n(
    create_trip: MakeTrip, add_expense: AddExpense
) -> None:
    trip = create_trip(participants=["Zoe", "Ñusta", "Álvaro", "Nora"])

    expense = add_expense(trip, amount="0.07", paid_by="Zoe")

    assert expense["shares"] == {
        "Álvaro": "0.02",
        "Nora": "0.02",
        "Ñusta": "0.02",
        "Zoe": "0.01",
    }


def test_settlements_ten_among_three_balances_sum_exactly_zero(
    client: TestClient, create_trip: MakeTrip, add_expense: AddExpense
) -> None:
    trip = create_trip()
    add_expense(trip, amount="10.00", paid_by="Ana")

    url = f"/api/v1/trips/{trip['id']}/settlements"
    summary = client.get(url).json()

    balances = summary["net_balances"]
    assert summary["total_spent"] == "10.00"
    assert balances == {
        "Ana": "6.66",
        "Luis": "-3.33",
        "Sofía": "-3.33",
    }
    assert sum(Decimal(v) for v in balances.values()) == 0
    assert summary["transfers"] == [
        {"from_participant": "Luis", "to_participant": "Ana", "amount": "3.33", "currency": "GTQ"},
        {"from_participant": "Sofía", "to_participant": "Ana", "amount": "3.33", "currency": "GTQ"},
    ]


def test_settlements_greedy_pays_largest_debt_first(
    client: TestClient, create_trip: MakeTrip, add_expense: AddExpense
) -> None:
    trip = create_trip(currency="GTQ")
    add_expense(trip, description="Vuelos", amount="90.00", paid_by="Ana")
    add_expense(trip, description="Entradas a Tikal", amount="30.00", paid_by="Luis")

    summary = client.get(f"/api/v1/trips/{trip['id']}/settlements").json()

    assert summary["total_spent"] == "120.00"
    assert summary["net_balances"] == {"Ana": "50.00", "Luis": "-10.00", "Sofía": "-40.00"}
    assert summary["transfers"] == [
        {
            "from_participant": "Sofía",
            "to_participant": "Ana",
            "amount": "40.00",
            "currency": "GTQ",
        },
        {"from_participant": "Luis", "to_participant": "Ana", "amount": "10.00", "currency": "GTQ"},
    ]


def test_settlements_with_two_creditors_needs_at_most_n_minus_one_transfers(
    client: TestClient, create_trip: MakeTrip, add_expense: AddExpense
) -> None:
    people = ["Ana", "Beto", "Carla", "Dani"]
    trip = create_trip(participants=people)
    add_expense(trip, amount="100.00", paid_by="Ana", split_among=people)
    add_expense(trip, amount="60.00", paid_by="Beto", split_among=people)

    summary = client.get(f"/api/v1/trips/{trip['id']}/settlements").json()

    assert summary["net_balances"] == {
        "Ana": "60.00",
        "Beto": "20.00",
        "Carla": "-40.00",
        "Dani": "-40.00",
    }
    pairs = [
        (t["from_participant"], t["to_participant"], t["amount"]) for t in summary["transfers"]
    ]
    assert pairs == [("Carla", "Ana", "40.00"), ("Dani", "Ana", "20.00"), ("Dani", "Beto", "20.00")]
    assert len(pairs) <= len(people) - 1


def test_settlements_of_trip_without_expenses_are_all_zero(
    client: TestClient, create_trip: MakeTrip
) -> None:
    trip = create_trip()

    summary = client.get(f"/api/v1/trips/{trip['id']}/settlements").json()

    assert summary["total_spent"] == "0.00"
    assert set(summary["net_balances"].values()) == {"0.00"}
    assert summary["transfers"] == []


def test_settlements_of_unknown_trip_return_404(client: TestClient) -> None:
    response = client.get("/api/v1/trips/trip-no-existe/settlements")

    assert response.status_code == 404
    assert response.json()["error_code"] == "TRIP_NOT_FOUND"
