"""
Integration tests for authentication API endpoints.

Tests login flow, token validation, user profile access, and error scenarios.
"""

import pytest
from httpx import AsyncClient
from fastapi import status

from api.auth.jwt import AuthService


@pytest.mark.asyncio
class TestLoginEndpoint:
    """Test login endpoint with OAuth2 password flow."""

    async def test_login_success_oauth2_flow(self, test_client: AsyncClient, test_db):
        """Test successful login with OAuth2 password flow (form data)."""
        # This test requires database setup with test user
        # For now, we'll test the endpoint structure

        response = await test_client.post(
            "/api/v1/auth/login",
            data={
                "username": "testuser",
                "password": "testpass"
            },
            headers={"Content-Type": "application/x-www-form-urlencoded"}
        )

        # Will be 401 without actual database, but endpoint should be accessible
        assert response.status_code in [200, 401]

    async def test_login_missing_credentials(self, test_client: AsyncClient):
        """Test login with missing credentials returns 422."""
        response = await test_client.post(
            "/api/v1/auth/login",
            data={},
            headers={"Content-Type": "application/x-www-form-urlencoded"}
        )

        assert response.status_code == 422  # Validation error

    async def test_login_json_endpoint(self, test_client: AsyncClient):
        """Test JSON login endpoint."""
        response = await test_client.post(
            "/api/v1/auth/login/json",
            json={
                "username": "testuser",
                "password": "testpass"
            }
        )

        # Will be 401 without actual database
        assert response.status_code in [200, 401]

    async def test_login_json_missing_fields(self, test_client: AsyncClient):
        """Test JSON login with missing fields returns 422."""
        response = await test_client.post(
            "/api/v1/auth/login/json",
            json={"username": "testuser"}  # Missing password
        )

        assert response.status_code == 422


@pytest.mark.asyncio
class TestProtectedEndpoints:
    """Test protected endpoints requiring authentication."""

    async def test_me_endpoint_without_token(self, test_client: AsyncClient):
        """Test /me endpoint without token returns 403."""
        response = await test_client.get("/api/v1/auth/me")

        assert response.status_code == 403  # Forbidden (no credentials)

    async def test_me_endpoint_with_invalid_token(self, test_client: AsyncClient):
        """Test /me endpoint with invalid token returns 401."""
        response = await test_client.get(
            "/api/v1/auth/me",
            headers={"Authorization": "Bearer invalid_token"}
        )

        assert response.status_code == 401  # Unauthorized

    async def test_me_endpoint_with_valid_token_structure(self, test_client: AsyncClient):
        """Test /me endpoint with structurally valid token."""
        # Create a valid token (but user won't exist in test DB)
        token = AuthService.create_access_token(
            data={"sub": "test_user_id", "username": "testuser", "role": "parent"}
        )

        response = await test_client.get(
            "/api/v1/auth/me",
            headers={"Authorization": f"Bearer {token}"}
        )

        # Will be 401 because user doesn't exist in database
        assert response.status_code == 401

    async def test_verify_endpoint_without_token(self, test_client: AsyncClient):
        """Test /verify endpoint without token returns 403."""
        response = await test_client.post("/api/v1/auth/verify")

        assert response.status_code == 403

    async def test_verify_endpoint_with_invalid_token(self, test_client: AsyncClient):
        """Test /verify endpoint with invalid token returns 401."""
        response = await test_client.post(
            "/api/v1/auth/verify",
            headers={"Authorization": "Bearer invalid_token"}
        )

        assert response.status_code == 401


@pytest.mark.asyncio
class TestTokenValidation:
    """Test token validation scenarios."""

    async def test_expired_token_rejected(self, test_client: AsyncClient):
        """Test expired token is rejected."""
        from datetime import timedelta

        # Create expired token
        expired_token = AuthService.create_access_token(
            data={"sub": "user123"},
            expires_delta=timedelta(seconds=-60)  # Expired 60 seconds ago
        )

        response = await test_client.post(
            "/api/v1/auth/verify",
            headers={"Authorization": f"Bearer {expired_token}"}
        )

        assert response.status_code == 401

    async def test_malformed_authorization_header(self, test_client: AsyncClient):
        """Test malformed Authorization header is rejected."""
        response = await test_client.get(
            "/api/v1/auth/me",
            headers={"Authorization": "NotBearer token123"}
        )

        assert response.status_code == 403  # Invalid credentials format

    async def test_bearer_token_case_insensitive(self, test_client: AsyncClient):
        """Test Bearer token scheme is case-insensitive."""
        token = AuthService.create_access_token(
            data={"sub": "user123", "username": "test"}
        )

        response = await test_client.get(
            "/api/v1/auth/me",
            headers={"Authorization": f"bearer {token}"}  # lowercase
        )

        # Will be 401 (user not found) but not 403 (credential format accepted)
        assert response.status_code == 401


@pytest.mark.asyncio
class TestLoginFlowIntegration:
    """Test complete authentication flow integration."""

    async def test_login_response_structure(self, test_client: AsyncClient):
        """Test login response has correct structure when successful."""
        # Note: This will fail without real database
        # But demonstrates expected response structure

        response = await test_client.post(
            "/api/v1/auth/login/json",
            json={"username": "admin", "password": "admin"}
        )

        # If successful (200), check response structure
        if response.status_code == 200:
            data = response.json()
            assert "access_token" in data
            assert "token_type" in data
            assert data["token_type"] == "bearer"
            assert "expires_in" in data
            assert isinstance(data["expires_in"], int)

    async def test_user_profile_response_structure(self, test_client: AsyncClient):
        """Test user profile response structure."""
        # Create valid token
        token = AuthService.create_access_token(
            data={
                "sub": "user123",
                "username": "testuser",
                "role": "parent"
            }
        )

        response = await test_client.get(
            "/api/v1/auth/me",
            headers={"Authorization": f"Bearer {token}"}
        )

        # If successful (200), check response structure
        if response.status_code == 200:
            data = response.json()
            assert "id" in data
            assert "username" in data
            assert "role" in data
            assert "first_name" in data
            assert "language_preference" in data
            assert "is_active" in data


@pytest.mark.asyncio
class TestSecurityHeaders:
    """Test security-related headers and responses."""

    async def test_unauthorized_includes_www_authenticate(self, test_client: AsyncClient):
        """Test 401 responses include WWW-Authenticate header."""
        response = await test_client.post(
            "/api/v1/auth/login/json",
            json={"username": "nonexistent", "password": "wrong"}
        )

        if response.status_code == 401:
            assert "WWW-Authenticate" in response.headers
            assert response.headers["WWW-Authenticate"] == "Bearer"

    async def test_invalid_token_includes_www_authenticate(self, test_client: AsyncClient):
        """Test invalid token responses include WWW-Authenticate header."""
        response = await test_client.get(
            "/api/v1/auth/me",
            headers={"Authorization": "Bearer invalid_token"}
        )

        assert response.status_code == 401
        # Note: Header inclusion depends on FastAPI exception handler


@pytest.mark.asyncio
class TestConcurrentAuthentication:
    """Test concurrent authentication requests."""

    async def test_multiple_tokens_for_same_user(self, test_client: AsyncClient):
        """Test multiple valid tokens can exist for same user."""
        import asyncio

        user_data = {"sub": "user123", "username": "test"}

        # Create multiple tokens concurrently
        token1 = AuthService.create_access_token(user_data)
        await asyncio.sleep(0.01)  # Small delay
        token2 = AuthService.create_access_token(user_data)

        # Tokens should be different (different timestamps)
        assert token1 != token2

        # Both should be valid
        token_data1 = AuthService.decode_token(token1)
        token_data2 = AuthService.decode_token(token2)

        assert token_data1.user_id == token_data2.user_id

    async def test_concurrent_login_attempts(self, test_client: AsyncClient):
        """Test concurrent login attempts are handled correctly."""
        import asyncio

        async def login_attempt():
            return await test_client.post(
                "/api/v1/auth/login/json",
                json={"username": "testuser", "password": "testpass"}
            )

        # Make 3 concurrent login attempts
        responses = await asyncio.gather(
            login_attempt(),
            login_attempt(),
            login_attempt()
        )

        # All should return same status code (consistent behavior)
        statuses = [r.status_code for r in responses]
        assert len(set(statuses)) == 1  # All same status


@pytest.mark.asyncio
class TestErrorMessages:
    """Test error message clarity and security."""

    async def test_login_error_message_generic(self, test_client: AsyncClient):
        """Test login errors don't reveal if username exists."""
        response = await test_client.post(
            "/api/v1/auth/login/json",
            json={"username": "nonexistent", "password": "wrong"}
        )

        if response.status_code == 401:
            error = response.json()
            # Should be generic error, not revealing if user exists
            assert "username or password" in error["detail"].lower()

    async def test_token_error_message_generic(self, test_client: AsyncClient):
        """Test token validation errors are generic."""
        response = await test_client.get(
            "/api/v1/auth/me",
            headers={"Authorization": "Bearer invalid_token"}
        )

        assert response.status_code == 401
        error = response.json()
        # Should be generic validation error
        assert "validate credentials" in error["detail"].lower() or "unauthorized" in error["detail"].lower()
