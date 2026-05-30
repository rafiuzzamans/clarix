
import uuid
import enum
from datetime import datetime
from sqlalchemy import (
    Column, String, Text, Boolean, Float, Integer,
    DateTime, Enum as SAEnum, text, JSON, UUID
)
from app.core.database import Base


class CaseStatus(str, enum.Enum):
    open = "open"
    in_progress = "in_progress"
    pending_customer = "pending_customer"
    escalated = "escalated"
    resolved = "resolved"
    closed = "closed"


class CasePriority(str, enum.Enum):
    low = "low"
    medium = "medium"
    high = "high"
    urgent = "urgent"


class CaseCategory(str, enum.Enum):
    mortgage = "mortgage"
    debt_collection = "debt_collection"
    credit_reporting = "credit_reporting"
    bank_account = "bank_account"
    credit_card = "credit_card"
    student_loan = "student_loan"
    other = "other"


class CaseSentiment(str, enum.Enum):
    positive = "positive"
    neutral = "neutral"
    negative = "negative"


class CaseSource(str, enum.Enum):
    web = "web"
    mobile = "mobile"
    chatbot = "chatbot"
    email = "email"
    phone = "phone"


class Case(Base):
    __tablename__ = "cases"

    id                = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    case_number       = Column(Integer, unique=True, nullable=False)
    title             = Column(String(500), nullable=False)
    message           = Column(Text, nullable=False)
    category          = Column(SAEnum(CaseCategory))
    priority          = Column(SAEnum(CasePriority), default=CasePriority.medium)
    sentiment         = Column(SAEnum(CaseSentiment))
    status            = Column(SAEnum(CaseStatus), default=CaseStatus.open)
    source            = Column(SAEnum(CaseSource), default=CaseSource.web)
    customer_id       = Column(UUID(as_uuid=True), nullable=False)
    assigned_to       = Column(UUID(as_uuid=True))
    team_id           = Column(UUID(as_uuid=True))
    is_escalated      = Column(Boolean, default=False)
    escalated_at      = Column(DateTime(timezone=True))
    escalation_reason = Column(Text)
    sla_deadline      = Column(DateTime(timezone=True))
    resolved_at       = Column(DateTime(timezone=True))
    closed_at         = Column(DateTime(timezone=True))
    resolution_note   = Column(Text)
    ai_explanation    = Column(Text)
    # AI predictions
    ai_category       = Column(SAEnum(CaseCategory))
    ai_priority       = Column(SAEnum(CasePriority))
    ai_sentiment      = Column(SAEnum(CaseSentiment))
    ai_confidence     = Column(Float)
    ai_overridden     = Column(Boolean, default=False)
    created_at        = Column(DateTime(timezone=True), server_default=text("now()"))
    updated_at        = Column(DateTime(timezone=True), server_default=text("now()"), onupdate=datetime.utcnow)


class CaseNote(Base):
    __tablename__ = "case_notes"

    id          = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    case_id     = Column(UUID(as_uuid=True), nullable=False)
    author_id   = Column(UUID(as_uuid=True), nullable=False)
    content     = Column(Text, nullable=False)
    is_internal = Column(Boolean, default=True)
    created_at  = Column(DateTime(timezone=True), server_default=text("now()"))
    updated_at  = Column(DateTime(timezone=True), server_default=text("now()"), onupdate=datetime.utcnow)


class CaseTimeline(Base):
    __tablename__ = "case_timeline"

    id          = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    case_id     = Column(UUID(as_uuid=True), nullable=False)
    actor_id    = Column(UUID(as_uuid=True))
    event_type  = Column(String(100), nullable=False)
    description = Column(Text, nullable=False)
    old_value   = Column(Text)
    new_value   = Column(Text)
    extra_metadata = Column("metadata", JSON, nullable=True)
    created_at  = Column(DateTime(timezone=True), server_default=text("now()"))




# Add composite index for status+priority
