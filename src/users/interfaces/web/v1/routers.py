from dataclasses import asdict
from fastapi import APIRouter, Depends, HTTPException, status
from .schemas import UserCreateRequest, UserResponse, UserUpdateRequest
from src.users.application.services import UserService
from src.users.infrastructure.dependencies import get_user_service
from src.users.application.exception import  EmailAlreadyExistsException


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

@router.put("/update_user", response_model= UserResponse)
async def update_user(
    user_data: UserUpdateRequest,
    user_service: UserService = Depends(get_user_service)
):
    update_payload_dict = user_data.model_dump(
        exclude_unset=True,
        exclude={"id"}
    )
    if not update_payload_dict:
        raise HTTPException(status_code = status.HTTP_400_BAD_REQUEST, detail= "No fields provided for update in the payload.")

    update_user = await user_service.update_user(user_data.id, update_payload_dict)
   
    update_user_dict = asdict(update_user)
    print(update_user_dict)
    return UserResponse.model_validate(update_user_dict)

    