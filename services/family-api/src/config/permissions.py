"""User permissions and role management."""

from enum import Enum
from typing import List, Dict
from pydantic import BaseModel


class UserRole(str, Enum):
    """User roles in the family assistant."""
    PARENT = "parent"
    CHILD = "child"
    ADMIN = "admin"


class UserPermissions(BaseModel):
    """Permissions for different actions."""
    finance: bool = False
    calendar: bool = False
    notes: bool = True
    tasks: bool = True
    admin: bool = False
    homework_help: bool = False


class UserProfile(BaseModel):
    """User profile with role and permissions."""
    user_id: str
    name: str
    role: UserRole
    age: int
    permissions: UserPermissions
    preferences: Dict = {}


# Default permission sets by role
DEFAULT_PERMISSIONS: Dict[UserRole, UserPermissions] = {
    UserRole.ADMIN: UserPermissions(
        finance=True,
        calendar=True,
        notes=True,
        tasks=True,
        admin=True,
        homework_help=False
    ),
    UserRole.PARENT: UserPermissions(
        finance=True,
        calendar=True,
        notes=True,
        tasks=True,
        admin=False,
        homework_help=False
    ),
    UserRole.CHILD: UserPermissions(
        finance=False,
        calendar=True,
        notes=True,
        tasks=True,
        admin=False,
        homework_help=True
    )
}


def get_default_permissions(role: UserRole) -> UserPermissions:
    """Get default permissions for a role."""
    return DEFAULT_PERMISSIONS.get(role, UserPermissions())


def check_permission(user_profile: UserProfile, permission: str) -> bool:
    """Check if user has a specific permission."""
    return getattr(user_profile.permissions, permission, False)
