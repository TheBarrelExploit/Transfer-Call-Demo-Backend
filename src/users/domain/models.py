from dataclasses import dataclass, field
from bson import ObjectId
from enum import Enum
from typing import List, Optional, Any
from datetime import datetime, timezone


class AuthProvider(str, Enum):
    LOCAL = "local"
    MICROSOFT = "microsoft"


@dataclass
class MFAConfig:
    secret: Optional[str] = None
    enabled: bool = False
    backup_codes: List[str] = field(default_factory=list)
    last_used_at: Optional[datetime] = None


@dataclass
class UserBase:
    email: str
    username: str
    password_hash: str
    entity: str
    auth_provider: AuthProvider
    complete_profile: bool
    logo: Optional[str] = None
    roles: List[str] = field(default_factory=lambda: ["user"])
    microsoft_id_account: str = None
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
        if not data:
            return None

        # Convertir auth_provider a Enum si es string
        if "auth_provider" in data and isinstance(data["auth_provider"], str):
            try:
                data["auth_provider"] = AuthProvider(data["auth_provider"])
            except ValueError:
                data["auth_provider"] = AuthProvider.LOCAL  # Valor por defecto

        # Convertir mfa a MFAConfig si es necesario
        if "mfa" in data and isinstance(data["mfa"], dict):
            mfa_dict = data["mfa"]
            data["mfa"] = MFAConfig(
                secret=mfa_dict.get("secret"),
                enabled=mfa_dict.get("enabled", False),
                backup_codes=mfa_dict.get("backup_codes", []),
                last_used_at=mfa_dict.get("last_used_at"),
            )

        filtered_data = {k: v for k, v in data.items() if k != "_id"}
        user = cls(**filtered_data)
        user._id = str(data["_id"])  # Asigna _id después de crear el objeto
        return user
