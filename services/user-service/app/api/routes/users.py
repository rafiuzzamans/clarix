from typing import Optional


from fastapi import APIRouter, Depends, Query
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_db
from app.core.dependencies import require_admin, require_manager_or_above
from app.models.user import UserRole, UserStatus
from app.schemas.user import UserCreate, UserOut, UserRoleUpdate, UserStatusUpdate, UserUpdate
from app.services.user_service import UserService

router = APIRouter(prefix="/users", tags=["Users"])


@router.post("", response_model=UserOut, status_code=201, summary="Create a new user")
async def create_user(
    body: UserCreate,
    db: AsyncSession = Depends(get_db),
    current_user=Depends(require_admin),
):
    return await UserService(db).create_user(body, str(current_user.id))


@router.get("", summary="List users with filters and pagination")
async def list_users(
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
    role: Optional[UserRole] = None,
    status: Optional[UserStatus] = None,
    search: Optional[str] = None,
    db: AsyncSession = Depends(get_db),
    _=Depends(require_manager_or_above),
):
    return await UserService(db).list_users(page, page_size, role, status, search)


@router.get("/{user_id}", response_model=UserOut, summary="Get user by ID")
async def get_user(
    user_id: str,
    db: AsyncSession = Depends(get_db),
    _=Depends(require_manager_or_above),
):
    return await UserService(db).get_user(user_id)


@router.patch("/{user_id}", response_model=UserOut, summary="Update user profile")
async def update_user(
    user_id: str,
    body: UserUpdate,
    db: AsyncSession = Depends(get_db),
    current_user=Depends(require_admin),
):
    return await UserService(db).update_user(user_id, body, str(current_user.id))


@router.patch("/{user_id}/role", response_model=UserOut, summary="Update user role")
async def update_role(
    user_id: str,
    body: UserRoleUpdate,
    db: AsyncSession = Depends(get_db),
    current_user=Depends(require_admin),
):
    return await UserService(db).update_role(user_id, UserRole(body.role.value), str(current_user.id))


@router.patch("/{user_id}/status", response_model=UserOut, summary="Update user status")
async def update_status(
    user_id: str,
    body: UserStatusUpdate,
    db: AsyncSession = Depends(get_db),
    current_user=Depends(require_admin),
):
    return await UserService(db).update_status(user_id, UserStatus(body.status.value), str(current_user.id))


@router.delete("/{user_id}", summary="Deactivate a user")
async def deactivate_user(
    user_id: str,
    db: AsyncSession = Depends(get_db),
    current_user=Depends(require_admin),
):
    return await UserService(db).deactivate_user(user_id, str(current_user.id))


@router.delete("/{user_id}/hard", summary="Permanently delete a user")
async def delete_user(
    user_id: str,
    db: AsyncSession = Depends(get_db),
    current_user=Depends(require_admin),
):
    return await UserService(db).delete_user(user_id, str(current_user.id))


