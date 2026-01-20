# Changelog

All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.1.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [0.1.0b1] - 2025-01-20

### Changed
- **Breaking:** Renamed package from `fastapi-builder` to `fastapi-app-builder`
- **Breaking:** Renamed import from `fastapi_builder` to `fastapi_app_builder`

### Added
- `py.typed` marker for PEP 561 type checking support

### Migration
```python
# Before
from fastapi_builder import AppBuilder

# After
from fastapi_app_builder import AppBuilder
```

## [0.1.0a3] - 2025-01-19

### Fixed
- Resolved mypy strict mode errors
- Ruff linting fixes

## [0.1.0a2] - 2025-01-18

### Fixed
- Pre-release fixes and improvements

## [0.1.0a1] - 2025-01-17

### Added
- Initial alpha release
- `AppBuilder` for configuring FastAPI applications
- `Services` container for dependency injection
- Service lifetimes: Singleton, Scoped, Transient
- Factory registration with `add_*_factory()` methods
- `resolve()` function for service resolution anywhere in code
- Automatic constructor injection
- Startup validation for missing dependencies
- `extend()` method to add DI to existing FastAPI apps
- CORS installer via `install_cors()`
- SQLAlchemy integration support
- `InjectableRouter` (optional, standard `APIRouter` works)
- Installer pattern for modular service registration
