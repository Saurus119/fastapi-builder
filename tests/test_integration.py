"""Integration tests for fastapi-builder."""

from fastapi import APIRouter, FastAPI
from fastapi.testclient import TestClient

from fastapi_builder import AppBuilder, InjectableRouter

from .conftest import (
    CounterService,
    GreetingService,
    IGreetingService,
    IUserRepository,
    IUserService,
    UserRepository,
    UserService,
)


class TestBasicIntegration:
    """Basic integration tests."""

    def test_simple_endpoint_with_injection(self) -> None:
        builder = AppBuilder()
        builder.services.add_singleton(IGreetingService, GreetingService)

        router = InjectableRouter(prefix="/api")

        @router.get("/greet/{name}")
        async def greet(name: str, greeting_service: IGreetingService) -> dict:
            return {"message": greeting_service.greet(name)}

        builder.add_controller(router)
        app = builder.build()

        client = TestClient(app)
        response = client.get("/api/greet/World")

        assert response.status_code == 200
        assert response.json() == {"message": "Hello, World!"}

    def test_endpoint_without_injection(self) -> None:
        builder = AppBuilder()

        router = InjectableRouter()

        @router.get("/hello")
        async def hello() -> dict:
            return {"message": "Hello!"}

        builder.add_controller(router)
        app = builder.build()

        client = TestClient(app)
        response = client.get("/hello")

        assert response.status_code == 200
        assert response.json() == {"message": "Hello!"}

    def test_nested_dependencies(self) -> None:
        builder = AppBuilder()
        builder.services.add_scoped(IUserRepository, UserRepository)
        builder.services.add_scoped(IUserService, UserService)

        router = InjectableRouter(prefix="/users")

        @router.get("/{user_id}")
        async def get_user(user_id: int, user_service: IUserService) -> dict:
            return user_service.get_user(user_id)

        builder.add_controller(router)
        app = builder.build()

        client = TestClient(app)
        response = client.get("/users/42")

        assert response.status_code == 200
        assert response.json() == {"id": 42, "name": "User 42"}


class TestScopedLifetime:
    """Tests for scoped service lifetime."""

    def test_scoped_service_same_within_request(self) -> None:
        CounterService.reset_count()
        builder = AppBuilder()
        builder.services.add_scoped(CounterService)

        router = InjectableRouter()

        @router.get("/check")
        async def check(
            counter1: CounterService, counter2: CounterService
        ) -> dict:
            return {
                "same_instance": counter1 is counter2,
                "id1": counter1.instance_id,
                "id2": counter2.instance_id,
            }

        builder.add_controller(router)
        app = builder.build()

        client = TestClient(app)
        response = client.get("/check")

        assert response.status_code == 200
        data = response.json()
        # Note: They'll have same ID because the wrapper resolves same service twice
        # but within the request they get the same instance
        assert data["id1"] == data["id2"]

    def test_scoped_service_different_across_requests(self) -> None:
        CounterService.reset_count()
        builder = AppBuilder()
        builder.services.add_scoped(CounterService)

        router = InjectableRouter()

        @router.get("/id")
        async def get_id(counter: CounterService) -> dict:
            return {"instance_id": counter.instance_id}

        builder.add_controller(router)
        app = builder.build()

        client = TestClient(app)
        response1 = client.get("/id")
        response2 = client.get("/id")

        id1 = response1.json()["instance_id"]
        id2 = response2.json()["instance_id"]

        assert id1 != id2


class TestSingletonLifetime:
    """Tests for singleton service lifetime."""

    def test_singleton_same_across_requests(self) -> None:
        CounterService.reset_count()
        builder = AppBuilder()
        builder.services.add_singleton(CounterService)

        router = InjectableRouter()

        @router.get("/id")
        async def get_id(counter: CounterService) -> dict:
            return {"instance_id": counter.instance_id}

        builder.add_controller(router)
        app = builder.build()

        client = TestClient(app)
        response1 = client.get("/id")
        response2 = client.get("/id")

        id1 = response1.json()["instance_id"]
        id2 = response2.json()["instance_id"]

        assert id1 == id2


class TestTransientLifetime:
    """Tests for transient service lifetime."""

    def test_transient_different_each_resolution(self) -> None:
        CounterService.reset_count()
        builder = AppBuilder()
        builder.services.add_transient(CounterService)

        router = InjectableRouter()

        @router.get("/id")
        async def get_id(counter: CounterService) -> dict:
            return {"instance_id": counter.instance_id}

        builder.add_controller(router)
        app = builder.build()

        client = TestClient(app)
        response1 = client.get("/id")
        response2 = client.get("/id")

        id1 = response1.json()["instance_id"]
        id2 = response2.json()["instance_id"]

        assert id1 != id2


class TestBuilderConfiguration:
    """Tests for AppBuilder configuration."""

    def test_with_title(self) -> None:
        builder = AppBuilder()
        builder.with_title("My API")
        app = builder.build()

        assert app.title == "My API"

    def test_with_version(self) -> None:
        builder = AppBuilder()
        builder.with_version("2.0.0")
        app = builder.build()

        assert app.version == "2.0.0"

    def test_with_description(self) -> None:
        builder = AppBuilder()
        builder.with_description("My API description")
        app = builder.build()

        assert app.description == "My API description"

    def test_with_docs_url(self) -> None:
        builder = AppBuilder()
        builder.with_docs_url("/swagger")
        app = builder.build()

        assert app.docs_url == "/swagger"

    def test_disable_docs(self) -> None:
        builder = AppBuilder()
        builder.with_docs_url(None)
        app = builder.build()

        assert app.docs_url is None

    def test_method_chaining(self) -> None:
        builder = AppBuilder()
        result = (
            builder.with_title("My API")
            .with_version("1.0.0")
            .with_description("Description")
            .with_docs_url("/docs")
        )

        assert result is builder


class TestInstallerPattern:
    """Tests for the installer pattern."""

    def test_install_custom_installer(self) -> None:
        def my_installer(builder: AppBuilder) -> None:
            builder.services.add_singleton(IGreetingService, GreetingService)

        builder = AppBuilder()
        builder.install(my_installer)

        assert builder.services.is_registered(IGreetingService)

    def test_install_multiple_installers(self) -> None:
        def install_repos(builder: AppBuilder) -> None:
            builder.services.add_scoped(IUserRepository, UserRepository)

        def install_services(builder: AppBuilder) -> None:
            builder.services.add_scoped(IUserService, UserService)

        builder = AppBuilder()
        builder.install(install_repos).install(install_services)

        assert builder.services.is_registered(IUserRepository)
        assert builder.services.is_registered(IUserService)

    def test_install_cors(self) -> None:
        builder = AppBuilder()
        builder.install_cors(["http://localhost:3000"])
        app = builder.build()

        # Check that CORS middleware was added
        assert app is not None
        assert len(app.user_middleware) > 0


class TestMultipleControllers:
    """Tests for multiple controllers."""

    def test_multiple_controllers(self) -> None:
        builder = AppBuilder()
        builder.services.add_singleton(IGreetingService, GreetingService)
        builder.services.add_scoped(IUserRepository, UserRepository)
        builder.services.add_scoped(IUserService, UserService)

        greeting_router = InjectableRouter(prefix="/greetings")

        @greeting_router.get("/{name}")
        async def greet(name: str, service: IGreetingService) -> dict:
            return {"message": service.greet(name)}

        user_router = InjectableRouter(prefix="/users")

        @user_router.get("/{user_id}")
        async def get_user(user_id: int, service: IUserService) -> dict:
            return service.get_user(user_id)

        builder.add_controller(greeting_router)
        builder.add_controller(user_router)

        app = builder.build()
        client = TestClient(app)

        greeting_response = client.get("/greetings/World")
        assert greeting_response.status_code == 200
        assert greeting_response.json() == {"message": "Hello, World!"}

        user_response = client.get("/users/1")
        assert user_response.status_code == 200
        assert user_response.json() == {"id": 1, "name": "User 1"}


class TestExtendExistingApp:
    """Tests for extending an existing FastAPI app."""

    def test_extend_existing_app(self) -> None:
        """Test that extend() adds DI to an existing FastAPI app."""
        # Create existing app with custom settings
        existing_app = FastAPI(
            title="My Custom API",
            version="2.0.0",
            description="Custom description",
        )

        # Add a route directly to the existing app
        @existing_app.get("/existing")
        async def existing_route():
            return {"source": "existing"}

        # Use builder to add DI
        builder = AppBuilder()
        builder.services.add_singleton(IGreetingService, GreetingService)

        router = APIRouter()

        @router.get("/injected")
        async def injected_route(service: IGreetingService):
            return {"message": service.greet("World")}

        builder.add_controller(router)
        app = builder.extend(existing_app)

        # Verify it's the same app instance
        assert app is existing_app
        assert app.title == "My Custom API"

        client = TestClient(app)

        # Existing route works
        response = client.get("/existing")
        assert response.status_code == 200
        assert response.json() == {"source": "existing"}

        # Injected route works
        response = client.get("/injected")
        assert response.status_code == 200
        assert response.json() == {"message": "Hello, World!"}

    def test_extend_preserves_lifespan(self) -> None:
        """Test that existing app's lifespan is preserved."""
        from contextlib import asynccontextmanager

        startup_called = []
        shutdown_called = []

        @asynccontextmanager
        async def lifespan(app):
            startup_called.append(True)
            yield
            shutdown_called.append(True)

        existing_app = FastAPI(lifespan=lifespan)

        builder = AppBuilder()
        builder.services.add_singleton(IGreetingService, GreetingService)
        builder.extend(existing_app)

        # TestClient triggers lifespan
        with TestClient(existing_app):
            assert len(startup_called) == 1

        assert len(shutdown_called) == 1


class TestSyncEndpoints:
    """Tests for synchronous endpoints."""

    def test_sync_endpoint_with_injection(self) -> None:
        builder = AppBuilder()
        builder.services.add_singleton(IGreetingService, GreetingService)

        router = InjectableRouter()

        @router.get("/sync/{name}")
        def sync_greet(name: str, service: IGreetingService) -> dict:
            return {"message": service.greet(name)}

        builder.add_controller(router)
        app = builder.build()

        client = TestClient(app)
        response = client.get("/sync/World")

        assert response.status_code == 200
        assert response.json() == {"message": "Hello, World!"}
