"""Service layer for business logic."""

from typing import Protocol

from pydantic import BaseModel

from .repositories import IUserRepository


class UserDto(BaseModel):
    """User data transfer object."""

    id: int
    name: str
    email: str


class CreateUserDto(BaseModel):
    """DTO for creating a user."""

    name: str
    email: str


class IUserService(Protocol):
    """Protocol for user service."""

    def get_user(self, user_id: int) -> UserDto | None:
        """Get a user by ID."""
        ...

    def get_all_users(self) -> list[UserDto]:
        """Get all users."""
        ...

    def create_user(self, data: CreateUserDto) -> UserDto:
        """Create a new user."""
        ...

    def delete_user(self, user_id: int) -> bool:
        """Delete a user."""
        ...


class UserService:
    """Implementation of user service."""

    def __init__(self, user_repository: IUserRepository) -> None:
        self.user_repository = user_repository

    def get_user(self, user_id: int) -> UserDto | None:
        user = self.user_repository.get_by_id(user_id)
        if user:
            return UserDto(id=user.id, name=user.name, email=user.email)
        return None

    def get_all_users(self) -> list[UserDto]:
        users = self.user_repository.get_all()
        return [UserDto(id=u.id, name=u.name, email=u.email) for u in users]

    def create_user(self, data: CreateUserDto) -> UserDto:
        user = self.user_repository.create(name=data.name, email=data.email)
        return UserDto(id=user.id, name=user.name, email=user.email)

    def delete_user(self, user_id: int) -> bool:
        return self.user_repository.delete(user_id)
