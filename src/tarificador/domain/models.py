from dataclasses import dataclass, field
from typing import Optional, Any
from enum import Enum
from bson import ObjectId
from datetime import datetime


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
            cls.LONG_DISTANCE_INTER: "Larga distancia internacional",
            cls.LOCAL: "Local",
            cls.LONG_DISTANCE_INTRA: "Larga distancia nacional",
            cls.INTERNATIONAL: "Internacional",
            cls.PREMIUM: "Premium",
        }
        return mapping.get(value, "Desconocido")


@dataclass
class CallBase:
    originational_number: str
    connected_number: str
    dialed_entity: str
    connected_entity: str
    start_date: datetime
    end_date: datetime
    type_of_call: str
    kind_of_call: str
    unique_call_id_ingress: str
    unique_call_id_egress: str
    entity_zone: str
    routing_id: str
    record_id: str
    corr_id: str
    feature: str
    call_progress_state: str
    call_completion_code: str
    class_call: CallClass
    erorr_code: str = None
    time_spent_in_call: str = "00:00:00"
    any_minutes: int = 0
    total_to_pay: int = 0

    _id: Optional[ObjectId] = field(default=None, init=False, repr=False)

    @property
    def id(self) -> str:
        return str(self._id) if self._id else None

    def __post_init__(self):
        # Se calcula automaticamente al crear la instancia
        self.class_call = CallClass.get_name(self.class_call)
        self.calculate_billable_minutes()

    def calculate_billable_minutes(self):
        """
        Calcula los minutos facturables a partir de time_spent_in_call.
        Cualquier fracción de minuto cuenta como un minuto adicional.
        """
        # Verificar si time_spent_in_call tiene formato válido "HH:MM:SS"
        if not self.time_spent_in_call or len(self.time_spent_in_call.split(":")) != 3:
            self.any_minutes = 0
            return

        try:
            # Extraer horas, minutos y segundos
            hours_str, minutes_str, seconds_str = self.time_spent_in_call.split(":")
            hours = int(hours_str)
            minutes = int(minutes_str)
            seconds = int(seconds_str)

            # Calcular minutos totales
            total_minutes = (hours * 60) + minutes

            # Si hay segundos, añadir un minuto más
            if seconds > 0:
                total_minutes += 1

            self.any_minutes = total_minutes
        except ValueError:
            # En caso de error en el formato
            self.any_minutes = 0

    @classmethod
    def from_mongo(cls, data: dict[str, Any]):
        """Constructor que filtra _id correctamente"""
        if not data:
            return None

        filtered_data = {k: v for k, v in data.items() if k != "_id"}
        user = cls(**filtered_data)
        user._id = str(data["_id"])  # Asigna _id después de crear el objeto
        return user
