from __future__ import annotations

from collections.abc import Callable
from typing import TYPE_CHECKING, Any, Protocol

if TYPE_CHECKING:
    from ..builder import AppBuilder


class IDbSession(Protocol):
    """Protocol for database session interface."""

    def commit(self) -> None:
        """Commit the current transaction."""
        ...

    def rollback(self) -> None:
        """Rollback the current transaction."""
        ...

    def close(self) -> None:
        """Close the session."""
        ...


def install_database(connection_string: str) -> Callable[[AppBuilder], None]:
    """Create a database installer using SQLAlchemy.

    This installer configures SQLAlchemy with the provided connection string
    and registers a scoped session factory.

    Args:
        connection_string: Database connection URL

    Returns:
        Installer function for database setup

    Example:
        builder.install(install_database("postgresql://localhost/mydb"))

    Note:
        Requires sqlalchemy to be installed:
        `pip install fastapi-injection[sqlalchemy]`
    """

    def installer(builder: AppBuilder) -> None:
        try:
            from sqlalchemy import create_engine  # type: ignore[import-not-found]
            from sqlalchemy.orm import (  # type: ignore[import-not-found]
                Session,
                sessionmaker,
            )
        except ImportError as e:
            raise ImportError(
                "SQLAlchemy is required for database support. "
                "Install with: pip install fastapi-injection[sqlalchemy]"
            ) from e

        # Create engine and session factory
        engine = create_engine(connection_string)
        session_factory = sessionmaker(bind=engine, expire_on_commit=False)

        def create_session() -> Session:
            return session_factory()

        # Register session as scoped (one per request)
        builder.services.add_scoped_factory(Session, create_session)

    return installer


def install_database_with_engine(engine: Any) -> Callable[[AppBuilder], None]:
    """Create a database installer using an existing SQLAlchemy engine.

    Args:
        engine: SQLAlchemy Engine instance

    Returns:
        Installer function for database setup

    Example:
        engine = create_engine("postgresql://localhost/mydb")
        builder.install(install_database_with_engine(engine))
    """

    def installer(builder: AppBuilder) -> None:
        try:
            from sqlalchemy.orm import Session, sessionmaker
        except ImportError as e:
            raise ImportError(
                "SQLAlchemy is required for database support. "
                "Install with: pip install fastapi-injection[sqlalchemy]"
            ) from e

        session_factory = sessionmaker(bind=engine, expire_on_commit=False)

        def create_session() -> Session:
            return session_factory()

        builder.services.add_scoped_factory(Session, create_session)

    return installer
