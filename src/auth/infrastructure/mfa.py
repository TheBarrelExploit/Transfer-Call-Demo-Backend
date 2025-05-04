import pyotp
import qrcode
from io import BytesIO
import base64
import time
import logging

logger = logging.getLogger(__name__)

class MFAService:
    @staticmethod
    def generate_secret() -> str:
        """Genera un secreto aleatorio para MFA"""
        return pyotp.random_base32()
    
    @staticmethod
    def get_totp_uri(username: str, secret: str) -> str:
        """Genera la URI para el QR code"""
        return pyotp.totp.TOTP(secret).provisioning_uri(
            name=username, 
            issuer_name="Transfer-Call-Demo"
        )
    
    @staticmethod
    def generate_qr_code(uri: str) -> str:
        """Genera un QR code en base64 para mostrarlo al usuario"""
        img = qrcode.make(uri)
        buffered = BytesIO()
        img.save(buffered, format="PNG")
        return f"data:image/png;base64,{base64.b64encode(buffered.getvalue()).decode()}"
    
    @staticmethod
    def verify_code(secret: str, code: str, window: int = 1) -> bool:
        """Verificación mejorada con logs detallados"""
        try:
            totp = pyotp.TOTP(secret)
            current_time = int(time.time())
            time_remaining = 30 - (current_time % 30)
            
            logger.info(f"Verificando código - Secreto: {secret}")
            logger.info(f"Código recibido: {code} | Esperado: {totp.now()}")
            logger.info(f"Tiempo restante: {time_remaining}s")
            
            # Verificación con ventana de tiempo
            return totp.verify(code, valid_window=window)
            
        except Exception as e:
            logger.error(f"Error en verify_code: {str(e)}")
            return False