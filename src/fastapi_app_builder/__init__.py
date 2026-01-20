"""FastAPI Builder - ASP.NET Core-style dependency injection for FastAPI.

This package provides a clean, familiar dependency injection experience for
FastAPI applications, inspired by ASP.NET Core's DI system.

Features:
- Clean controllers with no Depends() boilerplate
- Standard FastAPI APIRouter - no custom router classes needed
- Builder pattern for application configuration
- Proper service lifetimes (Singleton, Scoped, Transient)
- Startup validation to catch missing dependencies
- Familiar .NET-style naming conventions

Example:
    from typing import Protocol
    from fastapi import APIRouter
    from fastapi_app_builder import AppBuilder

    # Define your services
    class IUserService(Protocol):
        def get_user(self, user_id: int) -> dict: ...

    class UserService:
        def get_user(self, user_id: int) -> dict:
            return {"id": user_id, "name": "John"}

    # Create router - can be in a separate file, imported in any order
    router = APIRouter(prefix="/users")

    @router.get("/{user_id}")
    async def get_user(user_id: int, user_service: IUserService):
        return user_service.get_user(user_id)

    # Configure and build application
    builder = AppBuilder()
    builder.services.add_scoped(IUserService, UserService)
    builder.add_controller(router)
    app = builder.build()
"""

from .builder import AppBuilder
from .container import Services
from .exceptions import (
    CircularDependencyError,
    ScopeNotFoundError,
    ServiceNotRegisteredError,
    ValidationError,
)
from .lifetime import Lifetime
from .resolver import resolve
from .router import InjectableRouter

__all__ = [
    "AppBuilder",
    "Services",
    "Lifetime",
    "InjectableRouter",
    "resolve",
    "ServiceNotRegisteredError",
    "CircularDependencyError",
    "ScopeNotFoundError",
    "ValidationError",
]

__version__ = "0.1.0b1"
