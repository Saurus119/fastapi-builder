"""Tests for validation logic."""

import pytest

from fastapi_injection import AppBuilder, InjectableRouter, Services, ValidationError

from .conftest import (
    GreetingService,
    IGreetingService,
    IUserRepository,
    IUserService,
    ServiceA,
    ServiceB,
    UserRepository,
    UserService,
)


class TestServiceValidation:
    """Tests for service dependency validation."""

    def test_validate_returns_empty_for_valid_registrations(
        self, services: Services
    ) -> None:
        services.add_singleton(IUserRepository, UserRepository)
        services.add_singleton(IUserService, UserService)

        errors = services.validate()

        assert errors == []

    def test_validate_detects_missing_dependency(
        self, services: Services
    ) -> None:
        # UserService depends on IUserRepository which is not registered
        services.add_singleton(IUserService, UserService)

        errors = services.validate()

        assert len(errors) == 1
        assert "IUserRepository" in errors[0]
        assert "not registered" in errors[0]

    def test_validate_detects_circular_dependency(
        self, services: Services
    ) -> None:
        services.add_singleton(ServiceA)
        services.add_singleton(ServiceB)

        errors = services.validate()

        assert len(errors) >= 1
        assert any("Circular" in error for error in errors)


class TestEndpointValidation:
    """Tests for endpoint dependency validation."""

    def test_validate_endpoint_with_valid_dependencies(
        self, services: Services
    ) -> None:
        services.add_singleton(IGreetingService, GreetingService)

        async def endpoint(greeting_service: IGreetingService) -> dict:
            return {}

        errors = services.validate_endpoint(endpoint)

        assert errors == []

    def test_validate_endpoint_with_missing_dependency(
        self, services: Services
    ) -> None:
        async def endpoint(greeting_service: IGreetingService) -> dict:
            return {}

        errors = services.validate_endpoint(endpoint)

        assert len(errors) == 1
        assert "IGreetingService" in errors[0]

    def test_validate_endpoint_ignores_non_service_params(
        self, services: Services
    ) -> None:
        async def endpoint(user_id: int, name: str) -> dict:
            return {}

        errors = services.validate_endpoint(endpoint)

        assert errors == []


class TestBuildValidation:
    """Tests for validation during build."""

    def test_build_raises_on_missing_dependency(
        self, builder: AppBuilder
    ) -> None:
        # UserService depends on IUserRepository which is not registered
        builder.services.add_scoped(IUserService, UserService)

        router = InjectableRouter()

        @router.get("/")
        async def endpoint(user_service: IUserService) -> dict:
            return {}

        builder.add_controller(router)

        with pytest.raises(ValidationError) as exc:
            builder.build()

        assert "IUserRepository" in str(exc.value)

    def test_build_raises_on_endpoint_missing_dependency(
        self, builder: AppBuilder
    ) -> None:
        router = InjectableRouter()

        @router.get("/")
        async def endpoint(greeting_service: IGreetingService) -> dict:
            return {}

        builder.add_controller(router)

        with pytest.raises(ValidationError) as exc:
            builder.build()

        assert "IGreetingService" in str(exc.value)

    def test_build_succeeds_with_valid_dependencies(
        self, builder: AppBuilder
    ) -> None:
        builder.services.add_scoped(IUserRepository, UserRepository)
        builder.services.add_scoped(IUserService, UserService)

        router = InjectableRouter()

        @router.get("/")
        async def endpoint(user_service: IUserService) -> dict:
            return {}

        builder.add_controller(router)

        app = builder.build()

        assert app is not None

    def test_build_with_validation_disabled_skips_validation(
        self, builder: AppBuilder
    ) -> None:
        # Missing dependency
        builder.services.add_scoped(IUserService, UserService)

        router = InjectableRouter()

        @router.get("/")
        async def endpoint(user_service: IUserService) -> dict:
            return {}

        builder.add_controller(router)
        builder.with_validation(False)

        # Should not raise
        app = builder.build()

        assert app is not None
