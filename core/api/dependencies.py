"""
API Dependencies

Common dependencies for route handlers including authentication, database, and family context.
"""

from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from sqlalchemy.orm import Session
from jose import JWTError, jwt
from typing import Optional

try:
    from ..models.database import Family, FamilyMember
    from .database import get_db
except ImportError:
    from api.models.database import Family, FamilyMember
    from api.database import get_db

security = HTTPBearer()

# JWT Configuration (these should come from environment settings)
SECRET_KEY = "your-super-secret-jwt-key-change-this-in-production"
ALGORITHM = "HS256"


async def get_current_user(
    credentials: HTTPAuthorizationCredentials = Depends(security),
    db: Session = Depends(get_db)
):
    """Get current user from JWT token."""
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Could not validate credentials",
        headers={"WWW-Authenticate": "Bearer"},
    )

    try:
        payload = jwt.decode(credentials.credentials, SECRET_KEY, algorithms=[ALGORITHM])
        user_id: str = payload.get("sub")
        if user_id is None:
            raise credentials_exception
    except JWTError:
        raise credentials_exception

    # TODO: Implement proper user lookup
    # For now, we'll return a simple user object
    return {"id": user_id, "email": payload.get("email", "")}


async def get_current_family(
    current_user: dict = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Get current family from user context."""
    # TODO: Implement proper family lookup based on user
    # For now, we'll return the first family found
    family = db.query(Family).filter(Family.is_active == True).first()

    if not family:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Family not found"
        )

    return family


async def get_current_member(
    current_user: dict = Depends(get_current_user),
    current_family: Family = Depends(get_current_family),
    db: Session = Depends(get_db)
):
    """Get current family member from user context."""
    # TODO: Implement proper member lookup based on user
    # For now, we'll return the first member found
    member = db.query(FamilyMember).filter(
        FamilyMember.family_id == current_family.id,
        FamilyMember.is_active == True
    ).first()

    if not member:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Family member not found"
        )

    return member


def require_role(required_role: str):
    """Decorator to require specific family role."""
    def role_checker(current_member: FamilyMember = Depends(get_current_member)):
        if current_member.role != required_role and current_member.role != "parent":
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Insufficient permissions"
            )
        return current_member
    return role_checker


def require_parent(current_member: FamilyMember = Depends(get_current_member)):
    """Require parent role for sensitive operations."""
    if current_member.role not in ["parent", "grandparent"]:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Parental access required"
        )
    return current_member


# Common dependencies that can be used across routes
get_db = get_db
CurrentUser = Depends(get_current_user)
CurrentFamily = Depends(get_current_family)
CurrentMember = Depends(get_current_member)
RequireParent = Depends(require_parent)