"""Pytest fixtures for fastapi-injection tests."""

from typing import Protocol

import pytest
from fastapi import APIRouter

from fastapi_app_builder import AppBuilder, Services


# Test interfaces and implementations
class IGreetingService(Protocol):
    """Protocol for greeting service."""

    def greet(self, name: str) -> str:
        ...


class GreetingService:
    """Simple greeting service implementation."""

    def greet(self, name: str) -> str:
        return f"Hello, {name}!"


class IUserRepository(Protocol):
    """Protocol for user repository."""

    def get_by_id(self, user_id: int) -> dict:
        ...


class UserRepository:
    """Simple user repository implementation."""

    def get_by_id(self, user_id: int) -> dict:
        return {"id": user_id, "name": f"User {user_id}"}


class IUserService(Protocol):
    """Protocol for user service."""

    def get_user(self, user_id: int) -> dict:
        ...


class UserService:
    """User service that depends on IUserRepository."""

    def __init__(self, user_repository: IUserRepository) -> None:
        self.user_repository = user_repository

    def get_user(self, user_id: int) -> dict:
        return self.user_repository.get_by_id(user_id)


class ServiceA:
    """Service that depends on ServiceB (for circular dependency test)."""

    def __init__(self, service_b: "ServiceB") -> None:
        self.service_b = service_b


class ServiceB:
    """Service that depends on ServiceA (for circular dependency test)."""

    def __init__(self, service_a: ServiceA) -> None:
        self.service_a = service_a


class CounterService:
    """Service that tracks instance count."""

    _instance_count = 0

    def __init__(self) -> None:
        CounterService._instance_count += 1
        self.instance_id = CounterService._instance_count

    @classmethod
    def reset_count(cls) -> None:
        cls._instance_count = 0


@pytest.fixture
def services() -> Services:
    """Create a fresh Services container."""
    return Services()


@pytest.fixture
def builder() -> AppBuilder:
    """Create a fresh AppBuilder."""
    return AppBuilder()


@pytest.fixture
def greeting_router() -> APIRouter:
    """Create a router with greeting endpoints."""
    router = APIRouter(prefix="/greetings", tags=["Greetings"])

    @router.get("/{name}")
    async def greet(name: str, greeting_service: IGreetingService) -> dict:
        return {"message": greeting_service.greet(name)}

    return router


@pytest.fixture
def user_router() -> APIRouter:
    """Create a router with user endpoints."""
    router = APIRouter(prefix="/users", tags=["Users"])

    @router.get("/{user_id}")
    async def get_user(user_id: int, user_service: IUserService) -> dict:
        return user_service.get_user(user_id)

    return router


@pytest.fixture
def simple_router() -> APIRouter:
    """Create a router with no DI dependencies."""
    router = APIRouter(prefix="/simple", tags=["Simple"])

    @router.get("/hello")
    async def hello() -> dict:
        return {"message": "Hello, World!"}

    return router
