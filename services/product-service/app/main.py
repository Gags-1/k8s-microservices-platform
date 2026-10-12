import time
from prometheus_client import Counter, Histogram, make_asgi_app

import json
import logging
import sys
from fastapi import FastAPI, HTTPException, Request

app = FastAPI(title="Product Service")

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

# Configure JSON logging to stdout
logging.basicConfig(
    level=logging.INFO,
    stream=sys.stdout,
    format="%(message)s",
)

logger = logging.getLogger("product-service")


class JSONFormatter(logging.Formatter):
    def format(self, record):
        return json.dumps({
            "level": record.levelname,
            "service": "product-service",
            "message": record.getMessage(),
        })


for handler in logging.root.handlers:
    handler.setFormatter(JSONFormatter())


@app.middleware("http")
async def log_requests(request: Request, call_next):
    # Keep metrics scraping from inflating application request metrics.
    if request.url.path.startswith("/metrics"):
        return await call_next(request)

    start_time = time.perf_counter()

    response = await call_next(request)

    duration = time.perf_counter() - start_time
    endpoint = request.scope.get("route")
    endpoint_path = getattr(endpoint, "path", request.url.path)

    REQUEST_COUNT.labels(
        service="product-service",
        method=request.method,
        endpoint=endpoint_path,
        status=str(response.status_code),
    ).inc()

    REQUEST_LATENCY.labels(
        service="product-service",
        method=request.method,
        endpoint=endpoint_path,
    ).observe(duration)

    logger.info(json.dumps({
        "event": "http_request",
        "method": request.method,
        "path": request.url.path,
        "status_code": response.status_code,
    }))

    return response

PRODUCTS = {
    1: {"id": 1, "name": "Mechanical Keyboard", "price": 2500},
    2: {"id": 2, "name": "Wireless Mouse", "price": 1200},
    3: {"id": 3, "name": "USB-C Hub", "price": 1800},
}


@app.get("/health")
def health():
    return {"status": "healthy", "service": "product-service"}

@app.get("/version")
def version():
    return {"service": "product-service", "version": "v2"}

@app.get("/products")
def list_products():
    return list(PRODUCTS.values())


@app.get("/products/{product_id}")
def get_product(product_id: int):
    product = PRODUCTS.get(product_id)

    if product is None:
        raise HTTPException(status_code=404, detail="Product not found")

    return product
