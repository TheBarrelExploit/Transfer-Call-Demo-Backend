from datetime import datetime, timezone, timedelta
from typing import Dict, Any, Optional
from jose import jwt, JWTError
from dataclasses import asdict
from src.auth.application.services_sso import AuthServiceSSO
from src.auth.infrastructure.microsoft_sso import MicrosoftSSORepository
from src.users.application.services import UserService
from src.users.interfaces.web.v1.schemas import UserResponse
from src.users.domain.models import UserBase, AuthProvider
from src.shared.config import get_settings
import logging

settings = get_settings()


logger = logging.getLogger(__name__)


class MicrosoftAuthService(AuthServiceSSO):
    def __init__(self, user_repository: UserService, auth_sso: MicrosoftSSORepository):
        self.user_repository = user_repository
        self.microsoft = auth_sso

    async def get_user_info(self, token):
        return await self.microsoft.get_user_info(token)

    async def get_login_url(self) -> str:
        return self.microsoft.get_auth_url()

    async def process_auth_code(self, code: str) -> Dict[str, Any]:
        token_data = await self.microsoft.get_token_from_code(code)
        access_token = token_data.get("access_token")

        if not access_token:
            raise ValueError("No se pudo obtener el token de acceso")

        user_info = await self.microsoft.get_user_info(access_token)

        user = await self.create_user_sso(user_info)

        token = await self.create_access_token(user)

        return {
            "token": token.get("access_token"),
            "token_type": token.get("token_type"),
        }

    async def create_user_sso(self, user_info) -> UserBase:
        microsoft_id_account = user_info.get("microsoft_id")
        email = user_info.get("email")
        name = user_info.get("name")

        if not microsoft_id_account or not email:
            raise ValueError("La información del usuario no contiene ID o email")

        user = await self.user_repository.get_by_microsoft_id(microsoft_id_account)

        if not user:
            new_user = UserBase(
                email=email,
                username=name,
                microsoft_id_account=microsoft_id_account,
                created_at=datetime.now(timezone.utc),
                entity="",
                password_hash=None,
                auth_provider=AuthProvider.MICROSOFT,
                complete_profile=False,
            )
            user = await self.user_repository.create_user_sso(new_user)

        user._id = user.id
        return user

    async def create_access_token(self, user: UserBase):
        payload = {
            "id":str(user.id),
            "sub": str(user.username),
            "email": user.email,
            "roles": user.roles,
            "auth_provider": user.auth_provider,
            "exp": datetime.now(timezone.utc)
            + timedelta(minutes=settings.JWT_EXPIRATION),
        }

        access_token = jwt.encode(
            payload, settings.JWT_SECRET, algorithm=settings.JWT_ALGORITHM
        )

        return {"access_token": access_token, "token_type": "Bearer"}

    async def validate_token(self, token: str) -> Optional[UserBase]:
        try:
            payload = jwt.decode(
                token, settings.JWT_SECRET, algorithms=[settings.JWT_ALGORITHM]
            )

            user_id = payload.get("sub")
            if user_id is None:
                return

            user = await self.user_repository.get_by_id(user_id)
            return user

        except JWTError:
            return None
