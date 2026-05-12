"""
Automation Rule Engine — Unit Tests
Tests trigger dispatch, handler registration, and notification calls.
"""
import pytest
import asyncio
from unittest.mock import AsyncMock, patch, MagicMock
import sys, os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))


class TestTriggerRegistry:
    def test_all_8_triggers_registered(self):
        from app.services.rule_engine import TRIGGER_HANDLERS
        expected = {
            "case_created", "case_urgent", "sentiment_negative",
            "case_inactivity", "case_status_changed", "case_resolved",
            "case_overdue", "daily_summary",
        }
        assert expected.issubset(set(TRIGGER_HANDLERS.keys()))

    def test_handlers_are_callable(self):
        from app.services.rule_engine import TRIGGER_HANDLERS
        for name, handler in TRIGGER_HANDLERS.items():
            assert callable(handler), f"Handler '{name}' is not callable"

    def test_dispatch_unknown_trigger_returns_skipped(self):
        from app.services.rule_engine import dispatch_trigger
        result = asyncio.run(
            dispatch_trigger("non_existent_trigger", "case-123", {})
        )
        assert result["status"] == "skipped"

    @patch("app.services.rule_engine._send_notification", new_callable=AsyncMock)
    def test_case_created_calls_notification(self, mock_notif):
        from app.services.rule_engine import dispatch_trigger
        result = asyncio.run(
            dispatch_trigger("case_created", "case-abc", {
                "customer_id": "customer-123",
                "priority": "high",
            })
        )
        assert result["status"] == "processed"
        mock_notif.assert_called_once()
        call_kwargs = mock_notif.call_args[1]
        assert call_kwargs["recipient_id"] == "customer-123"

    @patch("app.services.rule_engine._send_notification", new_callable=AsyncMock)
    def test_case_created_no_customer_no_notification(self, mock_notif):
        from app.services.rule_engine import dispatch_trigger
        asyncio.run(
            dispatch_trigger("case_created", "case-abc", {})
        )
        mock_notif.assert_not_called()

    @patch("app.services.rule_engine._send_notification", new_callable=AsyncMock)
    def test_sentiment_negative_notifies_system(self, mock_notif):
        from app.services.rule_engine import dispatch_trigger
        asyncio.run(
            dispatch_trigger("sentiment_negative", "case-xyz", {})
        )
        mock_notif.assert_called_once()
        assert mock_notif.call_args[1]["recipient_id"] == "system"

    @patch("app.services.rule_engine._send_notification", new_callable=AsyncMock)
    def test_inactivity_notifies_assigned_agent(self, mock_notif):
        from app.services.rule_engine import dispatch_trigger
        asyncio.run(
            dispatch_trigger("case_inactivity", "case-789", {"assigned_to": "agent-444"})
        )
        mock_notif.assert_called_once()
        assert mock_notif.call_args[1]["recipient_id"] == "agent-444"

    @patch("app.services.rule_engine._send_notification", new_callable=AsyncMock)
    def test_status_changed_resolved_notifies_customer(self, mock_notif):
        from app.services.rule_engine import dispatch_trigger
        asyncio.run(
            dispatch_trigger("case_status_changed", "case-001", {
                "status": "resolved", "customer_id": "cust-999"
            })
        )
        mock_notif.assert_called_once()
        assert mock_notif.call_args[1]["recipient_id"] == "cust-999"

    @patch("app.services.rule_engine._send_notification", new_callable=AsyncMock)
    def test_status_changed_in_progress_no_notification(self, mock_notif):
        """Non-terminal status changes don't notify customer."""
        from app.services.rule_engine import dispatch_trigger
        asyncio.run(
            dispatch_trigger("case_status_changed", "case-001", {
                "status": "in_progress", "customer_id": "cust-999"
            })
        )
        mock_notif.assert_not_called()
