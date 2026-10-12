from fastapi.testclient import TestClient

from app.main import app

client = TestClient(app)


def test_health():
    response = client.get("/health")

    assert response.status_code == 200
    assert response.json() == {
        "status": "healthy",
        "service": "product-service",
    }


def test_list_products():
    response = client.get("/products")

    assert response.status_code == 200

    products = response.json()
    assert len(products) == 3
    assert products[0]["name"] == "Mechanical Keyboard"


def test_get_existing_product():
    response = client.get("/products/1")

    assert response.status_code == 200
    assert response.json() == {
        "id": 1,
        "name": "Mechanical Keyboard",
        "price": 2500,
    }


def test_get_missing_product():
    response = client.get("/products/999")

    assert response.status_code == 404
    assert response.json()["detail"] == "Product not found"


def test_version():
    response = client.get("/version")

    assert response.status_code == 200
    assert response.json()["version"] == "v2"



def test_metrics_endpoint_exposes_prometheus_metrics():
    # Generate a request so the counter has a known series.
    client.get("/health")

    response = client.get("/metrics")

    assert response.status_code == 200
    assert "text/plain" in response.headers["content-type"]
    assert "http_requests_total" in response.text
    assert 'service="product-service"' in response.text
