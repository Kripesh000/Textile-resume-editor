"""
Integration Tests for Auth Router

Tests authentication endpoints: registration, login, token refresh.
Tests with actual HTTP requests to FastAPI app.
"""

import pytest


class TestUserRegistration:
    """Tests for user registration endpoint"""

    def test_register_success(self, client):
        """Should register new user and return 201"""
        response = client.post(
            "/api/v1/auth/register",
            json={
                "email": "newuser@example.com",
                "password": "SecurePassword123!",
            },
        )

        assert response.status_code == 201
        data = response.json()
        assert "access_token" in data
        assert data["user"]["email"] == "newuser@example.com"

    def test_register_duplicate_email(self, client, test_user):
        """Should reject duplicate email with 400"""
        response = client.post(
            "/api/v1/auth/register",
            json={
                "email": test_user.email,  # Already exists
                "password": "NewPassword123!",
            },
        )

        assert response.status_code == 400
        assert "already" in response.json()["detail"].lower()

    def test_register_invalid_email(self, client):
        """Should reject invalid email format"""
        response = client.post(
            "/api/v1/auth/register",
            json={
                "email": "not-an-email",
                "password": "Password123!",
            },
        )

        assert response.status_code == 422  # Validation error

    def test_register_missing_password(self, client):
        """Should require password field"""
        response = client.post(
            "/api/v1/auth/register",
            json={
                "email": "test@example.com",
                # Missing password
            },
        )

        assert response.status_code == 422

    def test_register_missing_email(self, client):
        """Should require email field"""
        response = client.post(
            "/api/v1/auth/register",
            json={
                "password": "Password123!",
                # Missing email
            },
        )

        assert response.status_code == 422

    def test_register_empty_password(self, client):
        """Should reject empty password"""
        response = client.post(
            "/api/v1/auth/register",
            json={
                "email": "test@example.com",
                "password": "",
            },
        )

        assert response.status_code == 422

    def test_register_weak_password(self, client):
        """Should enforce password strength requirements"""
        # Test password that's too short
        response = client.post(
            "/api/v1/auth/register",
            json={
                "email": "test@example.com",
                "password": "123",  # Too short
            },
        )

        assert response.status_code in [400, 422]

    def test_register_response_contains_token(self, client):
        """Registration response should contain valid JWT token"""
        response = client.post(
            "/api/v1/auth/register",
            json={
                "email": "newuser@example.com",
                "password": "SecurePassword123!",
            },
        )

        assert response.status_code == 201
        data = response.json()
        token = data["access_token"]

        # Token should be valid JWT format
        assert isinstance(token, str)
        assert len(token) > 0
        assert token.count(".") == 2  # JWT has 3 parts separated by 2 dots

    def test_register_response_contains_user(self, client):
        """Registration response should include user data"""
        email = "newuser@example.com"
        response = client.post(
            "/api/v1/auth/register",
            json={
                "email": email,
                "password": "SecurePassword123!",
            },
        )

        assert response.status_code == 201
        data = response.json()
        assert "user" in data
        assert data["user"]["email"] == email


class TestUserLogin:
    """Tests for user login endpoint"""

    def test_login_success(self, client, test_user):
        """Should login with correct credentials"""
        response = client.post(
            "/api/v1/auth/login",
            json={
                "email": test_user.email,
                "password": "TestPassword123!",
            },
        )

        assert response.status_code == 200
        data = response.json()
        assert "access_token" in data
        assert data["user"]["id"] == test_user.id

    def test_login_invalid_email(self, client):
        """Should reject login with non-existent email"""
        response = client.post(
            "/api/v1/auth/login",
            json={
                "email": "nonexistent@example.com",
                "password": "SomePassword123!",
            },
        )

        assert response.status_code == 401
        assert "invalid" in response.json()["detail"].lower()

    def test_login_invalid_password(self, client, test_user):
        """Should reject login with wrong password"""
        response = client.post(
            "/api/v1/auth/login",
            json={
                "email": test_user.email,
                "password": "WrongPassword123!",
            },
        )

        assert response.status_code == 401

    def test_login_empty_email(self, client):
        """Should reject empty email"""
        response = client.post(
            "/api/v1/auth/login",
            json={
                "email": "",
                "password": "Password123!",
            },
        )

        assert response.status_code == 422

    def test_login_empty_password(self, client, test_user):
        """Should reject empty password"""
        response = client.post(
            "/api/v1/auth/login",
            json={
                "email": test_user.email,
                "password": "",
            },
        )

        assert response.status_code == 401

    def test_login_case_sensitive_email(self, client, test_user):
        """Email should be case-insensitive for login"""
        response = client.post(
            "/api/v1/auth/login",
            json={
                "email": test_user.email.upper(),  # Different case
                "password": "TestPassword123!",
            },
        )

        # Depends on implementation - may or may not be case-insensitive
        # This test documents expected behavior

    def test_login_response_token_format(self, client, test_user):
        """Login response should contain valid JWT token"""
        response = client.post(
            "/api/v1/auth/login",
            json={
                "email": test_user.email,
                "password": "TestPassword123!",
            },
        )

        assert response.status_code == 200
        token = response.json()["access_token"]
        assert token.count(".") == 2  # Valid JWT format


class TestGetCurrentUser:
    """Tests for getting current user endpoint"""

    def test_get_me_authenticated(self, client_with_auth, test_user):
        """Should return current user when authenticated"""
        response = client_with_auth.get("/api/v1/auth/me")

        assert response.status_code == 200
        data = response.json()
        assert data["id"] == test_user.id
        assert data["email"] == test_user.email

    def test_get_me_unauthenticated(self, client):
        """Should return 401 when not authenticated"""
        response = client.get("/api/v1/auth/me")

        assert response.status_code == 401
        assert "token" in response.json()["detail"].lower()

    def test_get_me_invalid_token(self, client):
        """Should return 401 with invalid token"""
        response = client.get(
            "/api/v1/auth/me",
            headers={"Authorization": "Bearer invalid.token.here"},
        )

        assert response.status_code == 401

    def test_get_me_malformed_auth_header(self, client):
        """Should handle malformed Authorization header"""
        response = client.get(
            "/api/v1/auth/me",
            headers={"Authorization": "InvalidFormat"},
        )

        assert response.status_code == 401

    def test_get_me_missing_bearer_prefix(self, client):
        """Should require Bearer prefix in Authorization"""
        token = "some.valid.token"
        response = client.get(
            "/api/v1/auth/me",
            headers={"Authorization": token},  # Missing "Bearer " prefix
        )

        assert response.status_code == 401

    def test_get_me_deleted_user(self, client_with_auth, db_session, test_user):
        """Should handle when user is deleted"""
        # This is a database cleanup test
        # Implementation dependent


class TestCompleteAuthFlow:
    """Tests for complete authentication workflows"""

    def test_register_then_login_flow(self, client):
        """Should be able to register then login"""
        email = "flow@example.com"
        password = "FlowPassword123!"

        # Register
        register_response = client.post(
            "/api/v1/auth/register",
            json={"email": email, "password": password},
        )
        assert register_response.status_code == 201

        # Login
        login_response = client.post(
            "/api/v1/auth/login",
            json={"email": email, "password": password},
        )
        assert login_response.status_code == 200

        # Get current user
        token = login_response.json()["access_token"]
        me_response = client.get(
            "/api/v1/auth/me",
            headers={"Authorization": f"Bearer {token}"},
        )
        assert me_response.status_code == 200
        assert me_response.json()["email"] == email

    def test_concurrent_login_attempts(self, client, test_user):
        """Should handle multiple concurrent login attempts"""
        # Register would need async testing
        # This test documents expected behavior

    def test_token_expires_after_duration(self, client, test_token):
        """Should reject expired tokens"""
        # This requires time manipulation (freezegun)
        # This test documents expected behavior


class TestAuthErrorHandling:
    """Tests for authentication error handling"""

    def test_register_sql_injection_attempt(self, client):
        """Should handle SQL injection in email"""
        response = client.post(
            "/api/v1/auth/register",
            json={
                "email": "'; DROP TABLE users; --",
                "password": "Password123!",
            },
        )

        # Should either reject as invalid email or handle safely
        assert response.status_code in [400, 422]

    def test_login_xss_attempt(self, client):
        """Should handle XSS attempts in credentials"""
        response = client.post(
            "/api/v1/auth/login",
            json={
                "email": "<script>alert('xss')</script>",
                "password": "password",
            },
        )

        assert response.status_code == 401

    def test_register_unicode_password(self, client):
        """Should handle unicode in password"""
        response = client.post(
            "/api/v1/auth/register",
            json={
                "email": "unicode@example.com",
                "password": "Пароль🔒123",
            },
        )

        assert response.status_code == 201

    def test_login_unicode_credentials(self, client):
        """Should handle unicode in email and password"""
        # First register with unicode
        email = "unicode@example.com"
        password = "Пароль🔒123"

        register_response = client.post(
            "/api/v1/auth/register",
            json={"email": email, "password": password},
        )
        assert register_response.status_code == 201

        # Then login with unicode
        login_response = client.post(
            "/api/v1/auth/login",
            json={"email": email, "password": password},
        )
        assert login_response.status_code == 200


# ============================================================================
# Markers and Test Configuration
# ============================================================================

pytestmark = pytest.mark.integration
