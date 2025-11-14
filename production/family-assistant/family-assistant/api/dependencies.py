"""
FastAPI Dependencies - Phase 3

Dependency injection for authentication, database, and services.
"""

from typing import Optional
from fastapi import Depends, HTTPException, Header, status
import asyncpg

from .config import get_settings
from .models.user_management import FamilyMember
from .services.user_manager import UserManager

settings = get_settings()


# ==============================================================================
# Database Dependencies
# ==============================================================================

_db_pool: Optional[asyncpg.Pool] = None


async def init_db_pool():
    """Initialize database connection pool"""
    global _db_pool
    if _db_pool is None:
        _db_pool = await asyncpg.create_pool(
            host=settings.POSTGRES_HOST,
            port=settings.POSTGRES_PORT,
            user=settings.POSTGRES_USER,
            password=settings.POSTGRES_PASSWORD,
            database=settings.POSTGRES_DB,
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


# ==============================================================================
# Authentication Dependencies
# ==============================================================================


async def get_current_user(
    x_telegram_user_id: Optional[int] = Header(None),
    x_user_id: Optional[str] = Header(None),
    db_pool: asyncpg.Pool = Depends(get_db_pool),
) -> FamilyMember:
    """
    Get current authenticated user from request headers

    Authentication can be provided via:
    - X-Telegram-User-Id: Telegram user ID
    - X-User-Id: Family member UUID

    TODO: Implement proper JWT authentication for production
    """
    user_mgr = UserManager(db_pool)

    # Try Telegram ID first
    if x_telegram_user_id:
        member = await user_mgr.get_family_member_by_telegram_id(x_telegram_user_id)
        if member and member.is_active:
            # Update last active timestamp
            await user_mgr.update_last_active(member.id)
            return member

    # Try user UUID
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

    # No valid authentication
    raise HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Authentication required. Provide X-Telegram-User-Id or X-User-Id header.",
        headers={"WWW-Authenticate": "Bearer"},
    )


async def get_current_active_user(
    current_user: FamilyMember = Depends(get_current_user),
) -> FamilyMember:
    """Get current active user (ensures user is not deactivated)"""
    if not current_user.is_active:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="User account is deactivated",
        )
    return current_user


async def get_current_admin_user(
    current_user: FamilyMember = Depends(get_current_user),
) -> FamilyMember:
    """Get current user and verify admin privileges"""
    if not current_user.is_admin:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Admin privileges required",
        )
    return current_user


async def get_current_parent_user(
    current_user: FamilyMember = Depends(get_current_user),
) -> FamilyMember:
    """Get current user and verify parent/grandparent role"""
    from .models.user_management import UserRole

    if current_user.role not in [UserRole.PARENT, UserRole.GRANDPARENT]:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Parent or grandparent role required",
        )
    return current_user


# ==============================================================================
# Service Dependencies
# ==============================================================================


async def get_user_manager(db_pool: asyncpg.Pool = Depends(get_db_pool)) -> UserManager:
    """Get user manager service"""
    return UserManager(db_pool)


async def get_content_filter(db_pool: asyncpg.Pool = Depends(get_db_pool)):
    """Get content filter service"""
    from .services.content_filter import ContentFilter
    return ContentFilter(db_pool)
