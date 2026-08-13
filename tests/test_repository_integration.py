from sqlalchemy import create_engine
from sqlalchemy.orm import Session

from practica_final.domain.order import Order, OrderLine
from practica_final.infrastructure.database import Base, SqlAlchemyOrderRepository


def test_repository_persists_order() -> None:
    engine = create_engine("sqlite:///:memory:")
    Base.metadata.create_all(engine)
    with Session(engine) as session:
        repository = SqlAlchemyOrderRepository(session)
        created = repository.add(Order("buyer@example.com", [OrderLine("City 1", 1, 40000)]))
        restored = repository.get(created.id)
    assert restored is not None
    assert restored.customer_email == "buyer@example.com"
    assert restored.lines[0].bicycle_model == "City 1"
