"""Basic example of fastapi-builder usage.

Run with: uvicorn examples.basic.main:app --reload
"""

from fastapi_builder import AppBuilder

from .controllers import counter_router, greeting_router
from .services import (
    CounterService,
    GreetingService,
    ICounterService,
    IGreetingService,
)

# Create builder
builder = AppBuilder()

# Configure the application
builder.with_title("Basic Example API")
builder.with_version("1.0.0")
builder.with_description("A simple example demonstrating fastapi-builder")

# Register services
# Singleton: Same instance shared across all requests
builder.services.add_singleton(IGreetingService, GreetingService)

# Scoped: New instance per request (useful for request-specific state)
builder.services.add_scoped(ICounterService, CounterService)

# Add controllers
builder.add_controller(greeting_router)
builder.add_controller(counter_router)

# Build the FastAPI application
app = builder.build()


if __name__ == "__main__":
    import uvicorn

    uvicorn.run(app, host="0.0.0.0", port=8000)
