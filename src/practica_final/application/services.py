"""Casos de uso del servicio de pedidos."""

from __future__ import annotations

from dataclasses import dataclass
from uuid import UUID

from practica_final.application.ports import EventPublisher, OrderRepository
from practica_final.domain.order import Order, OrderLine, OrderStatus


class OrderNotFoundError(LookupError):
    pass


@dataclass(frozen=True)
class CreateLine:
    bicycle_model: str
    quantity: int
    unit_price_cents: int


class OrderService:
    def __init__(self, repository: OrderRepository, events: EventPublisher) -> None:
        self.repository, self.events = repository, events

    def create_order(self, customer_email: str, lines: list[CreateLine]) -> Order:
        order = Order(customer_email, [OrderLine(**line.__dict__) for line in lines])
        saved = self.repository.add(order)
        self.events.publish("order.created", {"order_id": str(saved.id)})
        return saved

    def get_order(self, order_id: UUID) -> Order:
        order = self.repository.get(order_id)
        if order is None:
            raise OrderNotFoundError("Pedido no encontrado")
        return order

    def list_orders(self, offset: int, limit: int) -> list[Order]:
        return self.repository.list(offset, limit)

    def change_status(self, order_id: UUID, status: OrderStatus) -> Order:
        order = self.get_order(order_id)
        order.change_status(status)
        saved = self.repository.save(order)
        self.events.publish("order.status_changed", {"order_id": str(saved.id), "status": status})
        return saved
