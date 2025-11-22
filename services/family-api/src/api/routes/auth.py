"""
Authentication routes for Family Assistant API.

Provides login, token refresh, and user profile endpoints.
"""

from datetime import timedelta
from typing import Annotated
from fastapi import APIRouter, Depends, HTTPException, status, Request
from fastapi.security import OAuth2PasswordBearer, OAuth2PasswordRequestForm
from sqlalchemy.ext.asyncio import AsyncSession
from pydantic import BaseModel

from ..auth.jwt import (
    AuthService,
    get_current_active_user,
    ACCESS_TOKEN_EXPIRE_MINUTES
)
from ..auth.models import Token, UserInDB
from ..database import get_db
from ..middleware.rate_limit import limiter, auth_rate_limit
from ..observability.metrics import track_auth_attempt, track_token_validation
from ..observability.logging import get_logger

logger = get_logger(__name__)

router = APIRouter(prefix="/auth", tags=["authentication"])

oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/api/v1/auth/login")


class LoginRequest(BaseModel):
    """Login request body."""
    username: str
    password: str


class UserResponse(BaseModel):
    """User profile response."""
    id: str
    telegram_id: int | None
    first_name: str
    last_name: str | None
    username: str | None
    role: str
    age_group: str | None
    language_preference: str
    is_active: bool

    class Config:
        from_attributes = True


@router.post("/login", response_model=Token)
@limiter.limit("5/minute")  # Strict rate limit for login attempts
async def login(
    request: Request,
    form_data: Annotated[OAuth2PasswordRequestForm, Depends()],
    db: AsyncSession = Depends(get_db)
):
    """
    Authenticate user and return JWT access token.

    This endpoint accepts OAuth2 password flow (form data):
    - username: Username or telegram ID
    - password: User password

    Returns JWT token with user information embedded.

    Raises:
        401: Invalid credentials
    """
    user = await AuthService.authenticate_user(
        db,
        form_data.username,
        form_data.password
    )

    if not user:
        logger.warning(
            "Failed login attempt",
            extra={"username": form_data.username, "ip": request.client.host}
        )
        track_auth_attempt(success=False)
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect username or password",
            headers={"WWW-Authenticate": "Bearer"},
        )

    if not user.is_active:
        logger.warning(
            "Login attempt for inactive user",
            extra={"username": form_data.username, "user_id": user.id}
        )
        track_auth_attempt(success=False)
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="User account is inactive"
        )

    # Create access token
    access_token_expires = timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
    access_token = AuthService.create_access_token(
        data={
            "sub": user.id,
            "username": user.username,
            "role": user.role,
            "telegram_id": user.telegram_id
        },
        expires_delta=access_token_expires
    )

    logger.info(
        "Successful login",
        extra={"user_id": user.id, "username": user.username, "role": user.role}
    )
    track_auth_attempt(success=True)

    return Token(
        access_token=access_token,
        token_type="bearer",
        expires_in=ACCESS_TOKEN_EXPIRE_MINUTES * 60  # seconds
    )


@router.post("/login/json", response_model=Token)
@limiter.limit("5/minute")  # Strict rate limit for login attempts
async def login_json(
    request: Request,
    login_data: LoginRequest,
    db: AsyncSession = Depends(get_db)
):
    """
    Authenticate user with JSON request body.

    Alternative to OAuth2 password flow for clients that prefer JSON.

    Body:
    ```json
    {
      "username": "string",
      "password": "string"
    }
    ```

    Returns JWT token with user information embedded.

    Raises:
        401: Invalid credentials
    """
    user = await AuthService.authenticate_user(
        db,
        login_data.username,
        login_data.password
    )

    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect username or password",
            headers={"WWW-Authenticate": "Bearer"},
        )

    if not user.is_active:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="User account is inactive"
        )

    # Create access token
    access_token_expires = timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
    access_token = AuthService.create_access_token(
        data={
            "sub": user.id,
            "username": user.username,
            "role": user.role,
            "telegram_id": user.telegram_id
        },
        expires_delta=access_token_expires
    )

    return Token(
        access_token=access_token,
        token_type="bearer",
        expires_in=ACCESS_TOKEN_EXPIRE_MINUTES * 60
    )


@router.get("/me", response_model=UserResponse)
async def get_current_user_profile(
    current_user: UserInDB = Depends(get_current_active_user)
):
    """
    Get current authenticated user's profile.

    Requires valid JWT token in Authorization header:
    ```
    Authorization: Bearer <token>
    ```

    Returns user profile information.

    Raises:
        401: Invalid or missing token
        403: User account is inactive
    """
    return UserResponse(
        id=current_user.id,
        telegram_id=current_user.telegram_id,
        first_name=current_user.first_name,
        last_name=current_user.last_name,
        username=current_user.username,
        role=current_user.role,
        age_group=current_user.age_group,
        language_preference=current_user.language_preference,
        is_active=current_user.is_active
    )


@router.post("/verify", response_model=dict)
async def verify_token(
    request: Request,
    current_user: UserInDB = Depends(get_current_active_user)
):
    """
    Verify JWT token validity.

    Requires valid JWT token in Authorization header.

    Returns:
    ```json
    {
      "valid": true,
      "user_id": "uuid",
      "role": "string"
    }
    ```

    Raises:
        401: Invalid or expired token
    """
    track_token_validation(valid=True)
    logger.debug(
        "Token validated",
        extra={"user_id": current_user.id, "role": current_user.role}
    )

    return {
        "valid": True,
        "user_id": current_user.id,
        "role": current_user.role,
        "username": current_user.username
    }
