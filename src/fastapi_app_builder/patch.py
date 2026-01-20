"""Monkey-patching utilities to make standard APIRouter work with DI.

This module patches FastAPI's parameter analysis to recognize potential
service types (Protocols, ABCs) and automatically inject them using Depends.

The patch is applied at module import time, and service resolution happens
at request time. This allows routers to be defined in separate files and
imported before services are registered.

Usage:
    from fastapi_app_builder import AppBuilder
    from controllers import user_router  # Can import before registering!

    builder = AppBuilder()
    builder.services.add_scoped(IUserService, UserService)
    builder.add_controller(user_router)
    app = builder.build()
"""

from __future__ import annotations

import functools
import inspect
from collections.abc import Callable
from typing import TYPE_CHECKING, Any, Protocol

from fastapi import Depends

if TYPE_CHECKING:
    from .container import Services

# Global registry - shared across all Services instances
_global_services: Services | None = None
_patched = False
_original_analyze_param: Any = None


def set_global_services(services: Services) -> None:
    """Set the global services container for injection."""
    global _global_services
    _global_services = services


def get_global_services() -> Services | None:
    """Get the global services container."""
    return _global_services


def _is_potential_service_type(annotation: Any) -> bool:
    """Check if an annotation looks like a service type (Protocol or ABC).

    This is used at decoration time to determine if a parameter should be
    treated as an injectable service. We check for Protocol and ABC because
    these are commonly used for interface definitions in DI patterns.
    """
    if not isinstance(annotation, type):
        return False

    # Check if it's a Protocol
    # Protocol classes have _is_protocol attribute set to True
    if getattr(annotation, '_is_protocol', False):
        return True

    # Check if any base class is a Protocol
    for base in getattr(annotation, '__mro__', []):
        if getattr(base, '_is_protocol', False) and base is not Protocol:
            return True

    # Check if it's an ABC (Abstract Base Class)
    from abc import ABC, ABCMeta
    if isinstance(annotation, ABCMeta) or ABC in getattr(annotation, '__mro__', []):
        # But not built-in ABCs like Sequence, Mapping, etc.
        module = getattr(annotation, '__module__', '')
        if not module.startswith('collections') and not module.startswith('typing'):
            return True

    return False


def _apply_patch() -> None:
    """Apply the FastAPI patch to recognize injectable types.

    This patch intercepts FastAPI's parameter analysis and:
    1. At decoration time: detects potential service types (Protocols, ABCs)
    2. At request time: resolves the actual service from the container

    This allows routers to be defined before services are registered.
    """
    global _patched, _original_analyze_param
    if _patched:
        return

    try:
        from fastapi.dependencies import utils as dep_utils
        from pydantic_core import PydanticUndefined

        # Store the original function for potential restoration
        _original_analyze_param = dep_utils.analyze_param
        original_analyze_param = _original_analyze_param

        @functools.wraps(original_analyze_param)
        def patched_analyze_param(
            *,
            param_name: str,
            annotation: Any,
            value: Any,
            is_path_param: bool,
            **kwargs: Any,
        ) -> Any:
            # Check if no default is set (inspect._empty, PydanticUndefined, or None)
            has_no_default = (
                value is None
                or value is PydanticUndefined
                or value is inspect.Parameter.empty
            )

            # Determine if this parameter should be treated as an injectable service:
            # 1. Protocol/ABC → always injectable (works before registration)
            # 2. Registered concrete class → injectable
            services = get_global_services()
            is_injectable = False

            if has_no_default and isinstance(annotation, type):
                if _is_potential_service_type(annotation):
                    # Protocols and ABCs are always injectable
                    is_injectable = True
                elif services is not None and services.is_registered(annotation):
                    # Concrete classes that are explicitly registered
                    is_injectable = True

            if is_injectable:
                # Create a dependency resolver that looks up the service at request time
                service_type = annotation  # Capture for closure

                def make_resolver(svc_type: type) -> Callable[[], Any]:
                    def resolver() -> Any:
                        svc = get_global_services()
                        if svc is None:
                            from .exceptions import ServiceNotRegisteredError
                            raise ServiceNotRegisteredError(
                                "No service container configured. "
                                "Create an AppBuilder before handling requests."
                            )
                        if not svc.is_registered(svc_type):
                            from .exceptions import ServiceNotRegisteredError
                            raise ServiceNotRegisteredError(
                                f"Service {svc_type.__name__} is not registered. "
                                f"Register it with builder.services.add_*()"
                            )
                        return svc.resolve(svc_type)
                    return resolver

                # Replace with a Depends call
                value = Depends(make_resolver(service_type))
                # Change annotation to Any to avoid Pydantic validation
                annotation = Any

            return original_analyze_param(
                param_name=param_name,
                annotation=annotation,
                value=value,
                is_path_param=is_path_param,
                **kwargs,
            )

        dep_utils.analyze_param = patched_analyze_param
        _patched = True
    except Exception as e:
        # If patching fails, log a warning
        import warnings
        warnings.warn(
            f"Failed to patch FastAPI for automatic DI. "
            f"Use InjectableRouter instead. Error: {e}",
            stacklevel=2,
        )


def _reset_patch() -> None:
    """Reset the patch state (for testing).

    This restores the original analyze_param function and clears the services.
    After calling this, _apply_patch() can be called again.
    """
    global _patched, _global_services, _original_analyze_param

    # Restore original function if we have it
    if _original_analyze_param is not None:
        try:
            from fastapi.dependencies import utils as dep_utils
            dep_utils.analyze_param = _original_analyze_param
        except ImportError:
            pass

    _patched = False
    _global_services = None
    _original_analyze_param = None


# Apply patch at module import time
# This ensures the patch is in place before any routers are defined
_apply_patch()
