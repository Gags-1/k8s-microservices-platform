import os
import time
from prometheus_client import Counter, Histogram, make_asgi_app
import httpx
from fastapi import FastAPI, HTTPException

app = FastAPI(title="Order Service")

REQUEST_COUNT = Counter(
    "http_requests_total",
    "Total HTTP requests",
    ["service", "method", "endpoint", "status"],
)

REQUEST_LATENCY = Histogram(
    "http_request_duration_seconds",
    "HTTP request latency in seconds",
    ["service", "method", "endpoint"],
)

metrics_app = make_asgi_app()
app.mount("/metrics", metrics_app)


@app.middleware("http")
async def collect_metrics(request, call_next):
    if request.url.path.startswith("/metrics"):
        return await call_next(request)

    start_time = time.perf_counter()

    response = await call_next(request)

    duration = time.perf_counter() - start_time
    endpoint = request.scope.get("route")
    endpoint_path = getattr(endpoint, "path", request.url.path)

    REQUEST_COUNT.labels(
        service="order-service",
        method=request.method,
        endpoint=endpoint_path,
        status=str(response.status_code),
    ).inc()

    REQUEST_LATENCY.labels(
        service="order-service",
        method=request.method,
        endpoint=endpoint_path,
    ).observe(duration)

    return response


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
