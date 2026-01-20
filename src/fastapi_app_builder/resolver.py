"""Service resolver for accessing services from anywhere during a request.

This module provides a `resolve()` function that can be used to get services
from anywhere in your code during a request, not just in route handlers.

Usage:
    from fastapi_app_builder import resolve

    class UserService:
        def get_user(self, id: int):
            # Resolve a service from anywhere
            cache = resolve(ICacheService)
            return cache.get(f"user:{id}")
"""

from __future__ import annotations

from typing import TypeVar

from .exceptions import ServiceNotRegisteredError
from .patch import get_global_services

T = TypeVar("T")


def resolve(service_type: type[T]) -> T:
    """Resolve a service from anywhere during a request.

    This function allows you to get a registered service from anywhere in your
    code, not just in route handlers. It uses the current request's scope for
    scoped services.

    Args:
        service_type: The service type/interface to resolve

    Returns:
        The resolved service instance

    Raises:
        ServiceNotRegisteredError: If no service container is configured or
                                   the service type is not registered
        ScopeNotFoundError: If resolving a scoped service outside a request

    Example:
        from fastapi_app_builder import resolve

        class OrderService:
            def create_order(self, items: list):
                # Get services on-demand
                inventory = resolve(IInventoryService)
                payment = resolve(IPaymentService)

                for item in items:
                    inventory.reserve(item)

                return payment.charge(items)

    Note:
        While this works, prefer constructor injection when possible.
        Constructor injection makes dependencies explicit and easier to test.
    """
    services = get_global_services()

    if services is None:
        raise ServiceNotRegisteredError(
            "No service container configured. "
            "Make sure to create an AppBuilder and call build() or extend()."
        )

    if not services.is_registered(service_type):
        raise ServiceNotRegisteredError(
            f"Service {service_type.__name__} is not registered. "
            f"Register it with builder.services.add_*()"
        )

    return services.resolve(service_type)
