# Autores: Denuar Andres Ramos Lezama, Paola Andrea Morales Rodríguez
# Fecha: Junio 2025
# Proyecto: Demo Tarificador
# Derechos reservados
from fastapi import Depends
from src.datasend.application.services import EmailService
from src.users.domain.ports import UserRepository
from src.auth.interfaces.web.v1.dependencies import get_user_repository

def get_email_service(
    user_repo: UserRepository = Depends(get_user_repository)
) -> EmailService:
    """Dependencia para obtener una instancia del EmailService"""
    return EmailService(user_repo)