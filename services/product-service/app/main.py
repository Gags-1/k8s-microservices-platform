from fastapi import FastAPI, HTTPException

app = FastAPI(title="Product Service")

PRODUCTS = {
    1: {"id": 1, "name": "Mechanical Keyboard", "price": 2500},
    2: {"id": 2, "name": "Wireless Mouse", "price": 1200},
    3: {"id": 3, "name": "USB-C Hub", "price": 1800},
}


@app.get("/health")
def health():
    return {"status": "healthy", "service": "product-service"}


@app.get("/products")
def list_products():
    return list(PRODUCTS.values())


@app.get("/products/{product_id}")
def get_product(product_id: int):
    product = PRODUCTS.get(product_id)

    if product is None:
        raise HTTPException(status_code=404, detail="Product not found")

    return product
