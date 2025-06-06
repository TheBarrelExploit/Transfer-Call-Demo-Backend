# Autores: Denuar Andres Ramos Lezama, Paola Andrea Morales Rodríguez
# Fecha: Junio 2025
# Proyecto: Demo Tarificador
# Derechos reservados
import pyotp
import qrcode
from io import BytesIO
import base64
import logging
from datetime import datetime, timezone
from src.users.domain.models import MFAConfig
import time

logger = logging.getLogger(__name__)


class MFAService:
    def __init__(self, issuer_name: str = "Transfer-Call-Demo"):
        self.issuer_name = issuer_name

    def generate_secret(self) -> str:
        """Genera un secreto para MFA"""
        return pyotp.random_base32()

    def generate_provisioning_uri(self, username: str, secret: str) -> str:
        """Genera URI para configuración en apps autenticadoras"""
        return pyotp.totp.TOTP(secret).provisioning_uri(
            name=username, issuer_name=self.issuer_name
        )

    def generate_qr_code(self, uri: str) -> str:
        """Genera QR code como base64"""
        try:
            qr = qrcode.QRCode(
                version=1,
                error_correction=qrcode.constants.ERROR_CORRECT_L,
                box_size=10,
                border=4,
            )
            qr.add_data(uri)
            qr.make(fit=True)

            img = qr.make_image(fill_color="black", back_color="white")
            buffered = BytesIO()
            img.save(buffered, format="PNG")
            return f"data:image/png;base64,{base64.b64encode(buffered.getvalue()).decode()}"
        except Exception as e:
            logger.error(f"Error generando QR: {str(e)}")
            raise ValueError("Error generando código QR")

    def verify_code(self, secret: str, code: str, window: int = 3) -> bool:
        # Verificación robusta con ventana de tiempo ampliada y logging
        try:
            totp = pyotp.TOTP(
                secret,
                interval=30,  # 30 segundos (estándar)
                digits=6,  # 6 dígitos (estándar)
            )

            current_time = time.time()
            is_valid = totp.verify(code, valid_window=window)

            logger.info(
                f"Verificación MFA - "
                f"Secreto: {secret[:4]}...{secret[-4:]}, "
                f"Código: {code}, "
                f"Válido: {is_valid}, "
                f"Ventana: ±{window * 30} segundos"
            )

            return is_valid
        except Exception as e:
            logger.error(f"Error en verify_code: {str(e)}")
            return False

    def create_mfa_config(self, secret: str) -> MFAConfig:
        """Crea una nueva configuración MFA"""
        return MFAConfig(
            secret=secret,
            enabled=True,
            backup_codes=[],
            last_used_at=datetime.now(timezone.utc),
        )
