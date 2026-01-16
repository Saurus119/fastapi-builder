from fastapi_injection import Services

from demo.repositories import (
    IUserRepository,
    UserRepository,
    IProductRepository,
    ProductRepository,
)


def install_repositories(services: Services) -> None:
    """Register all repository services."""
    services.add_scoped(IUserRepository, UserRepository)
    services.add_scoped(IProductRepository, ProductRepository)
