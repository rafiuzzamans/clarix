"""
Chatbot Engine — Hybrid rule-based + NLP intent detection + FAQ retrieval.
"""
import re
import uuid
from datetime import datetime, timezone
from typing import Optional, List, Dict, Any


# ─── Intent Patterns ─────────────────────────────────────────
INTENT_PATTERNS = [
    ("greeting",          r"\b(hello|hi|hey|good morning|good afternoon|greetings)\b"),
    ("farewell",          r"\b(bye|goodbye|thanks|thank you|see you|that's all|done)\b"),
    ("password_reset",    r"\b(password|reset|forgot|can't log in|cannot login|locked out)\b"),
    ("order_tracking",    r"\b(track|order|where is|delivery|shipped|arrived|package)\b"),
    ("refund_request",    r"\b(refund|money back|return|reimburse|cancel.*charge)\b"),
    ("billing_issue",     r"\b(charged|invoice|bill|payment|credit card|overcharged|double charge)\b"),
    ("technical_issue",   r"\b(error|crash|bug|not working|broken|slow|freeze|issue|problem)\b"),
    ("account_help",      r"\b(account|profile|email|name|update|change|delete)\b"),
    ("human_handoff",     r"\b(agent|human|person|representative|speak to|talk to|escalate)\b"),
    ("support_hours",     r"\b(hours|open|available|when|schedule|time)\b"),
    ("create_ticket",     r"\b(submit|ticket|report|case|complaint|raise|open a)\b"),
    ("subscription",      r"\b(subscribe|subscription|plan|cancel|upgrade|downgrade|membership)\b"),
    ("general_help",      r".*"),  # catch-all
]


def detect_intent(text: str) -> str:
    text_lower = text.lower().strip()
    for intent, pattern in INTENT_PATTERNS:
        if re.search(pattern, text_lower):
            return intent
    return "general_help"


# ─── Conversation State Machine ───────────────────────────────
class ConversationState:
    IDLE = "idle"
    COLLECTING_ISSUE = "collecting_issue"
    COLLECTING_CONTACT = "collecting_contact"
    AWAITING_CONFIRM = "awaiting_confirm"
    ESCALATED = "escalated"
    RESOLVED = "resolved"


def get_response(
    message: str,
    session: Dict[str, Any],
    faq_results: List[Dict],
) -> Dict[str, Any]:
    """
    Core chatbot response logic.
    Returns: { reply, intent, state, action, case_payload }
    """
    intent = detect_intent(message)
    state = session.get("state", ConversationState.IDLE)
    collected = session.get("collected", {})
    action = None
    case_payload = None

    # ── Human handoff ──────────────────────────────────────
    if intent == "human_handoff":
        return {
            "reply": "Of course! Let me connect you with a human agent. Please hold on while I create a support ticket for you.",
            "intent": intent,
            "state": ConversationState.ESCALATED,
            "action": "escalate",
            "case_payload": {
                "title": "Chat escalation — customer requested human agent",
                "message": f"Customer requested escalation during chat session. Last message: {message}",
                "source": "chatbot",
            }
        }

    # ── Ticket creation flow ──────────────────────────────
    if intent == "create_ticket" or state == ConversationState.COLLECTING_ISSUE:
        if state != ConversationState.COLLECTING_ISSUE:
            return {
                "reply": "I'll help you submit a support ticket. Could you briefly describe your issue?",
                "intent": intent,
                "state": ConversationState.COLLECTING_ISSUE,
                "action": None,
            }
        else:
            # We have the issue description — collect contact (if guest)
            collected["issue"] = message
            if not session.get("user_id"):
                return {
                    "reply": "Got it. What email address should we use to follow up with you?",
                    "intent": intent,
                    "state": ConversationState.COLLECTING_CONTACT,
                    "action": None,
                    "collected": collected,
                }
            else:
                # Authenticated user — create ticket directly
                return {
                    "reply": "Thank you. Your support ticket has been created and our team will be in touch shortly. Is there anything else I can help with?",
                    "intent": intent,
                    "state": ConversationState.RESOLVED,
                    "action": "create_case",
                    "case_payload": {
                        "title": message[:100],
                        "message": message,
                        "source": "chatbot",
                    }
                }

    if state == ConversationState.COLLECTING_CONTACT:
        collected["email"] = message
        return {
            "reply": f"Perfect. I have created a ticket for you and will send updates to {message}. Our team typically responds within 24 hours.",
            "intent": intent,
            "state": ConversationState.RESOLVED,
            "action": "create_case",
            "case_payload": {
                "title": collected.get("issue", "Support request from chatbot")[:100],
                "message": collected.get("issue", message),
                "source": "chatbot",
            },
            "collected": collected,
        }

    # ── Greetings ────────────────────────────────────────
    if intent == "greeting":
        return {
            "reply": "Hello! Welcome to Customer Support. How can I help you today? You can ask me about orders, billing, account issues, or just describe your problem.",
            "intent": intent,
            "state": ConversationState.IDLE,
            "action": None,
        }

    if intent == "farewell":
        return {
            "reply": "Thank you for contacting us! Have a great day. Don't hesitate to reach out if you need anything else.",
            "intent": intent,
            "state": ConversationState.RESOLVED,
            "action": "end_session",
        }

    # ── FAQ match ────────────────────────────────────────
    if faq_results:
        top_faq = faq_results[0]
        return {
            "reply": f"{top_faq['answer']}\n\nDoes this answer your question? If not, type 'create ticket' and I'll raise a support request for you.",
            "intent": intent,
            "state": ConversationState.IDLE,
            "action": None,
            "faq_used": True,
        }

    # ── Fallback responses ───────────────────────────────
    FALLBACKS = {
        "support_hours": "Our team is available Monday to Friday, 9 AM to 6 PM. For urgent issues, type 'create ticket' to submit a priority request.",
        "technical_issue": "I'm sorry you're experiencing a technical issue. Let me help you create a support ticket so our technical team can investigate. Would you like me to raise a ticket?",
        "billing_issue": "I understand you have a billing concern. Our billing team will need to look into this. Would you like me to create a support ticket? Just type 'yes' or describe your issue.",
        "refund_request": "Refund requests are handled by our billing team. I can create a ticket for you right now. Could you describe the item or charge you'd like refunded?",
        "order_tracking": "For order tracking, please check the 'My Orders' section in your account. If you can't find your order, type 'create ticket' and I'll escalate this.",
        "password_reset": "To reset your password: click 'Forgot Password' on the login page. A reset link will be emailed to your registered address.",
        "subscription": "For subscription changes, go to Account Settings → Subscription. If you need help, I can connect you with our team.",
        "account_help": "For account issues, I can create a support ticket for our team to assist you. Shall I do that?",
    }

    reply = FALLBACKS.get(
        intent,
        "I'm not sure I fully understand that. Could you describe your issue in more detail? You can also type 'create ticket' to submit a support request or 'agent' to speak with a human."
    )

    return {
        "reply": reply,
        "intent": intent,
        "state": ConversationState.IDLE,
        "action": None,
    }
