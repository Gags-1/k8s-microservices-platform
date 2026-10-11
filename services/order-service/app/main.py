import os

import httpx
from fastapi import FastAPI, HTTPException

app = FastAPI(title="Order Service")

PRODUCT_SERVICE_URL = os.getenv(
    "PRODUCT_SERVICE_URL",
    "http://localhost:8001/products/1",
)


@app.get("/health")
def health():
    return {"status": "healthy", "service": "order-service"}


@app.get("/orders/demo")
def create_demo_order():
    try:
        response = httpx.get(PRODUCT_SERVICE_URL, timeout=3.0)
        response.raise_for_status()
        product = response.json()

    except httpx.HTTPError as exc:
        raise HTTPException(
            status_code=502,
            detail="Unable to retrieve product from Product Service",
        ) from exc

    return {
        "order_id": "ORD-1001",
        "status": "created",
        "product": product,
        "quantity": 1,
        "total": product["price"],
    }
