"""Example controllers for basic demo."""

from fastapi import APIRouter

from .services import ICounterService, IGreetingService

greeting_router = APIRouter(prefix="/greetings", tags=["Greetings"])


@greeting_router.get("/{name}")
async def greet(name: str, greeting_service: IGreetingService) -> dict:
    """Greet a user by name."""
    return {"message": greeting_service.greet(name)}


counter_router = APIRouter(prefix="/counter", tags=["Counter"])


@counter_router.post("/increment")
async def increment(counter_service: ICounterService) -> dict:
    """Increment the counter."""
    value = counter_service.increment()
    return {"value": value}


@counter_router.get("/value")
async def get_value(counter_service: ICounterService) -> dict:
    """Get current counter value."""
    return {"value": counter_service.get_value()}
