"""
Keycloak OAuth2 Authentication Service
"""
from fastapi import Depends, HTTPException, status
from fastapi.security import OAuth2AuthorizationCodeBearer
from jose import jwt, JWTError
from typing import Optional, Dict
import httpx
import logging
from app.core.config import settings

logger = logging.getLogger(__name__)

oauth2_scheme = OAuth2AuthorizationCodeBearer(
    authorizationUrl=f"{settings.KEYCLOAK_SERVER_URL}/realms/{settings.KEYCLOAK_REALM}/protocol/openid-connect/auth",
    tokenUrl=f"{settings.KEYCLOAK_SERVER_URL}/realms/{settings.KEYCLOAK_REALM}/protocol/openid-connect/token",
)

class KeycloakAuth:
    def __init__(self):
        self.server_url = settings.KEYCLOAK_SERVER_URL
        self.realm = settings.KEYCLOAK_REALM
        self.client_id = settings.KEYCLOAK_CLIENT_ID
        self.client_secret = settings.KEYCLOAK_CLIENT_SECRET
        self._public_key = None
    
    async def get_public_key(self) -> str:
        """Fetch Keycloak public key for token verification"""
        if self._public_key:
            return self._public_key
        
        try:
            url = f"{self.server_url}/realms/{self.realm}"
            async with httpx.AsyncClient() as client:
                response = await client.get(url)
                response.raise_for_status()
                realm_info = response.json()
                self._public_key = realm_info.get("public_key")
                return self._public_key
        except Exception as e:
            logger.error(f"Failed to fetch Keycloak public key: {e}")
            raise HTTPException(
                status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
                detail="Authentication service unavailable"
            )
    
    async def verify_token(self, token: str) -> Dict:
        """Verify JWT token from Keycloak"""
        try:
            public_key = await self.get_public_key()
            public_key_formatted = f"-----BEGIN PUBLIC KEY-----\n{public_key}\n-----END PUBLIC KEY-----"
            
            payload = jwt.decode(
                token,
                public_key_formatted,
                algorithms=["RS256"],
                audience=self.client_id,
                options={"verify_aud": False}  # Set to True in production
            )
            return payload
        except JWTError as e:
            logger.error(f"Token verification failed: {e}")
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid authentication credentials",
                headers={"WWW-Authenticate": "Bearer"},
            )
    
    async def get_current_user(self, token: str = Depends(oauth2_scheme)) -> Dict:
        """Get current authenticated user from token"""
        payload = await self.verify_token(token)
        username = payload.get("preferred_username")
        if username is None:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Could not validate credentials"
            )
        return {
            "username": username,
            "email": payload.get("email"),
            "roles": payload.get("realm_access", {}).get("roles", [])
        }

keycloak_auth = KeycloakAuth()

async def get_current_user(token: str = Depends(oauth2_scheme)) -> Dict:
    """Dependency for protected routes"""
    return await keycloak_auth.get_current_user(token)
