from demo.repositories import IUserRepository


class UserService:
    """User service with injected repository."""

    def __init__(self, user_repository: IUserRepository) -> None:
        self._repo = user_repository

    def get_user(self, user_id: int) -> dict | None:
        return self._repo.get_by_id(user_id)

    def list_users(self) -> list[dict]:
        return self._repo.get_all()
