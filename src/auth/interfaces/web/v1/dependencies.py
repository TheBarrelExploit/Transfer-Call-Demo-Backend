from fastapi import Depends, HTTPException, status, Request
from fastapi.security import OAuth2PasswordBearer
from src.shared.database.mongodb import MongoDB
from src.shared.config import get_settings
from src.users.application.services import UserService
from src.auth.infrastructure.repositories import MongoDBUserRepository
from src.auth.infrastructure.microsoft_sso import MicrosoftSSORepository
from src.auth.infrastructure.security import (
    verify_password,
    create_access_token,
    verify_token,
    is_token_blacklisted
)
from src.auth.application.services import AuthService
from src.auth.application.use_cases import MicrosoftAuthService
from src.auth.domain.entities import User  #
from src.users.infrastructure.repositories import DBUserRepository
from src.users.domain.ports import UserRepository
from typing import Annotated
from motor.motor_asyncio import  AsyncIOMotorCollection, AsyncIOMotorDatabase
from jose import JWTError

oauth2_scheme = OAuth2PasswordBearer(tokenUrl="api/v1/auth/token")

async def get_mongo() -> MongoDB:
    settings = get_settings()
    mongo = MongoDB()
    await mongo.connect(settings.MONGO_URI, settings.MONGO_DB)
    return mongo

async def get_user_repository(mongo: MongoDB = Depends(get_mongo)) -> MongoDBUserRepository:
    return MongoDBUserRepository(mongo)

async def get_auth_service(user_repo: MongoDBUserRepository = Depends(get_user_repository)) -> AuthService:
    return AuthService(user_repo)


def get_mongo(request: Request) -> MongoDB:
    return request.app.state.mongo

def get_db(mongo: Annotated[MongoDB, Depends(get_mongo)]) -> AsyncIOMotorDatabase:
    return mongo.get_database()

def get_users_collection(db: Annotated[AsyncIOMotorDatabase, Depends(get_db)]) -> AsyncIOMotorCollection:
    return db.get_collection("users")

def get_user_repository(
    collection: Annotated[AsyncIOMotorCollection, Depends(get_users_collection)]) -> UserRepository:
    return DBUserRepository(collection)

def get_user_service(
    repo: Annotated[UserRepository, Depends(get_user_repository)]
) -> UserService:
    return UserService(repo)

async def get_auth_microsoft_repository() -> MicrosoftSSORepository:
    return MicrosoftSSORepository()

async def get_auth_service_sso(user_repo: UserService = Depends(get_user_service), sso_auth: MicrosoftSSORepository= Depends(get_auth_microsoft_repository) ) -> MicrosoftAuthService:
    return MicrosoftAuthService(user_repo, sso_auth)


async def get_current_user(
    token: str = Depends(oauth2_scheme),
    user_repo: MongoDBUserRepository = Depends(get_user_repository)
) -> User:
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Could not validate credentials",
        headers={"WWW-Authenticate": "Bearer"},
    )
    
    try:
        if is_token_blacklisted(token):
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Token invalidado"
            )
            
        payload = verify_token(token)
        if payload is None:
            raise credentials_exception
            
        username: str = payload.get("sub")
        if username is None:
            raise credentials_exception
    except JWTError:
        raise credentials_exception

    user = await user_repo.get_user_by_username(username)
    if user is None:
        raise credentials_exception
        
    return user
