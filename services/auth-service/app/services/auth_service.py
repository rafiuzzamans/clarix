import hashlib
import secrets
from datetime import datetime, timedelta, timezone
from typing import Optional


import httpx
import pyotp
from fastapi import HTTPException, status
from sqlalchemy import select, update
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.config import settings
from app.core.security import (
    create_access_token,
    create_refresh_token,
    decode_token,
    hash_password,
    verify_password,
)
from app.models.user import RefreshToken, User, UserStatus
from app.schemas.auth import LoginRequest, TokenResponse, UserOut


def _hash_token(token: str) -> str:
    return hashlib.sha256(token.encode()).hexdigest()


async def _emit_audit(action: str, actor_id: Optional[str], resource_id: Optional[str],
                      description: str, ip: Optional[str], ua: Optional[str],
                      metadata: Optional[dict] = None):
    """Fire-and-forget audit log to audit service."""
    try:
        async with httpx.AsyncClient(timeout=2.0) as client:
            await client.post(
                f"{settings.AUDIT_SERVICE_URL}/audit/logs",
                json={
                    "actor_id": actor_id,
                    "action": action,
                    "resource_type": "user",
                    "resource_id": resource_id,
                    "description": description,
                    "ip_address": ip,
                    "user_agent": ua,
                    "metadata": metadata or {},
                },
            )
    except Exception:
        pass  # Non-blocking — audit failures must not break auth


class AuthService:
    def __init__(self, db: AsyncSession):
        self.db = db

    async def login(
        self,
        request: LoginRequest,
        ip_address: Optional[str] = None,
        user_agent: Optional[str] = None,
    ) -> TokenResponse:
        # Fetch user
        result = await self.db.execute(
            select(User).where(User.email == request.email)
        )
        user = result.scalar_one_or_none()

        if not user or not verify_password(request.password, user.hashed_password):
            await _emit_audit(
                "login_failed", None, None,
                f"Failed login attempt for {request.email}", ip_address, user_agent
            )
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid email or password",
            )

        if user.status != UserStatus.active:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail=f"Account is {user.status.value}",
            )

        # MFA check
        if user.mfa_enabled and user.mfa_secret:
            if not request.mfa_code:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail="MFA code required",
                )
            totp = pyotp.TOTP(user.mfa_secret)
            if not totp.verify(request.mfa_code, valid_window=1):
                raise HTTPException(
                    status_code=status.HTTP_401_UNAUTHORIZED,
                    detail="Invalid MFA code",
                )

        # Create tokens
        token_data = {
            "sub": str(user.id),
            "email": user.email,
            "role": user.role.value,
        }
        access_token = create_access_token(token_data)
        refresh_token_raw = create_refresh_token(token_data)

        # Persist refresh token
        token_obj = RefreshToken(
            user_id=user.id,
            token_hash=_hash_token(refresh_token_raw),
            expires_at=datetime.now(timezone.utc) + timedelta(days=settings.REFRESH_TOKEN_EXPIRE_DAYS),
            ip_address=ip_address,
            user_agent=user_agent,
        )
        self.db.add(token_obj)

        # Update last login
        await self.db.execute(
            update(User).where(User.id == user.id).values(last_login_at=datetime.now(timezone.utc))
        )
        await self.db.commit()

        await _emit_audit(
            "login", str(user.id), str(user.id),
            f"User {user.email} logged in", ip_address, user_agent
        )

        return TokenResponse(
            access_token=access_token,
            refresh_token=refresh_token_raw,
            expires_in=settings.ACCESS_TOKEN_EXPIRE_MINUTES * 60,
            user=UserOut.model_validate(user),
        )

    async def refresh(
        self,
        refresh_token_raw: str,
        ip_address: Optional[str] = None,
        user_agent: Optional[str] = None,
    ) -> TokenResponse:
        payload = decode_token(refresh_token_raw)
        if not payload or payload.get("type") != "refresh":
            raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid refresh token")

        token_hash = _hash_token(refresh_token_raw)
        result = await self.db.execute(
            select(RefreshToken).where(RefreshToken.token_hash == token_hash)
        )
        stored = result.scalar_one_or_none()

        if not stored or stored.revoked or stored.expires_at < datetime.now(timezone.utc):
            raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Refresh token expired or revoked")

        # Revoke old token (rotation)
        stored.revoked = True

        # Fetch user
        result = await self.db.execute(select(User).where(User.id == stored.user_id))
        user = result.scalar_one_or_none()
        if not user or user.status != UserStatus.active:
            raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="User not authorized")

        # Issue new tokens
        token_data = {"sub": str(user.id), "email": user.email, "role": user.role.value}
        new_access = create_access_token(token_data)
        new_refresh_raw = create_refresh_token(token_data)

        new_token = RefreshToken(
            user_id=user.id,
            token_hash=_hash_token(new_refresh_raw),
            expires_at=datetime.now(timezone.utc) + timedelta(days=settings.REFRESH_TOKEN_EXPIRE_DAYS),
            ip_address=ip_address,
            user_agent=user_agent,
        )
        self.db.add(new_token)
        await self.db.commit()

        await _emit_audit("token_refresh", str(user.id), str(user.id),
                          "Token refreshed", ip_address, user_agent)

        return TokenResponse(
            access_token=new_access,
            refresh_token=new_refresh_raw,
            expires_in=settings.ACCESS_TOKEN_EXPIRE_MINUTES * 60,
            user=UserOut.model_validate(user),
        )

    async def logout(self, refresh_token_raw: str, user_id: str) -> dict:
        token_hash = _hash_token(refresh_token_raw)
        result = await self.db.execute(
            select(RefreshToken).where(RefreshToken.token_hash == token_hash)
        )
        stored = result.scalar_one_or_none()
        if stored:
            stored.revoked = True
            await self.db.commit()
        await _emit_audit("logout", user_id, user_id, "User logged out", None, None)
        return {"message": "Logged out successfully"}

    async def setup_mfa(self, user_id: str) -> dict:
        result = await self.db.execute(select(User).where(User.id == user_id))
        user = result.scalar_one_or_none()
        if not user:
            raise HTTPException(status_code=404, detail="User not found")

        secret = pyotp.random_base32()
        totp = pyotp.TOTP(secret)
        qr_uri = totp.provisioning_uri(user.email, issuer_name="CS Platform")

        # Store secret (not yet enabled — user must verify first)
        user.mfa_secret = secret
        await self.db.commit()

        return {"secret": secret, "qr_uri": qr_uri}

    async def verify_mfa_setup(self, user_id: str, code: str) -> dict:
        result = await self.db.execute(select(User).where(User.id == user_id))
        user = result.scalar_one_or_none()
        if not user or not user.mfa_secret:
            raise HTTPException(status_code=400, detail="MFA not initialised")

        totp = pyotp.TOTP(user.mfa_secret)
        if not totp.verify(code, valid_window=1):
            raise HTTPException(status_code=400, detail="Invalid MFA code")

        user.mfa_enabled = True
        await self.db.commit()
        return {"message": "MFA enabled successfully"}

