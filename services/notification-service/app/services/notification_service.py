"""
Notification Service — sends email via SMTP (MailHog locally) and
persists in-app notifications to PostgreSQL.
"""
import os

from datetime import datetime, timezone
from typing import Optional

import aiosmtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart

SMTP_HOST = os.getenv("SMTP_HOST", "mailhog")
SMTP_PORT = int(os.getenv("SMTP_PORT", 1025))
EMAIL_FROM = os.getenv("EMAIL_FROM", "noreply@csplatform.local")


async def send_email(to: str, subject: str, body: str):
    """Send plain-text email via SMTP."""
    msg = MIMEMultipart("alternative")
    msg["Subject"] = subject
    msg["From"] = EMAIL_FROM
    msg["To"] = to

    html_body = f"""
    <!DOCTYPE html>
    <html>
    <body style="font-family: Arial, sans-serif; background: #f4f4f4; padding: 20px;">
      <div style="max-width:600px; margin:auto; background:white; border-radius:8px; padding:30px;">
        <div style="background: linear-gradient(135deg, #6366f1, #8b5cf6); padding:20px; border-radius:6px; margin-bottom:20px;">
          <h2 style="color:white; margin:0;">CS Platform</h2>
        </div>
        <p style="color:#374151; font-size:15px; line-height:1.6;">{body.replace(chr(10), '<br>')}</p>
        <hr style="border:none; border-top:1px solid #e5e7eb; margin:20px 0;">
        <p style="color:#9ca3af; font-size:12px;">
          This is an automated message from the CS Platform. Please do not reply directly.
        </p>
      </div>
    </body>
    </html>
    """

    msg.attach(MIMEText(body, "plain"))
    msg.attach(MIMEText(html_body, "html"))

    try:
        await aiosmtplib.send(
            msg,
            hostname=SMTP_HOST,
            port=SMTP_PORT,
            start_tls=False,
        )
        return True
    except Exception as e:
        print(f"[NOTIFICATION] Email send failed: {e}")
        return False


async def persist_notification(db, recipient_id: str, notif_type: str,
                                subject: Optional[str], body: str,
                                ref_type: Optional[str], ref_id: Optional[str]) -> dict:
    """Write notification record to PostgreSQL."""
    from sqlalchemy import text
    import uuid
    notif_id = str(uuid.uuid4())
    await db.execute(
        text("""
        INSERT INTO notifications (id, recipient_id, type, status, subject, body,
                                   reference_type, reference_id, sent_at)
        VALUES (:id, :recipient_id, :type, 'sent', :subject, :body,
                :ref_type, :ref_id, :sent_at)
        """),
        {
            "id": notif_id,
            "recipient_id": recipient_id,
            "type": notif_type,
            "subject": subject,
            "body": body,
            "ref_type": ref_type,
            "ref_id": ref_id,
            "sent_at": datetime.now(timezone.utc),
        }
    )
    await db.commit()
    return {"id": notif_id, "status": "sent"}

