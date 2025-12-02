"""
Authentication data models.
"""

from typing import Optional
from pydantic import BaseModel


class Token(BaseModel):
    """JWT access token response."""
    access_token: str
    token_type: str = "bearer"
    expires_in: int  # seconds


class TokenData(BaseModel):
    """Decoded JWT token data."""
    user_id: Optional[str] = None
    username: Optional[str] = None
    role: Optional[str] = None
    telegram_id: Optional[int] = None


class UserInDB(BaseModel):
    """User data from database."""
    id: str
    telegram_id: Optional[int] = None
    first_name: str
    last_name: Optional[str] = None
    username: Optional[str] = None
    role: str
    age_group: Optional[str] = None
    language_preference: str = "en"
    hashed_password: Optional[str] = None
    is_active: bool = True

    class Config:
        from_attributes = True
