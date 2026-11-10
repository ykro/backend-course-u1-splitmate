"""Capa HTTP de SplitMate API (Unidad 1)."""

import secrets
from collections.abc import Awaitable, Callable
from typing import Annotated

from fastapi import Depends, FastAPI, Path, Query, Request, Response, status
from fastapi.encoders import jsonable_encoder
from fastapi.exceptions import RequestValidationError
from fastapi.responses import HTMLResponse, JSONResponse
from starlette.exceptions import HTTPException as StarletteHTTPException

from app.schemas import (
    ExpenseCategory,
    ExpenseCreate,
    ExpenseResponse,
    SettlementSummaryResponse,
    TripCreate,
    TripResponse,
)
from app.store import DomainError, InMemorySplitMateStore, get_store
from app.ui import content_security_policy, render_console
from app.validation_es import validation_details

app = FastAPI(
    title="SplitMate API",
    version="1.1.0",
    description=(
        "API REST para dividir gastos de viaje y liquidar deudas al centavo. "
        "Los montos viajan como texto con 2 decimales (Unidad 1)."
    ),
)

_HTTP_ERRORS = {
    404: ("Ruta no encontrada", "NOT_FOUND"),
    405: ("Método no permitido para esta ruta", "METHOD_NOT_ALLOWED"),
}

TripId = Annotated[str, Path(max_length=64)]
ExpenseId = Annotated[str, Path(max_length=64)]


@app.exception_handler(RequestValidationError)
async def validation_error_handler(
    _request: Request,
    exc: RequestValidationError,
) -> JSONResponse:
    body = {"detail": validation_details(exc.errors()), "error_code": "VALIDATION_ERROR"}
    return JSONResponse(jsonable_encoder(body), status_code=422)


@app.exception_handler(StarletteHTTPException)
async def http_error_handler(
    _request: Request,
    exc: StarletteHTTPException,
) -> JSONResponse:
    if exc.status_code == 400:
        # FastAPI responde 400 en inglés cuando el cuerpo no es UTF-8 válido.
        error = {"loc": ["body"], "msg": "El cuerpo no es JSON válido", "type": "json_invalid"}
        body = {"detail": [error], "error_code": "VALIDATION_ERROR"}
        return JSONResponse(body, status_code=422)
    detail, code = _HTTP_ERRORS.get(exc.status_code, ("Error HTTP", "HTTP_ERROR"))
    body = {"detail": detail, "error_code": code}
    return JSONResponse(body, status_code=exc.status_code, headers=exc.headers)


@app.exception_handler(DomainError)
async def domain_error_handler(
    _request: Request,
    exc: DomainError,
) -> JSONResponse:
    body = {"detail": str(exc), "error_code": exc.error_code}
    return JSONResponse(body, status_code=exc.status_code)


@app.middleware("http")
async def security_headers(
    request: Request, call_next: Callable[[Request], Awaitable[Response]]
) -> Response:
    response = await call_next(request)
    response.headers.setdefault("X-Content-Type-Options", "nosniff")
    response.headers.setdefault("Referrer-Policy", "no-referrer")
    response.headers.setdefault("X-Frame-Options", "DENY")
    return response


@app.get("/", response_class=HTMLResponse, include_in_schema=False)
async def console() -> HTMLResponse:
    nonce = secrets.token_urlsafe(16)
    headers = {
        "Content-Security-Policy": content_security_policy(nonce),
        "Cache-Control": "no-store",
    }
    return HTMLResponse(content=render_console(nonce), headers=headers)


@app.get("/health", tags=["system"])
async def health_check() -> dict[str, str]:
    return {"status": "ok", "service": "splitmate-api"}


@app.post(
    "/api/v1/trips",
    response_model=TripResponse,
    status_code=status.HTTP_201_CREATED,
    tags=["trips"],
)
async def create_trip(
    payload: TripCreate,
    store: InMemorySplitMateStore = Depends(get_store),
) -> TripResponse:
    return store.create_trip(payload)


@app.get("/api/v1/trips", response_model=list[TripResponse], tags=["trips"])
async def list_trips(
    store: InMemorySplitMateStore = Depends(get_store),
) -> list[TripResponse]:
    return store.list_trips()


@app.get("/api/v1/trips/{trip_id}", response_model=TripResponse, tags=["trips"])
async def get_trip(
    trip_id: TripId,
    store: InMemorySplitMateStore = Depends(get_store),
) -> TripResponse:
    return store.get_trip(trip_id)


@app.post(
    "/api/v1/trips/{trip_id}/expenses",
    response_model=ExpenseResponse,
    status_code=status.HTTP_201_CREATED,
    tags=["expenses"],
)
async def create_expense(
    trip_id: TripId,
    payload: ExpenseCreate,
    store: InMemorySplitMateStore = Depends(get_store),
) -> ExpenseResponse:
    return store.add_expense(trip_id, payload)


@app.get(
    "/api/v1/trips/{trip_id}/expenses",
    response_model=list[ExpenseResponse],
    tags=["expenses"],
)
async def list_expenses(
    trip_id: TripId,
    category: ExpenseCategory | None = Query(default=None),
    paid_by: str | None = Query(default=None, max_length=60),
    store: InMemorySplitMateStore = Depends(get_store),
) -> list[ExpenseResponse]:
    return store.list_expenses(trip_id, category=category, paid_by=paid_by)


@app.delete(
    "/api/v1/trips/{trip_id}/expenses/{expense_id}",
    status_code=status.HTTP_204_NO_CONTENT,
    tags=["expenses"],
)
async def delete_expense(
    trip_id: TripId,
    expense_id: ExpenseId,
    store: InMemorySplitMateStore = Depends(get_store),
) -> None:
    store.delete_expense(trip_id, expense_id)


@app.get(
    "/api/v1/trips/{trip_id}/settlements",
    response_model=SettlementSummaryResponse,
    tags=["settlements"],
)
async def get_trip_settlements(
    trip_id: TripId,
    store: InMemorySplitMateStore = Depends(get_store),
) -> SettlementSummaryResponse:
    return store.calculate_settlements(trip_id)
