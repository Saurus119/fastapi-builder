"""
Demo application showing the installer pattern.

Run with: uvicorn demo.main:app --reload
"""

from demo.controllers import user_router
from demo.installers import install_repositories, install_services
from fastapi_injection import AppBuilder

# Create builder
builder = AppBuilder()

# Configure app
builder.with_title("Demo API")
builder.with_version("1.0.0")

# Install services using the installer pattern
builder.services.install(install_repositories).install(install_services)

# Add controllers
builder.add_controller(user_router)

# Build the app
app = builder.build()
