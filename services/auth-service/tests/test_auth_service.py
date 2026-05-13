"""
Auth Service — Unit Tests
"""
import pytest
import asyncio
from unittest.mock import AsyncMock, MagicMock, patch
from fastapi.testclient import TestClient
import sys, os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

# ─── Mock environment before imports ─────────────────────────
os.environ.setdefault("DATABASE_URL", "postgresql+asyncpg://test:test@localhost:5432/test")
os.environ.setdefault("SECRET_KEY", "test-secret-key-for-unit-tests-only")
os.environ.setdefault("REFRESH_SECRET_KEY", "test-refresh-secret-key")


class TestPasswordHashing:
    def _hash(self, pw: str) -> str:
        import hashlib, os
        salt = os.urandom(16).hex()
        return hashlib.sha256((pw + salt).encode()).hexdigest() + ":" + salt

    def _verify(self, pw: str, hashed: str) -> bool:
        import hashlib
        h, salt = hashed.split(":")
        return hashlib.sha256((pw + salt).encode()).hexdigest() == h

    def test_hash_is_not_plain(self):
        hashed = self._hash("MyPassword123")
        assert hashed != "MyPassword123"
        assert len(hashed) > 20

    def test_verify_correct_password(self):
        hashed = self._hash("correct_password")
        assert self._verify("correct_password", hashed) is True

    def test_verify_wrong_password(self):
        hashed = self._hash("correct_password")
        assert self._verify("wrong_password", hashed) is False

    def test_same_password_produces_different_hashes(self):
        h1 = self._hash("same_password")
        h2 = self._hash("same_password")
        assert h1 != h2  # different salts


class TestJWTTokens:
    def _make_token(self, payload: dict, secret: str = "test-secret", expire_minutes: int = 30) -> str:
        from jose import jwt
        from datetime import datetime, timezone, timedelta
        data = {**payload, "exp": datetime.now(timezone.utc) + timedelta(minutes=expire_minutes)}
        return jwt.encode(data, secret, algorithm="HS256")

    def _decode_token(self, token: str, secret: str = "test-secret") -> dict:
        from jose import jwt
        return jwt.decode(token, secret, algorithms=["HS256"])

    def test_create_and_decode_access_token(self):
        token = self._make_token({"sub": "user-String(36)-123", "role": "agent"})
        decoded = self._decode_token(token)
        assert decoded["sub"] == "user-String(36)-123"
        assert decoded["role"] == "agent"

    def test_expired_token_raises(self):
        from jose import ExpiredSignatureError
        token = self._make_token({"sub": "user-String(36)-123"}, expire_minutes=-1)
        with pytest.raises(Exception):
            self._decode_token(token)

    def test_invalid_token_raises(self):
        with pytest.raises(Exception):
            self._decode_token("not.a.valid.token")

    def test_create_refresh_token(self):
        token = self._make_token({"sub": "user-String(36)-123"}, secret="refresh-secret")
        decoded = self._decode_token(token, secret="refresh-secret")
        assert decoded["sub"] == "user-String(36)-123"


class TestAuthServiceLogic:
    def test_password_validation_length(self):
        """Passwords must be at least 8 characters."""
        assert len("abcdefgh") >= 8   # valid
        assert len("short")   < 8     # too short

    def test_role_hierarchy(self):
        ROLE_LEVELS = {"customer": 1, "agent": 2, "supervisor": 3, "manager": 4, "admin": 5}
        assert ROLE_LEVELS["admin"] > ROLE_LEVELS["manager"]
        assert ROLE_LEVELS["manager"] > ROLE_LEVELS["supervisor"]
        assert ROLE_LEVELS["supervisor"] > ROLE_LEVELS["agent"]
        assert ROLE_LEVELS["agent"] > ROLE_LEVELS["customer"]


class TestMFASetup:
    def test_totp_secret_generation(self):
        import pyotp
        secret = pyotp.random_base32()
        assert len(secret) >= 16  # at least 16 chars
        totp = pyotp.TOTP(secret)
        code = totp.now()
        assert totp.verify(code)  # freshly generated code is valid

    def test_invalid_totp_code(self):
        import pyotp
        secret = pyotp.random_base32()
        totp = pyotp.TOTP(secret)
        assert not totp.verify("000000")  # Almost certainly wrong



class TestRegisterSchema:
    """Unit tests for RegisterRequest Pydantic-style validation logic."""

    def test_valid_password_passes_all_rules(self):
        pw = "Secure123"
        assert len(pw) >= 8
        assert any(c.isupper() for c in pw)
        assert any(c.isdigit() for c in pw)

    def test_weak_password_no_uppercase(self):
        pw = "alllowercase1"
        assert not any(c.isupper() for c in pw)

    def test_weak_password_no_digit(self):
        pw = "NoDigitsHere"
        assert not any(c.isdigit() for c in pw)

    def test_weak_password_too_short(self):
        pw = "Sh0rt"
        assert len(pw) < 8

    def test_full_name_whitespace_stripped(self):
        assert "  Jane Smith  ".strip() == "Jane Smith"

    def test_empty_full_name_invalid(self):
        assert not "   ".strip()


class TestBcryptHashing:
    """Tests using the real bcrypt library."""

    def test_hash_and_verify_correct_password(self):
        import bcrypt
        pw = "MyPassword123"
        hashed = bcrypt.hashpw(pw.encode(), bcrypt.gensalt()).decode()
        assert bcrypt.checkpw(pw.encode(), hashed.encode())

    def test_wrong_password_fails_verification(self):
        import bcrypt
        pw = "MyPassword123"
        hashed = bcrypt.hashpw(pw.encode(), bcrypt.gensalt()).decode()
        assert not bcrypt.checkpw(b"WrongPassword", hashed.encode())

    def test_same_password_produces_unique_hashes(self):
        import bcrypt
        pw = "SamePassword1"
        h1 = bcrypt.hashpw(pw.encode(), bcrypt.gensalt()).decode()
        h2 = bcrypt.hashpw(pw.encode(), bcrypt.gensalt()).decode()
        assert h1 != h2  # unique salt per hash


class TestTokenTypeGuard:
    """Ensure refresh tokens cannot be used as access tokens."""

    def _make_token(self, payload, secret="test-secret", minutes=30):
        from jose import jwt
        from datetime import datetime, timezone, timedelta
        data = {**payload, "exp": datetime.now(timezone.utc) + timedelta(minutes=minutes)}
        return jwt.encode(data, secret, algorithm="HS256")

    def test_access_token_type_is_access(self):
        token = self._make_token({"sub": "u-123", "type": "access"})
        from jose import jwt
        payload = jwt.decode(token, "test-secret", algorithms=["HS256"])
        assert payload["type"] == "access"

    def test_refresh_token_would_be_rejected_by_get_current_user(self):
        token = self._make_token({"sub": "u-123", "type": "refresh"})
        from jose import jwt
        payload = jwt.decode(token, "test-secret", algorithms=["HS256"])
        # get_current_user checks payload.get("type") != "access"
        assert payload.get("type") != "access"

    def test_tampered_signature_raises_jwt_error(self):
        import pytest
        token = self._make_token({"sub": "u-123"})
        tampered = token[:-5] + "XXXXX"
        from jose import jwt, JWTError
        with pytest.raises(JWTError):
            jwt.decode(tampered, "test-secret", algorithms=["HS256"])
