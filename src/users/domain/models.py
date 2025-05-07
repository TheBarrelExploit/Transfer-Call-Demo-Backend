from dataclasses import dataclass, field
from bson import ObjectId
from typing import List, Optional, Any
from datetime import datetime, timezone

@dataclass
class MFAConfig:
    secret: Optional[str] = None
    enable: bool = False
    backup_codes: List[str] =  field(default_factory=list)
    last_used_at: Optional[datetime] = None

@dataclass
class UserBase:
    email: str
    username: str
    password_hash: str
    entity: str
    roles: List[str] = field(default_factory=lambda: ["user"])
    microsoft_id_account: Optional[str] = None
    mfa: MFAConfig = field(default_factory=MFAConfig)
    created_at: datetime = field(default_factory=lambda: datetime.now(timezone.utc))
    updated_at: datetime = field(default_factory=lambda: datetime.now(timezone.utc))
    
    
    # Campo interno para MongoDB (no incluido en __init__)
    _id: Optional[ObjectId] = field(default=None, init=False, repr=False)

    @property
    def id(self) -> str:
        return str(self._id) if self._id else None

    @classmethod
    def from_mongo(cls, data: dict[str, Any]):
        """Constructor que filtra _id correctamente"""
        filtered_data = {k: v for k, v in data.items() if k != '_id'}
        user = cls(**filtered_data)
        user._id = data['_id']  # Asigna _id después de crear el objeto
        return user


