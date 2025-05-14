from dataclasses import dataclass, field
from bson import ObjectId
from typing import Optional, Any
from datetime import datetime, timezone


@dataclass
class PriceBase:
    call_type: str
    rate_per_minute: int
    divisa: str
    created_by: str 
    valid_from: datetime = datetime.now(timezone.utc)
    valid_until: Optional[datetime] = None
    created_at: datetime = datetime.now(timezone.utc)
    is_active: bool = True
    _id: Optional[ObjectId] = field(default=None, init=False, repr=False)

    @property
    def id(self) -> str:
        return str(self._id) if self._id else None

    @classmethod
    def from_mongo(cls, data: dict[str, Any]):
        """Constructor que filtra _id correctamente"""
        if not data:
            return None

        filtered_data = {k: v for k, v in data.items() if k != "_id"}
        user = cls(**filtered_data)
        user._id = str(data["_id"])  # Asigna _id después de crear el objeto
        return user


@dataclass
class PriceHistory:
    action: str
    call_type: str
    previous_rate: int
    new_rate: int
    changed_by: str
    changed_at: datetime

    _id: Optional[ObjectId] = field(default=None, init=False, repr=False)

    @property
    def id(self) -> str:
        return str(self._id) if self._id else None

    @classmethod
    def from_mongo(cls, data: dict[str, Any]):
        """Constructor que filtra _id correctamente"""
        if not data:
            return None

        filtered_data = {k: v for k, v in data.items() if k != "_id"}
        user = cls(**filtered_data)
        user._id = str(data["_id"])  # Asigna _id después de crear el objeto
        return user
