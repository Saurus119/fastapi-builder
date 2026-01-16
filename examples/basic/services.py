"""Example services for basic demo."""

from typing import Protocol


class IGreetingService(Protocol):
    """Protocol for greeting service."""

    def greet(self, name: str) -> str:
        """Generate a greeting for the given name."""
        ...


class GreetingService:
    """Simple greeting service implementation."""

    def greet(self, name: str) -> str:
        return f"Hello, {name}!"


class ICounterService(Protocol):
    """Protocol for counter service."""

    def increment(self) -> int:
        """Increment counter and return new value."""
        ...

    def get_value(self) -> int:
        """Get current counter value."""
        ...


class CounterService:
    """Counter service that tracks a count."""

    def __init__(self) -> None:
        self._count = 0

    def increment(self) -> int:
        self._count += 1
        return self._count

    def get_value(self) -> int:
        return self._count
