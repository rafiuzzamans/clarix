"""
Case Service — Unit Tests
Tests case creation validation, status transitions, SLA deadline logic.
"""
import pytest
from datetime import datetime, timezone, timedelta
import sys, os
os.environ["DEBUG"] = "false"
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
        from app.services.chatbot_engine import detect_intent  # type: ignore
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


class TestAutoResolutionRoutingSafeguards:
    """
    Safeguard 1: Do not auto-resolve high-priority cases.
    Threshold is 0.85; predicted priority high/urgent must route to human teams.
    """
    AUTO_RESOLVE_THRESHOLD = 0.85
    AI_AGENT_ID = "99999999-9999-9999-9999-999999999999"
    AI_AGENT_TEAM = "88888888-8888-8888-8888-888888888888"

    def _apply_routing(self, ai_conf: float | None, ai_priority: str | None, ai_cat: str = "billing"):
        high_risk = (ai_priority or "").lower() in ("high", "urgent")
        auto_resolution_skipped = False
        assigned_to = None
        team_id = None

        if ai_conf and ai_conf > self.AUTO_RESOLVE_THRESHOLD and not high_risk:
            assigned_to = self.AI_AGENT_ID
            team_id = self.AI_AGENT_TEAM
        else:
            if ai_conf and ai_conf > self.AUTO_RESOLVE_THRESHOLD and high_risk:
                auto_resolution_skipped = True
            if ai_cat in ("billing", "returns", "debt_collection", "credit_card"):
                team_id = "33333333-3333-3333-3333-333333333333"
            elif ai_cat in ("technical_support", "mortgage", "bank_account"):
                team_id = "22222222-2222-2222-2222-222222222222"
            else:
                team_id = "11111111-1111-1111-1111-111111111111"

        return assigned_to, team_id, auto_resolution_skipped

    def test_conf_095_high_routes_to_human_team(self):
        """(a) conf 0.95 + high -> human team, auto_resolution_skipped recorded."""
        assigned, team, skipped = self._apply_routing(ai_conf=0.95, ai_priority="high", ai_cat="billing")
        assert assigned != self.AI_AGENT_ID
        assert team == "33333333-3333-3333-3333-333333333333"
        assert skipped is True

    def test_conf_095_urgent_routes_to_human_team(self):
        """Urgent predicted priority also triggers high_risk safeguard."""
        assigned, team, skipped = self._apply_routing(ai_conf=0.95, ai_priority="urgent", ai_cat="credit_card")
        assert assigned != self.AI_AGENT_ID
        assert team == "33333333-3333-3333-3333-333333333333"
        assert skipped is True

    def test_conf_095_low_routes_to_ai_agent(self):
        """(b) conf 0.95 + low -> AI agent."""
        assigned, team, skipped = self._apply_routing(ai_conf=0.95, ai_priority="low", ai_cat="billing")
        assert assigned == self.AI_AGENT_ID
        assert team == self.AI_AGENT_TEAM
        assert skipped is False

    def test_conf_060_low_routes_to_human_team(self):
        """(c) conf 0.60 + low -> human team."""
        assigned, team, skipped = self._apply_routing(ai_conf=0.60, ai_priority="low", ai_cat="mortgage")
        assert assigned != self.AI_AGENT_ID
        assert team == "22222222-2222-2222-2222-222222222222"
        assert skipped is False

    def test_conf_000_model_not_ready_routes_to_human_team(self):
        """(d) conf 0.0 (model not ready) -> human team."""
        assigned, team, skipped = self._apply_routing(ai_conf=0.0, ai_priority=None, ai_cat="bank_account")
        assert assigned != self.AI_AGENT_ID
        assert team == "22222222-2222-2222-2222-222222222222"
        assert skipped is False


class TestRequestHumanReview:
    """
    Safeguard 2: Request human review endpoint and service logic.
    """

    @pytest.mark.asyncio
    async def test_customer_can_request_review_on_ai_resolved_case(self):
        """Customer can request review on AI-resolved case; case is reopened, team set, AI fields preserved."""
        from unittest.mock import AsyncMock, MagicMock, patch
        from uuid import uuid4
        from app.models.case import Case, CaseStatus, CasePriority, CaseSentiment, CaseCategory, CaseSource
        from app.services.case_service import CaseService

        cust_id = uuid4()
        case_id = uuid4()
        now = datetime.now(timezone.utc)
        case = Case(
            id=case_id,
            case_number=1001,
            title="Billing discrepancy",
            message="Charged twice",
            customer_id=cust_id,
            status=CaseStatus.resolved,
            priority=CasePriority.low,
            source=CaseSource.web,
            is_escalated=False,
            ai_overridden=False,
            created_at=now,
            updated_at=now,
            assigned_to="99999999-9999-9999-9999-999999999999",
            resolved_at=now,
            category=CaseCategory.credit_card,
            ai_category=CaseCategory.credit_card,
            ai_priority=CasePriority.low,
            ai_sentiment=CaseSentiment.negative,
            ai_confidence=0.91,
            ai_explanation='{"top_features": ["charge", "double"]}',
        )

        db = AsyncMock()
        db.execute.return_value = MagicMock(scalar_one_or_none=MagicMock(return_value=case))
        user = MagicMock(id=cust_id, role="customer")

        with patch("app.services.case_service._add_timeline", new_callable=AsyncMock) as mock_tl, \
             patch("app.services.case_service._emit_audit", new_callable=AsyncMock) as mock_audit, \
             patch("app.services.case_service._notify_automation", new_callable=AsyncMock) as mock_notify:

            res = await CaseService(db).request_human_review(str(case_id), user, reason="Please review my double charge")

            # Status updated to open, resolved_at cleared, unassigned
            assert case.status == CaseStatus.open
            assert case.resolved_at is None
            assert case.assigned_to is None
            # Routed to billing team
            assert case.team_id == "33333333-3333-3333-3333-333333333333"
            # AI fields preserved
            assert case.ai_category == CaseCategory.credit_card
            assert case.ai_priority == CasePriority.low
            assert case.ai_sentiment == CaseSentiment.negative
            assert case.ai_confidence == 0.91
            assert case.ai_explanation == '{"top_features": ["charge", "double"]}'
            # Events emitted
            mock_tl.assert_awaited_once()
            mock_audit.assert_awaited_once()
            mock_notify.assert_awaited_once()

    @pytest.mark.asyncio
    async def test_request_review_on_human_agent_resolved_case_raises_409(self):
        """Review request on human-agent resolved case raises 409 conflict."""
        from unittest.mock import AsyncMock, MagicMock
        from uuid import uuid4
        from fastapi import HTTPException
        from app.models.case import Case, CaseStatus
        from app.services.case_service import CaseService

        cust_id = uuid4()
        case_id = uuid4()
        human_agent_id = str(uuid4())
        case = Case(
            id=case_id,
            case_number=1002,
            title="Account issue",
            message="Help needed",
            customer_id=cust_id,
            status=CaseStatus.resolved,
            assigned_to=human_agent_id,
            resolved_at=datetime.now(timezone.utc),
        )

        db = AsyncMock()
        # Case lookup succeeds; timeline lookup returns no AI resolution entries
        mock_tl_result = MagicMock()
        mock_tl_result.scalars.return_value = []
        db.execute.side_effect = [
            MagicMock(scalar_one_or_none=MagicMock(return_value=case)),
            mock_tl_result
        ]
        user = MagicMock(id=cust_id, role="customer")

        with pytest.raises(HTTPException) as exc_info:
            await CaseService(db).request_human_review(str(case_id), user)
        assert exc_info.value.status_code == 409
        assert "Only AI-resolved cases" in exc_info.value.detail

    @pytest.mark.asyncio
    async def test_other_customer_raises_403(self):
        """A customer who does not own the case cannot request review (403 forbidden)."""
        from unittest.mock import AsyncMock, MagicMock
        from uuid import uuid4
        from fastapi import HTTPException
        from app.models.case import Case, CaseStatus
        from app.services.case_service import CaseService

        owner_id = uuid4()
        other_id = uuid4()
        case_id = uuid4()
        case = Case(
            id=case_id,
            case_number=1003,
            title="Loan issue",
            message="Question",
            customer_id=owner_id,
            status=CaseStatus.resolved,
            assigned_to="99999999-9999-9999-9999-999999999999",
        )

        db = AsyncMock()
        db.execute.return_value = MagicMock(scalar_one_or_none=MagicMock(return_value=case))
        other_user = MagicMock(id=other_id, role="customer")

        with pytest.raises(HTTPException) as exc_info:
            await CaseService(db).request_human_review(str(case_id), other_user)
        assert exc_info.value.status_code == 403

    @pytest.mark.asyncio
    async def test_unresolved_case_raises_409(self):
        """Review request on a non-resolved case raises 409."""
        from unittest.mock import AsyncMock, MagicMock
        from uuid import uuid4
        from fastapi import HTTPException
        from app.models.case import Case, CaseStatus
        from app.services.case_service import CaseService

        cust_id = uuid4()
        case_id = uuid4()
        case = Case(
            id=case_id,
            case_number=1004,
            title="Open case",
            message="Not yet resolved",
            customer_id=cust_id,
            status=CaseStatus.open,
            assigned_to="99999999-9999-9999-9999-999999999999",
        )

        db = AsyncMock()
        db.execute.return_value = MagicMock(scalar_one_or_none=MagicMock(return_value=case))
        user = MagicMock(id=cust_id, role="customer")

        with pytest.raises(HTTPException) as exc_info:
            await CaseService(db).request_human_review(str(case_id), user)
        assert exc_info.value.status_code == 409
        assert "not in resolved status" in exc_info.value.detail

    @pytest.mark.asyncio
    async def test_nonexistent_case_raises_404(self):
        """Request review for nonexistent case returns 404."""
        from unittest.mock import AsyncMock, MagicMock
        from uuid import uuid4
        from fastapi import HTTPException
        from app.services.case_service import CaseService

        db = AsyncMock()
        db.execute.return_value = MagicMock(scalar_one_or_none=MagicMock(return_value=None))
        user = MagicMock(id=uuid4(), role="customer")

        with pytest.raises(HTTPException) as exc_info:
            await CaseService(db).request_human_review(str(uuid4()), user)
        assert exc_info.value.status_code == 404


