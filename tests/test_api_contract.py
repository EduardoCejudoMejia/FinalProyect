from fastapi.testclient import TestClient

from practica_final.api import app, engine
from practica_final.infrastructure.database import Base

Base.metadata.create_all(engine)
client = TestClient(app)


def token() -> dict[str, str]:
    response = client.post("/auth/token")
    return {"Authorization": f"Bearer {response.json()['access_token']}"}


def test_create_and_get_order_contract() -> None:
    created = client.post(
        "/orders",
        headers=token(),
        json={
            "customer_email": "cliente@example.com",
            "lines": [{"bicycle_model": "Gravel 400", "quantity": 1, "unit_price_cents": 99900}],
        },
    )
    assert created.status_code == 201
    body = created.json()
    assert body["status"] == "pending"
    assert body["total_cents"] == 99900
    found = client.get(f"/orders/{body['id']}", headers=token())
    assert found.status_code == 200


def test_orders_require_bearer_token() -> None:
    assert client.get("/orders").status_code == 401


def test_openapi_documents_order_schema() -> None:
    schema = client.get("/openapi.json").json()
    assert "/orders" in schema["paths"]
    assert "OrderCreate" in schema["components"]["schemas"]
