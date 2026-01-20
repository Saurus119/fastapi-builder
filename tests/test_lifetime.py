"""Tests for service lifetime behavior."""


from fastapi_app_builder import Lifetime, Services
from fastapi_app_builder.container import ServiceDescriptor


class TestLifetimeEnum:
    """Tests for the Lifetime enum."""

    def test_lifetime_values_exist(self) -> None:
        assert Lifetime.SINGLETON is not None
        assert Lifetime.SCOPED is not None
        assert Lifetime.TRANSIENT is not None

    def test_lifetimes_are_distinct(self) -> None:
        assert Lifetime.SINGLETON != Lifetime.SCOPED
        assert Lifetime.SCOPED != Lifetime.TRANSIENT
        assert Lifetime.SINGLETON != Lifetime.TRANSIENT


class TestServiceDescriptor:
    """Tests for ServiceDescriptor."""

    def test_descriptor_with_implementation(self) -> None:
        class IFoo:
            pass

        class Foo:
            pass

        descriptor = ServiceDescriptor(
            interface=IFoo,
            implementation=Foo,
            factory=None,
            lifetime=Lifetime.SINGLETON,
        )

        assert descriptor.interface is IFoo
        assert descriptor.implementation is Foo
        assert descriptor.factory is None
        assert descriptor.lifetime is Lifetime.SINGLETON

    def test_descriptor_with_factory(self) -> None:
        class IFoo:
            pass

        def factory() -> IFoo:
            return IFoo()

        descriptor = ServiceDescriptor(
            interface=IFoo,
            implementation=None,
            factory=factory,
            lifetime=Lifetime.TRANSIENT,
        )

        assert descriptor.interface is IFoo
        assert descriptor.implementation is None
        assert descriptor.factory is factory
        assert descriptor.lifetime is Lifetime.TRANSIENT


class TestLifetimeRegistration:
    """Tests for registering services with different lifetimes."""

    def test_add_singleton_sets_correct_lifetime(self) -> None:
        services = Services()

        class IFoo:
            pass

        class Foo:
            pass

        services.add_singleton(IFoo, Foo)
        descriptor = services.get_registration(IFoo)

        assert descriptor is not None
        assert descriptor.lifetime is Lifetime.SINGLETON

    def test_add_scoped_sets_correct_lifetime(self) -> None:
        services = Services()

        class IFoo:
            pass

        class Foo:
            pass

        services.add_scoped(IFoo, Foo)
        descriptor = services.get_registration(IFoo)

        assert descriptor is not None
        assert descriptor.lifetime is Lifetime.SCOPED

    def test_add_transient_sets_correct_lifetime(self) -> None:
        services = Services()

        class IFoo:
            pass

        class Foo:
            pass

        services.add_transient(IFoo, Foo)
        descriptor = services.get_registration(IFoo)

        assert descriptor is not None
        assert descriptor.lifetime is Lifetime.TRANSIENT
