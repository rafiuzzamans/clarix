from fastapi import APIRouter, Depends
from pydantic import BaseModel
from typing import Optional
from sqlalchemy.ext.asyncio import AsyncSession
from app.core.database import get_db
from app.services.notification_service import send_email, persist_notification

router = APIRouter(prefix="/notifications", tags=["Notifications"])


class SendRequest(BaseModel):
    recipient_id: str
    type: str = "in_app"
    subject: Optional[str] = None
    body: str
    reference_type: Optional[str] = None
    reference_id: Optional[str] = None
    email_address: Optional[str] = None   # override recipient email


@router.post("/send", summary="Send a notification (email + in-app)")
async def send_notification(body: SendRequest, db: AsyncSession = Depends(get_db)):
    email_sent = False

    # Only send email if we have an address (system passes it) or it's an email type
    if body.email_address and body.type in ("email", "in_app"):
        email_sent = await send_email(
            to=body.email_address,
            subject=body.subject or "Notification from CS Platform",
            body=body.body,
        )

    # Persist in-app notification (skip for "system" recipient)
    persisted = None
    if body.recipient_id != "system":
        persisted = await persist_notification(
            db=db,
            recipient_id=body.recipient_id,
            notif_type=body.type,
            subject=body.subject,
            body=body.body,
            ref_type=body.reference_type,
            ref_id=body.reference_id,
        )

    return {
        "status": "sent",
        "email_sent": email_sent,
        "notification": persisted,
    }


@router.get("/inbox/{user_id}", summary="Get in-app notifications for a user")
async def get_inbox(user_id: str, unread_only: bool = False, db: AsyncSession = Depends(get_db)):
    from sqlalchemy import text
    clause = "AND read_at IS NULL" if unread_only else ""
    result = await db.execute(
        text(f"""
        SELECT id, subject, body, type, status, reference_type, reference_id,
               read_at, sent_at, created_at
        FROM notifications
        WHERE recipient_id = :uid {clause}
        ORDER BY created_at DESC
        LIMIT 50
        """),
        {"uid": user_id}
    )
    rows = result.mappings().all()
    return {"notifications": [dict(r) for r in rows]}


@router.patch("/read/{notification_id}", summary="Mark notification as read")
async def mark_read(notification_id: str, db: AsyncSession = Depends(get_db)):
    from sqlalchemy import text
    from datetime import datetime, timezone
    await db.execute(
        text("UPDATE notifications SET read_at = :now WHERE id = :id"),
        {"now": datetime.now(timezone.utc), "id": notification_id}
    )
    await db.commit()
    return {"status": "marked_read"}
