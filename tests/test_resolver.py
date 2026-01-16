"""Tests for the resolve() function."""

import pytest
from fastapi import APIRouter
from fastapi.testclient import TestClient

from fastapi_injection import AppBuilder, resolve
from fastapi_injection.exceptions import ServiceNotRegisteredError
from fastapi_injection.patch import _apply_patch, _reset_patch

from .conftest import (
    GreetingService,
    IGreetingService,
    IUserRepository,
    UserRepository,
)


@pytest.fixture(autouse=True)
def reset_patch():
    """Reset the patch state before each test and re-apply."""
    _reset_patch()
    _apply_patch()
    yield
    _reset_patch()


class TestResolveFunction:
    """Tests for resolving services from anywhere."""

    def test_resolve_in_service_method(self) -> None:
        """Test resolving a service from within another service's method."""

        class OrderService:
            def create_order(self, item: str) -> dict:
                # Resolve another service on-demand
                greeting = resolve(IGreetingService)
                return {"item": item, "message": greeting.greet(item)}

        builder = AppBuilder()
        builder.services.add_singleton(IGreetingService, GreetingService)
        builder.services.add_scoped(OrderService)

        router = APIRouter()

        @router.post("/orders/{item}")
        async def create_order(item: str, order_service: OrderService) -> dict:
            return order_service.create_order(item)

        builder.add_controller(router)
        app = builder.build()

        client = TestClient(app)
        response = client.post("/orders/Widget")

        assert response.status_code == 200
        assert response.json() == {
            "item": "Widget",
            "message": "Hello, Widget!",
        }

    def test_resolve_in_utility_function(self) -> None:
        """Test resolving a service from a utility function."""

        def get_greeting_for(name: str) -> str:
            service = resolve(IGreetingService)
            return service.greet(name)

        builder = AppBuilder()
        builder.services.add_singleton(IGreetingService, GreetingService)

        router = APIRouter()

        @router.get("/greet/{name}")
        async def greet(name: str) -> dict:
            # Call utility function that uses resolve()
            message = get_greeting_for(name)
            return {"message": message}

        builder.add_controller(router)
        app = builder.build()

        client = TestClient(app)
        response = client.get("/greet/World")

        assert response.status_code == 200
        assert response.json() == {"message": "Hello, World!"}

    def test_resolve_scoped_service(self) -> None:
        """Test that scoped services work with resolve()."""
        from .conftest import CounterService

        CounterService.reset_count()

        builder = AppBuilder()
        builder.services.add_scoped(CounterService)

        router = APIRouter()

        @router.get("/check")
        async def check() -> dict:
            # Resolve same scoped service twice in one request
            counter1 = resolve(CounterService)
            counter2 = resolve(CounterService)
            return {
                "same_instance": counter1 is counter2,
                "id1": counter1.instance_id,
                "id2": counter2.instance_id,
            }

        builder.add_controller(router)
        app = builder.build()

        client = TestClient(app)
        response = client.get("/check")

        data = response.json()
        assert data["same_instance"] is True
        assert data["id1"] == data["id2"]

    def test_resolve_unregistered_service_raises(self) -> None:
        """Test that resolving an unregistered service raises an error."""

        class UnregisteredService:
            pass

        # Directly test resolve() without going through a request
        builder = AppBuilder()
        builder.services.add_singleton(IGreetingService, GreetingService)
        builder.build()  # This sets up the global services

        with pytest.raises(ServiceNotRegisteredError) as exc_info:
            resolve(UnregisteredService)

        assert "not registered" in str(exc_info.value)

    def test_resolve_without_container_raises(self) -> None:
        """Test that resolve() raises when no container is configured."""
        # Reset to ensure no global services
        _reset_patch()

        with pytest.raises(ServiceNotRegisteredError) as exc_info:
            resolve(IGreetingService)

        assert "No service container configured" in str(exc_info.value)

        # Re-apply patch for other tests
        _apply_patch()

    def test_resolve_nested_services(self) -> None:
        """Test resolving services that have their own dependencies."""

        class NotificationService:
            def send(self, user_id: int) -> dict:
                # Resolve user repo to get user info
                repo = resolve(IUserRepository)
                user = repo.get_by_id(user_id)  # Use correct method name
                return {"sent_to": user["name"]}

        builder = AppBuilder()
        builder.services.add_scoped(IUserRepository, UserRepository)
        builder.services.add_scoped(NotificationService)

        router = APIRouter()

        @router.post("/notify/{user_id}")
        async def notify(user_id: int, notifier: NotificationService) -> dict:
            return notifier.send(user_id)

        builder.add_controller(router)
        app = builder.build()

        client = TestClient(app)
        response = client.post("/notify/42")

        assert response.status_code == 200
        assert response.json() == {"sent_to": "User 42"}
