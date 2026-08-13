"""Adaptador HTTP FastAPI: validación, autenticación y observabilidad."""

from __future__ import annotations

import time
from collections.abc import AsyncIterator, Awaitable, Callable, Generator
from contextlib import asynccontextmanager
from datetime import UTC, datetime, timedelta
from typing import Annotated
from uuid import UUID

from fastapi import Depends, FastAPI, HTTPException, Query, Request, status
from fastapi.responses import Response
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from jose import JWTError, jwt
from prometheus_client import CONTENT_TYPE_LATEST, Counter, Histogram, generate_latest
from pydantic import BaseModel, EmailStr, Field

from practica_final.application.services import CreateLine, OrderNotFoundError, OrderService
from practica_final.domain.order import DomainError, Order, OrderStatus
from practica_final.infrastructure.config import settings
from practica_final.infrastructure.database import SqlAlchemyOrderRepository, create_session_factory
from practica_final.infrastructure.events import LoggingEventPublisher

REQUESTS = Counter("http_requests_total", "Peticiones HTTP", ["method", "path", "status"])
LATENCY = Histogram("http_request_duration_seconds", "Latencia HTTP", ["path"])
engine, SessionFactory = create_session_factory(settings.database_url)
security = HTTPBearer()


class LineIn(BaseModel):
    bicycle_model: str = Field(min_length=2, max_length=100, examples=["Ruta Carbono 700"])
    quantity: int = Field(ge=1, le=10)
    unit_price_cents: int = Field(ge=0, le=10_000_000)


class OrderCreate(BaseModel):
    customer_email: EmailStr
    lines: list[LineIn] = Field(min_length=1, max_length=20)


class StatusUpdate(BaseModel):
    status: OrderStatus


class OrderOut(BaseModel):
    id: UUID
    customer_email: EmailStr
    status: OrderStatus
    lines: list[LineIn]
    total_cents: int
    created_at: datetime

    @classmethod
    def from_domain(cls, order: Order) -> OrderOut:
        return cls(
            id=order.id,
            customer_email=order.customer_email,
            status=order.status,
            lines=[LineIn.model_validate(x, from_attributes=True) for x in order.lines],
            total_cents=order.total_cents,
            created_at=order.created_at,
        )


def get_service() -> Generator[OrderService, None, None]:
    session = SessionFactory(bind=engine)
    try:
        yield OrderService(SqlAlchemyOrderRepository(session), LoggingEventPublisher())
    finally:
        session.close()


Service = Annotated[OrderService, Depends(get_service)]


def require_token(credentials: Annotated[HTTPAuthorizationCredentials, Depends(security)]) -> None:
    try:
        jwt.decode(credentials.credentials, settings.jwt_secret, algorithms=["HS256"])
    except JWTError as exc:
        raise HTTPException(status_code=401, detail="Token inválido o expirado") from exc


@asynccontextmanager
async def lifespan(_: FastAPI) -> AsyncIterator[None]:
    yield
    engine.dispose()


app = FastAPI(
    title="Bicycle Orders API",
    version="1.0.0",
    lifespan=lifespan,
    description="Servicio seguro para crear y administrar pedidos de bicicletas.",
)


@app.middleware("http")
async def metrics_middleware(
    request: Request, call_next: Callable[[Request], Awaitable[Response]]
) -> Response:
    started = time.perf_counter()
    response = await call_next(request)
    route = request.url.path
    REQUESTS.labels(request.method, route, response.status_code).inc()
    LATENCY.labels(route).observe(time.perf_counter() - started)
    return response


@app.get("/health", tags=["operación"])
def health() -> dict[str, str]:
    return {"status": "ok", "service": "bicycle-orders"}


@app.get("/metrics", include_in_schema=False)
def metrics() -> Response:
    return Response(generate_latest(), media_type=CONTENT_TYPE_LATEST)


@app.post("/auth/token", tags=["seguridad"])
def issue_demo_token() -> dict[str, str]:
    """Token de demostración. Sustituir por proveedor de identidad en producción."""
    expiration = datetime.now(UTC) + timedelta(minutes=settings.access_token_expire_minutes)
    return {
        "access_token": jwt.encode(
            {"sub": "demo-user", "exp": expiration}, settings.jwt_secret, "HS256"
        ),
        "token_type": "bearer",
    }


@app.post("/orders", response_model=OrderOut, status_code=status.HTTP_201_CREATED, tags=["pedidos"])
def create_order(
    payload: OrderCreate, service: Service, _: Annotated[None, Depends(require_token)]
) -> OrderOut:
    try:
        lines = [CreateLine(**line.model_dump()) for line in payload.lines]
        return OrderOut.from_domain(service.create_order(str(payload.customer_email), lines))
    except DomainError as exc:
        raise HTTPException(422, detail=str(exc)) from exc


@app.get("/orders", response_model=list[OrderOut], tags=["pedidos"])
def list_orders(
    service: Service,
    _: Annotated[None, Depends(require_token)],
    offset: int = Query(0, ge=0),
    limit: int = Query(50, ge=1, le=100),
) -> list[OrderOut]:
    return [OrderOut.from_domain(order) for order in service.list_orders(offset, limit)]


@app.get("/orders/{order_id}", response_model=OrderOut, tags=["pedidos"])
def get_order(
    order_id: UUID, service: Service, _: Annotated[None, Depends(require_token)]
) -> OrderOut:
    try:
        return OrderOut.from_domain(service.get_order(order_id))
    except OrderNotFoundError as exc:
        raise HTTPException(404, detail=str(exc)) from exc


@app.patch("/orders/{order_id}/status", response_model=OrderOut, tags=["pedidos"])
def update_status(
    order_id: UUID,
    payload: StatusUpdate,
    service: Service,
    _: Annotated[None, Depends(require_token)],
) -> OrderOut:
    try:
        return OrderOut.from_domain(service.change_status(order_id, payload.status))
    except OrderNotFoundError as exc:
        raise HTTPException(404, detail=str(exc)) from exc
    except DomainError as exc:
        raise HTTPException(409, detail=str(exc)) from exc
