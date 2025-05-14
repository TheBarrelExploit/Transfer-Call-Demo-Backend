from pydantic import BaseModel, EmailStr, Field
from datetime import datetime
from enum import Enum
from typing import Optional, List
from bson import ObjectId


class PyObjectId(ObjectId):
    """Wrapper para ObjectId de MongoDB (solo en infraestructura)"""

    @classmethod
    def __get_validators__(cls):
        yield cls.validate

    @classmethod
    def validate(cls, v):
        if not ObjectId.is_valid(v):
            raise ValueError("Invalid ObjectId")
        return ObjectId(v)


class AuthProvider(str, Enum):
    LOCAL = "local"
    MICROSOFT = "microsoft"


class MFAConfigSchema(BaseModel):
    # secret: Optional[str] = None
    enabled: bool = False
    # backup_codes: List[str] = []
    # last_used_at: Optional[datetime] = None


class UserCreateRequest(BaseModel):
    """
    User creation schema.
    """

    email: EmailStr
    password: str = Field(..., min_length=8, max_length=16)
    username: str = Field(..., min_length=3, max_length=16)
    entity: str = Field(..., min_length=3, max_length=16)
    roles: List[str]


class UserUpdateRequest(BaseModel):
    """
    User Update schema
    """

    id: str = None
    entity: Optional[str] = Field(None, min_length=3, max_length=16)
    roles: List[str] = None
    logo: Optional[str] = None
    complete_profile: bool = None


class UserChangePassword(BaseModel):
    """
    Change Password User
    """

    id: str
    new_password: str


class UserResponse(BaseModel):
    """
    User output schema.
    """

    id: str = Field(alias="_id")
    email: EmailStr
    username: str
    entity: str
    # microsoft_id_account: Optional[str] = None
    role: List[str] = Field(alias="roles")
    mfa: MFAConfigSchema
    created_at: datetime
    logo: Optional[str] = None
    updated_at: Optional[datetime] = None
    auth_provider: AuthProvider
    complete_profile: bool
