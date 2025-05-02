from pydantic import BaseModel, EmailStr
from typing import Optional

class User(BaseModel):
    """User entity model"""
    username: str
    email: EmailStr
    hashed_password: str
    disabled: Optional[bool] = False
    full_name: Optional[str] = None

    class Config:
        from_attributes = True  # Para compatibilidad con ORM