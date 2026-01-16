"""Repository layer for database access."""

from typing import Protocol

from sqlalchemy.orm import Session

from .models import User


class IUserRepository(Protocol):
    """Protocol for user repository."""

    def get_by_id(self, user_id: int) -> User | None:
        """Get a user by ID."""
        ...

    def get_all(self) -> list[User]:
        """Get all users."""
        ...

    def create(self, name: str, email: str) -> User:
        """Create a new user."""
        ...

    def delete(self, user_id: int) -> bool:
        """Delete a user by ID."""
        ...


class UserRepository:
    """SQLAlchemy implementation of user repository."""

    def __init__(self, session: Session) -> None:
        self.session = session

    def get_by_id(self, user_id: int) -> User | None:
        return self.session.query(User).filter(User.id == user_id).first()

    def get_all(self) -> list[User]:
        return self.session.query(User).all()

    def create(self, name: str, email: str) -> User:
        user = User(name=name, email=email)
        self.session.add(user)
        self.session.commit()
        self.session.refresh(user)
        return user

    def delete(self, user_id: int) -> bool:
        user = self.get_by_id(user_id)
        if user:
            self.session.delete(user)
            self.session.commit()
            return True
        return False
