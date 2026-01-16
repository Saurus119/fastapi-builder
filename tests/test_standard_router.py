"""Tests for using standard FastAPI APIRouter with automatic DI.

These tests verify that when services are registered BEFORE creating
routers, the automatic DI patch works correctly.
"""

import pytest
from fastapi import APIRouter
from fastapi.testclient import TestClient

from fastapi_injection import AppBuilder
from fastapi_injection.patch import _apply_patch, _reset_patch

from .conftest import (
    CounterService,
    GreetingService,
    IGreetingService,
    IUserRepository,
    IUserService,
    UserRepository,
    UserService,
)


@pytest.fixture(autouse=True)
def reset_patch():
    """Reset the patch state before each test and re-apply."""
    _reset_patch()
    _apply_patch()  # Re-apply patch for the test
    yield
    _reset_patch()


class TestStandardAPIRouter:
    """Tests for standard APIRouter with automatic DI."""

    def test_simple_endpoint_with_standard_router(self) -> None:
        """Test that standard APIRouter works when services are registered first."""
        # 1. Create builder and register services FIRST
        builder = AppBuilder()
        builder.services.add_singleton(IGreetingService, GreetingService)

        # 2. Create router AFTER services are registered
        router = APIRouter(prefix="/api")

        @router.get("/greet/{name}")
        async def greet(name: str, greeting_service: IGreetingService) -> dict:
            return {"message": greeting_service.greet(name)}

        # 3. Add controller and build
        builder.add_controller(router)
        app = builder.build()

        client = TestClient(app)
        response = client.get("/api/greet/World")

        assert response.status_code == 200
        assert response.json() == {"message": "Hello, World!"}

    def test_nested_dependencies_with_standard_router(self) -> None:
        """Test nested dependencies with standard APIRouter."""
        builder = AppBuilder()
        builder.services.add_scoped(IUserRepository, UserRepository)
        builder.services.add_scoped(IUserService, UserService)

        router = APIRouter(prefix="/users")

        @router.get("/{user_id}")
        async def get_user(user_id: int, user_service: IUserService) -> dict:
            return user_service.get_user(user_id)

        builder.add_controller(router)
        app = builder.build()

        client = TestClient(app)
        response = client.get("/users/42")

        assert response.status_code == 200
        assert response.json() == {"id": 42, "name": "User 42"}

    def test_scoped_lifetime_with_standard_router(self) -> None:
        """Test scoped lifetime with standard APIRouter."""
        CounterService.reset_count()

        builder = AppBuilder()
        builder.services.add_scoped(CounterService)

        router = APIRouter()

        @router.get("/id")
        async def get_id(counter: CounterService) -> dict:
            return {"instance_id": counter.instance_id}

        builder.add_controller(router)
        app = builder.build()

        client = TestClient(app)
        response1 = client.get("/id")
        response2 = client.get("/id")

        # Different instances across requests (scoped)
        assert response1.json()["instance_id"] != response2.json()["instance_id"]

    def test_singleton_lifetime_with_standard_router(self) -> None:
        """Test singleton lifetime with standard APIRouter."""
        CounterService.reset_count()

        builder = AppBuilder()
        builder.services.add_singleton(CounterService)

        router = APIRouter()

        @router.get("/id")
        async def get_id(counter: CounterService) -> dict:
            return {"instance_id": counter.instance_id}

        builder.add_controller(router)
        app = builder.build()

        client = TestClient(app)
        response1 = client.get("/id")
        response2 = client.get("/id")

        # Same instance across requests (singleton)
        assert response1.json()["instance_id"] == response2.json()["instance_id"]

    def test_sync_endpoint_with_standard_router(self) -> None:
        """Test synchronous endpoint with standard APIRouter."""
        builder = AppBuilder()
        builder.services.add_singleton(IGreetingService, GreetingService)

        router = APIRouter()

        @router.get("/sync/{name}")
        def sync_greet(name: str, service: IGreetingService) -> dict:
            return {"message": service.greet(name)}

        builder.add_controller(router)
        app = builder.build()

        client = TestClient(app)
        response = client.get("/sync/World")

        assert response.status_code == 200
        assert response.json() == {"message": "Hello, World!"}

    def test_multiple_services_with_standard_router(self) -> None:
        """Test multiple services injected into same endpoint."""
        builder = AppBuilder()
        builder.services.add_singleton(IGreetingService, GreetingService)
        builder.services.add_scoped(IUserRepository, UserRepository)
        builder.services.add_scoped(IUserService, UserService)

        router = APIRouter()

        @router.get("/combined/{user_id}")
        async def combined(
            user_id: int,
            greeting: IGreetingService,
            users: IUserService,
        ) -> dict:
            user = users.get_user(user_id)
            return {
                "greeting": greeting.greet(user["name"]),
                "user": user,
            }

        builder.add_controller(router)
        app = builder.build()

        client = TestClient(app)
        response = client.get("/combined/5")

        assert response.status_code == 200
        data = response.json()
        assert data["user"] == {"id": 5, "name": "User 5"}
        assert data["greeting"] == "Hello, User 5!"

    def test_endpoint_without_services(self) -> None:
        """Test that endpoints without services still work."""
        builder = AppBuilder()

        router = APIRouter()

        @router.get("/hello")
        async def hello() -> dict:
            return {"message": "Hello!"}

        builder.add_controller(router)
        app = builder.build()

        client = TestClient(app)
        response = client.get("/hello")

        assert response.status_code == 200
        assert response.json() == {"message": "Hello!"}

    def test_mixed_params_with_standard_router(self) -> None:
        """Test mixing path params, query params, and injected services."""
        builder = AppBuilder()
        builder.services.add_singleton(IGreetingService, GreetingService)

        router = APIRouter()

        @router.get("/greet/{name}")
        async def greet(
            name: str,
            exclaim: bool = False,
            service: IGreetingService = None,
        ) -> dict:
            # Note: service will be injected even though it has a default
            message = service.greet(name)
            if exclaim:
                message += "!"
            return {"message": message}

        builder.add_controller(router)
        app = builder.build()

        client = TestClient(app)

        response = client.get("/greet/World")
        assert response.json() == {"message": "Hello, World!"}

        response = client.get("/greet/World?exclaim=true")
        assert response.json() == {"message": "Hello, World!!"}

    def test_router_defined_before_services_registered(self) -> None:
        """Test that routers can be defined BEFORE services are registered.

        This is the key feature that allows routers to be in separate files
        that are imported before the services are configured.
        """
        # 1. Create router BEFORE any services are registered
        # (simulates importing a controller module)
        router = APIRouter(prefix="/api")

        @router.get("/greet/{name}")
        async def greet(name: str, greeting_service: IGreetingService) -> dict:
            return {"message": greeting_service.greet(name)}

        # 2. NOW create builder and register services
        builder = AppBuilder()
        builder.services.add_singleton(IGreetingService, GreetingService)

        # 3. Add controller and build
        builder.add_controller(router)
        app = builder.build()

        # 4. Verify it works
        client = TestClient(app)
        response = client.get("/api/greet/World")

        assert response.status_code == 200
        assert response.json() == {"message": "Hello, World!"}
