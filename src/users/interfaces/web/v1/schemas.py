from pydantic import BaseModel, EmailStr, Field
from datetime import datetime
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
    
class MFAConfigSchema(BaseModel):
    secret: Optional[str] = None
    enabled: bool = False
    backup_codes: List[str] = []
    last_used_at: Optional[datetime] = None

class UserCreateRequest(BaseModel):
    """
    User creation schema.
    """
    email: EmailStr
    password: str = Field(..., min_length=8, max_length=16)
    username: str = Field(..., min_length=3, max_length=16)
    entity:str = Field(..., min_length=3, max_length=16)
    roles:List[str] 

class UserChangePassword(BaseModel):
    """
    Change Password User
    """
    id:str
    new_password:str

class UserResponse(BaseModel):
    """
    User output schema.
    """
    id: str = Field(alias="_id")
    email: EmailStr
    username: str
    entity:str
    microsoft_id_account:str
    roles:List[str]
    mfa: MFAConfigSchema
    created_at: datetime 
    updated_at: Optional[datetime] = None


