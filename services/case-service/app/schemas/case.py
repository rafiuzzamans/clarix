from pydantic import BaseModel
from typing import Optional, List
from datetime import datetime
from uuid import UUID

from app.models.case import CaseCategory, CasePriority, CaseSentiment, CaseSource, CaseStatus


class CaseCreate(BaseModel):
    title: str
    message: str
    source: CaseSource = CaseSource.web
    category: Optional[CaseCategory] = None
    priority: Optional[CasePriority] = None


class CaseUpdate(BaseModel):
    title: Optional[str] = None
    category: Optional[CaseCategory] = None
    priority: Optional[CasePriority] = None
    sentiment: Optional[CaseSentiment] = None
    status: Optional[CaseStatus] = None
    resolution_note: Optional[str] = None


class CaseAssign(BaseModel):
    agent_id: UUID
    team_id: Optional[UUID] = None


class CaseEscalate(BaseModel):
    reason: str


class CaseOut(BaseModel):
    id: UUID
    case_number: int
    title: str
    message: str
    category: Optional[CaseCategory] = None
    priority: CasePriority
    sentiment: Optional[CaseSentiment] = None
    status: CaseStatus
    source: CaseSource
    customer_id: UUID
    assigned_to: Optional[UUID] = None
    team_id: Optional[UUID] = None
    is_escalated: bool
    escalated_at: Optional[datetime] = None
    escalation_reason: Optional[str] = None
    sla_deadline: Optional[datetime] = None
    resolved_at: Optional[datetime] = None
    resolution_note: Optional[str] = None
    ai_category: Optional[CaseCategory] = None
    ai_priority: Optional[CasePriority] = None
    ai_sentiment: Optional[CaseSentiment] = None
    ai_confidence: Optional[float] = None
    ai_explanation: Optional[str] = None
    ai_overridden: bool
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True


class CaseListResponse(BaseModel):
    items: List[CaseOut]
    total: int
    page: int
    page_size: int
    total_pages: int


class NoteCreate(BaseModel):
    content: str
    is_internal: bool = True


class NoteUpdate(BaseModel):
    content: Optional[str] = None
    is_internal: Optional[bool] = None


class NoteOut(BaseModel):
    id: UUID
    case_id: UUID
    author_id: UUID
    content: str
    is_internal: bool
    created_at: datetime

    class Config:
        from_attributes = True


class TimelineOut(BaseModel):
    id: UUID
    case_id: UUID
    actor_id: Optional[UUID] = None
    event_type: str
    description: str
    old_value: Optional[str] = None
    new_value: Optional[str] = None
    created_at: datetime

    class Config:
        from_attributes = True

# Add ai_explanation to CaseOut schema

# Add closed_at to CaseOut
