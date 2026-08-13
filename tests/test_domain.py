import pytest

from practica_final.domain.order import DomainError, Order, OrderLine, OrderStatus


def test_total_and_valid_transition() -> None:
    order = Order("ana@example.com", [OrderLine("Montaña Pro", 2, 125_000)])
    assert order.total_cents == 250_000
    order.change_status(OrderStatus.CONFIRMED)
    assert order.status == OrderStatus.CONFIRMED


def test_cannot_ship_pending_order() -> None:
    order = Order("ana@example.com", [OrderLine("Urbana", 1, 50_000)])
    with pytest.raises(DomainError, match="No se puede"):
        order.change_status(OrderStatus.SHIPPED)


def test_order_requires_lines() -> None:
    with pytest.raises(DomainError):
        Order("ana@example.com", [])
