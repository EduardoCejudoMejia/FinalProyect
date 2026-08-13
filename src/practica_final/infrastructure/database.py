"""Adaptador SQLAlchemy del puerto de repositorio."""

from __future__ import annotations

from datetime import datetime
from uuid import UUID

from sqlalchemy import DateTime, String, create_engine
from sqlalchemy.orm import DeclarativeBase, Mapped, Session, mapped_column

from practica_final.domain.order import Order, OrderLine, OrderStatus


class Base(DeclarativeBase):
    pass


class OrderModel(Base):
    __tablename__ = "orders"
    id: Mapped[str] = mapped_column(String(36), primary_key=True)
    customer_email: Mapped[str] = mapped_column(String(320), index=True)
    status: Mapped[str] = mapped_column(String(20), index=True)
    lines_json: Mapped[str] = mapped_column(String)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True))


class SqlAlchemyOrderRepository:
    def __init__(self, session: Session) -> None:
        self.session = session

    def _to_domain(self, model: OrderModel) -> Order:
        import json

        lines = [OrderLine(**line) for line in json.loads(model.lines_json)]
        return Order(
            customer_email=model.customer_email,
            lines=lines,
            id=UUID(model.id),
            status=OrderStatus(model.status),
            created_at=model.created_at,
        )

    def _to_model(self, order: Order) -> OrderModel:
        import json

        return OrderModel(
            id=str(order.id),
            customer_email=order.customer_email,
            status=order.status,
            lines_json=json.dumps(
                [
                    {
                        "bicycle_model": x.bicycle_model,
                        "quantity": x.quantity,
                        "unit_price_cents": x.unit_price_cents,
                    }
                    for x in order.lines
                ]
            ),
            created_at=order.created_at,
        )

    def add(self, order: Order) -> Order:
        self.session.add(self._to_model(order))
        self.session.commit()
        return order

    def get(self, order_id: UUID) -> Order | None:
        model = self.session.get(OrderModel, str(order_id))
        return self._to_domain(model) if model else None

    def list(self, offset: int = 0, limit: int = 50) -> list[Order]:
        from sqlalchemy import select

        rows = self.session.scalars(
            select(OrderModel).order_by(OrderModel.created_at.desc()).offset(offset).limit(limit)
        )
        return [self._to_domain(row) for row in rows]

    def save(self, order: Order) -> Order:
        model = self.session.get(OrderModel, str(order.id))
        if model is None:
            raise LookupError("Pedido no encontrado")
        new = self._to_model(order)
        model.status, model.lines_json = new.status, new.lines_json
        self.session.commit()
        return order


def create_session_factory(database_url: str):  # type: ignore[no-untyped-def]
    engine = create_engine(
        database_url, connect_args={"check_same_thread": False} if "sqlite" in database_url else {}
    )
    return engine, Session
