from enum import Enum, auto


class Lifetime(Enum):
    """Service lifetime options for dependency injection."""

    SINGLETON = auto()  # One instance per application
    SCOPED = auto()  # One instance per request
    TRANSIENT = auto()  # New instance every time
