from demo.repositories import (
    IProductRepository,
    IUserRepository,
    ProductRepository,
    UserRepository,
)
from fastapi_app_builder import Services


def install_repositories(services: Services) -> None:
    """Register all repository services."""
    services.add_scoped(IUserRepository, UserRepository)
    services.add_scoped(IProductRepository, ProductRepository)
