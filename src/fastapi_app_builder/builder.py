from __future__ import annotations

from collections.abc import Callable
from typing import TYPE_CHECKING

from fastapi import APIRouter, FastAPI

from .container import Services
from .exceptions import ValidationError
from .middleware import RequestScopeMiddleware
from .patch import set_global_services

if TYPE_CHECKING:
    from .router import InjectableRouter


class AppBuilder:
    """Main entry point for configuring FastAPI application.

    Provides a builder pattern for configuring dependency injection,
    adding controllers, and building a FastAPI application.

    IMPORTANT: Register all services BEFORE importing/creating routers
    that depend on those services. This allows the automatic DI to work.

    Example:
        from fastapi_app_builder import AppBuilder

        # 1. Create builder and register services FIRST
        builder = AppBuilder()
        builder.services.add_scoped(IUserService, UserService)

        # 2. Import controllers AFTER services are registered
        from controllers import user_router

        # 3. Add controllers and build
        builder.add_controller(user_router)
        app = builder.build()

    With this pattern, you can use standard FastAPI APIRouter:

        # controllers.py
        from fastapi import APIRouter

        router = APIRouter(prefix="/users")

        @router.get("/{user_id}")
        async def get_user(user_id: int, user_service: IUserService):
            return user_service.get_user(user_id)
    """

    def __init__(self) -> None:
        self._services = Services()
        self._controllers: list[APIRouter | InjectableRouter] = []
        self._installers: list[Callable[[AppBuilder], None]] = []
        self._validation_enabled = True

        # FastAPI configuration
        self._title = "FastAPI"
        self._version = "0.1.0"
        self._description = ""
        self._docs_url: str | None = "/docs"
        self._redoc_url: str | None = "/redoc"
        self._openapi_url: str | None = "/openapi.json"

        # CORS configuration
        self._cors_config: dict[str, object] | None = None

        # Set this as the global services container for automatic DI
        set_global_services(self._services)

    @property
    def services(self) -> Services:
        """Access the dependency injection container."""
        return self._services

    # Controller registration
    def add_controller(
        self, router: APIRouter | InjectableRouter
    ) -> AppBuilder:
        """Add a controller (router) to the application.

        Supports both standard FastAPI APIRouter and InjectableRouter.

        Args:
            router: FastAPI APIRouter or InjectableRouter instance

        Returns:
            Self for method chaining
        """
        self._controllers.append(router)
        return self

    # Installer pattern
    def install(
        self,
        installer: Callable[[AppBuilder], None],
    ) -> AppBuilder:
        """Apply an installer function to configure the builder.

        Installers are functions that take an AppBuilder and configure it.
        This allows for modular configuration of services.

        Args:
            installer: Function that configures the builder

        Returns:
            Self for method chaining

        Example:
            def install_repositories(builder: AppBuilder) -> None:
                builder.services.add_scoped(IUserRepository, UserRepository)

            builder.install(install_repositories)
        """
        installer(self)
        return self

    # Configuration methods
    def with_validation(self, enabled: bool) -> AppBuilder:
        """Enable or disable startup validation.

        When enabled, all service registrations are validated at build time.

        Args:
            enabled: Whether to validate at startup

        Returns:
            Self for method chaining
        """
        self._validation_enabled = enabled
        return self

    def with_title(self, title: str) -> AppBuilder:
        """Set the application title.

        Args:
            title: Application title for OpenAPI docs

        Returns:
            Self for method chaining
        """
        self._title = title
        return self

    def with_version(self, version: str) -> AppBuilder:
        """Set the application version.

        Args:
            version: Application version for OpenAPI docs

        Returns:
            Self for method chaining
        """
        self._version = version
        return self

    def with_description(self, description: str) -> AppBuilder:
        """Set the application description.

        Args:
            description: Application description for OpenAPI docs

        Returns:
            Self for method chaining
        """
        self._description = description
        return self

    def with_docs_url(self, url: str | None) -> AppBuilder:
        """Set the Swagger UI docs URL.

        Args:
            url: URL path for Swagger docs, or None to disable

        Returns:
            Self for method chaining
        """
        self._docs_url = url
        return self

    def with_redoc_url(self, url: str | None) -> AppBuilder:
        """Set the ReDoc URL.

        Args:
            url: URL path for ReDoc, or None to disable

        Returns:
            Self for method chaining
        """
        self._redoc_url = url
        return self

    def with_openapi_url(self, url: str | None) -> AppBuilder:
        """Set the OpenAPI schema URL.

        Args:
            url: URL path for OpenAPI schema, or None to disable

        Returns:
            Self for method chaining
        """
        self._openapi_url = url
        return self

    # Built-in installers
    def install_cors(
        self,
        origins: list[str],
        allow_credentials: bool = True,
        allow_methods: list[str] | None = None,
        allow_headers: list[str] | None = None,
    ) -> AppBuilder:
        """Configure CORS middleware.

        Args:
            origins: List of allowed origins
            allow_credentials: Whether to allow credentials
            allow_methods: List of allowed HTTP methods (default: all)
            allow_headers: List of allowed headers (default: all)

        Returns:
            Self for method chaining
        """
        self._cors_config = {
            "allow_origins": origins,
            "allow_credentials": allow_credentials,
            "allow_methods": allow_methods or ["*"],
            "allow_headers": allow_headers or ["*"],
        }
        return self

    # Build
    def build(self) -> FastAPI:
        """Build and return a new FastAPI application.

        This method:
        1. Validates all service registrations (if enabled)
        2. Creates the FastAPI application with configured settings
        3. Adds middleware for request-scoped services
        4. Includes all controllers

        Returns:
            Configured FastAPI application

        Raises:
            ValidationError: If validation is enabled and fails
        """
        # Validate registrations
        if self._validation_enabled:
            errors = self._validate()
            if errors:
                raise ValidationError(errors)

        # Create FastAPI app
        app = FastAPI(
            title=self._title,
            version=self._version,
            description=self._description,
            docs_url=self._docs_url,
            redoc_url=self._redoc_url,
            openapi_url=self._openapi_url,
        )

        # Add CORS middleware if configured
        if self._cors_config:
            from starlette.middleware.cors import CORSMiddleware

            app.add_middleware(CORSMiddleware, **self._cors_config)  # type: ignore[arg-type]

        # Apply DI to the app
        self._apply_di(app)

        return app

    def extend(self, app: FastAPI) -> FastAPI:
        """Extend an existing FastAPI application with dependency injection.

        Use this when you have an existing FastAPI app and want to add
        DI support without replacing it. The app's existing configuration
        (title, version, lifespan, routes, etc.) is preserved.

        Args:
            app: Existing FastAPI instance to extend

        Returns:
            The same FastAPI instance with DI middleware and controllers added

        Raises:
            ValidationError: If validation is enabled and fails

        Example:
            # Create your own FastAPI instance
            app = FastAPI(title="My API", lifespan=my_lifespan)

            @app.get("/health")
            async def health():
                return {"status": "ok"}

            # Use builder for DI only
            builder = AppBuilder()
            builder.services.add_scoped(IUserService, UserService)
            builder.add_controller(user_router)
            builder.extend(app)  # Adds DI to existing app
        """
        # Validate registrations
        if self._validation_enabled:
            errors = self._validate()
            if errors:
                raise ValidationError(errors)

        # Apply DI to the app
        self._apply_di(app)

        return app

    def _apply_di(self, app: FastAPI) -> None:
        """Apply dependency injection middleware and controllers to an app."""
        # Import here to avoid circular imports
        from .router import InjectableRouter

        # Add request scope middleware
        app.add_middleware(RequestScopeMiddleware, services=self._services)

        # Include controllers
        for controller in self._controllers:
            if isinstance(controller, InjectableRouter):
                # InjectableRouter - build with DI support
                router = controller.build_router(self._services)
                app.include_router(router)
            else:
                # Standard APIRouter - the patch handles DI automatically
                app.include_router(controller)

    def _validate(self) -> list[str]:
        """Validate all registrations and endpoints."""
        from .router import InjectableRouter

        errors: list[str] = []

        # Validate service dependencies
        errors.extend(self._services.validate())

        # Validate endpoint dependencies
        for controller in self._controllers:
            if isinstance(controller, InjectableRouter):
                # Validate InjectableRouter endpoints
                for pending_route in controller.routes:
                    errors.extend(
                        self._services.validate_endpoint(pending_route.endpoint)
                    )
            else:
                # Validate standard APIRouter endpoints
                for base_route in controller.routes:
                    if hasattr(base_route, "endpoint"):
                        errors.extend(
                            self._services.validate_endpoint(base_route.endpoint)
                        )

        return errors
