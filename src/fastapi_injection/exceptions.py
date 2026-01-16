from __future__ import annotations


class ServiceNotRegisteredError(Exception):
    """Raised when resolving unregistered service."""

    def __init__(self, service_type_or_message: type | str) -> None:
        if isinstance(service_type_or_message, str):
            self.service_type = None
            super().__init__(service_type_or_message)
        else:
            self.service_type = service_type_or_message
            name = service_type_or_message.__name__
            super().__init__(f"Service '{name}' is not registered")


class CircularDependencyError(Exception):
    """Raised when circular dependency detected."""

    def __init__(self, chain: list[type]) -> None:
        self.chain = chain
        cycle = " -> ".join(t.__name__ for t in chain)
        super().__init__(f"Circular dependency detected: {cycle}")


class ScopeNotFoundError(Exception):
    """Raised when resolving scoped service outside request."""

    def __init__(self) -> None:
        super().__init__(
            "Cannot resolve scoped service outside of a request context. "
            "Ensure RequestScopeMiddleware is installed."
        )


class ValidationError(Exception):
    """Raised when validation fails at build time."""

    def __init__(self, errors: list[str]) -> None:
        self.errors = errors
        message = "Validation failed:\n" + "\n".join(f"  - {e}" for e in errors)
        super().__init__(message)
