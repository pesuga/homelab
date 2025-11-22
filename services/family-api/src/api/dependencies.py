"""
FastAPI Dependencies - Phase 3 (Updated with JWT Authentication)

Dependency injection for JWT authentication, database, and services.
Replaces insecure header-based authentication with production-ready JWT system.
"""

from typing import Optional
from fastapi import Depends, HTTPException, Header, status
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
import asyncpg

from config.settings import settings
from api.models.user_management import FamilyMember, UserRole
from api.services.user_manager import UserManager


# =============================================================================
# Database Dependencies
# ==============================================================================

_db_pool: Optional[asyncpg.Pool] = None


async def init_db_pool():
    """Initialize database connection pool"""
    global _db_pool
    if _db_pool is None:
        _db_pool = await asyncpg.create_pool(
            host=settings.postgres_host,
            port=settings.postgres_port,
            user=settings.postgres_user,
            password=settings.postgres_password,
            database=settings.postgres_db,
            min_size=5,
            max_size=20,
        )
    return _db_pool


async def close_db_pool():
    """Close database connection pool"""
    global _db_pool
    if _db_pool:
        await _db_pool.close()
        _db_pool = None


async def get_db_pool() -> asyncpg.Pool:
    """Get database connection pool"""
    if _db_pool is None:
        await init_db_pool()
    return _db_pool


# =============================================================================
# JWT Authentication Dependencies (Production Ready)
# ==============================================================================

# HTTP Bearer for JWT tokens
security = HTTPBearer()


async def get_current_user_from_token(
    credentials: HTTPAuthorizationCredentials = Depends(security),
    db_pool: asyncpg.Pool = Depends(get_db_pool)
) -> FamilyMember:
    """
    Extract and validate user from JWT access token

    This is the production-ready JWT authentication that replaces
    the insecure header-based authentication system.
    """
    from api.auth.jwt_auth import token_manager
    from api.services.user_manager import UserManager

    try:
        # Verify JWT token
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

    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail=f"Invalid authentication: {str(e)}",
        )


async def get_current_user_from_authentik(
    credentials: HTTPAuthorizationCredentials = Depends(security),
    db_pool: asyncpg.Pool = Depends(get_db_pool)
) -> FamilyMember:
    """
    Extract and validate user from Authentik OIDC JWT token
    
    This dependency validates tokens issued by Authentik SSO and
    auto-provisions users if they don't exist in the database.
    """
    from api.auth.authentik import authentik_validator
    from api.services.user_manager import UserManager
    
    try:
        # Validate token with Authentik
        claims = authentik_validator.validate_token(credentials.credentials)
        
        # Extract user info from claims
        email = claims.get("email")
        if not email:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Email claim missing from token"
            )
        
        # Get or create user in database
        user_manager = UserManager(db_pool)
        user = await user_manager.get_family_member_by_email(email)
        
        if not user:
            # Auto-provision user from Authentik claims
            user_info = authentik_validator.extract_user_info(claims)
            
            # Create new user with Authentik data
            from api.models.user_management import UserRole
            from uuid import UUID
            
            user = await user_manager.create_family_member(
                email=email,
                first_name=user_info.get("first_name", ""),
                last_name=user_info.get("last_name", ""),
                role=UserRole.PARENT if user_info.get("is_admin") else UserRole.CHILD,
                is_admin=user_info.get("is_admin", False),
            )
        
        if not user.is_active:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="User account is deactivated"
            )
        
        return user
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail=f"Authentik authentication failed: {str(e)}",
        )


# Legacy authentication for backward compatibility (DEPRECATED)
async def get_current_user(
    x_telegram_user_id: Optional[int] = Header(None, description="Deprecated: Use JWT authentication"),
    x_user_id: Optional[str] = Header(None, description="Deprecated: Use JWT authentication"),
    credentials: Optional[HTTPAuthorizationCredentials] = Depends(security),
    db_pool: asyncpg.Pool = Depends(get_db_pool),
) -> FamilyMember:
    """
    Get current authenticated user

    DEPRECATED: This function now prefers JWT authentication over insecure headers.
    New clients should use JWT tokens from /api/v1/auth/login endpoint.

    Priority order:
    1. JWT Bearer token (production clients)
    2. X-Telegram-User-Id (legacy support)
    3. X-User-Id (legacy support)
    """
    # Try JWT authentication first (preferred method)
    if credentials:
        try:
            return await get_current_user_from_token(credentials, db_pool)
        except HTTPException:
            # JWT failed, continue to legacy methods
            pass

    # Legacy header authentication (for backward compatibility)
    user_mgr = UserManager(db_pool)

    # Try Telegram ID first (legacy)
    if x_telegram_user_id:
        member = await user_mgr.get_family_member_by_telegram_id(x_telegram_user_id)
        if member and member.is_active:
            # Update last active timestamp
            await user_mgr.update_last_active(member.id)
            return member

    # Try user UUID (legacy)
    if x_user_id:
        try:
            from uuid import UUID
            user_uuid = UUID(x_user_id)
            member = await user_mgr.get_family_member(user_uuid)
            if member and member.is_active:
                # Update last active timestamp
                await user_mgr.update_last_active(member.id)
                return member
        except (ValueError, TypeError):
            pass

    # No valid authentication found
    raise HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Authentication required. Provide JWT Bearer token (recommended) or legacy headers.",
        headers={"WWW-Authenticate": "Bearer"},
    )


# =============================================================================
# Role-based Authentication Dependencies
# ==============================================================================

async def get_current_active_user(
    current_user: FamilyMember = Depends(get_current_user_from_token),
) -> FamilyMember:
    """Get current active user (ensures user is not deactivated)"""
    if not current_user.is_active:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="User account is deactivated",
        )
    return current_user


async def get_current_admin_user(
    current_user: FamilyMember = Depends(get_current_user_from_token),
) -> FamilyMember:
    """Get current user and verify admin privileges"""
    if not current_user.is_admin:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Admin privileges required",
        )
    return current_user


async def get_current_parent_user(
    current_user: FamilyMember = Depends(get_current_user_from_token),
) -> FamilyMember:
    """Get current user and verify parent/grandparent role"""
    if current_user.role not in [UserRole.PARENT, UserRole.GRANDPARENT]:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Parent or grandparent role required",
        )
    return current_user


# =============================================================================
# Permission-based Dependencies
# ==============================================================================

def require_permissions(permission: str):
    """
    Dependency factory for requiring specific permissions

    Usage:
    @app.get("/protected-endpoint")
    async def protected_endpoint(
        current_user: FamilyMember = Depends(require_permissions("read:family_data"))
    ):
        # User has required permission
        pass
    """
    async def permission_checker(
        current_user: FamilyMember = Depends(get_current_user_from_token)
    ) -> FamilyMember:
        from api.auth.jwt_auth import PermissionChecker

        if not PermissionChecker.has_permission(current_user.role, permission):
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail=f"Permission '{permission}' required for role '{current_user.role.value}'",
            )
        return current_user
    return permission_checker


def require_resource_access(resource: str, action: str):
    """
    Dependency factory for requiring resource access

    Usage:
    @app.delete("/users/{user_id}")
    async def delete_user(
        current_user: FamilyMember = Depends(require_resource_access("users", "delete"))
    ):
        # User can delete users resource
        pass
    """
    async def resource_checker(
        current_user: FamilyMember = Depends(get_current_user_from_token)
    ) -> FamilyMember:
        from api.auth.jwt_auth import PermissionChecker

        if not PermissionChecker.can_access_resource(current_user, resource, action):
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail=f"Access denied to {action} {resource} for role '{current_user.role.value}'",
            )
        return current_user
    return resource_checker


# =============================================================================
# Optional Authentication (for public endpoints with user context)
# ==============================================================================

async def get_optional_user(
    credentials: Optional[HTTPAuthorizationCredentials] = Depends(HTTPBearer(auto_error=False)),
    x_telegram_user_id: Optional[int] = Header(None),
    x_user_id: Optional[str] = Header(None),
    db_pool: asyncpg.Pool = Depends(get_db_pool),
) -> Optional[FamilyMember]:
    """
    Get user if authentication provided, but don't require it

    Useful for endpoints that work for authenticated users
    but have default behavior for anonymous users.
    """
    if credentials:
        try:
            return await get_current_user_from_token(credentials, db_pool)
        except HTTPException:
            pass

    # Try legacy methods if JWT not provided
    user_mgr = UserManager(db_pool)

    if x_telegram_user_id:
        member = await user_mgr.get_family_member_by_telegram_id(x_telegram_user_id)
        if member and member.is_active:
            await user_mgr.update_last_active(member.id)
            return member

    if x_user_id:
        try:
            from uuid import UUID
            user_uuid = UUID(x_user_id)
            member = await user_mgr.get_family_member(user_uuid)
            if member and member.is_active:
                await user_mgr.update_last_active(member.id)
                return member
        except (ValueError, TypeError):
            pass

    return None


# =============================================================================
# Service Dependencies
# ==============================================================================

async def get_user_manager(db_pool: asyncpg.Pool = Depends(get_db_pool)) -> UserManager:
    """Get user manager service"""
    return UserManager(db_pool)


async def get_content_filter(db_pool: asyncpg.Pool = Depends(get_db_pool)):
    """Get content filter service"""
    from .services.content_filter import ContentFilter
    return ContentFilter(db_pool)