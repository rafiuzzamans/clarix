import math
from datetime import datetime, timedelta, timezone
from typing import Optional


import httpx
from fastapi import HTTPException
from sqlalchemy import func, select, cast, String
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.config import settings
from app.models.case import Case, CaseNote, CaseTimeline, CasePriority, CaseStatus
from app.schemas.case import (
    CaseAssign, CaseCreate, CaseEscalate, CaseOut, CaseUpdate, NoteCreate, NoteUpdate, NoteOut, TimelineOut
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
                f"{settings.AI_SERVICE_URL}/ai/predict",
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


async def _emit_audit(action: str, actor_id: Optional[str], resource_id: Optional[str],
                      description: str, metadata: Optional[dict] = None):
    try:
        async with httpx.AsyncClient(timeout=2.0) as client:
            await client.post(
                f"{settings.AUDIT_SERVICE_URL}/audit/logs",
                json={
                    "actor_id": actor_id,
                    "action": action,
                    "resource_type": "case",
                    "resource_id": resource_id,
                    "description": description,
                    "metadata": metadata or {},
                },
            )
    except Exception:
        pass


class CaseService:
    def __init__(self, db: AsyncSession):
        self.db = db

    async def create_case(self, data: CaseCreate, customer_id: str, actor_id: str) -> CaseOut:
        # Get AI predictions
        ai_data = await _call_ai_service(f"{data.title}. {data.message}")

        # Determine priority (AI or default)
        priority = data.priority
        ai_priority = ai_cat = ai_sent = None
        ai_conf = ai_exp = None

        if ai_data:
            ai_cat = ai_data.get("label_category")
            ai_priority = ai_data.get("label_priority")
            ai_sent = ai_data.get("label_sentiment")
            ai_conf = ai_data.get("confidence")
            if "explanation" in ai_data and "top_features" in ai_data["explanation"]:
                import json
                ai_exp_obj = {
                    "top_features": ai_data["explanation"]["top_features"],
                    "probabilities": ai_data.get("category", {}).get("probabilities", {})
                }
                ai_exp = json.dumps(ai_exp_obj)
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
            category=data.category,
            priority=priority,
            customer_id=customer_id,
            sla_deadline=sla_deadline,
            ai_priority=ai_priority,
            ai_category=ai_cat,
            ai_sentiment=ai_sent,
            ai_confidence=ai_conf,
            ai_explanation=ai_exp,
        )

        # Set category from AI if not provided
        if not data.category and ai_cat:
            try:
                from app.models.case import CaseCategory
                case.category = CaseCategory(ai_cat)
            except (ValueError, TypeError):
                # Fallback if AI category doesn't strictly match Enum
                pass

        if ai_sent:
            try:
                from app.models.case import CaseSentiment
                case.sentiment = CaseSentiment(ai_sent)
            except (ValueError, TypeError):
                pass
                
        # AI Routing Logic
        # Route to human teams by default, but let AI Agent intercept high confidence issues
        if ai_conf and ai_conf > 0.85:
            # High confidence -> Route to AI Agent for auto-resolution
            case.assigned_to = "99999999-9999-9999-9999-999999999999"
            case.team_id = "88888888-8888-8888-8888-888888888888"
        else:
            # Route to human teams based on category
            if ai_cat in ("billing", "returns", "debt_collection", "credit_card"):
                case.team_id = "33333333-3333-3333-3333-333333333333" # Billing Team
            elif ai_cat in ("technical_support", "mortgage", "bank_account"):
                case.team_id = "22222222-2222-2222-2222-222222222222" # Tier 2 Support
            else:
                case.team_id = "11111111-1111-1111-1111-111111111111" # Tier 1 Support


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

        await _emit_audit(
            action="case_created",
            actor_id=actor_id,
            resource_id=str(case.id),
            description=f"Case #{case.case_number} was created",
            metadata={"priority": priority.value, "category": case.category.value if case.category else None}
        )

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
        customer_id=None, assigned_to=None, team_id=None, search=None
    ):
        query = select(Case)
        count_q = select(func.count()).select_from(Case)

        filters = []
        if status:     filters.append(cast(Case.status, String) == status.value)
        if priority:   filters.append(cast(Case.priority, String) == priority.value)
        if category:   filters.append(cast(Case.category, String) == category.value)
        if customer_id: filters.append(Case.customer_id == customer_id)
        if assigned_to: filters.append(Case.assigned_to == assigned_to)
        if team_id: filters.append(Case.team_id == team_id)
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
        
        await _emit_audit(
            action="case_updated",
            actor_id=actor_id,
            resource_id=case_id,
            description=f"Case #{case.case_number} was updated",
            metadata={"updated_fields": list(update_data.keys())}
        )
        
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
        
        await _emit_audit(
            action="case_assigned",
            actor_id=actor_id,
            resource_id=case_id,
            description=f"Case #{case.case_number} was assigned to agent {data.agent_id}",
        )
        
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

        # Trigger automation
        await _notify_automation("case_escalated", str(case.id), {
            "reason": data.reason,
            "customer_id": str(case.customer_id)
        })

        await _emit_audit(
            action="case_escalated",
            actor_id=actor_id,
            resource_id=case_id,
            description=f"Case #{case.case_number} was escalated",
            metadata={"reason": data.reason}
        )

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

    async def update_note(self, case_id: str, note_id: str, data: NoteUpdate, actor_id: str) -> NoteOut:
        result = await self.db.execute(select(CaseNote).where(CaseNote.id == note_id, CaseNote.case_id == case_id))
        note = result.scalar_one_or_none()
        if not note:
            raise HTTPException(status_code=404, detail="Note not found")

        # Allow update if actor is the author, or if we assume supervisors can (omitted for simplicity, checked at route)
        if data.content is not None:
            note.content = data.content
        if data.is_internal is not None:
            note.is_internal = data.is_internal

        await _add_timeline(
            self.db, case_id, actor_id, "note_updated",
            f"Note updated"
        )
        await self.db.commit()
        await self.db.refresh(note)
        return NoteOut.model_validate(note)

    async def delete_note(self, case_id: str, note_id: str, actor_id: str):
        result = await self.db.execute(select(CaseNote).where(CaseNote.id == note_id, CaseNote.case_id == case_id))
        note = result.scalar_one_or_none()
        if not note:
            raise HTTPException(status_code=404, detail="Note not found")

        await self.db.delete(note)
        await _add_timeline(
            self.db, case_id, actor_id, "note_deleted",
            f"Note deleted"
        )
        await self.db.commit()
        return {"status": "deleted"}

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

# Validate agent role on assign

# Add note count to case list

# Add sentiment auto-update from AI
