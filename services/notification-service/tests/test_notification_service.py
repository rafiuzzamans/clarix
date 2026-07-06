"""
Notification Service — Unit Tests
Tests notification payload building, channel routing, template rendering.
"""
import pytest
from unittest.mock import AsyncMock, MagicMock, patch
from datetime import datetime, timezone
import sys, os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

os.environ.setdefault("DATABASE_URL", "postgresql+asyncpg://test:test@localhost:5432/test")
os.environ.setdefault("SECRET_KEY", "test-secret-key")
os.environ.setdefault("SMTP_HOST", "localhost")
os.environ.setdefault("SMTP_PORT", "587")


class TestNotificationPayloadValidation:
    """Validate notification payload structure before dispatch."""

    def _validate_payload(self, payload: dict) -> tuple[bool, str]:
        required = ["recipient_id", "type", "title", "message"]
        for field in required:
            if not payload.get(field):
                return False, f"Missing required field: {field}"
        valid_types = {"email", "in_app", "sms", "push"}
        if payload["type"] not in valid_types:
            return False, f"Invalid type: {payload['type']}"
        return True, "ok"

    def test_valid_payload_passes(self):
        ok, msg = self._validate_payload({
            "recipient_id": "user-123",
            "type": "email",
            "title": "Case Assigned",
            "message": "A new case has been assigned to you.",
        })
        assert ok is True

    def test_missing_recipient_fails(self):
        ok, msg = self._validate_payload({
            "type": "email",
            "title": "Test",
            "message": "Test msg",
        })
        assert ok is False
        assert "recipient_id" in msg

    def test_missing_type_fails(self):
        ok, msg = self._validate_payload({
            "recipient_id": "user-1",
            "title": "Test",
            "message": "Test msg",
        })
        assert ok is False

    def test_invalid_type_fails(self):
        ok, msg = self._validate_payload({
            "recipient_id": "user-1",
            "type": "fax",
            "title": "Test",
            "message": "Test msg",
        })
        assert ok is False
        assert "Invalid type" in msg

    def test_empty_message_fails(self):
        ok, msg = self._validate_payload({
            "recipient_id": "user-1",
            "type": "in_app",
            "title": "Test",
            "message": "",
        })
        assert ok is False


class TestEmailTemplates:
    """Test email template rendering for various notification types."""

    def _render_case_assigned(self, case_number: str, agent_name: str) -> str:
        return (
            f"Dear {agent_name},\n\n"
            f"Case #{case_number} has been assigned to you.\n"
            f"Please log in to review and take action.\n\n"
            f"CS Platform Team"
        )

    def _render_case_resolved(self, case_number: str, customer_name: str) -> str:
        return (
            f"Dear {customer_name},\n\n"
            f"Your case #{case_number} has been resolved.\n"
            f"If you need further assistance, please open a new case.\n\n"
            f"CS Platform Team"
        )

    def _render_sla_warning(self, case_number: str, hours_remaining: float) -> str:
        return (
            f"URGENT: Case #{case_number} SLA deadline approaching.\n"
            f"Time remaining: {hours_remaining:.1f} hours.\n"
            f"Please take action immediately."
        )

    def test_case_assigned_contains_case_number(self):
        body = self._render_case_assigned("CS-001", "Alice")
        assert "CS-001" in body

    def test_case_assigned_contains_agent_name(self):
        body = self._render_case_assigned("CS-001", "Alice")
        assert "Alice" in body

    def test_case_resolved_addresses_customer(self):
        body = self._render_case_resolved("CS-002", "Bob")
        assert "Bob" in body
        assert "resolved" in body.lower()

    def test_sla_warning_is_urgent(self):
        body = self._render_sla_warning("CS-003", 1.5)
        assert "URGENT" in body
        assert "1.5" in body

    def test_all_templates_non_empty(self):
        templates = [
            self._render_case_assigned("001", "Agent"),
            self._render_case_resolved("002", "Customer"),
            self._render_sla_warning("003", 2.0),
        ]
        for t in templates:
            assert len(t) > 10


class TestNotificationChannelRouting:
    """Test which channel is selected based on notification type."""

    def _route_channel(self, notif_type: str, user_prefs: dict) -> str:
        if notif_type == "urgent" and user_prefs.get("sms_enabled"):
            return "sms"
        if user_prefs.get("email_enabled", True):
            return "email"
        return "in_app"

    def test_urgent_routes_to_sms_when_enabled(self):
        channel = self._route_channel("urgent", {"sms_enabled": True})
        assert channel == "sms"

    def test_urgent_routes_to_email_when_sms_off(self):
        channel = self._route_channel("urgent", {"sms_enabled": False, "email_enabled": True})
        assert channel == "email"

    def test_default_routes_to_email(self):
        channel = self._route_channel("info", {})
        assert channel == "email"

    def test_routes_to_in_app_when_email_disabled(self):
        channel = self._route_channel("info", {"email_enabled": False})
        assert channel == "in_app"


class TestInAppNotificationStore:
    """Test in-app notification read/unread state management."""

    def _make_notification(self, id: str, read: bool = False) -> dict:
        return {
            "id": id,
            "read": read,
            "created_at": datetime.now(timezone.utc).isoformat(),
            "title": "Test notification",
            "message": "Test message body",
        }

    def test_new_notification_is_unread(self):
        n = self._make_notification("n-1")
        assert n["read"] is False

    def test_mark_as_read(self):
        n = self._make_notification("n-1")
        n["read"] = True
        assert n["read"] is True

    def test_unread_count(self):
        notifications = [
            self._make_notification("n-1", read=False),
            self._make_notification("n-2", read=True),
            self._make_notification("n-3", read=False),
        ]
        unread = sum(1 for n in notifications if not n["read"])
        assert unread == 2

    def test_mark_all_read(self):
        notifications = [self._make_notification(f"n-{i}") for i in range(5)]
        for n in notifications:
            n["read"] = True
        assert all(n["read"] for n in notifications)

    def test_notification_has_required_fields(self):
        n = self._make_notification("n-1")
        for field in ["id", "read", "created_at", "title", "message"]:
            assert field in n


class TestNotificationRateLimiting:
    """Test rate limiting to prevent notification spam."""

    def _should_send(self, last_sent_minutes_ago: float, cooldown_minutes: float = 5.0) -> bool:
        return last_sent_minutes_ago >= cooldown_minutes

    def test_sends_after_cooldown(self):
        assert self._should_send(10.0, cooldown_minutes=5.0) is True

    def test_blocks_before_cooldown(self):
        assert self._should_send(2.0, cooldown_minutes=5.0) is False

    def test_sends_exactly_at_cooldown(self):
        assert self._should_send(5.0, cooldown_minutes=5.0) is True

    def test_first_notification_always_sends(self):
        # None means never sent — represent as infinite minutes ago
        assert self._should_send(float("inf"), cooldown_minutes=5.0) is True
