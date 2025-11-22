"""
JWT authentication service with role-based access control.

Provides secure token generation, validation, and user authentication.
"""

import os
from datetime import datetime, timedelta
from typing import Optional
from jose import JWTError, jwt
from passlib.context import CryptContext
from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncSession

from .models import TokenData, UserInDB
from ..database import get_db

# Security configuration
SECRET_KEY = os.getenv("JWT_SECRET_KEY", "your-secret-key-change-in-production")
ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_MINUTES = int(os.getenv("JWT_EXPIRATION_MINUTES", "60"))

# Password hashing
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

# Bearer token security
security = HTTPBearer()


class AuthService:
    """JWT authentication service."""

    @staticmethod
    def verify_password(plain_password: str, hashed_password: str) -> bool:
        """Verify plain password against hashed password."""
        return pwd_context.verify(plain_password, hashed_password)

    @staticmethod
    def get_password_hash(password: str) -> str:
        """Hash a password using bcrypt."""
        return pwd_context.hash(password)

    @staticmethod
    def create_access_token(
        data: dict,
        expires_delta: Optional[timedelta] = None
    ) -> str:
        """
        Create JWT access token.

        Args:
            data: Payload to encode (must include 'sub' for user ID)
            expires_delta: Token expiration time (default: ACCESS_TOKEN_EXPIRE_MINUTES)

        Returns:
            Encoded JWT token string
        """
        to_encode = data.copy()

        if expires_delta:
            expire = datetime.utcnow() + expires_delta
        else:
            expire = datetime.utcnow() + timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)

        to_encode.update({
            "exp": expire,
            "iat": datetime.utcnow(),
            "type": "access"
        })

        encoded_jwt = jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)
        return encoded_jwt

    @staticmethod
    def decode_token(token: str) -> TokenData:
        """
        Decode and validate JWT token.

        Args:
            token: JWT token string

        Returns:
            TokenData with decoded payload

        Raises:
            HTTPException: If token is invalid or expired
        """
        credentials_exception = HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Could not validate credentials",
            headers={"WWW-Authenticate": "Bearer"},
        )

        try:
            payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
            user_id: str = payload.get("sub")

            if user_id is None:
                raise credentials_exception

            token_data = TokenData(
                user_id=user_id,
                username=payload.get("username"),
                role=payload.get("role"),
                telegram_id=payload.get("telegram_id")
            )

            return token_data

        except JWTError:
            raise credentials_exception

    @staticmethod
    async def authenticate_user(
        db: AsyncSession,
        username: str,
        password: str
    ) -> Optional[UserInDB]:
        """
        Authenticate user by username and password.

        Args:
            db: Database session
            username: Username or telegram_id
            password: Plain text password

        Returns:
            UserInDB if authentication successful, None otherwise
        """
        # Query user by username
        query = text("""
            SELECT id, telegram_id, first_name, last_name, username,
                   role, age_group, language_preference,
                   hashed_password, is_active
            FROM family_members
            WHERE username = :username
            LIMIT 1
        """)

        result = await db.execute(query, {"username": username})
        row = result.fetchone()

        if not row:
            return None

        user_dict = {
            "id": str(row[0]),
            "telegram_id": row[1],
            "first_name": row[2],
            "last_name": row[3],
            "username": row[4],
            "role": row[5],
            "age_group": row[6],
            "language_preference": row[7],
            "hashed_password": row[8],
            "is_active": bool(row[9]) if row[9] is not None else True
        }

        user = UserInDB(**user_dict)

        # Verify password
        if not user.hashed_password:
            return None

        if not AuthService.verify_password(password, user.hashed_password):
            return None

        return user


async def get_current_user(
    credentials: HTTPAuthorizationCredentials = Depends(security),
    db: AsyncSession = Depends(get_db)
) -> UserInDB:
    """
    Get current authenticated user from JWT token.

    Dependency for protected routes requiring authentication.

    Args:
        credentials: HTTP bearer token
        db: Database session

    Returns:
        Current authenticated user

    Raises:
        HTTPException: If token invalid or user not found
    """
    token = credentials.credentials
    token_data = AuthService.decode_token(token)

    # Query user from database
    query = text("""
        SELECT id, telegram_id, first_name, last_name, username,
               role, age_group, language_preference, is_active
        FROM family_members
        WHERE id = :user_id
        LIMIT 1
    """)

    result = await db.execute(query, {"user_id": token_data.user_id})
    row = result.fetchone()

    if not row:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="User not found",
            headers={"WWW-Authenticate": "Bearer"},
        )

    user_dict = {
        "id": str(row[0]),
        "telegram_id": row[1],
        "first_name": row[2],
        "last_name": row[3],
        "username": row[4],
        "role": row[5],
        "age_group": row[6],
        "language_preference": row[7],
        "is_active": bool(row[8]) if row[8] is not None else True
    }

    return UserInDB(**user_dict)


async def get_current_active_user(
    current_user: UserInDB = Depends(get_current_user)
) -> UserInDB:
    """
    Get current active user (not disabled).

    Dependency for routes requiring active user account.

    Args:
        current_user: Current authenticated user

    Returns:
        Current active user

    Raises:
        HTTPException: If user is inactive
    """
    if not current_user.is_active:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Inactive user"
        )

    return current_user


def require_role(*allowed_roles: str):
    """
    Create dependency to require specific role(s).

    Usage:
        @app.get("/admin", dependencies=[Depends(require_role("parent"))])

    Args:
        allowed_roles: One or more allowed role names

    Returns:
        Dependency function for FastAPI
    """
    async def role_checker(
        current_user: UserInDB = Depends(get_current_active_user)
    ) -> UserInDB:
        if current_user.role not in allowed_roles:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail=f"Role '{current_user.role}' not authorized. Required: {', '.join(allowed_roles)}"
            )
        return current_user

    return role_checker
