from fastapi import Depends, HTTPException, status, Request
from fastapi.security import OAuth2PasswordBearer
from src.shared.database.mongodb import MongoDB
from src.shared.config import get_settings
from src.users.application.services import UserService
from src.auth.infrastructure.microsoft_sso import MicrosoftSSORepository
from src.auth.infrastructure.mfa import MFAService
from src.auth.infrastructure.security import (
    verify_password,
    create_access_token,
    verify_token,
    is_token_blacklisted,
)
from src.auth.application.services import AuthService
from src.auth.application.use_cases import MicrosoftAuthService
from src.users.domain.models import UserBase
from src.users.infrastructure.repositories import DBUserRepository
from src.users.domain.ports import UserRepository
from typing import Annotated
from motor.motor_asyncio import AsyncIOMotorCollection, AsyncIOMotorDatabase
from jose import JWTError
import logging

logger = logging.getLogger(__name__)

oauth2_scheme = OAuth2PasswordBearer(tokenUrl="api/v1/auth/token")


async def get_mongo() -> MongoDB:
    settings = get_settings()
    mongo = MongoDB()
    await mongo.connect(settings.MONGO_URI, settings.MONGO_DB)
    return mongo


def get_mongo_from_app(request: Request) -> MongoDB:
    return request.app.state.mongo


def get_db(
    mongo: Annotated[MongoDB, Depends(get_mongo_from_app)],
) -> AsyncIOMotorDatabase:
    return mongo.get_database()


def get_users_collection(
    db: Annotated[AsyncIOMotorDatabase, Depends(get_db)],
) -> AsyncIOMotorCollection:
    return db.get_collection("users")


def get_user_repository(
    collection: Annotated[AsyncIOMotorCollection, Depends(get_users_collection)],
) -> UserRepository:
    return DBUserRepository(collection)


def get_user_service(
    repo: Annotated[UserRepository, Depends(get_user_repository)],
) -> UserService:
    return UserService(repo)


def get_mfa_service() -> MFAService:
    return MFAService()


async def get_auth_microsoft_repository() -> MicrosoftSSORepository:
    return MicrosoftSSORepository()


async def get_auth_service_sso(
    user_repo: UserService = Depends(get_user_service),
    sso_auth: MicrosoftSSORepository = Depends(get_auth_microsoft_repository),
) -> MicrosoftAuthService:
    return MicrosoftAuthService(user_repo, sso_auth)


async def get_auth_service(
    user_repo: UserRepository = Depends(get_user_repository),
    mfa_service: MFAService = Depends(get_mfa_service),
) -> AuthService:
    return AuthService(user_repo, mfa_service)


async def get_current_user(
    token: str = Depends(oauth2_scheme),
    user_repo: UserRepository = Depends(get_user_repository),
) -> UserBase:
    if token == "undefined":
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED, detail="Token no proporcionado"
        )
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Could not validate credentials",
        headers={"WWW-Authenticate": "Bearer"},
    )

    try:
        if is_token_blacklisted(token):
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED, detail="Token invalidado"
            )

        payload = verify_token(token)
        if payload is None:
            raise credentials_exception

        # Primero intentamos obtener el ID del usuario
        user_id: str = payload.get("id")

        # Si no hay ID, fallamos al username (para retrocompatibilidad)
        if user_id:
            user = await user_repo.find_by_id(user_id)
        else:
            username: str = payload.get("sub")
            if username is None:
                raise credentials_exception
            user = await user_repo.find_by_username(username)

        if user is None:
            raise credentials_exception

        return user
    except JWTError:
        raise credentials_exception
    except Exception as e:
        logger.error(f"Error en get_current_user: {str(e)}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Error interno del servidor al validar usuario",
        )


async def get_current_user_sso(
    token: str = Depends(oauth2_scheme),
    user_repo: UserRepository = Depends(get_user_repository),
) -> UserBase:
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Could not validate credentials",
        headers={"WWW-Authenticate": "Bearer"},
    )

    try:
        if is_token_blacklisted(token):
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED, detail="Token invalidado"
            )

        payload = verify_token(token)
        if payload is None:
            raise credentials_exception

        sub: str = payload.get("sub")
        if sub is None:
            raise credentials_exception
    except JWTError:
        raise credentials_exception

    user = await user_repo.find_by_id(payload.get("id"))
    if user is None:
        raise credentials_exception

    return user
