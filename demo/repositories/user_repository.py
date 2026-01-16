class UserRepository:
    """In-memory user repository for demo purposes."""

    _users = [
        {"id": 1, "name": "Alice", "email": "alice@example.com"},
        {"id": 2, "name": "Bob", "email": "bob@example.com"},
    ]

    def get_by_id(self, user_id: int) -> dict | None:
        return next((u for u in self._users if u["id"] == user_id), None)

    def get_all(self) -> list[dict]:
        return self._users
