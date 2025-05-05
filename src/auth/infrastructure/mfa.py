import pyotp
import qrcode
from io import BytesIO
import base64
import time
import logging
from datetime import datetime

logger = logging.getLogger(__name__)

class MFAService:
    @staticmethod
    def generate_secret() -> str:
        """Genera un secreto compatible con Google Authenticator"""
        return pyotp.random_base32(length=32)  # Longitud estándar para GA
    
    @staticmethod
    def get_totp_uri(username: str, secret: str) -> str:
        """Genera URI compatible con estándares"""
        return pyotp.totp.TOTP(
            secret,
            interval=30,  # 30 segundos (estándar)
            digits=6,     # 6 dígitos (estándar)
            issuer="Transfer-Call-Demo"
        ).provisioning_uri(name=username)
    
    @staticmethod
    def generate_qr_code(uri: str) -> str:
        """Genera QR code con configuración estándar"""
        try:
            # Configuración compatible con la mayoría de apps
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
    
    @staticmethod
    def verify_code(secret: str, code: str, window: int = 3) -> bool:
        """Verificación con ventana ampliada y logging detallado"""
        try:
            totp = pyotp.TOTP(
                secret,
                interval=30,
                digits=6
            )
            
            current_time = time.time()
            is_valid = totp.verify(code, valid_window=window)
            
            logger.info(
                f"Verificación MFA - "
                f"Secreto: {secret[:4]}...{secret[-4:]}, "
                f"Código: {code}, "
                f"Válido: {is_valid}, "
                f"Tiempo: {datetime.fromtimestamp(current_time)}, "
                f"Ventana: ±{window*30} segundos"
            )
            
            return is_valid
        except Exception as e:
            logger.error(f"Error en verify_code: {str(e)}")
            return False