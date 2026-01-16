"""Tests for the Services container."""

import pytest

from fastapi_injection import ServiceNotRegisteredError, Services
from fastapi_injection.container import get_request_scope

from .conftest import (
    CounterService,
    GreetingService,
    IGreetingService,
    IUserRepository,
    IUserService,
    UserRepository,
    UserService,
)


class TestRegistration:
    """Tests for service registration."""

    def test_add_singleton_registers_service(self, services: Services) -> None:
        services.add_singleton(IGreetingService, GreetingService)
        assert services.is_registered(IGreetingService)

    def test_add_scoped_registers_service(self, services: Services) -> None:
        services.add_scoped(IGreetingService, GreetingService)
        assert services.is_registered(IGreetingService)

    def test_add_transient_registers_service(self, services: Services) -> None:
        services.add_transient(IGreetingService, GreetingService)
        assert services.is_registered(IGreetingService)

    def test_is_registered_returns_false_for_unregistered(
        self, services: Services
    ) -> None:
        assert not services.is_registered(IGreetingService)

    def test_registration_with_same_interface_implementation(
        self, services: Services
    ) -> None:
        services.add_singleton(GreetingService)
        assert services.is_registered(GreetingService)

    def test_method_chaining(self, services: Services) -> None:
        result = (
            services.add_singleton(IGreetingService, GreetingService)
            .add_scoped(IUserRepository, UserRepository)
            .add_transient(IUserService, UserService)
        )
        assert result is services
        assert services.is_registered(IGreetingService)
        assert services.is_registered(IUserRepository)
        assert services.is_registered(IUserService)


class TestSingletonResolution:
    """Tests for singleton lifetime resolution."""

    def test_singleton_returns_same_instance(self, services: Services) -> None:
        services.add_singleton(IGreetingService, GreetingService)

        instance1 = services.resolve(IGreetingService)
        instance2 = services.resolve(IGreetingService)

        assert instance1 is instance2

    def test_singleton_persists_across_resolutions(
        self, services: Services
    ) -> None:
        CounterService.reset_count()
        services.add_singleton(CounterService)

        instance1 = services.resolve(CounterService)
        instance2 = services.resolve(CounterService)

        assert instance1.instance_id == instance2.instance_id
        assert CounterService._instance_count == 1


class TestTransientResolution:
    """Tests for transient lifetime resolution."""

    def test_transient_returns_different_instances(
        self, services: Services
    ) -> None:
        CounterService.reset_count()
        services.add_transient(CounterService)

        instance1 = services.resolve(CounterService)
        instance2 = services.resolve(CounterService)

        assert instance1 is not instance2
        assert instance1.instance_id != instance2.instance_id
        assert CounterService._instance_count == 2


class TestScopedResolution:
    """Tests for scoped lifetime resolution."""

    def test_scoped_returns_same_instance_within_scope(
        self, services: Services
    ) -> None:
        CounterService.reset_count()
        services.add_scoped(CounterService)

        # Set up a request scope
        scope_var = get_request_scope()
        token = scope_var.set({})

        try:
            instance1 = services.resolve(CounterService)
            instance2 = services.resolve(CounterService)

            assert instance1 is instance2
            assert CounterService._instance_count == 1
        finally:
            scope_var.reset(token)

    def test_scoped_returns_different_instances_across_scopes(
        self, services: Services
    ) -> None:
        CounterService.reset_count()
        services.add_scoped(CounterService)

        scope_var = get_request_scope()

        # First scope
        token1 = scope_var.set({})
        instance1 = services.resolve(CounterService)
        scope_var.reset(token1)

        # Second scope
        token2 = scope_var.set({})
        instance2 = services.resolve(CounterService)
        scope_var.reset(token2)

        assert instance1 is not instance2
        assert CounterService._instance_count == 2


class TestDependencyResolution:
    """Tests for resolving services with dependencies."""

    def test_resolves_nested_dependencies(self, services: Services) -> None:
        services.add_singleton(IUserRepository, UserRepository)
        services.add_singleton(IUserService, UserService)

        user_service = services.resolve(IUserService)

        assert isinstance(user_service, UserService)
        assert isinstance(user_service.user_repository, UserRepository)

    def test_resolve_unregistered_raises(self, services: Services) -> None:
        with pytest.raises(ServiceNotRegisteredError) as exc:
            services.resolve(IGreetingService)

        assert "IGreetingService" in str(exc.value)


class TestFactoryRegistration:
    """Tests for factory-based registration."""

    def test_singleton_factory(self, services: Services) -> None:
        call_count = 0

        def factory() -> GreetingService:
            nonlocal call_count
            call_count += 1
            return GreetingService()

        services.add_singleton_factory(IGreetingService, factory)

        instance1 = services.resolve(IGreetingService)
        instance2 = services.resolve(IGreetingService)

        assert instance1 is instance2
        assert call_count == 1

    def test_transient_factory(self, services: Services) -> None:
        call_count = 0

        def factory() -> GreetingService:
            nonlocal call_count
            call_count += 1
            return GreetingService()

        services.add_transient_factory(IGreetingService, factory)

        instance1 = services.resolve(IGreetingService)
        instance2 = services.resolve(IGreetingService)

        assert instance1 is not instance2
        assert call_count == 2


class TestClear:
    """Tests for clearing the container."""

    def test_clear_removes_registrations(self, services: Services) -> None:
        services.add_singleton(IGreetingService, GreetingService)
        assert services.is_registered(IGreetingService)

        services.clear()

        assert not services.is_registered(IGreetingService)

    def test_clear_removes_singleton_instances(self, services: Services) -> None:
        CounterService.reset_count()
        services.add_singleton(CounterService)

        instance1 = services.resolve(CounterService)

        services.clear()
        services.add_singleton(CounterService)

        instance2 = services.resolve(CounterService)

        assert instance1 is not instance2


class TestInstaller:
    """Tests for the installer pattern."""

    def test_install_applies_installer_function(self, services: Services) -> None:
        def install_repositories(svc: Services) -> None:
            svc.add_scoped(IUserRepository, UserRepository)

        services.install(install_repositories)

        assert services.is_registered(IUserRepository)

    def test_install_returns_self_for_chaining(self, services: Services) -> None:
        def installer(svc: Services) -> None:
            svc.add_singleton(IGreetingService, GreetingService)

        result = services.install(installer)

        assert result is services

    def test_install_multiple_installers(self, services: Services) -> None:
        def install_repositories(svc: Services) -> None:
            svc.add_scoped(IUserRepository, UserRepository)

        def install_services(svc: Services) -> None:
            svc.add_scoped(IUserService, UserService)

        services.install(install_repositories).install(install_services)

        assert services.is_registered(IUserRepository)
        assert services.is_registered(IUserService)

    def test_install_with_method_chaining(self, services: Services) -> None:
        def install_all(svc: Services) -> None:
            svc.add_singleton(IGreetingService, GreetingService)
            svc.add_scoped(IUserRepository, UserRepository)
            svc.add_scoped(IUserService, UserService)

        services.install(install_all)

        assert services.is_registered(IGreetingService)
        assert services.is_registered(IUserRepository)
        assert services.is_registered(IUserService)
