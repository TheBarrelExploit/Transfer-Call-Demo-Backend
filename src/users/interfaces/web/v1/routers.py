from fastapi import APIRouter, Depends, HTTPException, status
from .schemas import UserCreateRequest, UserResponse
from src.users.application.services import UserService
from src.users.infrastructure.dependencies import get_user_service
from src.users.application.exception import UserNotFoundException, EmailAlreadyExistsException, InvalidPasswordException


router = APIRouter(
    prefix="/v1/users",
    tags=["users"]
)

@router.post("/create_user", response_model=UserResponse, status_code=status.HTTP_201_CREATED)
async def create_user(
    user_data: UserCreateRequest,
    user_service: UserService = Depends(get_user_service)):
    
    try:
        created_user = await user_service.create_user(user_data)
        user_dict = created_user.__dict__.copy()
        user_dict["mfa"] = created_user.mfa.__dict__
        return UserResponse.model_validate(user_dict)
    except EmailAlreadyExistsException as e:
        raise HTTPException(
            status_code= status.HTTP_409_CONFLICT,
            detail=str(e)
        )
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=str(e)
        )

@router.post("/change_password")
async def change_password(
    
):
    print("")
    