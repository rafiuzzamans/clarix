from pydantic import BaseModel
from typing import Optional, List
from datetime import datetime

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
    agent_id: str
    team_id: Optional[str] = None


class CaseEscalate(BaseModel):
    reason: str


class CaseOut(BaseModel):
    id: str
    case_number: int
    title: str
    message: str
    category: Optional[CaseCategory] = None
    priority: CasePriority
    sentiment: Optional[CaseSentiment] = None
    status: CaseStatus
    source: CaseSource
    customer_id: str
    assigned_to: Optional[str] = None
    team_id: Optional[str] = None
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


class NoteOut(BaseModel):
    id: str
    case_id: str
    author_id: str
    content: str
    is_internal: bool
    created_at: datetime

    class Config:
        from_attributes = True


class TimelineOut(BaseModel):
    id: str
    case_id: str
    actor_id: Optional[str] = None
    event_type: str
    description: str
    old_value: Optional[str] = None
    new_value: Optional[str] = None
    created_at: datetime

    class Config:
        from_attributes = True
