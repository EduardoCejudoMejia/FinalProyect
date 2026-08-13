"""Entidades y reglas de negocio puras para pedidos de bicicletas."""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import UTC, datetime
from enum import StrEnum
from uuid import UUID, uuid4


class OrderStatus(StrEnum):
    PENDING = "pending"
    CONFIRMED = "confirmed"
    SHIPPED = "shipped"
    CANCELLED = "cancelled"


class DomainError(ValueError):
    """Se lanza cuando una regla del dominio no se cumple."""


@dataclass(frozen=True, slots=True)
class OrderLine:
    bicycle_model: str
    quantity: int
    unit_price_cents: int

    def __post_init__(self) -> None:
        if not self.bicycle_model.strip():
            raise DomainError("El modelo de bicicleta es obligatorio")
        if self.quantity < 1:
            raise DomainError("La cantidad debe ser al menos 1")
        if self.unit_price_cents < 0:
            raise DomainError("El precio no puede ser negativo")

    @property
    def subtotal_cents(self) -> int:
        return self.quantity * self.unit_price_cents


@dataclass(slots=True)
class Order:
    customer_email: str
    lines: list[OrderLine]
    id: UUID = field(default_factory=uuid4)
    status: OrderStatus = OrderStatus.PENDING
    created_at: datetime = field(default_factory=lambda: datetime.now(UTC))

    def __post_init__(self) -> None:
        if "@" not in self.customer_email:
            raise DomainError("El correo del cliente no es válido")
        if not self.lines:
            raise DomainError("Un pedido requiere al menos una bicicleta")

    @property
    def total_cents(self) -> int:
        return sum(line.subtotal_cents for line in self.lines)

    def change_status(self, new_status: OrderStatus) -> None:
        transitions = {
            OrderStatus.PENDING: {OrderStatus.CONFIRMED, OrderStatus.CANCELLED},
            OrderStatus.CONFIRMED: {OrderStatus.SHIPPED, OrderStatus.CANCELLED},
            OrderStatus.SHIPPED: set(),
            OrderStatus.CANCELLED: set(),
        }
        if new_status not in transitions[self.status]:
            raise DomainError(f"No se puede pasar de {self.status} a {new_status}")
        self.status = new_status
