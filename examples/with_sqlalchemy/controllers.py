"""Controllers for the SQLAlchemy example."""

from fastapi import APIRouter, HTTPException

from .services import CreateUserDto, IUserService, UserDto

router = APIRouter(prefix="/users", tags=["Users"])


@router.get("/", response_model=list[UserDto])
async def get_all_users(user_service: IUserService) -> list[UserDto]:
    """Get all users."""
    return user_service.get_all_users()


@router.get("/{user_id}", response_model=UserDto)
async def get_user(user_id: int, user_service: IUserService) -> UserDto:
    """Get a user by ID."""
    user = user_service.get_user(user_id)
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    return user


@router.post("/", response_model=UserDto, status_code=201)
async def create_user(
    data: CreateUserDto, user_service: IUserService
) -> UserDto:
    """Create a new user."""
    return user_service.create_user(data)


@router.delete("/{user_id}", status_code=204)
async def delete_user(user_id: int, user_service: IUserService) -> None:
    """Delete a user."""
    if not user_service.delete_user(user_id):
        raise HTTPException(status_code=404, detail="User not found")
