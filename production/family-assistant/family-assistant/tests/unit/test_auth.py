"""
Unit tests for JWT authentication service.

Tests password hashing, token generation, token validation, and role-based access.
"""

import pytest
from datetime import timedelta
from jose import jwt
from fastapi import HTTPException

from api.auth.jwt import (
    AuthService,
    SECRET_KEY,
    ALGORITHM,
    ACCESS_TOKEN_EXPIRE_MINUTES
)
from api.auth.models import TokenData


class TestPasswordHashing:
    """Test password hashing and verification."""

    def test_hash_password(self):
        """Test password hashing produces different hashes."""
        password = "test_password_123"

        hash1 = AuthService.get_password_hash(password)
        hash2 = AuthService.get_password_hash(password)

        # Different salts should produce different hashes
        assert hash1 != hash2
        assert hash1.startswith("$2b$")  # bcrypt prefix
        assert len(hash1) == 60  # bcrypt hash length

    def test_verify_password_correct(self):
        """Test password verification with correct password."""
        password = "secure_password_456"
        hashed = AuthService.get_password_hash(password)

        assert AuthService.verify_password(password, hashed) is True

    def test_verify_password_incorrect(self):
        """Test password verification with incorrect password."""
        password = "correct_password"
        wrong_password = "wrong_password"
        hashed = AuthService.get_password_hash(password)

        assert AuthService.verify_password(wrong_password, hashed) is False

    def test_verify_password_empty(self):
        """Test password verification with empty password."""
        password = "test_password"
        hashed = AuthService.get_password_hash(password)

        assert AuthService.verify_password("", hashed) is False


class TestTokenGeneration:
    """Test JWT token creation."""

    def test_create_access_token(self):
        """Test basic token creation."""
        data = {"sub": "user123", "username": "testuser", "role": "parent"}
        token = AuthService.create_access_token(data)

        assert isinstance(token, str)
        assert len(token) > 0

        # Decode token without verification to check payload
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        assert payload["sub"] == "user123"
        assert payload["username"] == "testuser"
        assert payload["role"] == "parent"
        assert "exp" in payload
        assert "iat" in payload
        assert payload["type"] == "access"

    def test_create_access_token_with_expiration(self):
        """Test token creation with custom expiration."""
        data = {"sub": "user123"}
        expires_delta = timedelta(minutes=30)
        token = AuthService.create_access_token(data, expires_delta=expires_delta)

        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])

        # Check expiration is approximately 30 minutes from now
        exp_time = payload["exp"]
        iat_time = payload["iat"]
        assert (exp_time - iat_time) == 1800  # 30 minutes in seconds

    def test_create_access_token_default_expiration(self):
        """Test token creation uses default expiration."""
        data = {"sub": "user123"}
        token = AuthService.create_access_token(data)

        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])

        exp_time = payload["exp"]
        iat_time = payload["iat"]
        expected_delta = ACCESS_TOKEN_EXPIRE_MINUTES * 60
        assert (exp_time - iat_time) == expected_delta

    def test_create_access_token_with_telegram_id(self):
        """Test token creation with telegram_id."""
        data = {
            "sub": "user123",
            "username": "testuser",
            "role": "parent",
            "telegram_id": 987654321
        }
        token = AuthService.create_access_token(data)

        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        assert payload["telegram_id"] == 987654321


class TestTokenDecoding:
    """Test JWT token validation and decoding."""

    def test_decode_valid_token(self):
        """Test decoding a valid token."""
        data = {
            "sub": "user123",
            "username": "testuser",
            "role": "parent",
            "telegram_id": 123456789
        }
        token = AuthService.create_access_token(data)

        token_data = AuthService.decode_token(token)

        assert isinstance(token_data, TokenData)
        assert token_data.user_id == "user123"
        assert token_data.username == "testuser"
        assert token_data.role == "parent"
        assert token_data.telegram_id == 123456789

    def test_decode_token_without_sub(self):
        """Test decoding token without 'sub' claim raises exception."""
        # Create token manually without 'sub'
        payload = {"username": "testuser", "role": "parent"}
        token = jwt.encode(payload, SECRET_KEY, algorithm=ALGORITHM)

        with pytest.raises(HTTPException) as exc_info:
            AuthService.decode_token(token)

        assert exc_info.value.status_code == 401
        assert "Could not validate credentials" in exc_info.value.detail

    def test_decode_invalid_token(self):
        """Test decoding an invalid token raises exception."""
        invalid_token = "invalid.token.string"

        with pytest.raises(HTTPException) as exc_info:
            AuthService.decode_token(invalid_token)

        assert exc_info.value.status_code == 401

    def test_decode_token_wrong_secret(self):
        """Test decoding token with wrong secret raises exception."""
        data = {"sub": "user123"}
        # Create token with different secret
        wrong_token = jwt.encode(data, "wrong_secret_key", algorithm=ALGORITHM)

        with pytest.raises(HTTPException) as exc_info:
            AuthService.decode_token(wrong_token)

        assert exc_info.value.status_code == 401

    def test_decode_expired_token(self):
        """Test decoding expired token raises exception."""
        from datetime import datetime

        data = {"sub": "user123"}
        # Create token that expired 1 hour ago
        expires_delta = timedelta(hours=-1)
        expired_token = AuthService.create_access_token(data, expires_delta=expires_delta)

        with pytest.raises(HTTPException) as exc_info:
            AuthService.decode_token(expired_token)

        assert exc_info.value.status_code == 401

    def test_decode_token_with_partial_data(self):
        """Test decoding token with only required fields."""
        data = {"sub": "user123"}  # Only user_id
        token = AuthService.create_access_token(data)

        token_data = AuthService.decode_token(token)

        assert token_data.user_id == "user123"
        assert token_data.username is None
        assert token_data.role is None
        assert token_data.telegram_id is None


class TestAuthServiceIntegration:
    """Test authentication service integration scenarios."""

    def test_full_auth_flow(self):
        """Test complete authentication flow: hash → verify → token → decode."""
        # 1. Hash password
        password = "my_secure_password"
        hashed = AuthService.get_password_hash(password)

        # 2. Verify password
        assert AuthService.verify_password(password, hashed) is True

        # 3. Create token
        user_data = {
            "sub": "user123",
            "username": "testuser",
            "role": "parent"
        }
        token = AuthService.create_access_token(user_data)

        # 4. Decode token
        token_data = AuthService.decode_token(token)
        assert token_data.user_id == "user123"
        assert token_data.username == "testuser"
        assert token_data.role == "parent"

    def test_multiple_users_different_tokens(self):
        """Test different users get different tokens."""
        user1_data = {"sub": "user1", "username": "alice"}
        user2_data = {"sub": "user2", "username": "bob"}

        token1 = AuthService.create_access_token(user1_data)
        token2 = AuthService.create_access_token(user2_data)

        assert token1 != token2

        decoded1 = AuthService.decode_token(token1)
        decoded2 = AuthService.decode_token(token2)

        assert decoded1.user_id == "user1"
        assert decoded2.user_id == "user2"


class TestRoleBasedAccess:
    """Test role-based access control patterns."""

    def test_parent_role_token(self):
        """Test token for parent role."""
        data = {"sub": "parent1", "username": "parent", "role": "parent"}
        token = AuthService.create_access_token(data)

        token_data = AuthService.decode_token(token)
        assert token_data.role == "parent"

    def test_child_role_token(self):
        """Test token for child role."""
        data = {"sub": "child1", "username": "child", "role": "child"}
        token = AuthService.create_access_token(data)

        token_data = AuthService.decode_token(token)
        assert token_data.role == "child"

    def test_teenager_role_token(self):
        """Test token for teenager role."""
        data = {"sub": "teen1", "username": "teen", "role": "teenager"}
        token = AuthService.create_access_token(data)

        token_data = AuthService.decode_token(token)
        assert token_data.role == "teenager"
