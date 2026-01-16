class ProductRepository:
    """In-memory product repository for demo purposes."""

    _products = [
        {"id": 1, "name": "Laptop", "price": 999.99},
        {"id": 2, "name": "Mouse", "price": 29.99},
    ]

    def get_by_id(self, product_id: int) -> dict | None:
        return next((p for p in self._products if p["id"] == product_id), None)

    def get_all(self) -> list[dict]:
        return self._products
