"""Puertos de entrada/salida; la aplicación no conoce FastAPI ni SQLAlchemy."""

from __future__ import annotations

from typing import Protocol
from uuid import UUID

from practica_final.domain.order import Order


class OrderRepository(Protocol):
    def add(self, order: Order) -> Order: ...
    def get(self, order_id: UUID) -> Order | None: ...
    def list(self, offset: int = 0, limit: int = 50) -> list[Order]: ...
    def save(self, order: Order) -> Order: ...


class EventPublisher(Protocol):
    def publish(self, name: str, payload: dict[str, str]) -> None: ...
