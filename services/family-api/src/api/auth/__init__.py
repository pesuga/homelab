"""
Authentication module for Family Assistant.

Provides JWT-based authentication with role-based access control (RBAC).
"""

from .jwt import AuthService, get_current_user, get_current_active_user
from .models import Token, TokenData, UserInDB

__all__ = [
    "AuthService",
    "get_current_user",
    "get_current_active_user",
    "Token",
    "TokenData",
    "UserInDB",
]
