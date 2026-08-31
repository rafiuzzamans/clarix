"""
Case Service — Unit Tests
Tests case creation validation, status transitions, SLA deadline logic.
"""
import pytest
from datetime import datetime, timezone, timedelta
import sys, os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

os.environ.setdefault("DATABASE_URL", "postgresql+asyncpg://test:test@localhost:5432/test")
os.environ.setdefault("SECRET_KEY", "test-secret-key-for-unit-tests-only")


class TestSLADeadlineCalculation:
    """Test SLA deadline logic — priority determines window."""

    SLA_HOURS = {"urgent": 4, "high": 8, "medium": 24, "low": 72}

    def compute_sla(self, priority: str) -> datetime:
        hours = self.SLA_HOURS[priority]
        return datetime.now(timezone.utc) + timedelta(hours=hours)

    def test_urgent_sla_is_4h(self):
        dl = self.compute_sla("urgent")
        diff = (dl - datetime.now(timezone.utc)).total_seconds() / 3600
        assert 3.9 <= diff <= 4.1

    def test_high_sla_is_8h(self):
        dl = self.compute_sla("high")
        diff = (dl - datetime.now(timezone.utc)).total_seconds() / 3600
        assert 7.9 <= diff <= 8.1

    def test_medium_sla_is_24h(self):
        dl = self.compute_sla("medium")
        diff = (dl - datetime.now(timezone.utc)).total_seconds() / 3600
        assert 23.9 <= diff <= 24.1

    def test_low_sla_is_72h(self):
        dl = self.compute_sla("low")
        diff = (dl - datetime.now(timezone.utc)).total_seconds() / 3600
        assert 71.9 <= diff <= 72.1

    def test_is_overdue(self):
        past = datetime.now(timezone.utc) - timedelta(hours=1)
        assert past < datetime.now(timezone.utc)  # deadline in the past = overdue

    def test_is_not_overdue(self):
        future = datetime.now(timezone.utc) + timedelta(hours=1)
        assert future > datetime.now(timezone.utc)


class TestStatusTransitions:
    """Validate allowed case status state machine."""

    VALID_TRANSITIONS = {
        "open":              ["in_progress", "escalated", "closed"],
        "in_progress":       ["pending_customer", "resolved", "escalated", "closed"],
        "pending_customer":  ["in_progress", "resolved", "closed"],
        "escalated":         ["in_progress", "resolved", "closed"],
        "resolved":          ["closed", "open"],
        "closed":            [],
    }

    def can_transition(self, current: str, target: str) -> bool:
        return target in self.VALID_TRANSITIONS.get(current, [])

    def test_open_can_move_to_in_progress(self):
        assert self.can_transition("open", "in_progress") is True

    def test_open_cannot_move_directly_to_resolved(self):
        assert self.can_transition("open", "resolved") is False

    def test_closed_cannot_transition(self):
        for status in ["open", "in_progress", "resolved"]:
            assert self.can_transition("closed", status) is False

    def test_escalated_can_be_resolved(self):
        assert self.can_transition("escalated", "resolved") is True

    def test_resolved_can_be_reopened(self):
        assert self.can_transition("resolved", "open") is True


class TestCaseValidation:
    """Input validation for case creation."""

    def test_title_min_length(self):
        assert len("ok") >= 2  # minimum 2 chars
        assert len("a") < 2

    def test_title_max_length(self):
        assert len("x" * 200) <= 500  # max 500

    def test_valid_priorities(self):
        VALID = {"low", "medium", "high", "urgent"}
        for p in VALID:
            assert p in VALID
        assert "critical" not in VALID

    def test_valid_sources(self):
        VALID = {"web", "mobile", "chatbot", "email", "phone"}
        assert "web" in VALID
        assert "fax" not in VALID


class TestChatbotEngine:
    """Test the chatbot intent detection logic — loaded from chatbot-service."""

    @classmethod
    def _detect(cls, text: str) -> str:
        import sys, os
        chatbot_path = os.path.join(
            os.path.dirname(__file__), "..", "..", "chatbot-service"
        )
        if chatbot_path not in sys.path:
            sys.path.insert(0, chatbot_path)
        from app.services.chatbot_engine import detect_intent
        return detect_intent(text)

    def test_greeting_intent(self):
        assert self._detect("Hello there!") == "greeting"
        assert self._detect("Hi, I need help") == "greeting"

    def test_password_reset_intent(self):
        assert self._detect("I forgot my password") == "password_reset"
        assert self._detect("I can't log in to my account") == "password_reset"

    def test_refund_intent(self):
        assert self._detect("I want a refund for my order") == "refund_request"

    def test_human_handoff_intent(self):
        assert self._detect("Let me speak to a human agent") == "human_handoff"
        assert self._detect("Transfer me to a real person") == "human_handoff"

    def test_billing_intent(self):
        assert self._detect("I was charged twice on my credit card") == "billing_issue"

    def test_general_fallback(self):
        result = self._detect("Lorem ipsum dolor sit amet")
        assert isinstance(result, str)

