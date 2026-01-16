from __future__ import annotations

import inspect
from collections.abc import Callable, Sequence
from dataclasses import dataclass
from typing import TYPE_CHECKING, Any, get_type_hints

from fastapi import APIRouter, Depends
from fastapi.responses import JSONResponse
from fastapi.types import IncEx
from starlette.responses import Response
from starlette.routing import BaseRoute

from .container import Services

if TYPE_CHECKING:
    from fastapi.params import Depends as DependsType


@dataclass
class PendingRoute:
    """Stores route information before processing."""

    path: str
    endpoint: Callable[..., Any]
    methods: set[str] | None
    name: str | None
    response_model: Any
    status_code: int | None
    tags: list[str] | None
    summary: str | None
    description: str | None
    response_description: str
    responses: dict[int | str, dict[str, Any]] | None
    deprecated: bool | None
    operation_id: str | None
    include_in_schema: bool
    response_class: type[Response] | None
    response_model_include: IncEx | None
    response_model_exclude: IncEx | None
    callbacks: list[BaseRoute] | None
    openapi_extra: dict[str, Any] | None
    generate_unique_id_function: Callable[[Any], str] | None


class InjectableRouter:
    """A router that supports automatic dependency injection.

    This router stores endpoint definitions and processes them when
    attached to an AppBuilder, enabling clean dependency injection
    without explicit Depends() calls.

    Example:
        router = InjectableRouter(prefix="/users", tags=["Users"])

        @router.get("/{user_id}")
        async def get_user(user_id: int, user_service: IUserService):
            return user_service.get_user(user_id)

        builder = AppBuilder()
        builder.services.add_scoped(IUserService, UserService)
        builder.add_controller(router)
    """

    def __init__(
        self,
        prefix: str = "",
        tags: list[str] | None = None,
        dependencies: Sequence[DependsType] | None = None,
        default_response_class: type[Response] | None = None,
        responses: dict[int | str, dict[str, Any]] | None = None,
        callbacks: list[BaseRoute] | None = None,
        redirect_slashes: bool = True,
        default: Callable[..., Any] | None = None,
        dependency_overrides_provider: Any | None = None,
        deprecated: bool | None = None,
        include_in_schema: bool = True,
        generate_unique_id_function: Callable[[Any], str] | None = None,
    ) -> None:
        self.prefix = prefix
        self.tags = tags or []
        self.dependencies = list(dependencies) if dependencies else []
        self.default_response_class = default_response_class or JSONResponse
        self.responses = responses or {}
        self.callbacks = callbacks
        self.redirect_slashes = redirect_slashes
        self.default = default
        self.dependency_overrides_provider = dependency_overrides_provider
        self.deprecated = deprecated
        self.include_in_schema = include_in_schema
        self.generate_unique_id_function = generate_unique_id_function
        self._pending_routes: list[PendingRoute] = []

    def _add_route(
        self,
        path: str,
        endpoint: Callable[..., Any],
        methods: set[str] | None = None,
        name: str | None = None,
        response_model: Any = None,
        status_code: int | None = None,
        tags: list[str] | None = None,
        summary: str | None = None,
        description: str | None = None,
        response_description: str = "Successful Response",
        responses: dict[int | str, dict[str, Any]] | None = None,
        deprecated: bool | None = None,
        operation_id: str | None = None,
        include_in_schema: bool = True,
        response_class: type[Response] | None = None,
        response_model_include: IncEx | None = None,
        response_model_exclude: IncEx | None = None,
        callbacks: list[BaseRoute] | None = None,
        openapi_extra: dict[str, Any] | None = None,
        generate_unique_id_function: Callable[[Any], str] | None = None,
    ) -> None:
        """Store a route for later processing."""
        self._pending_routes.append(
            PendingRoute(
                path=path,
                endpoint=endpoint,
                methods=methods,
                name=name,
                response_model=response_model,
                status_code=status_code,
                tags=tags,
                summary=summary,
                description=description,
                response_description=response_description,
                responses=responses,
                deprecated=deprecated,
                operation_id=operation_id,
                include_in_schema=include_in_schema,
                response_class=response_class or self.default_response_class,
                response_model_include=response_model_include,
                response_model_exclude=response_model_exclude,
                callbacks=callbacks,
                openapi_extra=openapi_extra,
                generate_unique_id_function=generate_unique_id_function,
            )
        )

    def get(
        self,
        path: str,
        *,
        response_model: Any = None,
        status_code: int | None = None,
        tags: list[str] | None = None,
        summary: str | None = None,
        description: str | None = None,
        response_description: str = "Successful Response",
        responses: dict[int | str, dict[str, Any]] | None = None,
        deprecated: bool | None = None,
        operation_id: str | None = None,
        include_in_schema: bool = True,
        response_class: type[Response] | None = None,
        name: str | None = None,
        callbacks: list[BaseRoute] | None = None,
        openapi_extra: dict[str, Any] | None = None,
        generate_unique_id_function: Callable[[Any], str] | None = None,
    ) -> Callable[[Callable[..., Any]], Callable[..., Any]]:
        """Decorator for GET endpoints."""

        def decorator(func: Callable[..., Any]) -> Callable[..., Any]:
            self._add_route(
                path,
                func,
                methods={"GET"},
                response_model=response_model,
                status_code=status_code,
                tags=tags,
                summary=summary,
                description=description,
                response_description=response_description,
                responses=responses,
                deprecated=deprecated,
                operation_id=operation_id,
                include_in_schema=include_in_schema,
                response_class=response_class,
                name=name,
                callbacks=callbacks,
                openapi_extra=openapi_extra,
                generate_unique_id_function=generate_unique_id_function,
            )
            return func

        return decorator

    def post(
        self,
        path: str,
        *,
        response_model: Any = None,
        status_code: int | None = None,
        tags: list[str] | None = None,
        summary: str | None = None,
        description: str | None = None,
        response_description: str = "Successful Response",
        responses: dict[int | str, dict[str, Any]] | None = None,
        deprecated: bool | None = None,
        operation_id: str | None = None,
        include_in_schema: bool = True,
        response_class: type[Response] | None = None,
        name: str | None = None,
        callbacks: list[BaseRoute] | None = None,
        openapi_extra: dict[str, Any] | None = None,
        generate_unique_id_function: Callable[[Any], str] | None = None,
    ) -> Callable[[Callable[..., Any]], Callable[..., Any]]:
        """Decorator for POST endpoints."""

        def decorator(func: Callable[..., Any]) -> Callable[..., Any]:
            self._add_route(
                path,
                func,
                methods={"POST"},
                response_model=response_model,
                status_code=status_code,
                tags=tags,
                summary=summary,
                description=description,
                response_description=response_description,
                responses=responses,
                deprecated=deprecated,
                operation_id=operation_id,
                include_in_schema=include_in_schema,
                response_class=response_class,
                name=name,
                callbacks=callbacks,
                openapi_extra=openapi_extra,
                generate_unique_id_function=generate_unique_id_function,
            )
            return func

        return decorator

    def put(
        self,
        path: str,
        *,
        response_model: Any = None,
        status_code: int | None = None,
        tags: list[str] | None = None,
        summary: str | None = None,
        description: str | None = None,
        response_description: str = "Successful Response",
        responses: dict[int | str, dict[str, Any]] | None = None,
        deprecated: bool | None = None,
        operation_id: str | None = None,
        include_in_schema: bool = True,
        response_class: type[Response] | None = None,
        name: str | None = None,
        callbacks: list[BaseRoute] | None = None,
        openapi_extra: dict[str, Any] | None = None,
        generate_unique_id_function: Callable[[Any], str] | None = None,
    ) -> Callable[[Callable[..., Any]], Callable[..., Any]]:
        """Decorator for PUT endpoints."""

        def decorator(func: Callable[..., Any]) -> Callable[..., Any]:
            self._add_route(
                path,
                func,
                methods={"PUT"},
                response_model=response_model,
                status_code=status_code,
                tags=tags,
                summary=summary,
                description=description,
                response_description=response_description,
                responses=responses,
                deprecated=deprecated,
                operation_id=operation_id,
                include_in_schema=include_in_schema,
                response_class=response_class,
                name=name,
                callbacks=callbacks,
                openapi_extra=openapi_extra,
                generate_unique_id_function=generate_unique_id_function,
            )
            return func

        return decorator

    def delete(
        self,
        path: str,
        *,
        response_model: Any = None,
        status_code: int | None = None,
        tags: list[str] | None = None,
        summary: str | None = None,
        description: str | None = None,
        response_description: str = "Successful Response",
        responses: dict[int | str, dict[str, Any]] | None = None,
        deprecated: bool | None = None,
        operation_id: str | None = None,
        include_in_schema: bool = True,
        response_class: type[Response] | None = None,
        name: str | None = None,
        callbacks: list[BaseRoute] | None = None,
        openapi_extra: dict[str, Any] | None = None,
        generate_unique_id_function: Callable[[Any], str] | None = None,
    ) -> Callable[[Callable[..., Any]], Callable[..., Any]]:
        """Decorator for DELETE endpoints."""

        def decorator(func: Callable[..., Any]) -> Callable[..., Any]:
            self._add_route(
                path,
                func,
                methods={"DELETE"},
                response_model=response_model,
                status_code=status_code,
                tags=tags,
                summary=summary,
                description=description,
                response_description=response_description,
                responses=responses,
                deprecated=deprecated,
                operation_id=operation_id,
                include_in_schema=include_in_schema,
                response_class=response_class,
                name=name,
                callbacks=callbacks,
                openapi_extra=openapi_extra,
                generate_unique_id_function=generate_unique_id_function,
            )
            return func

        return decorator

    def patch(
        self,
        path: str,
        *,
        response_model: Any = None,
        status_code: int | None = None,
        tags: list[str] | None = None,
        summary: str | None = None,
        description: str | None = None,
        response_description: str = "Successful Response",
        responses: dict[int | str, dict[str, Any]] | None = None,
        deprecated: bool | None = None,
        operation_id: str | None = None,
        include_in_schema: bool = True,
        response_class: type[Response] | None = None,
        name: str | None = None,
        callbacks: list[BaseRoute] | None = None,
        openapi_extra: dict[str, Any] | None = None,
        generate_unique_id_function: Callable[[Any], str] | None = None,
    ) -> Callable[[Callable[..., Any]], Callable[..., Any]]:
        """Decorator for PATCH endpoints."""

        def decorator(func: Callable[..., Any]) -> Callable[..., Any]:
            self._add_route(
                path,
                func,
                methods={"PATCH"},
                response_model=response_model,
                status_code=status_code,
                tags=tags,
                summary=summary,
                description=description,
                response_description=response_description,
                responses=responses,
                deprecated=deprecated,
                operation_id=operation_id,
                include_in_schema=include_in_schema,
                response_class=response_class,
                name=name,
                callbacks=callbacks,
                openapi_extra=openapi_extra,
                generate_unique_id_function=generate_unique_id_function,
            )
            return func

        return decorator

    def build_router(self, services: Services) -> APIRouter:
        """Build an APIRouter with all routes processed for DI.

        Args:
            services: The Services container for dependency resolution

        Returns:
            An APIRouter with all endpoints configured
        """
        router = APIRouter(
            prefix=self.prefix,
            tags=self.tags if self.tags else None,  # type: ignore[arg-type]
            dependencies=self.dependencies if self.dependencies else None,
            responses=self.responses if self.responses else None,
            redirect_slashes=self.redirect_slashes,
            deprecated=self.deprecated,
            include_in_schema=self.include_in_schema,
        )

        for route in self._pending_routes:
            wrapped_endpoint = _wrap_endpoint_with_depends(
                route.endpoint, services
            )

            # Build kwargs, only including non-None values
            route_kwargs: dict[str, Any] = {
                "methods": list(route.methods) if route.methods else None,
            }

            # Only add optional parameters if they have values
            if route.name:
                route_kwargs["name"] = route.name
            if route.response_model is not None:
                route_kwargs["response_model"] = route.response_model
            if route.status_code is not None:
                route_kwargs["status_code"] = route.status_code
            if route.tags:
                route_kwargs["tags"] = route.tags
            if route.summary:
                route_kwargs["summary"] = route.summary
            if route.description:
                route_kwargs["description"] = route.description
            if route.response_description != "Successful Response":
                route_kwargs["response_description"] = route.response_description
            if route.responses:
                route_kwargs["responses"] = route.responses
            if route.deprecated is not None:
                route_kwargs["deprecated"] = route.deprecated
            if route.operation_id:
                route_kwargs["operation_id"] = route.operation_id
            if not route.include_in_schema:
                route_kwargs["include_in_schema"] = route.include_in_schema
            if route.openapi_extra:
                route_kwargs["openapi_extra"] = route.openapi_extra

            router.add_api_route(route.path, wrapped_endpoint, **route_kwargs)

        return router

    @property
    def routes(self) -> list[PendingRoute]:
        """Get all pending routes for validation."""
        return self._pending_routes


def _create_service_dependency(
    service_type: type,
    services: Services,
) -> Callable[[], Any]:
    """Create a FastAPI dependency function for a service type."""

    def dependency() -> Any:
        return services.resolve(service_type)

    return dependency


def _wrap_endpoint_with_depends(
    endpoint: Callable[..., Any],
    services: Services,
) -> Callable[..., Any]:
    """Wrap endpoint to use FastAPI Depends for service injection."""
    from functools import wraps

    sig = inspect.signature(endpoint)

    try:
        hints = get_type_hints(endpoint)
    except Exception:
        return endpoint

    # Identify service parameters
    service_params: dict[str, type] = {}
    for name, hint in hints.items():
        if name == "return":
            continue
        if services.is_registered(hint):
            service_params[name] = hint

    if not service_params:
        return endpoint

    # Build new parameters with Depends
    new_params = []
    for param in sig.parameters.values():
        if param.name in service_params:
            service_type = service_params[param.name]
            dependency = _create_service_dependency(service_type, services)
            new_param = param.replace(
                default=Depends(dependency),
                annotation=Any,
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
