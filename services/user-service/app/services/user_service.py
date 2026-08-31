import math
from typing import Optional


from fastapi import HTTPException, status
import httpx
from passlib.context import CryptContext
from sqlalchemy import func, select, update
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.config import settings
from app.models.user import User, UserRole, UserStatus
from app.schemas.user import UserCreate, UserOut, UserUpdate

pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

async def _emit_audit(action: str, actor_id: Optional[str], resource_id: Optional[str],
                      description: str, metadata: Optional[dict] = None):
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
                    "metadata": metadata or {},
                },
            )
    except Exception:
        pass


class UserService:
    def __init__(self, db: AsyncSession):
        self.db = db

    async def create_user(self, data: UserCreate, actor_id: Optional[str] = None) -> UserOut:
        # Check uniqueness
        existing = await self.db.execute(select(User).where(User.email == data.email))
        if existing.scalar_one_or_none():
            raise HTTPException(status_code=400, detail="Email already registered")

        user = User(
            email=data.email,
            hashed_password=pwd_context.hash(data.password),
            full_name=data.full_name,
            role=UserRole(data.role.value),
            phone=data.phone,
            department=data.department,
            team_id=data.team_id,
        )
        self.db.add(user)
        await self.db.commit()
        await self.db.refresh(user)
        
        await _emit_audit(
            action="user_created",
            actor_id=actor_id,
            resource_id=str(user.id),
            description=f"User {user.email} was created with role {user.role.value}",
        )
        
        return UserOut.model_validate(user)

    async def get_user(self, user_id: str) -> UserOut:
        import uuid
        result = await self.db.execute(select(User).where(User.id == uuid.UUID(user_id)))
        user = result.scalar_one_or_none()
        if not user:
            raise HTTPException(status_code=404, detail="User not found")
        return UserOut.model_validate(user)

    async def list_users(
        self,
        page: int = 1,
        page_size: int = 20,
        role: Optional[UserRole] = None,
        status: Optional[UserStatus] = None,
        search: Optional[str] = None,
    ):
        query = select(User)
        count_query = select(func.count()).select_from(User)

        from sqlalchemy import cast, String
        if role:
            query = query.where(cast(User.role, String) == role.value)
            count_query = count_query.where(cast(User.role, String) == role.value)
        if status:
            query = query.where(cast(User.status, String) == status.value)
            count_query = count_query.where(cast(User.status, String) == status.value)
        if search:
            like = f"%{search}%"
            query = query.where(
                (User.full_name.ilike(like)) | (User.email.ilike(like))
            )
            count_query = count_query.where(
                (User.full_name.ilike(like)) | (User.email.ilike(like))
            )

        total = (await self.db.execute(count_query)).scalar()
        query = query.offset((page - 1) * page_size).limit(page_size)
        result = await self.db.execute(query)
        users = result.scalars().all()

        return {
            "items": [UserOut.model_validate(u) for u in users],
            "total": total,
            "page": page,
            "page_size": page_size,
            "total_pages": math.ceil(total / page_size),
        }

    async def update_user(self, user_id: str, data: UserUpdate, actor_id: Optional[str] = None) -> UserOut:
        import uuid
        result = await self.db.execute(select(User).where(User.id == uuid.UUID(user_id)))
        user = result.scalar_one_or_none()
        if not user:
            raise HTTPException(status_code=404, detail="User not found")

        update_data = data.model_dump(exclude_unset=True)
        
        if "email" in update_data and update_data["email"] != user.email:
            existing = await self.db.execute(select(User).where(User.email == update_data["email"]))
            if existing.scalar_one_or_none():
                raise HTTPException(status_code=400, detail="Email already registered")
        for field, value in update_data.items():
            setattr(user, field, value)

        await self.db.commit()
        await self.db.refresh(user)
        
        await _emit_audit(
            action="user_updated",
            actor_id=actor_id,
            resource_id=user_id,
            description=f"User {user.email} profile was updated",
            metadata={"updated_fields": list(update_data.keys())}
        )
        
        return UserOut.model_validate(user)

    async def update_role(self, user_id: str, role: UserRole, actor_id: Optional[str] = None) -> UserOut:
        import uuid
        result = await self.db.execute(select(User).where(User.id == uuid.UUID(user_id)))
        user = result.scalar_one_or_none()
        if not user:
            raise HTTPException(status_code=404, detail="User not found")
        
        old_role = user.role
        user.role = role
        await self.db.commit()
        await self.db.refresh(user)
        
        await _emit_audit(
            action="user_role_changed",
            actor_id=actor_id,
            resource_id=user_id,
            description=f"User {user.email} role changed from {old_role.value} to {role.value}",
        )
        
        return UserOut.model_validate(user)

    async def update_status(self, user_id: str, new_status: UserStatus, actor_id: Optional[str] = None) -> UserOut:
        import uuid
        result = await self.db.execute(select(User).where(User.id == uuid.UUID(user_id)))
        user = result.scalar_one_or_none()
        if not user:
            raise HTTPException(status_code=404, detail="User not found")
        
        old_status = user.status
        user.status = new_status
        await self.db.commit()
        await self.db.refresh(user)
        
        await _emit_audit(
            action="user_status_changed",
            actor_id=actor_id,
            resource_id=user_id,
            description=f"User {user.email} status changed from {old_status.value} to {new_status.value}",
        )
        
        return UserOut.model_validate(user)

    async def deactivate_user(self, user_id: str, actor_id: Optional[str] = None) -> dict:
        await self.update_status(user_id, UserStatus.inactive, actor_id)
        return {"message": "User deactivated successfully"}

    async def delete_user(self, user_id: str, actor_id: Optional[str] = None) -> dict:
        import uuid
        result = await self.db.execute(select(User).where(User.id == uuid.UUID(user_id)))
        user = result.scalar_one_or_none()
        if not user:
            raise HTTPException(status_code=404, detail="User not found")

        await self.db.delete(user)
        await self.db.commit()

        await _emit_audit(
            action="user_deleted",
            actor_id=actor_id,
            resource_id=user_id,
            description=f"User {user.email} was permanently deleted",
        )
        return {"message": "User permanently deleted"}


