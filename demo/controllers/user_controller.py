from fastapi import APIRouter

from demo.services import IUserService

router = APIRouter(prefix="/users", tags=["Users"])


@router.get("/")
async def list_users(user_service: IUserService):
    """Get all users."""
    return user_service.list_users()


@router.get("/{user_id}")
async def get_user(user_id: int, user_service: IUserService):
    """Get user by ID."""
    user = user_service.get_user(user_id)
    if not user:
        return {"error": "User not found"}
    return user
