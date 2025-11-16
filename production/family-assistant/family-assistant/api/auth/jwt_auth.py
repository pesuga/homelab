"""
JWT Authentication Module - Phase 1 Security Implementation

Secure JSON Web Token authentication with role-based access control.
Replaces insecure header-based authentication with production-ready JWT system.
"""

from datetime import datetime, timedelta, timezone
from typing import Optional, Dict, Any
from uuid import UUID
from jose import jwt
from passlib.context import CryptContext
from fastapi import HTTPException, status
import secrets
import redis.asyncio as redis

from config.settings import settings
from api.models.user_management import FamilyMember, UserRole


# =============================================================================
# JWT Configuration
# =============================================================================

# JWT Settings
JWT_ALGORITHM = "HS256"
JWT_SECRET_KEY = settings.SECRET_KEY if hasattr(settings, 'SECRET_KEY') else secrets.token_urlsafe(32)
JWT_ACCESS_TOKEN_EXPIRE_MINUTES = 30
JWT_REFRESH_TOKEN_EXPIRE_DAYS = 7

# Password hashing
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")


# =============================================================================
# Token Management
# =============================================================================

class TokenManager:
    """Manages JWT token creation, validation, and refresh operations"""

    def __init__(self):
        self.secret_key = JWT_SECRET_KEY
        self.algorithm = JWT_ALGORITHM
        self.access_token_expire_minutes = JWT_ACCESS_TOKEN_EXPIRE_MINUTES
        self.refresh_token_expire_days = JWT_REFRESH_TOKEN_EXPIRE_DAYS

    def create_access_token(
        self,
        data: Dict[str, Any],
        expires_delta: Optional[timedelta] = None
    ) -> str:
        """Create JWT access token with user claims"""
        to_encode = data.copy()

        # Set expiration
        if expires_delta:
            expire = datetime.now(timezone.utc) + expires_delta
        else:
            expire = datetime.now(timezone.utc) + timedelta(
                minutes=self.access_token_expire_minutes
            )

        to_encode.update({
            "exp": expire,
            "iat": datetime.now(timezone.utc),
            "type": "access"
        })

        return jwt.encode(to_encode, self.secret_key, algorithm=self.algorithm)

    def create_refresh_token(
        self,
        data: Dict[str, Any],
        expires_delta: Optional[timedelta] = None
    ) -> str:
        """Create JWT refresh token for token renewal"""
        to_encode = data.copy()

        # Set expiration
        if expires_delta:
            expire = datetime.now(timezone.utc) + expires_delta
        else:
            expire = datetime.now(timezone.utc) + timedelta(
                days=self.refresh_token_expire_days
            )

        to_encode.update({
            "exp": expire,
            "iat": datetime.now(timezone.utc),
            "type": "refresh"
        })

        return jwt.encode(to_encode, self.secret_key, algorithm=self.algorithm)

    def verify_token(self, token: str, token_type: str = "access") -> Dict[str, Any]:
        """Verify and decode JWT token"""
        try:
            payload = jwt.decode(token, self.secret_key, algorithms=[self.algorithm])

            # Verify token type
            if payload.get("type") != token_type:
                raise HTTPException(
                    status_code=status.HTTP_401_UNAUTHORIZED,
                    detail=f"Invalid token type. Expected {token_type}",
                )

            # Check expiration
            exp = payload.get("exp")
            if exp is None or datetime.fromtimestamp(exp, timezone.utc) < datetime.now(timezone.utc):
                raise HTTPException(
                    status_code=status.HTTP_401_UNAUTHORIZED,
                    detail="Token has expired",
                )

            return payload

        except jwt.ExpiredSignatureError:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Token has expired",
            )
        except jwt.JWTError:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid token",
            )


# =============================================================================
# Password Management
# =============================================================================

class PasswordManager:
    """Manages password hashing and verification"""

    def __init__(self):
        self.pwd_context = pwd_context

    def hash_password(self, password: str) -> str:
        """Hash password using bcrypt"""
        return self.pwd_context.hash(password)

    def verify_password(self, plain_password: str, hashed_password: str) -> bool:
        """Verify password against hash"""
        return self.pwd_context.verify(plain_password, hashed_password)

    def create_password_reset_token(self, email: str) -> str:
        """Create secure password reset token"""
        delta = timedelta(hours=1)  # Reset tokens expire in 1 hour
        now = datetime.now(timezone.utc)
        expires = now + delta
        exp = expires.timestamp()
        encoded_jwt = jwt.encode(
            {"exp": exp, "nbf": now, "sub": email, "type": "password_reset"},
            JWT_SECRET_KEY,
            algorithm=JWT_ALGORITHM,
        )
        return encoded_jwt

    def verify_password_reset_token(self, token: str) -> Optional[str]:
        """Verify password reset token and return email"""
        try:
            decoded_token = jwt.decode(token, JWT_SECRET_KEY, algorithms=[JWT_ALGORITHM])
            if decoded_token.get("type") != "password_reset":
                return None
            return decoded_token["sub"]
        except jwt.JWTError:
            return None


# =============================================================================
# Authentication Service
# =============================================================================

class AuthenticationService:
    """Main authentication service integrating JWT and user management"""

    def __init__(self, db_pool, redis_client: Optional[redis.Redis] = None):
        self.db_pool = db_pool
        self.redis_client = redis_client
        self.token_manager = TokenManager()
        self.password_manager = PasswordManager()

    async def authenticate_user(self, email: str, password: str) -> Optional[FamilyMember]:
        """Authenticate user with email and password"""
        from api.services.user_manager import UserManager

        user_manager = UserManager(self.db_pool)

        # Get user by email (add email field to FamilyMember if not exists)
        user = await user_manager.get_family_member_by_email(email)
        if not user:
            return None

        # For now, create a temporary password hash for demo
        # In production, all users should have password hashes
        if not hasattr(user, 'hashed_password') or not user.hashed_password:
            # Create default password for existing users
            default_password = "family123"
            user.hashed_password = self.password_manager.hash_password(default_password)

        if not self.password_manager.verify_password(password, user.hashed_password):
            return None

        return user

    async def create_user_tokens(self, user: FamilyMember) -> Dict[str, Any]:
        """Create access and refresh tokens for user"""
        # Token payload with user claims
        token_data = {
            "sub": str(user.id),
            "email": user.email,
            "role": user.role.value,
            "is_admin": user.is_admin,
            "family_id": str(getattr(user, 'family_id', 'default')) if hasattr(user, 'family_id') else 'default'
        }

        # Create tokens
        access_token = self.token_manager.create_access_token(data=token_data)
        refresh_token = self.token_manager.create_refresh_token(data={"sub": str(user.id)})

        # Store refresh token in Redis for additional security
        if self.redis_client:
            await self._store_refresh_token(str(user.id), refresh_token)

        return {
            "access_token": access_token,
            "refresh_token": refresh_token,
            "token_type": "bearer",
            "expires_in": JWT_ACCESS_TOKEN_EXPIRE_MINUTES * 60,  # seconds
            "user": {
                "id": str(user.id),
                "email": user.email,
                "role": user.role.value,
                "is_admin": user.is_admin,
                "display_name": user.display_name,
                "first_name": user.first_name,
                "last_name": user.last_name
            }
        }

    async def refresh_access_token(self, refresh_token: str) -> Dict[str, Any]:
        """Create new access token from valid refresh token"""
        try:
            # Verify refresh token
            payload = self.token_manager.verify_token(refresh_token, "refresh")
            user_id = payload.get("sub")

            if not user_id:
                raise HTTPException(
                    status_code=status.HTTP_401_UNAUTHORIZED,
                    detail="Invalid refresh token",
                )

            # Check if refresh token is valid in Redis
            if self.redis_client:
                stored_token = await self.redis_client.get(f"refresh_token:{user_id}")
                if not stored_token or stored_token.decode() != refresh_token:
                    raise HTTPException(
                        status_code=status.HTTP_401_UNAUTHORIZED,
                        detail="Refresh token revoked or invalid",
                    )

            # Get user from database
            from api.services.user_manager import UserManager
            user_manager = UserManager(self.db_pool)
            user = await user_manager.get_family_member(UUID(user_id))

            if not user or not user.is_active:
                raise HTTPException(
                    status_code=status.HTTP_401_UNAUTHORIZED,
                    detail="User not found or inactive",
                )

            # Create new access token
            token_data = {
                "sub": str(user.id),
                "email": user.email,
                "role": user.role.value,
                "is_admin": user.is_admin,
                "family_id": str(getattr(user, 'family_id', 'default')) if hasattr(user, 'family_id') else 'default'
            }

            access_token = self.token_manager.create_access_token(data=token_data)

            return {
                "access_token": access_token,
                "token_type": "bearer",
                "expires_in": JWT_ACCESS_TOKEN_EXPIRE_MINUTES * 60
            }

        except jwt.JWTError:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid refresh token",
            )

    async def logout_user(self, refresh_token: str) -> None:
        """Logout user by revoking refresh token"""
        try:
            payload = self.token_manager.verify_token(refresh_token, "refresh")
            user_id = payload.get("sub")

            # Remove refresh token from Redis
            if self.redis_client and user_id:
                await self.redis_client.delete(f"refresh_token:{user_id}")

        except jwt.JWTError:
            # Token is invalid, but we don't need to raise an error for logout
            pass

    async def _store_refresh_token(self, user_id: str, refresh_token: str) -> None:
        """Store refresh token in Redis with expiration"""
        if self.redis_client:
            await self.redis_client.setex(
                f"refresh_token:{user_id}",
                JWT_REFRESH_TOKEN_EXPIRE_DAYS * 24 * 60 * 60,  # seconds
                refresh_token
            )


# =============================================================================
# Role-Based Access Control (RBAC)
# =============================================================================

class PermissionChecker:
    """Implements role-based access control"""

    # Define role permissions
    ROLE_PERMISSIONS = {
        UserRole.PARENT: [
            "read:own_data", "write:own_data", "read:family_data", "write:family_data",
            "manage_children", "view_analytics", "manage_settings", "approve_content"
        ],
        UserRole.GRANDPARENT: [
            "read:own_data", "write:own_data", "read:family_data", "view_analytics"
        ],
        UserRole.TEENAGER: [
            "read:own_data", "write:own_data", "read:sibling_data", "chat:ai"
        ],
        UserRole.CHILD: [
            "read:own_data", "chat:ai", "games:play"
        ],
        UserRole.MEMBER: [
            "read:own_data", "write:own_data", "chat:ai"
        ]
    }

    @classmethod
    def has_permission(cls, user_role: UserRole, permission: str) -> bool:
        """Check if user role has specific permission"""
        role_permissions = cls.ROLE_PERMISSIONS.get(user_role, [])
        return permission in role_permissions

    @classmethod
    def can_access_resource(cls, user: FamilyMember, resource: str, action: str) -> bool:
        """Check if user can access specific resource with action"""
        permission = f"{action}:{resource}"

        # Admin users have all permissions
        if user.is_admin:
            return True

        return cls.has_permission(user.role, permission)


# =============================================================================
# Global Instances
# =============================================================================

token_manager = TokenManager()
password_manager = PasswordManager()