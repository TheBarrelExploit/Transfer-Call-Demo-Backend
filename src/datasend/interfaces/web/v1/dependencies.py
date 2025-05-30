from fastapi import Depends
from src.datasend.application.services import EmailService
from src.users.domain.ports import UserRepository
from src.auth.interfaces.web.v1.dependencies import get_user_repository

def get_email_service(
    user_repo: UserRepository = Depends(get_user_repository)
) -> EmailService:
    """Dependencia para obtener una instancia del EmailService"""
    return EmailService(user_repo)