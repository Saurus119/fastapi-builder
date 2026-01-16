"""Tests for RequestScopeMiddleware."""

import pytest
from fastapi import FastAPI
from fastapi.testclient import TestClient
from starlette.responses import JSONResponse

from fastapi_injection import Services, ScopeNotFoundError
from fastapi_injection.container import get_request_scope
from fastapi_injection.middleware import RequestScopeMiddleware

from .conftest import CounterService


class TestRequestScopeMiddleware:
    """Tests for the request scope middleware."""

    def test_middleware_creates_scope_for_request(self) -> None:
        app = FastAPI()
        services = Services()
        services.add_scoped(CounterService)

        app.add_middleware(RequestScopeMiddleware, services=services)

        scope_found = False

        @app.get("/")
        async def endpoint() -> dict:
            nonlocal scope_found
            scope_var = get_request_scope()
            scope_found = scope_var.get() is not None
            return {"ok": True}

        client = TestClient(app)
        response = client.get("/")

        assert response.status_code == 200
        assert scope_found

    def test_middleware_clears_scope_after_request(self) -> None:
        app = FastAPI()
        services = Services()

        app.add_middleware(RequestScopeMiddleware, services=services)

        @app.get("/")
        async def endpoint() -> dict:
            return {"ok": True}

        client = TestClient(app)
        client.get("/")

        # After request, scope should be None
        scope_var = get_request_scope()
        assert scope_var.get() is None

    def test_scoped_service_same_within_request(self) -> None:
        CounterService.reset_count()
        app = FastAPI()
        services = Services()
        services.add_scoped(CounterService)

        app.add_middleware(RequestScopeMiddleware, services=services)

        @app.get("/")
        async def endpoint() -> dict:
            instance1 = services.resolve(CounterService)
            instance2 = services.resolve(CounterService)
            return {
                "same_instance": instance1 is instance2,
                "id1": instance1.instance_id,
                "id2": instance2.instance_id,
            }

        client = TestClient(app)
        response = client.get("/")

        assert response.status_code == 200
        data = response.json()
        assert data["same_instance"] is True
        assert data["id1"] == data["id2"]

    def test_scoped_service_different_across_requests(self) -> None:
        CounterService.reset_count()
        app = FastAPI()
        services = Services()
        services.add_scoped(CounterService)

        app.add_middleware(RequestScopeMiddleware, services=services)

        @app.get("/")
        async def endpoint() -> dict:
            instance = services.resolve(CounterService)
            return {"instance_id": instance.instance_id}

        client = TestClient(app)

        response1 = client.get("/")
        response2 = client.get("/")

        assert response1.json()["instance_id"] != response2.json()["instance_id"]

    def test_scope_not_found_outside_request(self) -> None:
        services = Services()
        services.add_scoped(CounterService)

        with pytest.raises(ScopeNotFoundError):
            services.resolve(CounterService)

    def test_middleware_handles_exceptions(self) -> None:
        app = FastAPI()
        services = Services()
        services.add_scoped(CounterService)

        app.add_middleware(RequestScopeMiddleware, services=services)

        @app.get("/")
        async def endpoint() -> dict:
            raise ValueError("Test error")

        @app.exception_handler(ValueError)
        async def handle_error(request, exc):
            return JSONResponse(
                status_code=500, content={"error": str(exc)}
            )

        client = TestClient(app, raise_server_exceptions=False)
        response = client.get("/")

        assert response.status_code == 500

        # Scope should be cleared even after exception
        scope_var = get_request_scope()
        assert scope_var.get() is None

    def test_dispose_called_after_request(self) -> None:
        """Test that dispose function is called when request ends."""
        disposed = []

        class FakeSession:
            def __init__(self):
                self.closed = False

            def close(self):
                self.closed = True
                disposed.append(self)

        def create_session():
            return FakeSession()

        app = FastAPI()
        services = Services()
        services.add_scoped_factory(
            FakeSession,
            factory=create_session,
            dispose=lambda s: s.close()
        )

        app.add_middleware(RequestScopeMiddleware, services=services)

        @app.get("/")
        async def endpoint() -> dict:
            session = services.resolve(FakeSession)
            assert not session.closed
            return {"ok": True}

        client = TestClient(app)
        response = client.get("/")

        assert response.status_code == 200
        assert len(disposed) == 1
        assert disposed[0].closed is True

    def test_dispose_called_even_on_exception(self) -> None:
        """Test that dispose is called even when request fails."""
        disposed = []

        class FakeSession:
            def close(self):
                disposed.append(self)

        app = FastAPI()
        services = Services()
        services.add_scoped_factory(
            FakeSession,
            factory=FakeSession,
            dispose=lambda s: s.close()
        )

        app.add_middleware(RequestScopeMiddleware, services=services)

        @app.get("/")
        async def endpoint() -> dict:
            services.resolve(FakeSession)  # Create the session
            raise ValueError("Test error")

        @app.exception_handler(ValueError)
        async def handle_error(request, exc):
            return JSONResponse(status_code=500, content={"error": str(exc)})

        client = TestClient(app, raise_server_exceptions=False)
        response = client.get("/")

        assert response.status_code == 500
        assert len(disposed) == 1  # Session was still disposed
