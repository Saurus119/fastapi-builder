from __future__ import annotations

import inspect
from collections.abc import Callable
from functools import wraps
from typing import Any, get_type_hints

from fastapi import Depends

from .container import Services


def create_service_dependency(
    service_type: type,
    services: Services,
) -> Callable[[], Any]:
    """Create a FastAPI dependency function for a service type."""

    def dependency() -> Any:
        return services.resolve(service_type)

    return dependency


def wrap_endpoint(
    endpoint: Callable[..., Any],
    services: Services,
) -> Callable[..., Any]:
    """Wrap endpoint to inject services automatically using FastAPI's Depends.

    This function inspects the endpoint's type hints, identifies parameters
    that are registered services, and creates a wrapper that uses FastAPI's
    Depends mechanism to inject them.
    """
    sig = inspect.signature(endpoint)

    try:
        hints = get_type_hints(endpoint)
    except Exception:
        # If we can't get type hints, return original endpoint
        return endpoint

    # Identify which params are registered services
    service_params: dict[str, type] = {}
    for name, hint in hints.items():
        if name == "return":
            continue
        if services.is_registered(hint):
            service_params[name] = hint

    # No services to inject - return original
    if not service_params:
        return endpoint

    # Build new parameters - replace service types with Depends() defaults
    new_params = []
    for param in sig.parameters.values():
        if param.name in service_params:
            service_type = service_params[param.name]
            dependency = create_service_dependency(service_type, services)
            new_param = param.replace(
                default=Depends(dependency),
                annotation=Any,  # Use Any to avoid Pydantic validation issues
            )
            new_params.append(new_param)
        else:
            new_params.append(param)

    is_async = inspect.iscoroutinefunction(endpoint)

    if is_async:

        @wraps(endpoint)
        async def async_wrapper(*args: Any, **kwargs: Any) -> Any:
            return await endpoint(*args, **kwargs)

        async_wrapper.__signature__ = sig.replace(parameters=new_params)  # type: ignore[attr-defined]
        return async_wrapper
    else:

        @wraps(endpoint)
        def sync_wrapper(*args: Any, **kwargs: Any) -> Any:
            return endpoint(*args, **kwargs)

        sync_wrapper.__signature__ = sig.replace(parameters=new_params)  # type: ignore[attr-defined]
        return sync_wrapper
