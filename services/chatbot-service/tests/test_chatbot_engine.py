"""
Chatbot Service — Unit Tests
Tests intent detection and conversation response logic.
"""
import pytest
import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

from app.services.chatbot_engine import detect_intent, get_response, ConversationState


class TestIntentDetection:
    def test_greeting(self):
        assert detect_intent("Hello there!") == "greeting"
        assert detect_intent("Hi, I need help") == "greeting"
        assert detect_intent("Good morning!") == "greeting"

    def test_password_reset(self):
        assert detect_intent("I forgot my password") == "password_reset"
        assert detect_intent("I can't log in to my account") == "password_reset"
        assert detect_intent("my account is locked out") == "password_reset"

    def test_refund(self):
        assert detect_intent("Please refund my payment") == "refund_request"
        assert detect_intent("I need to return this item for a refund") == "refund_request"

    def test_human_handoff(self):
        assert detect_intent("Let me speak to a human agent") == "human_handoff"
        assert detect_intent("Transfer me to a real person") == "human_handoff"
        assert detect_intent("I want to escalate this") == "human_handoff"

    def test_billing(self):
        assert detect_intent("I was charged twice on my credit card") == "billing_issue"
        assert detect_intent("my invoice shows the wrong amount") == "billing_issue"

    def test_farewell(self):
        assert detect_intent("Thank you, goodbye!") == "farewell"
        assert detect_intent("that's all I needed") == "farewell"

    def test_order_tracking(self):
        assert detect_intent("Where is my order?") == "order_tracking"
        assert detect_intent("my package has not arrived") == "order_tracking"

    def test_technical_issue(self):
        assert detect_intent("the app has a bug and is broken") == "technical_issue"
        assert detect_intent("there is a bug in the system") == "technical_issue"

    def test_general_fallback(self):
        result = detect_intent("Lorem ipsum dolor sit amet")
        assert isinstance(result, str)
        assert len(result) > 0


class TestChatbotResponses:
    def _session(self, state: str = "idle", collected: dict = None) -> dict:
        return {"state": state, "collected": collected or {}, "user_id": None}

    def test_greeting_response(self):
        result = get_response("Hello!", self._session(), [])
        assert result["intent"] == "greeting"
        assert result["state"] == ConversationState.IDLE
        assert "action" in result
        assert result["action"] is None

    def test_farewell_ends_session(self):
        result = get_response("goodbye thanks", self._session(), [])
        assert result["state"] == ConversationState.RESOLVED
        assert result["action"] == "end_session"

    def test_human_handoff_creates_case(self):
        result = get_response("I want to speak to an agent", self._session(), [])
        assert result["action"] == "escalate"
        assert result["state"] == ConversationState.ESCALATED
        assert "case_payload" in result

    def test_ticket_creation_flow_step1(self):
        result = get_response("I want to create a ticket", self._session(), [])
        assert result["state"] == ConversationState.COLLECTING_ISSUE

    def test_faq_result_used_when_available(self):
        faqs = [{"question": "How do I reset?", "answer": "Click forgot password."}]
        result = get_response("password question", self._session(), faqs)
        assert "forgot password" in result["reply"].lower() or "reset" in result["reply"].lower()

    def test_response_always_has_reply(self):
        for msg in ["hi", "help me", "billing", "order", "refund", "xyz"]:
            result = get_response(msg, self._session(), [])
            assert "reply" in result
            assert len(result["reply"]) > 0

    def test_support_hours_fallback(self):
        result = get_response("what are your support hours?", self._session(), [])
        assert "hours" in result["reply"].lower() or "available" in result["reply"].lower()
