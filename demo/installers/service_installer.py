from fastapi_injection import Services

from demo.services import IUserService, UserService


def install_services(services: Services) -> None:
    """Register all application services."""
    services.add_scoped(IUserService, UserService)
