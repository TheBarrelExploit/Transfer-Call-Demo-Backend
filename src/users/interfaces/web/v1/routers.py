from dataclasses import asdict
from typing import Dict, Any
from fastapi import APIRouter, BackgroundTasks, Depends, HTTPException, status, Query, Path
from .schemas import UserCreateRequest, UserResponse, UserUpdateRequest, UserResponseList, UserChangePassword, UserChangePasswordResponse
from src.users.application.services import UserService
from src.users.infrastructure.dependencies import get_user_service, get_verify_token
from src.users.application.exception import EmailAlreadyExistsException, UserNotFoundException
from src.datasend.application.services import EmailService
from src.datasend.interfaces.web.v1.dependencies import get_email_service
import logging

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/v1/users", tags=["users"])


@router.post(
    "/create_user", response_model=UserResponse, status_code=status.HTTP_201_CREATED
)
async def create_user(
    user_data: UserCreateRequest,
    background_tasks: BackgroundTasks,
    user_service: UserService = Depends(get_user_service),
    email_service: EmailService = Depends(get_email_service)
):
    try:
        created_user = await user_service.create_user(user_data)
        user_dict = created_user.__dict__.copy()
        user_dict["mfa"] = created_user.mfa.__dict__
        
        # NUEVA FUNCIONALIDAD: Enviar email de bienvenida
        try:
            # La contraseña provisional es la que ya registrada en la BD
            # (la que viene en user_data.password)
            await email_service.send_welcome_email(
                background_tasks=background_tasks,
                email=created_user.email,
                provisional_password=user_data.password,
                role = created_user.roles,
                entity= created_user.entity  # Contraseña provisional generada por el frontend
            )
            logger.info(f"Email de bienvenida enviado a {created_user.email}")
        except Exception as email_error:
            logger.error(f"Error al enviar email de bienvenida a {created_user.email}: {str(email_error)}")        
        return UserResponse.model_validate(user_dict)
        
    except EmailAlreadyExistsException as e:
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail=str(e))
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=str(e)
        )


@router.put("/change_password", response_model=UserChangePasswordResponse, status_code=status.HTTP_200_OK)
async def change_password(
    user_data: UserChangePassword,
    user_service: UserService = Depends(get_user_service),
    auth_token:Dict[str, Any] = Depends(get_verify_token)
):
    verify_token:Dict[str, Any] = auth_token(user_data.secret_token)
    if not verify_token:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Enlace no valido para el cambio de la contraseña")    
    
    password = await user_service.change_password(email = verify_token.get("email"), new_password=user_data.new_password)
   
    return UserChangePasswordResponse(status="success", message="Cambio de contraseña exitoso!", is_change_password=password)


@router.put("/update_user", response_model=UserResponse, status_code=status.HTTP_200_OK)
async def update_user(
    user_data: UserUpdateRequest, user_service: UserService = Depends(get_user_service)
):
    update_payload_dict = user_data.model_dump(exclude_unset=True, exclude={"id"})
    if not update_payload_dict:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="No fields provided for update in the payload.",
        )

    update_user = await user_service.update_user(user_data.id, update_payload_dict)

    update_user_dict = asdict(update_user)

    return UserResponse.model_validate(update_user_dict)

@router.get("/user_all", response_model= UserResponseList, status_code=status.HTTP_200_OK)
async def get_user(
    user_service: UserService = Depends(get_user_service),
    page: int = Query(1, ge=1, description="Numero de página"),
    per_page: int = Query(10, le=100, description="Items por página"),
):
    user_all, total = await user_service.list_users(page=page, per_page=per_page)

    user_all_validate = [UserResponse.model_validate(asdict(user)) for user in user_all]

    total_pages = (total + per_page - 1) // per_page
    pagination = {
        "total": total,
        "page": page,
        "per_page": per_page,
        "total_pages": total_pages,
    }
    return UserResponseList(user = user_all_validate , pagination= pagination)

@router.delete("/delete_user/{user_id}", status_code=status.HTTP_200_OK)
async def delete_user(
    user_id: str = Path(..., description="id del usuario a eliminar"),
    user_service: UserService = Depends(get_user_service)
):
    try:
        print(f"user_email: {user_id}")

        delete = await user_service.delete_user(id=user_id)

        return {"status":"success","delete": delete}
    except UserNotFoundException as e:
        raise HTTPException(status_code= status.HTTP_400_BAD_REQUEST, detail=str(e))

    



