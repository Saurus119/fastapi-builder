"""SQLAlchemy example of fastapi-app-builder usage.

This example demonstrates:
- Database integration with SQLAlchemy
- Repository pattern
- Service layer
- Clean controllers with no Depends()

Run with: uvicorn examples.with_sqlalchemy.main:app --reload

Note: Requires sqlalchemy to be installed:
    pip install fastapi-app-builder[sqlalchemy]
"""

from sqlalchemy import create_engine
from sqlalchemy.orm import Session, sessionmaker

from fastapi_app_builder import AppBuilder

from .controllers import router as user_router
from .models import Base
from .repositories import IUserRepository, UserRepository
from .services import IUserService, UserService

# Database setup
DATABASE_URL = "sqlite:///./example.db"
engine = create_engine(DATABASE_URL, connect_args={"check_same_thread": False})
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

# Create tables
Base.metadata.create_all(bind=engine)


# Installer functions for modular configuration
def install_database(builder: AppBuilder) -> None:
    """Configure database session."""

    def create_session() -> Session:
        return SessionLocal()

    builder.services.add_scoped_factory(Session, create_session)


def install_repositories(builder: AppBuilder) -> None:
    """Configure repository services."""
    builder.services.add_scoped(IUserRepository, UserRepository)


def install_services(builder: AppBuilder) -> None:
    """Configure application services."""
    builder.services.add_scoped(IUserService, UserService)


# Build application
builder = AppBuilder()

# Configure
builder.with_title("SQLAlchemy Example API")
builder.with_version("1.0.0")
builder.with_description(
    "Example demonstrating fastapi-app-builder with SQLAlchemy"
)

# Install components
builder.install(install_database)
builder.install(install_repositories)
builder.install(install_services)

# Configure CORS for frontend development
builder.install_cors(
    origins=["http://localhost:3000"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Add controllers
builder.add_controller(user_router)

# Build the app
app = builder.build()


if __name__ == "__main__":
    import uvicorn

    uvicorn.run(app, host="0.0.0.0", port=8000)
