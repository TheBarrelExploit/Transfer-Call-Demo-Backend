from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.security import OAuth2PasswordRequestForm
from src.auth.application.services import AuthService
from .schemas import Token
from .dependencies import get_auth_service


router = APIRouter(
    prefix="/v1/auth",
    tags=["auth"]
)

@router.post("/token", response_model=Token)
async def login_for_access_token(
    form_data: OAuth2PasswordRequestForm = Depends(),
    auth_service: AuthService = Depends(get_auth_service)
):
    user = await auth_service.authenticate_user(form_data.username, form_data.password)
    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect username or password",
            headers={"WWW-Authenticate": "Bearer"},
        )
    
    access_token = await auth_service.create_access_token(user.username)
    return {"access_token": access_token, "token_type": "bearer"}