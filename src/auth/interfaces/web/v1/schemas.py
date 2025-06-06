# Autores: Denuar Andres Ramos Lezama, Paola Andrea Morales Rodríguez
# Fecha: Junio 2025
# Proyecto: Demo Tarificador
# Derechos reservados
from pydantic import BaseModel


class Token(BaseModel):
    access_token: str
    token_type: str


class TokenData(BaseModel):
    username: str | None = None
