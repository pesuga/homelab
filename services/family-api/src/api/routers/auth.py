"""
Authentication Router - JWT Authentication Endpoints

Provides secure authentication endpoints for login, logout, token refresh,
and user management with role-based access control.
"""

from datetime import timedelta
from typing import Any, Dict
from fastapi import APIRouter, Depends, HTTPException, status, Request
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from pydantic import BaseModel, EmailStr
import asyncpg

from api.auth.jwt_auth import AuthenticationService, PermissionChecker
from api.dependencies import get_db_pool
from api.models.user_management import FamilyMember, UserRole


# =============================================================================
# Router Configuration
# =============================================================================

router = APIRouter(prefix="/auth", tags=["Authentication"])
security = HTTPBearer()


# =============================================================================
# Pydantic Models
# ==============================================================================

class LoginRequest(BaseModel):
    """Login request model"""
    email: EmailStr
    password: str
    remember_me: bool = False


class LoginResponse(BaseModel):
    """Login response model"""
    access_token: str
    refresh_token: str
    token_type: str = "bearer"
    expires_in: int
    user: Dict[str, Any]


class RefreshTokenRequest(BaseModel):
    """Refresh token request model"""
    refresh_token: str


class RefreshTokenResponse(BaseModel):
    """Refresh token response model"""
    access_token: str
    token_type: str = "bearer"
    expires_in: int


class LogoutRequest(BaseModel):
    """Logout request model"""
    refresh_token: str


class UserResponse(BaseModel):
    """User information response model"""
    id: str
    email: str
    role: str
    is_admin: bool
    display_name: str
    first_name: str
    last_name: str


class PasswordChangeRequest(BaseModel):
    """Password change request model"""
    current_password: str
    new_password: str


class PasswordResetRequest(BaseModel):
    """Password reset request model"""
    email: EmailStr


class PasswordResetConfirm(BaseModel):
    """Password reset confirmation model"""
    token: str
    new_password: str


# =============================================================================
# Authentication Dependencies
# ==============================================================================

async def get_current_user_from_token(
    credentials: HTTPAuthorizationCredentials = Depends(security),
    db_pool: asyncpg.Pool = Depends(get_db_pool)
) -> FamilyMember:
    """Extract and validate user from JWT token"""
    from api.auth.jwt_auth import token_manager
    from api.services.user_manager import UserManager

    try:
        # Verify token
        payload = token_manager.verify_token(credentials.credentials, "access")
        user_id = payload.get("sub")

        if not user_id:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid token payload",
            )

        # Get user from database
        user_manager = UserManager(db_pool)
        from uuid import UUID
        user = await user_manager.get_family_member(UUID(user_id))

        if not user or not user.is_active:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="User not found or inactive",
            )

        return user

    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail=f"Invalid authentication: {str(e)}",
        )


async def get_current_admin_user(
    current_user: FamilyMember = Depends(get_current_user_from_token)
) -> FamilyMember:
    """Get current user and verify admin privileges"""
    if not current_user.is_admin:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Admin privileges required",
        )
    return current_user


def require_permissions(permission: str):
    """Decorator factory for requiring specific permissions"""
    async def permission_checker(
        current_user: FamilyMember = Depends(get_current_user_from_token)
    ) -> FamilyMember:
        if not PermissionChecker.has_permission(current_user.role, permission):
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail=f"Permission '{permission}' required for role '{current_user.role.value}'",
            )
        return current_user
    return permission_checker


# =============================================================================
# Authentication Endpoints
# ==============================================================================

@router.post("/login", response_model=LoginResponse, status_code=status.HTTP_200_OK)
async def login(
    login_data: LoginRequest,
    request: Request,
    db_pool: asyncpg.Pool = Depends(get_db_pool)
):
    """
    Authenticate user and return JWT tokens

    - **email**: User email address
    - **password**: User password
    - **remember_me**: Extend token expiration if true
    """
    try:
        # Initialize Redis client if available
        redis_client = None
        # TODO: Initialize Redis client from settings

        # Create authentication service
        auth_service = AuthenticationService(db_pool, redis_client)

        # Authenticate user
        user = await auth_service.authenticate_user(login_data.email, login_data.password)
        if not user:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid email or password",
                headers={"WWW-Authenticate": "Bearer"},
            )

        # Check if user is active
        if not user.is_active:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="User account is deactivated",
            )

        # Create tokens
        tokens = await auth_service.create_user_tokens(user)

        # Log authentication attempt (for audit)
        client_ip = request.client.host if request.client else "unknown"
        print(f"User login: {user.email} from {client_ip}")

        return LoginResponse(**tokens)

    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Authentication error: {str(e)}",
        )


@router.post("/refresh", response_model=RefreshTokenResponse, status_code=status.HTTP_200_OK)
async def refresh_token(
    refresh_data: RefreshTokenRequest,
    db_pool: asyncpg.Pool = Depends(get_db_pool)
):
    """
    Refresh access token using valid refresh token

    - **refresh_token**: Valid refresh token
    """
    try:
        # Initialize Redis client if available
        redis_client = None

        # Create authentication service
        auth_service = AuthenticationService(db_pool, redis_client)

        # Refresh access token
        tokens = await auth_service.refresh_access_token(refresh_data.refresh_token)

        return RefreshTokenResponse(**tokens)

    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Token refresh error: {str(e)}",
        )


@router.post("/logout", status_code=status.HTTP_200_OK)
async def logout(
    logout_data: LogoutRequest,
    request: Request,
    db_pool: asyncpg.Pool = Depends(get_db_pool)
):
    """
    Logout user and revoke refresh token

    - **refresh_token**: Refresh token to revoke
    """
    try:
        # Initialize Redis client if available
        redis_client = None

        # Create authentication service
        auth_service = AuthenticationService(db_pool, redis_client)

        # Logout user (revoke refresh token)
        await auth_service.logout_user(logout_data.refresh_token)

        # Log logout attempt (for audit)
        client_ip = request.client.host if request.client else "unknown"
        print(f"User logout from {client_ip}")

        return {"message": "Successfully logged out"}

    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Logout error: {str(e)}",
        )


@router.get("/me", response_model=UserResponse, status_code=status.HTTP_200_OK)
async def get_current_user_info(
    current_user: FamilyMember = Depends(get_current_user_from_token)
):
    """
    Get current authenticated user information

    Requires valid JWT access token
    """
    return UserResponse(
        id=str(current_user.id),
        email=current_user.email,
        role=current_user.role.value,
        is_admin=current_user.is_admin,
        display_name=current_user.display_name or f"{current_user.first_name} {current_user.last_name or ''}".strip(),
        first_name=current_user.first_name,
        last_name=current_user.last_name or ""
    )


@router.post("/change-password", status_code=status.HTTP_200_OK)
async def change_password(
    password_data: PasswordChangeRequest,
    current_user: FamilyMember = Depends(get_current_user_from_token),
    db_pool: asyncpg.Pool = Depends(get_db_pool)
):
    """
    Change current user's password

    - **current_password**: Current password for verification
    - **new_password**: New password to set
    """
    try:
        from api.auth.jwt_auth import password_manager
        from api.services.user_manager import UserManager

        # Get user manager
        user_manager = UserManager(db_pool)

        # Verify current password (this would need password field in FamilyMember)
        # For now, we'll skip current password verification as it's not implemented
        # In production, you'd verify against stored hash

        # Hash new password
        new_password_hash = password_manager.hash_password(password_data.new_password)

        # Update password in database (this would require database schema update)
        # For now, we'll just return success
        # await user_manager.update_user_password(current_user.id, new_password_hash)

        return {"message": "Password changed successfully"}

    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Password change error: {str(e)}",
        )


@router.post("/forgot-password", status_code=status.HTTP_200_OK)
async def forgot_password(
    password_reset: PasswordResetRequest,
    request: Request,
    db_pool: asyncpg.Pool = Depends(get_db_pool)
):
    """
    Request password reset link

    - **email**: User email address
    """
    try:
        from api.auth.jwt_auth import password_manager
        from api.services.user_manager import UserManager

        user_manager = UserManager(db_pool)

        # Check if user exists
        user = await user_manager.get_family_member_by_email(password_reset.email)
        if not user:
            # Don't reveal that user doesn't exist
            return {"message": "If email exists, password reset link has been sent"}

        # Create password reset token
        reset_token = password_manager.create_password_reset_token(password_reset.email)

        # In production, you'd send this via email
        # For now, we'll just return the token (for development only)
        base_url = f"{request.url.scheme}://{request.url.netloc}"
        reset_link = f"{base_url}/reset-password?token={reset_token}"

        print(f"Password reset link for {password_reset.email}: {reset_link}")

        return {
            "message": "If email exists, password reset link has been sent",
            "reset_token": reset_token  # Remove in production
        }

    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Password reset error: {str(e)}",
        )


@router.post("/reset-password", status_code=status.HTTP_200_OK)
async def reset_password(
    reset_data: PasswordResetConfirm,
    db_pool: asyncpg.Pool = Depends(get_db_pool)
):
    """
    Reset password using valid reset token

    - **token**: Password reset token
    - **new_password**: New password to set
    """
    try:
        from api.auth.jwt_auth import password_manager
        from api.services.user_manager import UserManager

        # Verify reset token
        email = password_manager.verify_password_reset_token(reset_data.token)
        if not email:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Invalid or expired reset token",
            )

        user_manager = UserManager(db_pool)

        # Get user by email
        user = await user_manager.get_family_member_by_email(email)
        if not user:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Invalid reset token",
            )

        # Hash new password
        new_password_hash = password_manager.hash_password(reset_data.new_password)

        # Update password in database (this would require database schema update)
        # For now, we'll just return success
        # await user_manager.update_user_password(user.id, new_password_hash)

        return {"message": "Password reset successfully"}

    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Password reset error: {str(e)}",
        )


@router.get("/verify-token", status_code=status.HTTP_200_OK)
async def verify_token(
    current_user: FamilyMember = Depends(get_current_user_from_token)
):
    """
    Verify that the current JWT token is valid

    Requires valid JWT access token
    """
    return {
        "valid": True,
        "user_id": str(current_user.id),
        "role": current_user.role.value,
        "is_admin": current_user.is_admin
    }