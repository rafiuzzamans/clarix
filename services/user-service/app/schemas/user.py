from pydantic import BaseModel, EmailStr, field_validator
from typing import Optional
from datetime import datetime
from uuid import UUID

from enum import Enum


class UserRole(str, Enum):
    customer = "customer"
    agent = "agent"
    supervisor = "supervisor"
    manager = "manager"
    admin = "admin"


class UserStatus(str, Enum):
    active = "active"
    inactive = "inactive"
    suspended = "suspended"


class UserCreate(BaseModel):
    email: EmailStr
    password: str
    full_name: str
    role: UserRole = UserRole.customer
    phone: Optional[str] = None
    department: Optional[str] = None
    team_id: Optional[str] = None

    @field_validator("password")
    @classmethod
    def password_strength(cls, v: str) -> str:
        if len(v) < 8:
            raise ValueError("Password must be at least 8 characters")
        if not any(c.isupper() for c in v):
            raise ValueError("Must contain uppercase letter")
        if not any(c.isdigit() for c in v):
            raise ValueError("Must contain a digit")
        return v


class UserUpdate(BaseModel):
    full_name: Optional[str] = None
    phone: Optional[str] = None
    department: Optional[str] = None
    team_id: Optional[str] = None
    avatar_url: Optional[str] = None


class UserRoleUpdate(BaseModel):
    role: UserRole


class UserStatusUpdate(BaseModel):
    status: UserStatus


class UserOut(BaseModel):
    id: UUID
    email: str
    full_name: str
    role: UserRole
    status: UserStatus
    phone: Optional[str] = None
    avatar_url: Optional[str] = None
    department: Optional[str] = None
    team_id: Optional[UUID] = None
    mfa_enabled: bool
    last_login_at: Optional[datetime] = None
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True


class UserListResponse(BaseModel):
    items: list[UserOut]
    total: int
    page: int
    page_size: int
    total_pages: int
