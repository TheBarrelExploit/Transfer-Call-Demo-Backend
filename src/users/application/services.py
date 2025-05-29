from typing import List, Optional, Dict, Any, Tuple
from passlib.context import CryptContext
from datetime import datetime, timezone
from base64 import b64encode
from .interfaces import UserServiceUser
from .exception import (
    UserNotFoundException,
    InvalidPasswordException,
    EmailAlreadyExistsException,
    InvalidDataException,
)
from ..domain.models import UserBase, MFAConfig, AuthProvider
from ..domain.ports import UserRepository
from ..interfaces.web.v1.schemas import UserCreateRequest

pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")


class UserService(UserServiceUser):
    def __init__(self, repository: UserRepository):
        self.repository = repository

    def _hash_password(self, password: str) -> str:
        return pwd_context.hash(password)

    def _verify_password(self, plain_password: str, hashed_password: str):
        return pwd_context.verify(plain_password, hashed_password)

    async def get_by_id(self, id: str) -> Optional[UserBase]:
        user = await self.repository.find_by_id(id)
        if not user:
            raise UserNotFoundException(f"User with id {id} not found")
        return user

    async def get_by_email(self, email: str) -> Optional[UserBase]:
        user = await self.repository.find_by_email(email)
        if not user:
            raise UserNotFoundException(f"User with email {email} not found")
        return user

    async def get_by_microsoft_id(self, id) -> Optional[UserBase]:
        user = await self.repository.find_by_id_microsoft(id)
        if not user:
            return None
        return user

    async def create_user_sso(self, user: UserBase) -> UserBase:
        existing_user = await self.repository.find_by_id_microsoft(
            user.microsoft_id_account
        )
        if existing_user:
            return existing_user

        return await self.repository.create(user)

    async def create_user(self, user: UserCreateRequest) -> UserBase:
        existing_user = await self.repository.find_by_email(user.email)
        if existing_user:
            raise EmailAlreadyExistsException(f"Email {user.email} already exists")

        new_user = UserBase(
            username=user.username,
            email=user.email,
            password_hash=self._hash_password(user.password),
            entity=user.entity,
            roles=user.roles,
            mfa=MFAConfig(),
            auth_provider=AuthProvider.LOCAL,
            complete_profile=False,
            logo= await self.image_to_b64("src/shared/Logo_2.png"),
            created_at=datetime.now(timezone.utc),
            updated_at=datetime.now(timezone.utc),
        )
        return await self.repository.create(new_user)

    async def update_user(
        self, id: str, data_user: Dict[str, Any]
    ) -> Optional[UserBase]:
        user = await self.repository.find_by_id(id)
        if not user:
            raise UserNotFoundException(f"User with id {id} not found")

        if "email" in data_user and data_user["email"] != user.email:
            existing_user = await self.repository.find_by_email(data_user["email"])
            if existing_user and str(existing_user.id) != id:
                raise EmailAlreadyExistsException(
                    f"Email {data_user['email']} already exists"
                )

        updated_data = {**{k: v for k, v in data_user.items() if k != "password"}}

        if "password" in data_user:
            updated_data["password"] = self._hash_password(data_user["password"])

        return await self.repository.update(id, updated_data)

    async def delete_user(self, id: str) -> bool:
        user = await self.repository.find_by_id(id)
        if not user:
            raise UserNotFoundException(f"User with id {id} not found")

        return await self.repository.delete(id)

    async def list_users(self, page: int = 0, per_page: int = 10) -> Tuple[List[UserBase], int]:
        return await self.repository.list(page, per_page)

    async def change_password(
        self, email: str, new_password: str
    ) -> bool:
        user = await self.repository.find_by_email(email=email)
        if not user:
            raise UserNotFoundException(f"User with email {email} not found")

        return await self.repository.update(
            email,
            {
                "password_hash": self._hash_password(new_password),
                "updated_at": datetime.now(timezone.utc),
            },
        )
    
    async def image_to_b64(self, img:str)->str:
        try:
            with open(img,"rb") as image:
                img_data = image.read()
                img_b64 = b64encode(img_data).decode("utf-8")
                return img_b64
        except FileNotFoundError as e:
            print(f"Error: no se encontro el archivo {e}")
            return ""

        
