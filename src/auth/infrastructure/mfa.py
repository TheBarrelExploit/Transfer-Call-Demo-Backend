import pyotp
import qrcode
from io import BytesIO
import base64

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
    def verify_code(secret: str, code: str) -> bool:
        """Verifica si el código proporcionado es válido"""
        totp = pyotp.TOTP(secret)
        return totp.verify(code, valid_window=1)  # Permite 1 código anterior/siguiente