"""
Unit Tests for AuthService

Tests password hashing, JWT token generation and validation,
and authentication logic without database dependencies.
"""

import pytest
from datetime import datetime, timedelta
from jose import JWTError

from app.services.auth_service import AuthService
from app.config import settings


class TestPasswordHashing:
    """Tests for password hashing functionality"""

    def test_hash_password_creates_hash(self):
        """Password hashing should create a non-empty hash"""
        password = "TestPassword123!"
        hashed = AuthService.hash_password(password)

        assert hashed is not None
        assert len(hashed) > 0
        assert hashed != password

    def test_hash_password_is_deterministic(self):
        """Same password creates different hashes (due to salt)"""
        password = "TestPassword123!"
        hash1 = AuthService.hash_password(password)
        hash2 = AuthService.hash_password(password)

        # Different hashes but both should verify correctly
        assert hash1 != hash2
        assert AuthService.verify_password(password, hash1)
        assert AuthService.verify_password(password, hash2)

    def test_hash_password_empty_string(self):
        """Empty password should still produce a hash"""
        password = ""
        hashed = AuthService.hash_password(password)

        assert hashed is not None
        assert len(hashed) > 0
        assert AuthService.verify_password(password, hashed)

    def test_hash_password_special_characters(self):
        """Password with special characters should hash correctly"""
        password = "P@ssw0rd!#$%^&*()"
        hashed = AuthService.hash_password(password)

        assert AuthService.verify_password(password, hashed)

    def test_hash_password_unicode(self):
        """Password with unicode characters should hash correctly"""
        password = "Пароль🔒123"
        hashed = AuthService.hash_password(password)

        assert AuthService.verify_password(password, hashed)


class TestPasswordVerification:
    """Tests for password verification functionality"""

    def test_verify_password_correct(self):
        """Correct password should verify successfully"""
        password = "TestPassword123!"
        hashed = AuthService.hash_password(password)

        assert AuthService.verify_password(password, hashed) is True

    def test_verify_password_incorrect(self):
        """Incorrect password should fail verification"""
        password = "TestPassword123!"
        wrong_password = "WrongPassword456!"
        hashed = AuthService.hash_password(password)

        assert AuthService.verify_password(wrong_password, hashed) is False

    def test_verify_password_empty_hashed(self):
        """Empty hash should not verify any password"""
        password = "TestPassword123!"
        empty_hash = ""

        assert AuthService.verify_password(password, empty_hash) is False

    def test_verify_password_empty_input(self):
        """Empty input password should handle gracefully"""
        correct_password = "TestPassword123!"
        hashed = AuthService.hash_password(correct_password)

        assert AuthService.verify_password("", hashed) is False

    def test_verify_password_case_sensitive(self):
        """Password verification should be case-sensitive"""
        password = "TestPassword123!"
        wrong_case = "testpassword123!"
        hashed = AuthService.hash_password(password)

        assert AuthService.verify_password(wrong_case, hashed) is False


class TestJWTTokenGeneration:
    """Tests for JWT token generation and validation"""

    def test_create_access_token(self):
        """Should create a valid JWT token"""
        user_id = "test-user-id-123"
        token = AuthService.create_access_token(user_id)

        assert token is not None
        assert isinstance(token, str)
        assert len(token) > 0
        assert "." in token  # JWT format: header.payload.signature

    def test_create_access_token_contains_user_id(self):
        """Token should contain the user_id"""
        user_id = "test-user-123"
        token = AuthService.create_access_token(user_id)

        # Decode without verification (test only)
        from jose import jwt
        payload = jwt.decode(token, options={"verify_signature": False})

        assert payload["sub"] == user_id

    def test_create_access_token_with_expiration(self):
        """Token should have expiration time"""
        user_id = "test-user-123"
        token = AuthService.create_access_token(user_id)

        from jose import jwt
        payload = jwt.decode(token, options={"verify_signature": False})

        assert "exp" in payload
        assert payload["exp"] > datetime.utcnow().timestamp()

    def test_create_access_token_different_expiry(self):
        """Tokens with different expiry times should differ"""
        user_id = "test-user-123"
        token1 = AuthService.create_access_token(user_id, expires_delta=timedelta(hours=1))
        token2 = AuthService.create_access_token(user_id, expires_delta=timedelta(hours=2))

        # Tokens should be different due to different expiration times
        assert token1 != token2

        from jose import jwt
        payload1 = jwt.decode(token1, options={"verify_signature": False})
        payload2 = jwt.decode(token2, options={"verify_signature": False})

        assert payload2["exp"] > payload1["exp"]

    def test_create_access_token_with_custom_secret(self):
        """Token should be verifiable with correct secret"""
        user_id = "test-user-123"
        token = AuthService.create_access_token(user_id)

        from jose import jwt
        try:
            payload = jwt.decode(token, settings.secret_key, algorithms=["HS256"])
            assert payload["sub"] == user_id
        except JWTError:
            pytest.fail("Token should be verifiable with correct secret")

    def test_create_access_token_invalid_with_wrong_secret(self):
        """Token should not be verifiable with wrong secret"""
        user_id = "test-user-123"
        token = AuthService.create_access_token(user_id)

        from jose import jwt
        with pytest.raises(JWTError):
            jwt.decode(token, "wrong-secret-key", algorithms=["HS256"])


class TestCurrentUserExtraction:
    """Tests for extracting and validating current user from token"""

    @pytest.mark.asyncio
    async def test_get_current_user_valid_token(self, test_user):
        """Should extract user_id from valid token"""
        token = AuthService.create_access_token(test_user.id)
        user_id = AuthService.get_user_id_from_token(token)

        assert user_id == test_user.id

    @pytest.mark.asyncio
    async def test_get_current_user_invalid_token(self):
        """Should raise error for invalid token"""
        invalid_token = "invalid.token.here"

        with pytest.raises(JWTError):
            AuthService.get_user_id_from_token(invalid_token)

    @pytest.mark.asyncio
    async def test_get_current_user_expired_token(self):
        """Should raise error for expired token"""
        user_id = "test-user-123"
        # Create token that's already expired
        expires_delta = timedelta(seconds=-10)  # Negative = already expired
        token = AuthService.create_access_token(user_id, expires_delta)

        with pytest.raises(JWTError):
            AuthService.get_user_id_from_token(token)

    @pytest.mark.asyncio
    async def test_get_current_user_no_token(self):
        """Should raise error when no token provided"""
        with pytest.raises((JWTError, AttributeError)):
            AuthService.get_user_id_from_token(None)

    @pytest.mark.asyncio
    async def test_get_current_user_empty_token(self):
        """Should raise error for empty token"""
        with pytest.raises(JWTError):
            AuthService.get_user_id_from_token("")

    @pytest.mark.asyncio
    async def test_get_current_user_malformed_token(self):
        """Should raise error for malformed token"""
        with pytest.raises(JWTError):
            AuthService.get_user_id_from_token("not.a.valid.jwt.token.with.many.parts")


class TestTokenRoundTrip:
    """Tests for complete token creation and validation flow"""

    def test_create_and_validate_token(self):
        """Should create and validate token in complete flow"""
        original_user_id = "user-12345"

        # Create token
        token = AuthService.create_access_token(original_user_id)
        assert token is not None

        # Validate and extract user_id
        extracted_user_id = AuthService.get_user_id_from_token(token)
        assert extracted_user_id == original_user_id

    def test_token_structure(self):
        """Token should have correct JWT structure"""
        user_id = "test-user-123"
        token = AuthService.create_access_token(user_id)

        parts = token.split(".")
        assert len(parts) == 3  # Header.Payload.Signature

        # Verify parts are base64 encoded
        import base64
        for part in parts:
            try:
                base64.urlsafe_b64decode(part + "==")  # Add padding
            except Exception:
                pytest.fail(f"Token part {part} is not valid base64")

    def test_multiple_tokens_are_unique(self):
        """Multiple tokens for same user should be different"""
        user_id = "test-user-123"
        token1 = AuthService.create_access_token(user_id)
        token2 = AuthService.create_access_token(user_id)

        # Tokens should be different (due to iat claim)
        assert token1 != token2

        # But both should validate to same user_id
        assert AuthService.get_user_id_from_token(token1) == user_id
        assert AuthService.get_user_id_from_token(token2) == user_id


# ============================================================================
# Markers and Test Configuration
# ============================================================================

pytestmark = pytest.mark.unit
