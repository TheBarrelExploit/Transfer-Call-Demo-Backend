# Autores: Denuar Andres Ramos Lezama, Paola Andrea Morales Rodríguez
# Fecha: Junio 2025
# Proyecto: Demo Tarificador
# Derechos reservados
import logging
from datetime import timedelta
from src.shared.config import get_settings
from src.auth.infrastructure.mfa import MFAService
from src.users.domain.models import UserBase
from src.auth.infrastructure.security import verify_password, create_access_token
from src.auth.interfaces.repositories import UserRepository

logger = logging.getLogger(__name__)


class AuthService:
    def __init__(self, user_repository: UserRepository, mfa_service: MFAService = None):
        self.user_repository = user_repository
        self.mfa_service = mfa_service or MFAService()
        self._settings = get_settings()

    @property
    def settings(self):
        """Propiedad para acceder a la configuración"""
        return self._settings

    async def authenticate_user(self, username: str, password: str) -> UserBase:
        """Autentica un usuario con credenciales locales"""
        try:
            logger.info(f"Intentando autenticar usuario: {username}")
            user = await self.user_repository.find_by_username(username)

            if not user:
                logger.warning(f"Usuario no encontrado: {username}")
                return None

            logger.info(f"Usuario encontrado: {user.username}")

            if not verify_password(password, user.password_hash):
                logger.warning(f"Contraseña incorrecta para usuario: {username}")
                return None

            logger.info(f"Autenticación exitosa para: {username}")
            return user

        except Exception as e:
            logger.error(f"Error en authenticate_user: {str(e)}", exc_info=True)
            raise

    async def create_access_token(
        self, user: UserBase, mfa_verified: bool = False
    ) -> str:
        # Crea un token JWT compatible con la estructura actual
        token_data = {
            "id": str(user._id) if hasattr(user, "_id") else None,
            "sub": user.username,
            "username": user.username,
            "email": user.email,
            "entity": user.entity,
            "roles": user.roles,
            "mfa_verified": mfa_verified,
            # Maneja tanto AuthProvider enum como string
            "auth_provider": user.auth_provider.value
            if hasattr(user.auth_provider, "value")
            else user.auth_provider,
        }
        return create_access_token(
            data=token_data,
            expires_delta=timedelta(minutes=self.settings.JWT_EXPIRATION),
        )

    async def initiate_mfa_setup(self, username: str) -> dict:
        # Inicia el proceso de configuración MFA
        user = await self.user_repository.find_by_username(username)
        if not user:
            raise ValueError("Usuario no encontrado")

        secret = self.mfa_service.generate_secret()
        uri = self.mfa_service.generate_provisioning_uri(user.username, secret)
        qr_code = self.mfa_service.generate_qr_code(uri)

        return {"secret": secret, "qr_code": qr_code, "uri": uri}

    async def verify_and_enable_mfa(
        self, username: str, secret: str, code: str
    ) -> bool:
        # Verifica y activa MFA para un usuario
        if not self.mfa_service.verify_code(secret, code):
            return False

        user = await self.user_repository.find_by_username(username)
        if not user:
            return False

        mfa_config = self.mfa_service.create_mfa_config(secret)
        return await self.user_repository.update_user_mfa(username, mfa_config)

    async def verify_mfa_login(self, username: str, code: str) -> bool:
        # Verifica un código MFA durante el login
        user = await self.user_repository.find_by_username(username)
        if not user or not user.mfa or not user.mfa.secret or not user.mfa.enabled:
            return False
        return self.mfa_service.verify_code(user.mfa.secret, code)
