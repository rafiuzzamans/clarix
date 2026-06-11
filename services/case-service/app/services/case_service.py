import math
from datetime import datetime, timedelta, timezone
from typing import Optional


import httpx
from fastapi import HTTPException
from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.config import settings
from app.models.case import Case, CaseNote, CaseTimeline, CasePriority, CaseStatus
from app.schemas.case import (
    CaseAssign, CaseCreate, CaseEscalate, CaseOut, CaseUpdate, NoteCreate, NoteOut, TimelineOut
)

SLA_HOURS = {
    CasePriority.urgent: 2,
    CasePriority.high: 8,
    CasePriority.medium: 24,
    CasePriority.low: 72,
}


async def _call_ai_service(text: str) -> Optional[dict]:
    try:
        async with httpx.AsyncClient(timeout=5.0) as client:
            resp = await client.post(
                f"{settings.AI_SERVICE_URL}/predict",
                json={"text": text}
            )
            if resp.status_code == 200:
                return resp.json()
    except Exception:
        pass
    return None


async def _notify_automation(trigger: str, case_id: str, metadata: dict):
    try:
        async with httpx.AsyncClient(timeout=2.0) as client:
            await client.post(
                f"{settings.AUTOMATION_SERVICE_URL}/trigger",
                json={"trigger_type": trigger, "reference_id": case_id, "extra_data": metadata}
            )
    except Exception:
        pass


async def _add_timeline(db: AsyncSession, case_id, actor_id, event_type, description,
                         old_value=None, new_value=None, meta=None):
    entry = CaseTimeline(
        case_id=case_id, actor_id=actor_id,
        event_type=event_type, description=description,
        old_value=old_value, new_value=new_value, metadata=meta
    )
    db.add(entry)


class CaseService:
    def __init__(self, db: AsyncSession):
        self.db = db

    async def create_case(self, data: CaseCreate, customer_id: str, actor_id: str) -> CaseOut:
        # Get AI predictions
        ai_data = await _call_ai_service(f"{data.title}. {data.message}")

        # Determine priority (AI or default)
        priority = data.priority
        ai_priority = ai_cat = ai_sent = None
        ai_conf = None

        if ai_data:
            ai_cat = ai_data.get("category")
            ai_priority = ai_data.get("priority")
            ai_sent = ai_data.get("sentiment")
            ai_conf = ai_data.get("confidence")
            if not priority and ai_priority:
                try:
                    priority = CasePriority(ai_priority)
                except ValueError:
                    pass

        priority = priority or CasePriority.medium
        sla_deadline = datetime.now(timezone.utc) + timedelta(hours=SLA_HOURS[priority])

        case = Case(
            title=data.title,
            message=data.message,
            source=data.source,
            category=data.category or (ai_cat and __builtins__),
            priority=priority,
            customer_id=customer_id,
            sla_deadline=sla_deadline,
            ai_priority=ai_priority,
            ai_category=ai_cat,
            ai_sentiment=ai_sent,
            ai_confidence=ai_conf,
        )

        # Set category from AI if not provided
        if not data.category and ai_cat:
            try:
                from app.models.case import CaseCategory
                case.category = CaseCategory(ai_cat)
            except (ValueError, TypeError):
                pass

        if ai_sent:
            try:
                from app.models.case import CaseSentiment
                case.sentiment = CaseSentiment(ai_sent)
            except (ValueError, TypeError):
                pass
                
        # AI Routing Logic
        if ai_cat:
            # Route to AI Agent by default for Agentic resolution
            case.assigned_to = "99999999-9999-9999-9999-999999999999"
            case.team_id = "88888888-8888-8888-8888-888888888888"
            
            # If we wanted to route to specific human teams based on category:
            # if ai_cat == "billing": case.team_id = "77777777-..."


        self.db.add(case)
        await self.db.flush()  # Get generated case_number and id

        # Handle case_number (SERIAL — assigned by DB)
        await self.db.refresh(case)

        await _add_timeline(
            self.db, case.id, actor_id, "case_created",
            f"Case #{case.case_number} created via {data.source.value}"
        )
        await self.db.commit()
        await self.db.refresh(case)

        # Trigger automation
        await _notify_automation("case_created", str(case.id), {
            "priority": priority.value,
            "customer_id": str(customer_id),
        })
        if priority in (CasePriority.urgent, CasePriority.high):
            await _notify_automation("case_urgent", str(case.id), {"priority": priority.value})

        return CaseOut.model_validate(case)

    async def get_case(self, case_id: str) -> CaseOut:
        result = await self.db.execute(select(Case).where(Case.id == case_id))
        case = result.scalar_one_or_none()
        if not case:
            raise HTTPException(status_code=404, detail="Case not found")
        return CaseOut.model_validate(case)

    async def list_cases(
        self, page=1, page_size=20,
        status=None, priority=None, category=None,
        customer_id=None, assigned_to=None, search=None
    ):
        query = select(Case)
        count_q = select(func.count()).select_from(Case)

        filters = []
        if status:     filters.append(Case.status == status)
        if priority:   filters.append(Case.priority == priority)
        if category:   filters.append(Case.category == category)
        if customer_id: filters.append(Case.customer_id == customer_id)
        if assigned_to: filters.append(Case.assigned_to == assigned_to)
        if search:
            like = f"%{search}%"
            filters.append((Case.title.ilike(like)) | (Case.message.ilike(like)))

        for f in filters:
            query = query.where(f)
            count_q = count_q.where(f)

        total = (await self.db.execute(count_q)).scalar()
        query = query.order_by(Case.created_at.desc()).offset((page - 1) * page_size).limit(page_size)
        result = await self.db.execute(query)
        cases = result.scalars().all()

        return {
            "items": [CaseOut.model_validate(c) for c in cases],
            "total": total,
            "page": page,
            "page_size": page_size,
            "total_pages": math.ceil(total / page_size),
        }

    async def update_case(self, case_id: str, data: CaseUpdate, actor_id: str) -> CaseOut:
        result = await self.db.execute(select(Case).where(Case.id == case_id))
        case = result.scalar_one_or_none()
        if not case:
            raise HTTPException(status_code=404, detail="Case not found")

        update_data = data.model_dump(exclude_unset=True)
        for field, value in update_data.items():
            old_val = str(getattr(case, field)) if getattr(case, field) else None
            setattr(case, field, value)
            await _add_timeline(
                self.db, case.id, actor_id, "case_updated",
                f"Field '{field}' updated", old_val, str(value)
            )

        # Handle resolved state
        if data.status == CaseStatus.resolved and not case.resolved_at:
            case.resolved_at = datetime.now(timezone.utc)
            await _notify_automation("case_status_changed", str(case_id),
                                     {"status": "resolved", "customer_id": str(case.customer_id)})

        await self.db.commit()
        await self.db.refresh(case)
        return CaseOut.model_validate(case)

    async def assign_case(self, case_id: str, data: CaseAssign, actor_id: str) -> CaseOut:
        result = await self.db.execute(select(Case).where(Case.id == case_id))
        case = result.scalar_one_or_none()
        if not case:
            raise HTTPException(status_code=404, detail="Case not found")

        old_agent = str(case.assigned_to) if case.assigned_to else "unassigned"
        case.assigned_to = data.agent_id
        if data.team_id:
            case.team_id = data.team_id
        if case.status == CaseStatus.open:
            case.status = CaseStatus.in_progress

        await _add_timeline(
            self.db, case.id, actor_id, "case_assigned",
            f"Case assigned to agent {data.agent_id}",
            old_agent, str(data.agent_id)
        )
        await self.db.commit()
        await self.db.refresh(case)
        return CaseOut.model_validate(case)

    async def escalate_case(self, case_id: str, data: CaseEscalate, actor_id: str) -> CaseOut:
        result = await self.db.execute(select(Case).where(Case.id == case_id))
        case = result.scalar_one_or_none()
        if not case:
            raise HTTPException(status_code=404, detail="Case not found")

        case.is_escalated = True
        case.escalated_at = datetime.now(timezone.utc)
        case.escalation_reason = data.reason
        case.status = CaseStatus.escalated
        case.priority = CasePriority.urgent

        await _add_timeline(
            self.db, case.id, actor_id, "case_escalated",
            f"Case escalated: {data.reason}"
        )
        await self.db.commit()
        await self.db.refresh(case)

        await _notify_automation("case_urgent", str(case_id), {
            "reason": data.reason,
            "customer_id": str(case.customer_id)
        })
        return CaseOut.model_validate(case)

    async def add_note(self, case_id: str, data: NoteCreate, author_id: str) -> NoteOut:
        result = await self.db.execute(select(Case).where(Case.id == case_id))
        if not result.scalar_one_or_none():
            raise HTTPException(status_code=404, detail="Case not found")

        note = CaseNote(case_id=case_id, author_id=author_id,
                        content=data.content, is_internal=data.is_internal)
        self.db.add(note)
        await _add_timeline(
            self.db, case_id, author_id, "note_added",
            f"{'Internal' if data.is_internal else 'Public'} note added"
        )
        await self.db.commit()
        await self.db.refresh(note)
        return NoteOut.model_validate(note)

    async def get_timeline(self, case_id: str) -> list[TimelineOut]:
        result = await self.db.execute(
            select(CaseTimeline)
            .where(CaseTimeline.case_id == case_id)
            .order_by(CaseTimeline.created_at.asc())
        )
        entries = result.scalars().all()
        return [TimelineOut.model_validate(e) for e in entries]

    async def get_notes(self, case_id: str, include_internal: bool = True) -> list[NoteOut]:
        query = select(CaseNote).where(CaseNote.case_id == case_id)
        if not include_internal:
            query = query.where(CaseNote.is_internal == False)
        result = await self.db.execute(query.order_by(CaseNote.created_at.asc()))
        return [NoteOut.model_validate(n) for n in result.scalars().all()]




# Add SLA breach detection logic

# Improve pagination performance

# Emit timeline event on status change

# Handle unassigned cases in manager view

# Add escalation audit trail

# Sort cases by created_at desc by default

# Return 404 when case not found

# Prevent closing already-closed cases

# Add reassignment timeline event

# Compute SLA deadline on create
