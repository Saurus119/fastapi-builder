from __future__ import annotations

from collections.abc import Callable
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from ..builder import AppBuilder


def install_cors(
    origins: list[str],
    allow_credentials: bool = True,
    allow_methods: list[str] | None = None,
    allow_headers: list[str] | None = None,
) -> Callable[[AppBuilder], None]:
    """Create a CORS installer.

    Args:
        origins: List of allowed origins
        allow_credentials: Whether to allow credentials
        allow_methods: List of allowed HTTP methods
        allow_headers: List of allowed headers

    Returns:
        Installer function for CORS

    Example:
        builder.install(install_cors(["http://localhost:3000"]))
    """

    def installer(builder: AppBuilder) -> None:
        builder.install_cors(
            origins=origins,
            allow_credentials=allow_credentials,
            allow_methods=allow_methods,
            allow_headers=allow_headers,
        )

    return installer
