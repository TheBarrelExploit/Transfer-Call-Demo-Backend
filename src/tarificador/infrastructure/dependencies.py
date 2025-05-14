from fastapi import Request, Depends, HTTPException, status
from fastapi.security import OAuth2PasswordBearer
from motor.motor_asyncio import AsyncIOMotorDatabase, AsyncIOMotorCollection
from typing import Annotated, Dict, Any
from src.tarificador.infrastructure.repository import CallRepository
from src.shared.database.mongodb import MongoDB
from src.tarificador.application.services import CallService
from src.auth.infrastructure.security import verify_token, is_token_blacklisted

oauth2_scheme = OAuth2PasswordBearer(tokenUrl="api/v1/auth/token")


def get_mongo(request: Request) -> MongoDB:
    return request.app.state.mongo


def get_db(mongo: Annotated[MongoDB, Depends(get_mongo)]) -> AsyncIOMotorDatabase:
    return mongo.get_database()


def get_users_collection(
    db: Annotated[AsyncIOMotorDatabase, Depends(get_db)],
) -> AsyncIOMotorCollection:
    return db.get_collection("llamadas")


def get_user_repository(
    collection: Annotated[AsyncIOMotorCollection, Depends(get_users_collection)],
) -> CallRepository:
    return CallRepository(collection)


def get_user_service(
    repo: Annotated[CallRepository, Depends(get_user_repository)],
) -> CallService:
    return CallService(repo)


async def get_current_payload(
    token: str = Depends(oauth2_scheme),
) -> Dict[str, Any]:
    """Obtiene solo el payload del token JWT validado"""
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

        return payload
    except JWTError:
        raise credentials_exception
    except Exception as e:
        logger.error(f"Error en get_current_payload: {str(e)}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Error interno del servidor al validar token",
        )
