"""Authentik OIDC token validation

This module provides token validation for Authentik-issued JWT tokens.
Supports both online validation (JWKS) and offline validation (cached keys).
"""

from typing import Optional, Dict, Any
from fastapi import HTTPException, status
from jose import jwt, JWTError
import requests
from functools import lru_cache
from datetime import datetime, timedelta
import logging

from config.settings import settings

logger = logging.getLogger(__name__)


class AuthentikTokenValidator:
    """Validates Authentik-issued JWT tokens using JWKS"""
    
    def __init__(self):
        self.issuer = settings.authentik_url
        self.client_id = settings.authentik_client_id
        self._jwks_cache: Optional[Dict] = None
        self._jwks_cache_time: Optional[datetime] = None
        self._cache_ttl = timedelta(hours=1)
        
        # Validate configuration
        if not self.issuer or not self.client_id:
            logger.warning(
                "Authentik not configured. Set AUTHENTIK_URL and AUTHENTIK_CLIENT_ID "
                "environment variables to enable OIDC authentication."
            )
    
    def is_configured(self) -> bool:
        """Check if Authentik is properly configured"""
        return bool(self.issuer and self.client_id)
    
    def _get_jwks(self) -> Dict:
        """
        Fetch JWKS from Authentik, with caching
        
        Returns:
            JWKS dictionary
            
        Raises:
            HTTPException: If JWKS cannot be fetched
        """
        now = datetime.utcnow()
        
        # Return cached JWKS if still valid
        if self._jwks_cache and self._jwks_cache_time:
            if now - self._jwks_cache_time < self._cache_ttl:
                logger.debug("Using cached JWKS")
                return self._jwks_cache
        
        try:
            # Fetch fresh JWKS from Authentik
            # The well-known JWKS URL for Authentik
            jwks_url = f"{self.issuer}/application/o/{self.client_id}/.well-known/jwks.json"
            
            logger.info(f"Fetching JWKS from {jwks_url}")
            response = requests.get(jwks_url, timeout=10)
            response.raise_for_status()
            
            jwks = response.json()
            
            # Cache the JWKS
            self._jwks_cache = jwks
            self._jwks_cache_time = now
            
            logger.info("Successfully fetched and cached JWKS")
            return jwks
            
        except requests.exceptions.RequestException as e:
            logger.error(f"Failed to fetch JWKS: {str(e)}")
            raise HTTPException(
                status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
                detail=f"Unable to fetch identity provider keys: {str(e)}",
            )
    
    def validate_token(self, token: str) -> Dict[str, Any]:
        """
        Validate Authentik JWT token and return claims
        
        Args:
            token: JWT token from Authorization header
            
        Returns:
            Dict with user claims including:
                - sub: User UUID
                - email: User email
                - name: User full name
                - preferred_username: Username
                - groups: List of user groups
                
        Raises:
            HTTPException: If token is invalid
        """
        if not self.is_configured():
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Authentik authentication is not configured",
            )
        
        try:
            # Get JWKS for token validation
            jwks = self._get_jwks()
            
            # Decode and validate token
            claims = jwt.decode(
                token,
                jwks,
                algorithms=["RS256"],
                audience=self.client_id,
                issuer=self.issuer,
                options={
                    "verify_signature": True,
                    "verify_aud": True,
                    "verify_iat": True,
                    "verify_exp": True,
                    "verify_nbf": True,
                    "verify_iss": True,
                }
            )
            
            logger.info(f"Successfully validated token for user {claims.get('sub')}")
            return claims
            
        except JWTError as e:
            logger.warning(f"Token validation failed: {str(e)}")
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail=f"Invalid token: {str(e)}",
                headers={"WWW-Authenticate": "Bearer"},
            )
        except Exception as e:
            logger.error(f"Unexpected error during token validation: {str(e)}")
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=f"Token validation error: {str(e)}",
            )
    
    def extract_user_info(self, claims: Dict[str, Any]) -> Dict[str, Any]:
        """
        Extract standardized user information from token claims
        
        Args:
            claims: JWT token claims
            
        Returns:
            Standardized user information dict
        """
        return {
            "id": claims.get("sub"),
            "email": claims.get("email"),
            "username": claims.get("preferred_username"),
            "first_name": claims.get("given_name", ""),
            "last_name": claims.get("family_name", ""),
            "full_name": claims.get("name", ""),
            "groups": claims.get("groups", []),
            "is_admin": "admins" in claims.get("groups", []),
        }


# Global instance (initialized when settings are loaded)
authentik_validator = AuthentikTokenValidator()
