"""
auth/routes/auth.py
All authentication endpoints for the CLARIX platform.

Endpoints:
  POST /auth/register         - Create new account (customer self-register)
  POST /auth/login            - Authenticate and receive JWT tokens
  POST /auth/refresh          - Exchange refresh token for new access token
  POST /auth/logout           - Revoke refresh token
  GET  /auth/me               - Get current user profile
  POST /auth/change-password  - Change authenticated user's password
  POST /auth/verify-token     - Validate token (inter-service use)
  POST /auth/mfa/setup        - Generate TOTP secret and QR code
  POST /auth/mfa/verify       - Confirm MFA code and enable MFA
"""
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
    RegisterRequest,
    TokenResponse,
)
from app.services.auth_service import AuthService

router = APIRouter(prefix="/auth", tags=["Authentication"])


def _get_client_info(request: Request) -> tuple:
    """Extract client IP and User-Agent for audit logging."""
    ip = request.headers.get("X-Forwarded-For", request.client.host if request.client else "unknown")
    ua = request.headers.get("User-Agent", "unknown")
    return ip, ua


@router.post(
    "/register",
    response_model=TokenResponse,
    status_code=201,
    summary="Register a new customer account",
    description=(
        "Creates a new customer account. Returns access and refresh tokens "
        "so the user is immediately authenticated after registration."
    ),
)
async def register(
    body: RegisterRequest,
    request: Request,
    db: AsyncSession = Depends(get_db),
):
    ip, ua = _get_client_info(request)
    service = AuthService(db)
    return await service.register(body, ip_address=ip, user_agent=ua)


@router.post(
    "/login",
    response_model=TokenResponse,
    summary="Login and receive JWT tokens",
    description=(
        "Authenticates with email/password (and optional MFA code). "
        "Returns a short-lived access token (30 min) and a long-lived "
        "refresh token (7 days) that can be rotated via /auth/refresh."
    ),
)
async def login(
    body: LoginRequest,
    request: Request,
    db: AsyncSession = Depends(get_db),
):
    ip, ua = _get_client_info(request)
    service = AuthService(db)
    return await service.login(body, ip_address=ip, user_agent=ua)


@router.post(
    "/refresh",
    response_model=TokenResponse,
    summary="Refresh access token",
    description=(
        "Exchanges a valid refresh token for a new access + refresh token pair. "
        "The old refresh token is immediately revoked (rotation pattern)."
    ),
)
async def refresh_token(
    body: RefreshRequest,
    request: Request,
    db: AsyncSession = Depends(get_db),
):
    ip, ua = _get_client_info(request)
    service = AuthService(db)
    return await service.refresh(body.refresh_token, ip_address=ip, user_agent=ua)


@router.post(
    "/logout",
    summary="Revoke refresh token",
    description="Revokes the provided refresh token. The access token will expire naturally.",
)
async def logout(
    body: RefreshRequest,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    service = AuthService(db)
    return await service.logout(body.refresh_token, str(current_user.id))


@router.get(
    "/me",
    summary="Get current authenticated user",
    description="Returns the authenticated user's profile from the JWT claims.",
)
async def get_me(current_user: User = Depends(get_current_user)):
    return {
        "id":           str(current_user.id),
        "email":        current_user.email,
        "full_name":    current_user.full_name,
        "role":         current_user.role.value,
        "status":       current_user.status.value,
        "mfa_enabled":  current_user.mfa_enabled,
        "department":   current_user.department,
        "team_id":      str(current_user.team_id) if current_user.team_id else None,
        "last_login_at": current_user.last_login_at.isoformat() if current_user.last_login_at else None,
    }


@router.post(
    "/change-password",
    summary="Change authenticated user's password",
    description=(
        "Allows an authenticated user to change their own password. "
        "Requires current password for verification. "
        "All existing refresh tokens are revoked after a successful change."
    ),
)
async def change_password(
    body: PasswordChangeRequest,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
    request: Request = None,
):
    ip, ua = _get_client_info(request) if request else (None, None)
    service = AuthService(db)
    return await service.change_password(
        user_id=str(current_user.id),
        current_password=body.current_password,
        new_password=body.new_password,
        ip_address=ip,
        user_agent=ua,
    )


@router.post(
    "/verify-token",
    summary="Validate a token (inter-service use)",
    description=(
        "Used by other microservices to validate a JWT and retrieve the "
        "authenticated user's id, role, and email without hitting the DB directly."
    ),
)
async def verify_token(
    current_user: User = Depends(get_current_user),
):
    return {
        "valid":   True,
        "user_id": str(current_user.id),
        "role":    current_user.role.value,
        "email":   current_user.email,
    }


@router.post(
    "/mfa/setup",
    summary="Generate MFA secret and QR code",
    description=(
        "Generates a TOTP secret and provisioning URI for the authenticated user. "
        "The user must scan the QR code in an authenticator app, then call "
        "/auth/mfa/verify with a valid code to activate MFA."
    ),
)
async def setup_mfa(
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    service = AuthService(db)
    return await service.setup_mfa(current_user.id)


@router.post(
    "/mfa/verify",
    summary="Verify MFA code and enable MFA",
    description="Confirms the TOTP code from the authenticator app and enables MFA on the account.",
)
async def verify_mfa(
    body: MFAVerifyRequest,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    service = AuthService(db)
    return await service.verify_mfa_setup(current_user.id, body.code)
