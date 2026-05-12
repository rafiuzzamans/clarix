"""
Automation Rule Engine — handles all 8 automation triggers.
Each trigger sends notifications via the Notification Service.
"""
import os
import httpx
from typing import Optional

NOTIFICATION_URL = os.getenv("NOTIFICATION_SERVICE_URL", "http://notification-service:8007")
CASE_SERVICE_URL = os.getenv("CASE_SERVICE_URL", "http://case-service:8003")


async def _send_notification(recipient_id: str, subject: str, body: str,
                              ref_type: Optional[str] = None, ref_id: Optional[str] = None,
                              notif_type: str = "in_app"):
    """Call notification service to send email + in-app alert."""
    try:
        async with httpx.AsyncClient(timeout=5.0) as client:
            await client.post(f"{NOTIFICATION_URL}/notifications/send", json={
                "recipient_id": recipient_id,
                "type": notif_type,
                "subject": subject,
                "body": body,
                "reference_type": ref_type,
                "reference_id": ref_id,
            })
    except Exception as e:
        print(f"Notification error: {e}")


TRIGGER_HANDLERS = {}


def register_trigger(name: str):
    def decorator(fn):
        TRIGGER_HANDLERS[name] = fn
        return fn
    return decorator


@register_trigger("case_created")
async def on_case_created(reference_id: str, metadata: dict):
    customer_id = metadata.get("customer_id")
    priority = metadata.get("priority", "medium")
    if customer_id:
        await _send_notification(
            recipient_id=customer_id,
            subject="Your support ticket has been created",
            body=f"Your support case has been received and assigned priority: {priority.upper()}. "
                 f"Case ID: {reference_id}. We will be in touch shortly.",
            ref_type="case",
            ref_id=reference_id,
        )


@register_trigger("case_urgent")
async def on_case_urgent(reference_id: str, metadata: dict):
    # Alert supervisors/managers — in real system we'd query user service for supervisor IDs
    # Here we use a system broadcast pattern
    print(f"[AUTOMATION] URGENT case alert: {reference_id} | {metadata}")
    await _send_notification(
        recipient_id="system",  # Would fan out to supervisors
        subject="🚨 Urgent Case Alert",
        body=f"A new urgent priority case has been created or escalated.\nCase ID: {reference_id}\n"
             f"Reason: {metadata.get('reason', 'High priority / escalation')}",
        ref_type="case",
        ref_id=reference_id,
    )


@register_trigger("sentiment_negative")
async def on_negative_sentiment(reference_id: str, metadata: dict):
    print(f"[AUTOMATION] Negative sentiment detected on case {reference_id}")
    await _send_notification(
        recipient_id="system",
        subject="⚠️ Negative Sentiment Alert",
        body=f"Customer sentiment for Case {reference_id} has been detected as NEGATIVE. "
             f"Please review and consider escalation.",
        ref_type="case",
        ref_id=reference_id,
    )


@register_trigger("case_inactivity")
async def on_case_inactivity(reference_id: str, metadata: dict):
    assigned_to = metadata.get("assigned_to")
    if assigned_to:
        await _send_notification(
            recipient_id=assigned_to,
            subject="⏰ Case Inactivity Reminder",
            body=f"Case {reference_id} has had no activity for 24 hours. Please review and update.",
            ref_type="case",
            ref_id=reference_id,
        )


@register_trigger("case_status_changed")
async def on_status_changed(reference_id: str, metadata: dict):
    new_status = metadata.get("status", "unknown")
    customer_id = metadata.get("customer_id")
    if customer_id and new_status in ("resolved", "closed"):
        await _send_notification(
            recipient_id=customer_id,
            subject=f"Your case has been {new_status}",
            body=f"Your support case (ID: {reference_id}) has been marked as {new_status.upper()}. "
                 f"If you have further questions, please create a new ticket.",
            ref_type="case",
            ref_id=reference_id,
        )


@register_trigger("case_resolved")
async def on_case_resolved(reference_id: str, metadata: dict):
    customer_id = metadata.get("customer_id")
    if customer_id:
        await _send_notification(
            recipient_id=customer_id,
            subject="✅ Your case has been resolved",
            body=f"Great news! Your support case {reference_id} has been resolved. "
                 f"We hope we were able to help. Please let us know if you need anything else.",
            ref_type="case",
            ref_id=reference_id,
        )


@register_trigger("case_overdue")
async def on_case_overdue(reference_id: str, metadata: dict):
    assigned_to = metadata.get("assigned_to")
    if assigned_to:
        await _send_notification(
            recipient_id=assigned_to,
            subject="🔴 Overdue Case Alert",
            body=f"Case {reference_id} has exceeded its SLA deadline. Immediate attention required.",
            ref_type="case",
            ref_id=reference_id,
        )


@register_trigger("daily_summary")
async def on_daily_summary(reference_id: str, metadata: dict):
    manager_id = metadata.get("manager_id")
    summary = metadata.get("summary", "No summary available.")
    if manager_id:
        await _send_notification(
            recipient_id=manager_id,
            subject="📊 Daily Case Summary Report",
            body=f"Here is your daily summary:\n\n{summary}",
        )


async def dispatch_trigger(trigger_type: str, reference_id: str, metadata: dict) -> dict:
    handler = TRIGGER_HANDLERS.get(trigger_type)
    if not handler:
        return {"status": "skipped", "reason": f"No handler for trigger '{trigger_type}'"}
    try:
        await handler(reference_id, metadata)
        return {"status": "processed", "trigger": trigger_type}
    except Exception as e:
        return {"status": "error", "trigger": trigger_type, "error": str(e)}
