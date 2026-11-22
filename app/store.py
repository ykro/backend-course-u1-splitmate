"""Almacenamiento en memoria y lógica de dominio de SplitMate API.

Este módulo no conoce HTTP: lanza excepciones de dominio que app/main.py
traduce a respuestas JSON con status_code y error_code.
"""

import os
from dataclasses import dataclass, field
from datetime import UTC, datetime
from decimal import Decimal
from uuid import uuid4

from app.money import ZERO
from app.names import NameKey, alphabetical_key, clean_name
from app.schemas import (
    ExpenseCategory,
    ExpenseCreate,
    ExpenseResponse,
    SettlementSummaryResponse,
    TripCreate,
    TripResponse,
)

ExpenseLike = ExpenseCreate | ExpenseResponse


class DomainError(Exception):
    """Error de negocio independiente de HTTP."""

    status_code = 400
    error_code = "DOMAIN_ERROR"


class TripNotFoundError(DomainError):
    status_code = 404
    error_code = "TRIP_NOT_FOUND"


class ExpenseNotFoundError(DomainError):
    status_code = 404
    error_code = "EXPENSE_NOT_FOUND"


class InvalidParticipantError(DomainError):
    error_code = "INVALID_PARTICIPANT"


class CurrencyMismatchError(DomainError):
    error_code = "CURRENCY_MISMATCH"


@dataclass
class _Balance:
    participant: str
    amount: Decimal


def _rank(entry: _Balance) -> tuple[Decimal, NameKey]:
    """Mayor monto primero; en empate, orden alfabético del nombre."""
    name = entry.participant
    return (-entry.amount, alphabetical_key(name))


@dataclass
class _TripRecord:
    id: str
    name: str
    default_currency: str
    participants: list[str]
    created_at: datetime
    expenses: list[ExpenseResponse] = field(default_factory=list)


class InMemorySplitMateStore:
    """Almacén en memoria que las rutas reciben con Depends(get_store)."""

    def __init__(self) -> None:
        self._trips: dict[str, _TripRecord] = {}

    def create_trip(self, payload: TripCreate) -> TripResponse:
        record = _TripRecord(
            id=f"trip-{uuid4().hex[:8]}",
            name=payload.name,
            default_currency=payload.default_currency,
            participants=list(payload.participants),
            created_at=datetime.now(UTC),
        )
        self._trips[record.id] = record
        return self._to_trip_response(record)

    def list_trips(self) -> list[TripResponse]:
        return [self._to_trip_response(r) for r in self._trips.values()]

    def get_trip(self, trip_id: str) -> TripResponse:
        return self._to_trip_response(self._get_trip_or_raise(trip_id))

    def add_expense(
        self,
        trip_id: str,
        payload: ExpenseCreate,
    ) -> ExpenseResponse:
        # TALLER, paso 5 del codelab:
        # 1. Obtén el viaje con self._get_trip_or_raise(trip_id).
        # 2. Valida moneda y participantes con self._check_expense_rules(record, payload).
        # 3. Construye ExpenseResponse con id "exp-xxxxxxxx", trip_id y created_at en UTC.
        # 4. Agrégalo a record.expenses y devuélvelo.
        raise NotImplementedError("Taller: implementa add_expense en app/store.py")

    def list_expenses(
        self,
        trip_id: str,
        category: ExpenseCategory | None = None,
        paid_by: str | None = None,
    ) -> list[ExpenseResponse]:
        record = self._get_trip_or_raise(trip_id)
        items = list(record.expenses)
        if category is not None:
            items = [e for e in items if e.category == category]
        if paid_by is not None:
            payer = clean_name(paid_by)
            items = [e for e in items if e.paid_by == payer]
        return items

    def delete_expense(self, trip_id: str, expense_id: str) -> None:
        record = self._get_trip_or_raise(trip_id)
        index = self._find_expense_index(record, expense_id)
        record.expenses.pop(index)

    def calculate_settlements(self, trip_id: str) -> SettlementSummaryResponse:
        # TALLER, paso 6 del codelab:
        # 1. Saldo neto en Decimal: suma amount al pagador y resta cada cuota de shares.
        # 2. Separa deudores (saldo < 0) y acreedores (saldo > 0) en objetos _Balance.
        # 3. Ordena ambos con key=_rank (mayor monto primero) y empareja con dos punteros.
        # 4. Cada transferencia es min(deuda, crédito); avanza el puntero que llega a 0.
        #    Importa SettlementTransfer desde app.schemas para construirlas.
        raise NotImplementedError("Taller: implementa calculate_settlements en app/store.py")

    @staticmethod
    def _check_expense_rules(
        record: _TripRecord,
        expense: ExpenseLike,
    ) -> None:
        # TALLER, paso 5 del codelab:
        # 1. Si expense.currency difiere de record.default_currency: CurrencyMismatchError.
        # 2. Si paid_by o alguien de split_among no está en record.participants:
        #    InvalidParticipantError con los nombres ajenos al viaje.
        raise NotImplementedError("Taller: implementa _check_expense_rules en app/store.py")

    def _get_trip_or_raise(self, trip_id: str) -> _TripRecord:
        record = self._trips.get(trip_id)
        if record is None:
            raise TripNotFoundError(f"El viaje '{trip_id}' no existe")
        return record

    @staticmethod
    def _find_expense_index(record: _TripRecord, expense_id: str) -> int:
        for index, expense in enumerate(record.expenses):
            if expense.id == expense_id:
                return index
        raise ExpenseNotFoundError(f"El gasto '{expense_id}' no existe en el viaje '{record.id}'")

    @staticmethod
    def _total(record: _TripRecord) -> Decimal:
        return sum((e.amount for e in record.expenses), ZERO)

    def _to_trip_response(self, record: _TripRecord) -> TripResponse:
        return TripResponse(
            id=record.id,
            name=record.name,
            default_currency=record.default_currency,
            participants=list(record.participants),
            created_at=record.created_at,
            expense_count=len(record.expenses),
            total_spent=self._total(record),
        )


def _build_demo_store() -> InMemorySplitMateStore:
    store = InMemorySplitMateStore()
    trip = store.create_trip(
        TripCreate(
            name="Expedición Antigua 2027",
            default_currency="GTQ",
            participants=["Ana", "Luis", "Sofía"],
        )
    )
    demo_expenses = [
        ("Hotel boutique en el centro", "600.00", "lodging", "Ana"),
        ("Cena tradicional", "300.00", "food", "Luis"),
        ("Shuttle desde el aeropuerto", "100.00", "transport", "Ana"),
    ]
    for description, amount, category, payer in demo_expenses:
        expense = ExpenseCreate(
            description=description,
            amount=Decimal(amount),
            currency="GTQ",
            category=category,
            paid_by=payer,
            split_among=["Ana", "Luis", "Sofía"],
        )
        try:
            store.add_expense(trip.id, expense)
        except NotImplementedError:
            break  # El taller todavía no implementa add_expense.
    return store


def _seed_enabled() -> bool:
    return os.getenv("SEED_DEMO_DATA", "").strip().lower() == "true"


_default_store = _build_demo_store() if _seed_enabled() else InMemorySplitMateStore()


def get_store() -> InMemorySplitMateStore:
    """Dependencia que entrega el store activo."""
    return _default_store
