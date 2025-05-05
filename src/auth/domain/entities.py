from pydantic import BaseModel, EmailStr
from typing import Optional

class User(BaseModel):
    username: str
    email: EmailStr
    hashed_password: str
    disabled: bool = False
    mfa_enabled: bool = False
    mfa_secret: Optional[str] = None
    
    class Config:
        from_attributes = True