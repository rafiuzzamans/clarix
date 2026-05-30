from fastapi import APIRouter, Depends, Request
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_db
from app.core.dependencies import get_current_user
from app.models.user import User
from app.schemas.auth import (
    LoginRequest,
    MFAVerifyRequest,
    PasswordChangeRequest,
    RefreshRequest,
    TokenResponse,
)
from app.services.auth_service import AuthService

router = APIRouter(prefix="/auth", tags=["Authentication"])


def _get_client_info(request: Request) -> tuple:
    ip = request.headers.get("X-Forwarded-For", request.client.host if request.client else "unknown")
    ua = request.headers.get("User-Agent", "unknown")
    return ip, ua


@router.post("/login", response_model=TokenResponse, summary="Login and receive JWT tokens")
async def login(
    body: LoginRequest,
    request: Request,
    db: AsyncSession = Depends(get_db),
):
    ip, ua = _get_client_info(request)
    service = AuthService(db)
    return await service.login(body, ip_address=ip, user_agent=ua)


@router.post("/refresh", response_model=TokenResponse, summary="Refresh access token")
async def refresh_token(
    body: RefreshRequest,
    request: Request,
    db: AsyncSession = Depends(get_db),
):
    ip, ua = _get_client_info(request)
    service = AuthService(db)
    return await service.refresh(body.refresh_token, ip_address=ip, user_agent=ua)


@router.post("/logout", summary="Revoke refresh token")
async def logout(
    body: RefreshRequest,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    service = AuthService(db)
    return await service.logout(body.refresh_token, str(current_user.id))


@router.get("/me", summary="Get current authenticated user")
async def get_me(current_user: User = Depends(get_current_user)):
    return {
        "id": str(current_user.id),
        "email": current_user.email,
        "full_name": current_user.full_name,
        "role": current_user.role.value,
        "status": current_user.status.value,
        "mfa_enabled": current_user.mfa_enabled,
        "department": current_user.department,
        "team_id": str(current_user.team_id) if current_user.team_id else None,
    }


@router.post("/verify-token", summary="Validate a token (inter-service use)")
async def verify_token(
    current_user: User = Depends(get_current_user),
):
    """Used by other services to validate a JWT and get user info."""
    return {
        "valid": True,
        "user_id": str(current_user.id),
        "role": current_user.role.value,
        "email": current_user.email,
    }


@router.post("/mfa/setup", summary="Generate MFA secret and QR code")
async def setup_mfa(
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    service = AuthService(db)
    return await service.setup_mfa(current_user.id)


@router.post("/mfa/verify", summary="Verify MFA code and enable MFA")
async def verify_mfa(
    body: MFAVerifyRequest,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    service = AuthService(db)
    return await service.verify_mfa_setup(current_user.id, body.code)

# Rate limit login attempts
