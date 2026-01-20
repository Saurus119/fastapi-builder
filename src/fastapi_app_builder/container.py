from __future__ import annotations

from collections.abc import Callable
from contextvars import ContextVar
from dataclasses import dataclass
from typing import TypeVar, get_type_hints

from .exceptions import (
    CircularDependencyError,
    ScopeNotFoundError,
    ServiceNotRegisteredError,
)
from .lifetime import Lifetime

T = TypeVar("T")

# Context variable for request-scoped services
_request_scope: ContextVar[dict[type, object] | None] = ContextVar(
    "request_scope", default=None
)


def get_request_scope() -> ContextVar[dict[type, object] | None]:
    """Get the request scope context variable."""
    return _request_scope


@dataclass
class ServiceDescriptor:
    """Describes a registered service."""

    interface: type
    implementation: type | None
    factory: Callable[[], object] | None
    lifetime: Lifetime
    dispose: Callable[[object], None] | None = None  # Cleanup function


class Services:
    """Dependency injection container."""

    def __init__(self) -> None:
        self._registrations: dict[type, ServiceDescriptor] = {}
        self._singletons: dict[type, object] = {}
        self._resolution_stack: list[type] = []

    # Registration methods
    def add_singleton(
        self,
        interface: type[T],
        implementation: type[T] | None = None,
    ) -> Services:
        """Register a singleton service (one instance per application)."""
        self._registrations[interface] = ServiceDescriptor(
            interface=interface,
            implementation=implementation,
            factory=None,
            lifetime=Lifetime.SINGLETON,
        )
        return self

    def add_scoped(
        self,
        interface: type[T],
        implementation: type[T] | None = None,
    ) -> Services:
        """Register a scoped service (one instance per request)."""
        self._registrations[interface] = ServiceDescriptor(
            interface=interface,
            implementation=implementation,
            factory=None,
            lifetime=Lifetime.SCOPED,
        )
        return self

    def add_transient(
        self,
        interface: type[T],
        implementation: type[T] | None = None,
    ) -> Services:
        """Register a transient service (new instance every time)."""
        self._registrations[interface] = ServiceDescriptor(
            interface=interface,
            implementation=implementation,
            factory=None,
            lifetime=Lifetime.TRANSIENT,
        )
        return self

    def add_singleton_factory(
        self,
        interface: type[T],
        factory: Callable[[], T],
    ) -> Services:
        """Register a singleton service using a factory function."""
        self._registrations[interface] = ServiceDescriptor(
            interface=interface,
            implementation=None,
            factory=factory,
            lifetime=Lifetime.SINGLETON,
        )
        return self

    def add_scoped_factory(
        self,
        interface: type[T],
        factory: Callable[[], T],
        dispose: Callable[[T], None] | None = None,
    ) -> Services:
        """Register a scoped service using a factory function.

        Args:
            interface: The service type/interface
            factory: Function that creates the service instance
            dispose: Optional cleanup function called when request ends

        Example:
            # DB session with automatic cleanup
            builder.services.add_scoped_factory(
                Session,
                factory=SessionLocal,
                dispose=lambda s: s.close()
            )
        """
        self._registrations[interface] = ServiceDescriptor(
            interface=interface,
            implementation=None,
            factory=factory,
            lifetime=Lifetime.SCOPED,
            dispose=dispose,  # type: ignore[arg-type]
        )
        return self

    def add_transient_factory(
        self,
        interface: type[T],
        factory: Callable[[], T],
    ) -> Services:
        """Register a transient service using a factory function."""
        self._registrations[interface] = ServiceDescriptor(
            interface=interface,
            implementation=None,
            factory=factory,
            lifetime=Lifetime.TRANSIENT,
        )
        return self

    def install(self, installer: Callable[[Services], None]) -> Services:
        """Apply an installer function to register services.

        Installers are functions that take a Services container and register
        services. This allows organizing registrations into reusable modules.

        Args:
            installer: Function that registers services

        Returns:
            Self for method chaining

        Example:
            # repositories.py
            def install_repositories(services: Services) -> None:
                services.add_scoped(IUserRepository, UserRepository)
                services.add_scoped(IProductRepository, ProductRepository)

            # services.py
            def install_services(services: Services) -> None:
                services.add_scoped(IUserService, UserService)
                services.add_scoped(IOrderService, OrderService)

            # main.py
            builder = AppBuilder()
            builder.services.install(install_repositories)
            builder.services.install(install_services)
        """
        installer(self)
        return self

    # Resolution
    def is_registered(self, interface: type) -> bool:
        """Check if a service is registered."""
        return interface in self._registrations

    def resolve(self, interface: type[T]) -> T:
        """Resolve a service instance."""
        if not self.is_registered(interface):
            raise ServiceNotRegisteredError(interface)

        descriptor = self._registrations[interface]

        match descriptor.lifetime:
            case Lifetime.SINGLETON:
                return self._resolve_singleton(descriptor)  # type: ignore[return-value]
            case Lifetime.SCOPED:
                return self._resolve_scoped(descriptor)  # type: ignore[return-value]
            case Lifetime.TRANSIENT:
                return self._resolve_transient(descriptor)  # type: ignore[return-value]

        raise ValueError(f"Unknown lifetime: {descriptor.lifetime}")

    def _resolve_singleton(self, descriptor: ServiceDescriptor) -> object:
        """Resolve a singleton service."""
        if descriptor.interface not in self._singletons:
            instance = self._create_instance(descriptor)
            self._singletons[descriptor.interface] = instance
        return self._singletons[descriptor.interface]

    def _resolve_scoped(self, descriptor: ServiceDescriptor) -> object:
        """Resolve a scoped service."""
        scope = _request_scope.get()
        if scope is None:
            raise ScopeNotFoundError()

        if descriptor.interface not in scope:
            instance = self._create_instance(descriptor)
            scope[descriptor.interface] = instance
        return scope[descriptor.interface]

    def _resolve_transient(self, descriptor: ServiceDescriptor) -> object:
        """Resolve a transient service."""
        return self._create_instance(descriptor)

    def _create_instance(self, descriptor: ServiceDescriptor) -> object:
        """Create a new instance of a service."""
        # Check for circular dependencies
        if descriptor.interface in self._resolution_stack:
            cycle = self._resolution_stack + [descriptor.interface]
            raise CircularDependencyError(cycle)

        self._resolution_stack.append(descriptor.interface)
        try:
            if descriptor.factory:
                return descriptor.factory()

            impl = descriptor.implementation or descriptor.interface

            # Get constructor type hints
            try:
                hints = get_type_hints(impl.__init__)  # type: ignore[misc]
            except Exception:
                hints = {}

            # Resolve constructor dependencies
            kwargs: dict[str, object] = {}
            for name, hint in hints.items():
                if name == "return":
                    continue
                if self.is_registered(hint):
                    kwargs[name] = self.resolve(hint)

            return impl(**kwargs)
        finally:
            self._resolution_stack.pop()

    # Validation
    def validate(self) -> list[str]:
        """Validate all registrations and return list of errors."""
        errors: list[str] = []

        for _interface, descriptor in self._registrations.items():
            if descriptor.factory:
                # Can't validate factory dependencies
                continue

            impl = descriptor.implementation or descriptor.interface
            errors.extend(self._validate_dependencies(impl, chain=[]))

        return errors

    def validate_endpoint(self, func: Callable[..., object]) -> list[str]:
        """Validate that all injected dependencies for an endpoint are available."""
        errors: list[str] = []

        try:
            hints = get_type_hints(func)
        except Exception:
            return errors

        for name, hint in hints.items():
            if name == "return":
                continue
            if self._is_injectable_type(hint) and not self.is_registered(hint):
                errors.append(
                    f"Endpoint '{func.__name__}' requires "
                    f"'{hint.__name__}' which is not registered"
                )

        return errors

    def _validate_dependencies(
        self,
        impl: type,
        chain: list[type],
    ) -> list[str]:
        """Validate dependencies recursively."""
        errors: list[str] = []

        if impl in chain:
            cycle = " -> ".join(t.__name__ for t in chain + [impl])
            return [f"Circular dependency: {cycle}"]

        try:
            hints = get_type_hints(impl.__init__)  # type: ignore[misc]
        except Exception:
            return errors

        for name, hint in hints.items():
            if name == "return":
                continue
            if self._is_injectable_type(hint):
                if not self.is_registered(hint):
                    errors.append(
                        f"Service '{impl.__name__}' requires "
                        f"'{hint.__name__}' which is not registered"
                    )
                else:
                    descriptor = self._registrations[hint]
                    if descriptor.factory:
                        # Can't validate factory dependencies further
                        continue
                    dep_impl = descriptor.implementation or hint
                    errors.extend(
                        self._validate_dependencies(dep_impl, chain + [impl])
                    )

        return errors

    def _is_injectable_type(self, hint: type) -> bool:
        """Check if a type hint represents an injectable service."""
        # Skip primitives and common types
        skip = {str, int, float, bool, list, dict, set, tuple, type(None)}
        if hint in skip:
            return False

        # Skip generic types
        origin = getattr(hint, "__origin__", None)
        if origin is not None:
            return False

        # Skip Pydantic models (have model_fields attribute)
        if hasattr(hint, "model_fields"):
            return False

        # Check if it's a class (not a primitive or generic)
        if not isinstance(hint, type):
            return False

        return True

    # Scope management
    def dispose_scope(self) -> None:
        """Dispose all scoped services in the current request.

        This calls the dispose function for any scoped services that have one.
        Should be called at the end of each request.
        """
        scope = _request_scope.get()
        if scope is None:
            return

        for interface, instance in scope.items():
            descriptor = self._registrations.get(interface)
            if descriptor and descriptor.dispose:
                try:
                    descriptor.dispose(instance)
                except Exception:
                    # Log but don't fail - cleanup should be best-effort
                    pass

    # Testing helpers
    def clear(self) -> None:
        """Clear all registrations and cached instances."""
        self._registrations.clear()
        self._singletons.clear()
        self._resolution_stack.clear()

    def get_registration(self, interface: type) -> ServiceDescriptor | None:
        """Get the registration for a service (for testing/introspection)."""
        return self._registrations.get(interface)
