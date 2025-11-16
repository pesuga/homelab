"""
Authentication Service

Handles JWT tokens, user authentication, and authorization for family members.
"""

from datetime import datetime, timedelta
from typing import Optional, Dict, Any
from jose import JWTError, jwt
import secrets

from ..models.database import FamilyMember


class AuthService:
    """Service for authentication and authorization."""

    def __init__(self, secret_key: str, algorithm: str = "HS256"):
        self.secret_key = secret_key
        self.algorithm = algorithm
        self.access_token_expire_minutes = 1440  # 24 hours

    def create_access_token(self, data: Dict[str, Any], expires_delta: Optional[timedelta] = None) -> str:
        """Create a JWT access token."""
        to_encode = data.copy()

        if expires_delta:
            expire = datetime.utcnow() + expires_delta
        else:
            expire = datetime.utcnow() + timedelta(minutes=self.access_token_expire_minutes)

        to_encode.update({"exp": expire})
        encoded_jwt = jwt.encode(to_encode, self.secret_key, algorithm=self.algorithm)

        return encoded_jwt

    def verify_token(self, token: str) -> Dict[str, Any]:
        """Verify and decode JWT token."""
        try:
            payload = jwt.decode(token, self.secret_key, algorithms=[self.algorithm])
            return payload
        except JWTError:
            return {}

    def authenticate_family_member(self, email: str, password: str) -> Optional[FamilyMember]:
        """Authenticate family member with email and password."""
        # TODO: Implement actual password verification
        # For now, we'll just check if the email exists
        # In a real implementation, you would hash and verify passwords

        member = FamilyMember.query.filter(
            FamilyMember.email == email,
            FamilyMember.is_active == True
        ).first()

        return member

    def create_family_token(self, member: FamilyMember) -> str:
        """Create token for family member access."""
        token_data = {
            "sub": member.id,
            "email": member.email,
            "name": member.name,
            "role": member.role,
            "family_id": member.family_id,
            "type": "family_member"
        }

        return self.create_access_token(token_data)

    def generate_family_code(self) -> str:
        """Generate a unique family code for joining."""
        return secrets.token_urlsafe(8).upper()

    def validate_family_access(self, member: FamilyMember, resource: str, action: str) -> bool:
        """Validate if a family member can access a resource or perform an action."""
        # Parents can do everything
        if member.role in ["parent", "grandparent"]:
            return True

        # Define permissions by role
        permissions = {
            "teenager": {
                "read": True,
                "write": True,
                "delete": False,
                "settings": False,
                "parental_controls": False
            },
            "child": {
                "read": True,
                "write": False,
                "delete": False,
                "settings": False,
                "parental_controls": False
            }
        }

        role_permissions = permissions.get(member.role, {})
        return role_permissions.get(action, False)

    def can_access_content(self, member: FamilyMember, content: Dict[str, Any]) -> bool:
        """Check if member can access specific content based on age-appropriate filtering."""
        # Parents and grandparents can access everything
        if member.role in ["parent", "grandparent"]:
            return True

        # Calculate member's approximate age if birth year is known
        if member.birth_year:
            age = datetime.now().year - member.birth_year

            # Content filtering based on age
            content_rating = content.get("rating", "general")  # general, teen, mature

            if member.role == "teenager":
                return content_rating in ["general", "teen"]
            elif member.role == "child":
                return content_rating == "general"
            elif member.role == "grandparent":
                return True  # Assume grandparents can access everything

        return True  # Default to allowing access if we can't determine age