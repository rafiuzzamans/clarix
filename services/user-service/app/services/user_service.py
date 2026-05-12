import math
from typing import Optional


from fastapi import HTTPException, status
from passlib.context import CryptContext
from sqlalchemy import func, select, update
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.user import User, UserRole, UserStatus
from app.schemas.user import UserCreate, UserOut, UserUpdate

pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")


class UserService:
    def __init__(self, db: AsyncSession):
        self.db = db

    async def create_user(self, data: UserCreate) -> UserOut:
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
        return UserOut.model_validate(user)

    async def get_user(self, user_id: str) -> UserOut:
        result = await self.db.execute(select(User).where(User.id == user_id))
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

        if role:
            query = query.where(User.role == role)
            count_query = count_query.where(User.role == role)
        if status:
            query = query.where(User.status == status)
            count_query = count_query.where(User.status == status)
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

    async def update_user(self, user_id: str, data: UserUpdate) -> UserOut:
        result = await self.db.execute(select(User).where(User.id == user_id))
        user = result.scalar_one_or_none()
        if not user:
            raise HTTPException(status_code=404, detail="User not found")

        update_data = data.model_dump(exclude_unset=True)
        for field, value in update_data.items():
            setattr(user, field, value)

        await self.db.commit()
        await self.db.refresh(user)
        return UserOut.model_validate(user)

    async def update_role(self, user_id: str, role: UserRole) -> UserOut:
        result = await self.db.execute(select(User).where(User.id == user_id))
        user = result.scalar_one_or_none()
        if not user:
            raise HTTPException(status_code=404, detail="User not found")
        user.role = role
        await self.db.commit()
        await self.db.refresh(user)
        return UserOut.model_validate(user)

    async def update_status(self, user_id: str, new_status: UserStatus) -> UserOut:
        result = await self.db.execute(select(User).where(User.id == user_id))
        user = result.scalar_one_or_none()
        if not user:
            raise HTTPException(status_code=404, detail="User not found")
        user.status = new_status
        await self.db.commit()
        await self.db.refresh(user)
        return UserOut.model_validate(user)

    async def deactivate_user(self, user_id: str) -> dict:
        await self.update_status(user_id, UserStatus.inactive)
        return {"message": "User deactivated successfully"}


