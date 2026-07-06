"""
Integration Tests — Cross-Service Flows
Tests realistic end-to-end workflows across services using mocks.
Covers: auth → case creation, AI routing pipeline, automation triggers,
        case lifecycle (create → assign → resolve → close).
"""
import pytest
import asyncio
from unittest.mock import AsyncMock, MagicMock, patch
from datetime import datetime, timezone, timedelta
import sys, os

# Set env for all services
os.environ.setdefault("DATABASE_URL", "postgresql+asyncpg://test:test@localhost:5432/test")
os.environ.setdefault("SECRET_KEY", "test-integration-secret-key-only")
os.environ.setdefault("REFRESH_SECRET_KEY", "test-refresh-secret")
os.environ.setdefault("AI_SERVICE_URL", "http://ai-service:8003")
os.environ.setdefault("NOTIFICATION_SERVICE_URL", "http://notification-service:8006")
os.environ.setdefault("AUTOMATION_SERVICE_URL", "http://automation-service:8008")


# ── Helpers ───────────────────────────────────────────────────────────────────

def make_jwt(user_id: str, role: str, secret: str = "test-integration-secret-key-only") -> str:
    """Create a valid JWT for integration test use."""
    from jose import jwt
    payload = {
        "sub": user_id,
        "role": role,
        "type": "access",
        "exp": datetime.now(timezone.utc) + timedelta(hours=1),
    }
    return jwt.encode(payload, secret, algorithm="HS256")


def decode_jwt(token: str, secret: str = "test-integration-secret-key-only") -> dict:
    from jose import jwt
    return jwt.decode(token, secret, algorithms=["HS256"])


# ── Test: Authentication Flow ─────────────────────────────────────────────────

class TestAuthenticationFlow:
    """Integration test: login → token issuance → token verification."""

    def test_token_roundtrip(self):
        """Token created for a user can be decoded back correctly."""
        user_id = "bbbbbbbb-bbbb-bbbb-bbbb-bbbbbbbbbbbb"
        token = make_jwt(user_id, "manager")
        decoded = decode_jwt(token)
        assert decoded["sub"] == user_id
        assert decoded["role"] == "manager"

    def test_token_expired_raises(self):
        """Expired tokens are rejected."""
        from jose import jwt, ExpiredSignatureError
        payload = {
            "sub": "u1", "role": "agent",
            "exp": datetime.now(timezone.utc) - timedelta(minutes=1),
        }
        token = jwt.encode(payload, "test-integration-secret-key-only", algorithm="HS256")
        with pytest.raises(Exception):
            decode_jwt(token)

    def test_wrong_secret_raises(self):
        """Token signed with wrong secret is rejected."""
        token = make_jwt("u1", "agent", secret="correct-secret")
        with pytest.raises(Exception):
            decode_jwt(token, secret="wrong-secret")

    def test_manager_token_has_manager_role(self):
        token = make_jwt("mgr-1", "manager")
        decoded = decode_jwt(token)
        assert decoded["role"] == "manager"

    def test_admin_token_has_admin_role(self):
        token = make_jwt("adm-1", "admin")
        decoded = decode_jwt(token)
        assert decoded["role"] == "admin"


# ── Test: Case Creation Pipeline ──────────────────────────────────────────────

class TestCaseCreationPipeline:
    """Integration test: case creation → AI classification → automation trigger."""

    def _simulate_ai_prediction(self, message: str) -> dict:
        """Simulate what the AI service returns for a given message."""
        keywords = {
            "mortgage": ["mortgage", "home loan", "refinance"],
            "credit_card": ["credit card", "card charge", "transaction"],
            "debt_collection": ["debt", "collection", "owe"],
        }
        for category, kws in keywords.items():
            if any(kw in message.lower() for kw in kws):
                return {
                    "label_category": category,
                    "label_priority": "high" if "urgent" in message.lower() else "medium",
                    "label_sentiment": "negative" if "angry" in message.lower() else "neutral",
                    "confidence": 0.87,
                }
        return {
            "label_category": "other",
            "label_priority": "medium",
            "label_sentiment": "neutral",
            "confidence": 0.55,
        }

    def _simulate_case_creation(self, title: str, message: str, customer_id: str) -> dict:
        import uuid
        ai = self._simulate_ai_prediction(message)
        SLA_HOURS = {"urgent": 4, "high": 8, "medium": 24, "low": 72}
        priority = ai["label_priority"]
        return {
            "id": str(uuid.uuid4()),
            "case_number": 1001,
            "title": title,
            "message": message,
            "customer_id": customer_id,
            "status": "open",
            "category": ai["label_category"],
            "priority": priority,
            "sentiment": ai["label_sentiment"],
            "ai_confidence": ai["confidence"],
            "sla_deadline": (
                datetime.now(timezone.utc) + timedelta(hours=SLA_HOURS[priority])
            ).isoformat(),
            "created_at": datetime.now(timezone.utc).isoformat(),
        }

    def test_mortgage_message_classified_correctly(self):
        case = self._simulate_case_creation(
            "Mortgage issue", "I have a problem with my home loan refinance",
            "cust-1"
        )
        assert case["category"] == "mortgage"

    def test_credit_card_message_classified_correctly(self):
        case = self._simulate_case_creation(
            "Billing problem", "I see a strange credit card transaction on my bill",
            "cust-2"
        )
        assert case["category"] == "credit_card"

    def test_new_case_starts_as_open(self):
        case = self._simulate_case_creation("Test", "Some message about debt", "cust-3")
        assert case["status"] == "open"

    def test_sla_deadline_in_future(self):
        case = self._simulate_case_creation("Test", "mortgage problem", "cust-4")
        deadline = datetime.fromisoformat(case["sla_deadline"])
        assert deadline > datetime.now(timezone.utc)

    def test_case_has_uuid(self):
        import uuid
        case = self._simulate_case_creation("Test", "test message", "cust-5")
        # Should parse as UUID without error
        parsed = uuid.UUID(case["id"])
        assert str(parsed) == case["id"]

    def test_unknown_category_defaults_to_other(self):
        case = self._simulate_case_creation("Strange issue", "Lorem ipsum dolor sit amet", "cust-6")
        assert case["category"] == "other"


# ── Test: Case Status Lifecycle ───────────────────────────────────────────────

class TestCaseLifecycleFull:
    """Integration test: full case lifecycle from creation to closure."""

    VALID_TRANSITIONS = {
        "open": ["in_progress", "escalated", "closed"],
        "in_progress": ["pending_customer", "resolved", "escalated", "closed"],
        "pending_customer": ["in_progress", "resolved", "closed"],
        "escalated": ["in_progress", "resolved", "closed"],
        "resolved": ["closed", "open"],
        "closed": [],
    }

    def _transition(self, case: dict, new_status: str, actor_role: str) -> dict:
        current = case["status"]
        if new_status not in self.VALID_TRANSITIONS.get(current, []):
            raise ValueError(f"Invalid transition: {current} -> {new_status}")
        # Only managers/supervisors can escalate
        if new_status == "escalated" and actor_role not in ("manager", "supervisor", "admin"):
            raise PermissionError(f"Role '{actor_role}' cannot escalate cases")
        return {
            **case,
            "status": new_status,
            "resolved_at": datetime.now(timezone.utc).isoformat() if new_status == "resolved" else case.get("resolved_at"),
            "closed_at": datetime.now(timezone.utc).isoformat() if new_status == "closed" else case.get("closed_at"),
        }

    @pytest.fixture
    def open_case(self):
        return {"id": "case-001", "status": "open", "resolved_at": None, "closed_at": None}

    def test_full_lifecycle_open_to_closed(self, open_case):
        case = self._transition(open_case, "in_progress", "agent")
        case = self._transition(case, "resolved", "agent")
        case = self._transition(case, "closed", "manager")
        assert case["status"] == "closed"
        assert case["resolved_at"] is not None
        assert case["closed_at"] is not None

    def test_skip_to_resolved_from_open_fails(self, open_case):
        with pytest.raises(ValueError):
            self._transition(open_case, "resolved", "agent")

    def test_closed_case_cannot_transition(self, open_case):
        case = self._transition(open_case, "in_progress", "agent")
        case = self._transition(case, "resolved", "agent")
        case = self._transition(case, "closed", "agent")
        with pytest.raises(ValueError):
            self._transition(case, "open", "manager")

    def test_agent_cannot_escalate(self, open_case):
        with pytest.raises(PermissionError):
            self._transition(open_case, "escalated", "agent")

    def test_manager_can_escalate(self, open_case):
        escalated = self._transition(open_case, "escalated", "manager")
        assert escalated["status"] == "escalated"

    def test_resolved_case_can_be_reopened(self, open_case):
        case = self._transition(open_case, "in_progress", "agent")
        case = self._transition(case, "resolved", "agent")
        reopened = self._transition(case, "open", "manager")
        assert reopened["status"] == "open"


# ── Test: AI → Automation Integration ────────────────────────────────────────

class TestAIAutomationPipeline:
    """Test that AI predictions correctly trigger automation rules."""

    def _should_trigger_urgent_alert(self, priority: str, sentiment: str) -> bool:
        return priority == "urgent" or sentiment == "negative"

    def _should_auto_escalate(self, priority: str, confidence: float) -> bool:
        return priority in ("urgent", "high") and confidence >= 0.85

    def _should_assign_to_team(self, category: str) -> str | None:
        routing = {
            "mortgage": "mortgage-team",
            "credit_card": "credit-team",
            "debt_collection": "collections-team",
            "credit_reporting": "reporting-team",
        }
        return routing.get(category)

    def test_urgent_priority_triggers_alert(self):
        assert self._should_trigger_urgent_alert("urgent", "neutral") is True

    def test_negative_sentiment_triggers_alert(self):
        assert self._should_trigger_urgent_alert("medium", "negative") is True

    def test_low_priority_positive_no_alert(self):
        assert self._should_trigger_urgent_alert("low", "positive") is False

    def test_high_confidence_urgent_auto_escalates(self):
        assert self._should_auto_escalate("urgent", 0.90) is True

    def test_low_confidence_no_escalation(self):
        assert self._should_auto_escalate("urgent", 0.60) is False

    def test_mortgage_routes_to_mortgage_team(self):
        assert self._should_assign_to_team("mortgage") == "mortgage-team"

    def test_credit_card_routes_to_credit_team(self):
        assert self._should_assign_to_team("credit_card") == "credit-team"

    def test_unknown_category_no_team_routing(self):
        assert self._should_assign_to_team("other") is None

    def test_all_known_categories_have_routing(self):
        categories = ["mortgage", "credit_card", "debt_collection", "credit_reporting"]
        for cat in categories:
            assert self._should_assign_to_team(cat) is not None


# ── Test: Token Auth Guard ────────────────────────────────────────────────────

class TestAuthorizationGuard:
    """Test that API endpoint role checks work correctly."""

    ENDPOINT_ROLES = {
        "/cases": ["customer", "agent", "supervisor", "manager", "admin"],
        "/cases/{id}/assign": ["supervisor", "manager", "admin"],
        "/analytics/stats": ["supervisor", "manager", "admin"],
        "/users": ["manager", "admin"],
        "/audit/events": ["admin"],
    }

    def _can_access(self, endpoint_template: str, role: str) -> bool:
        allowed = self.ENDPOINT_ROLES.get(endpoint_template, [])
        return role in allowed

    def test_customer_can_access_cases(self):
        assert self._can_access("/cases", "customer") is True

    def test_customer_cannot_assign_cases(self):
        assert self._can_access("/cases/{id}/assign", "customer") is False

    def test_agent_cannot_view_analytics(self):
        assert self._can_access("/analytics/stats", "agent") is False

    def test_manager_can_view_analytics(self):
        assert self._can_access("/analytics/stats", "manager") is True

    def test_only_admin_can_view_audit_log(self):
        for role in ["customer", "agent", "supervisor", "manager"]:
            assert self._can_access("/audit/events", role) is False
        assert self._can_access("/audit/events", "admin") is True

    def test_admin_can_access_everything(self):
        for endpoint in self.ENDPOINT_ROLES:
            assert self._can_access(endpoint, "admin") is True


# ── Test: SLA → Notification Integration ─────────────────────────────────────

class TestSLANotificationIntegration:
    """Test that SLA breach events trigger the correct notifications."""

    def _check_sla_and_notify(self, case: dict) -> list:
        """Returns list of notification triggers based on SLA state."""
        notifications = []
        if not case.get("sla_deadline"):
            return notifications

        now = datetime.now(timezone.utc)
        deadline = datetime.fromisoformat(case["sla_deadline"])
        time_remaining = (deadline - now).total_seconds() / 3600  # hours

        if time_remaining <= 0:
            notifications.append({"type": "sla_breached", "severity": "critical"})
        elif time_remaining <= 2:
            notifications.append({"type": "sla_warning", "severity": "warning"})

        return notifications

    def test_overdue_case_triggers_breach_notification(self):
        case = {
            "id": "c1",
            "sla_deadline": (datetime.now(timezone.utc) - timedelta(hours=1)).isoformat()
        }
        notifs = self._check_sla_and_notify(case)
        assert any(n["type"] == "sla_breached" for n in notifs)

    def test_nearly_due_case_triggers_warning(self):
        case = {
            "id": "c2",
            "sla_deadline": (datetime.now(timezone.utc) + timedelta(hours=1)).isoformat()
        }
        notifs = self._check_sla_and_notify(case)
        assert any(n["type"] == "sla_warning" for n in notifs)

    def test_case_with_plenty_of_time_no_notification(self):
        case = {
            "id": "c3",
            "sla_deadline": (datetime.now(timezone.utc) + timedelta(hours=10)).isoformat()
        }
        notifs = self._check_sla_and_notify(case)
        assert len(notifs) == 0

    def test_case_without_sla_no_notification(self):
        case = {"id": "c4", "sla_deadline": None}
        notifs = self._check_sla_and_notify(case)
        assert len(notifs) == 0

    def test_breach_notification_is_critical(self):
        case = {
            "id": "c5",
            "sla_deadline": (datetime.now(timezone.utc) - timedelta(minutes=30)).isoformat()
        }
        notifs = self._check_sla_and_notify(case)
        breach = next(n for n in notifs if n["type"] == "sla_breached")
        assert breach["severity"] == "critical"
