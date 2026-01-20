# fastapi-app-builder

[![PyPI version](https://img.shields.io/pypi/v/fastapi-app-builder.svg)](https://pypi.org/project/fastapi-app-builder/)
[![Python versions](https://img.shields.io/pypi/pyversions/fastapi-app-builder.svg)](https://pypi.org/project/fastapi-app-builder/)
[![Downloads](https://static.pepy.tech/badge/fastapi-app-builder)](https://pepy.tech/project/fastapi-app-builder)
[![License](https://img.shields.io/pypi/l/fastapi-app-builder.svg)](https://github.com/Saurus119/fastapi-app-builder/blob/main/LICENSE)

[![Buy Me A Coffee](https://img.shields.io/badge/Buy%20Me%20A%20Coffee-support-yellow.svg?style=flat&logo=buy-me-a-coffee)](https://buymeacoffee.com/saurus119)

ASP.NET Core-style dependency injection for FastAPI - clean controllers, builder pattern, zero boilerplate.

## Features

- **Clean controllers** - No `Depends()`, `Injected[]`, or `Provide[]` - just type hints
- **Standard FastAPI** - Use standard `APIRouter` - no custom router classes needed
- **Builder pattern** - Familiar `AppBuilder` for application configuration
- **Proper lifetimes** - Singleton, Scoped (per-request), and Transient
- **Fail fast** - Validate all dependencies at startup
- **Familiar API** - Mirror .NET naming conventions

## Installation

```bash
pip install fastapi-app-builder
```

With SQLAlchemy support:
```bash
pip install fastapi-app-builder[sqlalchemy]
```

## Quick Start

```python
from typing import Protocol
from fastapi import APIRouter
from fastapi_app_builder import AppBuilder

# Define your service interface and implementation
class IGreetingService(Protocol):
    def greet(self, name: str) -> str: ...

class GreetingService:
    def greet(self, name: str) -> str:
        return f"Hello, {name}!"

# Create router with clean dependency injection - no Depends() needed!
router = APIRouter(prefix="/greetings")

@router.get("/{name}")
async def greet(name: str, greeting_service: IGreetingService):
    return {"message": greeting_service.greet(name)}

# Configure and build the application
builder = AppBuilder()
builder.services.add_singleton(IGreetingService, GreetingService)
builder.add_controller(router)
app = builder.build()
```

## Using Standard APIRouter

Use FastAPI's standard `APIRouter` - the dependency injection works automatically. Routers can be defined in separate files and imported in any order:

```python
# controllers/users.py
from fastapi import APIRouter
from services import IUserService

router = APIRouter(prefix="/users", tags=["Users"])

@router.get("/{user_id}")
async def get_user(user_id: int, user_service: IUserService):
    # user_service is automatically injected - no Depends() needed!
    return user_service.get_user(user_id)

@router.post("/")
async def create_user(data: CreateUserDto, user_service: IUserService):
    return user_service.create(data)
```

```python
# main.py
from fastapi_app_builder import AppBuilder
from controllers.users import router as user_router
from services import IUserRepository, UserRepository, IUserService, UserService

builder = AppBuilder()
builder.services.add_scoped(IUserRepository, UserRepository)
builder.services.add_scoped(IUserService, UserService)
builder.add_controller(user_router)
app = builder.build()
```

## Service Lifetimes

### Singleton
One instance shared across the entire application:
```python
builder.services.add_singleton(IMyService, MyService)
```

### Scoped
One instance per HTTP request:
```python
builder.services.add_scoped(IMyService, MyService)
```

### Transient
New instance every time it's requested:
```python
builder.services.add_transient(IMyService, MyService)
```

## Factory Registration

Register services with custom factory functions:
```python
builder.services.add_singleton_factory(IMyService, lambda: MyService(config))
builder.services.add_scoped_factory(IMyService, create_my_service)
```

## Nested Dependencies

Dependencies are automatically resolved via constructor injection:
```python
class UserRepository:
    pass

class UserService:
    def __init__(self, user_repository: UserRepository):
        self.repo = user_repository

builder.services.add_scoped(UserRepository)
builder.services.add_scoped(UserService)
# UserService will automatically receive UserRepository
```

## Resolving Services Anywhere

Use `resolve()` to get services from anywhere in your code during a request:

```python
from fastapi_app_builder import resolve

class OrderService:
    def create_order(self, items: list):
        # Resolve services on-demand (not just in constructors)
        inventory = resolve(IInventoryService)
        payment = resolve(IPaymentService)

        for item in items:
            inventory.reserve(item)

        return payment.charge(items)

# Also works in utility functions
def get_current_user():
    auth = resolve(IAuthService)
    return auth.get_current_user()
```

Note: Prefer constructor injection when possible - it makes dependencies explicit and easier to test.

## Installer Pattern

Organize service registrations with installers for better modularity:

```python
# installers/repositories.py
from fastapi_app_builder import Services

def install_repositories(services: Services) -> None:
    services.add_scoped(IUserRepository, UserRepository)
    services.add_scoped(IProductRepository, ProductRepository)

# installers/services.py
def install_services(services: Services) -> None:
    services.add_scoped(IUserService, UserService)
    services.add_scoped(IProductService, ProductService)

# main.py
builder = AppBuilder()
builder.services.install(install_repositories).install(install_services)
```

You can also use `builder.install()` if you need access to the full builder:
```python
def install_all(builder: AppBuilder) -> None:
    builder.services.add_scoped(IUserRepository, UserRepository)
    builder.with_title("My API")

builder.install(install_all)
```

## Configuration

```python
builder = AppBuilder()

# Configure OpenAPI docs
builder.with_title("My API")
builder.with_version("1.0.0")
builder.with_description("My awesome API")
builder.with_docs_url("/swagger")

# Configure CORS
builder.install_cors(
    origins=["http://localhost:3000"],
    allow_credentials=True,
)

# Disable validation (not recommended)
builder.with_validation(False)
```

## Validation

By default, all dependencies are validated at startup:
```python
builder.services.add_scoped(IUserService, UserService)
# If UserService depends on IUserRepository which isn't registered,
# builder.build() will raise ValidationError
```

## Extending an Existing FastAPI App

Use `extend()` to add DI to an existing FastAPI app:

```python
from fastapi import FastAPI
from fastapi_app_builder import AppBuilder
from controllers import user_router

# Create your own FastAPI instance with custom settings
app = FastAPI(
    title="My API",
    lifespan=my_lifespan,  # Custom lifespan handler
)

# Add routes directly
@app.get("/health")
async def health():
    return {"status": "ok"}

# Use builder for DI only
builder = AppBuilder()
builder.services.add_scoped(IUserService, UserService)
builder.add_controller(user_router)
builder.extend(app)  # Adds DI to existing app
```

## SQLAlchemy Integration

```python
from sqlalchemy import create_engine
from sqlalchemy.orm import Session, sessionmaker
from fastapi_app_builder import AppBuilder

engine = create_engine("sqlite:///./app.db")
SessionLocal = sessionmaker(bind=engine)

def install_database(builder: AppBuilder) -> None:
    # Use dispose to automatically close sessions after each request
    builder.services.add_scoped_factory(
        Session,
        factory=SessionLocal,
        dispose=lambda s: s.close()
    )

builder = AppBuilder()
builder.install(install_database)
```

The `dispose` parameter ensures resources are properly cleaned up when the request ends, even if an exception occurs.

## API Reference

### AppBuilder

The main entry point for configuring your FastAPI application.

| Method | Description |
|--------|-------------|
| `services` | Property to access the DI container |
| `add_controller(router)` | Add a standard FastAPI `APIRouter` to the application |
| `install(installer)` | Apply an installer function |
| `install_cors(origins, ...)` | Configure CORS middleware |
| `with_title(title)` | Set application title |
| `with_version(version)` | Set application version |
| `with_description(desc)` | Set application description |
| `with_docs_url(url)` | Set Swagger UI URL |
| `with_validation(enabled)` | Enable/disable startup validation |
| `build()` | Build and return a new FastAPI app |
| `extend(app)` | Add DI to an existing FastAPI app |

### Services

The dependency injection container.

| Method | Description |
|--------|-------------|
| `add_singleton(interface, impl)` | Register a singleton service |
| `add_scoped(interface, impl)` | Register a scoped service |
| `add_transient(interface, impl)` | Register a transient service |
| `add_singleton_factory(interface, factory)` | Register singleton with factory |
| `add_scoped_factory(interface, factory, dispose=None)` | Register scoped with factory and optional cleanup |
| `add_transient_factory(interface, factory)` | Register transient with factory |
| `install(installer)` | Apply an installer function to register services |
| `is_registered(interface)` | Check if a service is registered |
| `resolve(interface)` | Manually resolve a service |
| `validate()` | Validate all registrations |

### resolve()

Resolve a service from anywhere during a request:

```python
from fastapi_app_builder import resolve

service = resolve(IMyService)
```

## License

MIT
