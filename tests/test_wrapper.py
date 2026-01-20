"""Tests for endpoint wrapping."""

import inspect
from typing import Protocol

from fastapi_builder import Services
from fastapi_builder.wrapper import wrap_endpoint

from .conftest import GreetingService, IGreetingService


def _is_depends(obj) -> bool:
    """Check if an object is a FastAPI Depends instance."""
    # Depends objects have a 'dependency' attribute
    return hasattr(obj, "dependency") and callable(obj.dependency)


class TestWrapEndpoint:
    """Tests for the wrap_endpoint function."""

    def test_wraps_async_endpoint_with_service(
        self, services: Services
    ) -> None:
        services.add_singleton(IGreetingService, GreetingService)

        async def endpoint(
            name: str, greeting_service: IGreetingService
        ) -> dict:
            return {"message": greeting_service.greet(name)}

        wrapped = wrap_endpoint(endpoint, services)

        # Check that the signature was modified to have Depends
        sig = inspect.signature(wrapped)
        assert "name" in sig.parameters
        assert "greeting_service" in sig.parameters
        # The service param should have a Depends default
        param = sig.parameters["greeting_service"]
        assert _is_depends(param.default)

    def test_wraps_sync_endpoint_with_service(
        self, services: Services
    ) -> None:
        services.add_singleton(IGreetingService, GreetingService)

        def endpoint(name: str, greeting_service: IGreetingService) -> dict:
            return {"message": greeting_service.greet(name)}

        wrapped = wrap_endpoint(endpoint, services)

        sig = inspect.signature(wrapped)
        assert "name" in sig.parameters
        assert "greeting_service" in sig.parameters
        param = sig.parameters["greeting_service"]
        assert _is_depends(param.default)

    def test_returns_original_if_no_services(
        self, services: Services
    ) -> None:
        async def endpoint(name: str) -> dict:
            return {"name": name}

        wrapped = wrap_endpoint(endpoint, services)

        # Should return original function
        assert wrapped is endpoint

    def test_preserves_function_metadata(self, services: Services) -> None:
        services.add_singleton(IGreetingService, GreetingService)

        async def my_endpoint(greeting_service: IGreetingService) -> dict:
            """My endpoint docstring."""
            return {}

        wrapped = wrap_endpoint(my_endpoint, services)

        assert wrapped.__name__ == "my_endpoint"
        assert wrapped.__doc__ == "My endpoint docstring."

    def test_handles_multiple_services(self, services: Services) -> None:
        class IAnotherService(Protocol):
            def process(self) -> str:
                ...

        class AnotherService:
            def process(self) -> str:
                return "processed"

        services.add_singleton(IGreetingService, GreetingService)
        services.add_singleton(IAnotherService, AnotherService)

        async def endpoint(
            greeting_service: IGreetingService,
            another_service: IAnotherService,
        ) -> dict:
            return {
                "greeting": greeting_service.greet("Test"),
                "processed": another_service.process(),
            }

        wrapped = wrap_endpoint(endpoint, services)

        sig = inspect.signature(wrapped)
        # Both service params should be there with Depends defaults
        assert "greeting_service" in sig.parameters
        assert "another_service" in sig.parameters
        assert _is_depends(sig.parameters["greeting_service"].default)
        assert _is_depends(sig.parameters["another_service"].default)

    def test_preserves_non_service_parameters(
        self, services: Services
    ) -> None:
        services.add_singleton(IGreetingService, GreetingService)

        async def endpoint(
            user_id: int,
            name: str,
            greeting_service: IGreetingService,
            count: int = 1,
        ) -> dict:
            return {}

        wrapped = wrap_endpoint(endpoint, services)

        sig = inspect.signature(wrapped)
        params = list(sig.parameters.keys())

        assert "user_id" in params
        assert "name" in params
        assert "count" in params
        assert "greeting_service" in params
        # Non-service params should keep their original defaults
        assert sig.parameters["count"].default == 1
        # Service param should have Depends default
        assert _is_depends(sig.parameters["greeting_service"].default)
