from pydantic import BaseModel, EmailStr
from typing import Optional

class User(BaseModel):
    username: str
    email: EmailStr
    hashed_password: str
    disabled: Optional[bool] = False
    full_name: Optional[str] = None
    mfa_enabled: bool = False  # Nuevo campo para controlar MFA
    mfa_secret: Optional[str] = None  # Almacena el secreto para generar TOTP
    
    class Config:
        from_attributes = True