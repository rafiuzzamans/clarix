
from datetime import datetime
import uuid
from sqlalchemy import Column, String, Boolean, DateTime, Enum as SAEnum, text, UUID
from sqlalchemy import Text
from app.core.database import Base
import enum


class UserRole(str, enum.Enum):
    customer = "customer"
    agent = "agent"
    supervisor = "supervisor"
    manager = "manager"
    admin = "admin"


class UserStatus(str, enum.Enum):
    active = "active"
    inactive = "inactive"
    suspended = "suspended"


class User(Base):
    __tablename__ = "users"

    id              = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    email           = Column(String(255), unique=True, nullable=False, index=True)
    hashed_password = Column(String(255), nullable=False)
    full_name       = Column(String(255), nullable=False)
    role            = Column(SAEnum(UserRole), nullable=False, default=UserRole.customer)
    status          = Column(SAEnum(UserStatus), nullable=False, default=UserStatus.active)
    phone           = Column(String(50))
    avatar_url      = Column(String)
    department      = Column(String(100))
    team_id         = Column(UUID(as_uuid=True))
    mfa_enabled     = Column(Boolean, default=False)
    mfa_secret      = Column(String(255))
    last_login_at   = Column(DateTime(timezone=True))
    created_at      = Column(DateTime(timezone=True), server_default=text("now()"))
    updated_at      = Column(DateTime(timezone=True), server_default=text("now()"), onupdate=datetime.utcnow)


class RefreshToken(Base):
    __tablename__ = "refresh_tokens"

    id          = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    user_id     = Column(UUID(as_uuid=True), nullable=False, index=True)
    token_hash  = Column(String(255), unique=True, nullable=False)
    expires_at  = Column(DateTime(timezone=True), nullable=False)
    revoked     = Column(Boolean, default=False)
    ip_address  = Column(String(45))
    user_agent  = Column(String)
    created_at  = Column(DateTime(timezone=True), server_default=text("now()"))


