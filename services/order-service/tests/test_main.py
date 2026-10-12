import httpx
from fastapi.testclient import TestClient

from app.main import app

client = TestClient(app)


def test_health():
    response = client.get("/health")

    assert response.status_code == 200
    assert response.json() == {
        "status": "healthy",
        "service": "order-service",
    }


def test_create_demo_order(monkeypatch):
    def mock_get(url, timeout):
        assert url.endswith("/products/1")
        assert timeout == 3.0

        return httpx.Response(
            200,
            json={
                "id": 1,
                "name": "Mechanical Keyboard",
                "price": 2500,
            },
            request=httpx.Request("GET", url),
        )

    monkeypatch.setattr("app.main.httpx.get", mock_get)

    response = client.get("/orders/demo")

    assert response.status_code == 200
    assert response.json() == {
        "order_id": "ORD-1001",
        "status": "created",
        "product": {
            "id": 1,
            "name": "Mechanical Keyboard",
            "price": 2500,
        },
        "quantity": 1,
        "total": 2500,
    }


def test_product_service_failure_returns_502(monkeypatch):
    def mock_get(url, timeout):
        request = httpx.Request("GET", url)

        raise httpx.ConnectError(
            "Product Service unavailable",
            request=request,
        )

    monkeypatch.setattr("app.main.httpx.get", mock_get)

    response = client.get("/orders/demo")

    assert response.status_code == 502
    assert response.json()["detail"] == (
        "Unable to retrieve product from Product Service"
    )
