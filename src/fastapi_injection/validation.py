from __future__ import annotations

from collections.abc import Callable
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from .container import Services


def validate_endpoint_dependencies(
    endpoint: Callable[..., object],
    services: Services,
) -> list[str]:
    """Validate that all service dependencies for an endpoint are available.

    Args:
        endpoint: The endpoint function to validate
        services: The services container

    Returns:
        List of validation error messages
    """
    return services.validate_endpoint(endpoint)


def validate_all_services(services: Services) -> list[str]:
    """Validate all registered services.

    Args:
        services: The services container

    Returns:
        List of validation error messages
    """
    return services.validate()
