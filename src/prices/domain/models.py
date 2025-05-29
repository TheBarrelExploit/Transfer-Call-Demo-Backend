from dataclasses import dataclass, field
from bson import ObjectId
from enum import Enum
from typing import Optional, Any
from datetime import datetime, timezone

class CallClass(str, Enum):
    LONG_DISTANCE_INTER = "0"
    LOCAL = "2"
    LONG_DISTANCE_INTRA = "3"
    INTERNATIONAL = "10"
    PREMIUM = "15"

    @classmethod
    def get_name(cls, value: str) -> str:
        """
        Obtiene el nombre descriptivo a partir del valor del código.
        Mantiene compatibilidad con el código existente.
        """
        mapping = {
            cls.LONG_DISTANCE_INTER: "Larga distancia inter",
            cls.LOCAL: "Local",
            cls.LONG_DISTANCE_INTRA: "Larga distancia intra",
            cls.INTERNATIONAL: "Internacional",
            cls.PREMIUM: "Premium",
        }
        return mapping.get(value, "Desconocido")


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
    modified_by: Optional[str] = None
    modification_date: Optional[datetime] = None
    last_modified: Optional[datetime] = None
    last_modified_by:Optional[str] = None
    _id: Optional[ObjectId] = field(default=None, init=False, repr=False)

    def __post_init__(self):
        # Se calcula automaticamente al crear la instancia
        self.call_type = CallClass.get_name(self.call_type)

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
