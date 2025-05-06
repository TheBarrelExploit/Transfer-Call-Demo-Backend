import httpx
import json
from msal import ConfidentialClientApplication
from typing import Dict, Any, Optional
from src.auth.domain.ports_sso import AuthLoginSSO
from src.shared.config import get_settings

settings = get_settings()

class MicrosoftSSORepository(AuthLoginSSO):

    def __init__(self):
        self.client_id = settings.MICROSOFT_CLIENT_ID
        self.client_secret = settings.MICROSOFT_CLIENT_SECRET
        self.tenant_id = settings.MICROSOFT_TENANT_ID
        self.redirect_uri = settings.MICROSOFT_REDIRECT_URI
        self.authority = f"https://login.microsoftonline.com/{self.tenant_id}"
        self.scope = ["User.Read"]

        self.app = ConfidentialClientApplication(
            client_id= self.client_id,
            client_credential=self.client_secret,
            authority=self.authority
        )
    
    def get_auth_url(self) -> str:
        auth_url = self.app.get_authorization_request_url(
            scopes=self.scope,
            redirect_uri=self.redirect_uri,
            state=json.dumps({"state":"some-state"}),
            prompt="select_account"
        )

        return auth_url
    
    async def get_token_from_code(self, code:str) -> Dict[str, Any]:
        result = self.app.acquire_token_by_authorization_code(
            code = code,
            scopes = self.scope,
            redirect_uri=self.redirect_uri
        )

        if not result:
            raise Exception(f"Error al obtener el token: {result.get("error_description")}")
        
        return result
    
    async def get_user_info(self, access_token: str) -> Dict[str, Any]:
        headers = {
            "Authorization": f"Bearer {access_token}",
            "Content-Type":"application/json"
        }

        async with httpx.AsyncClient() as client:
            response = await client.get(
                "https://graph.microsoft.com/v1.0/me",
                headers=headers
            )

            if response.status_code != 200:
                raise Exception(f"Error al obtener la informacion del usuario")
            
            user_data = response.json()

            return { 
                "microsoft_id": user_data.get("id"),
                "email": user_data.get("mail") or user_data.get("userPrincipalName"),
                "name": user_data.get("displayName", ""),
                "raw_data": user_data
            }

        





