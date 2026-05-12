import uuid
from datetime import datetime, timezone
from typing import Optional
import httpx
from motor.motor_asyncio import AsyncIOMotorDatabase
from app.services.chatbot_engine import get_response, detect_intent, ConversationState


async def search_faq(db: AsyncIOMotorDatabase, query: str, limit: int = 3) -> list:
    """Full-text search FAQ knowledge base."""
    try:
        cursor = db.faq_knowledge.find(
            {"$text": {"$search": query}},
            {"score": {"$meta": "textScore"}}
        ).sort([("score", {"$meta": "textScore"})]).limit(limit)
        return await cursor.to_list(length=limit)
    except Exception:
        return []


async def get_or_create_session(db: AsyncIOMotorDatabase, session_id: str, user_id: Optional[str] = None) -> dict:
    session = await db.chatbot_sessions.find_one({"session_id": session_id})
    if not session:
        session = {
            "session_id": session_id,
            "user_id": user_id,
            "status": "active",
            "state": ConversationState.IDLE,
            "collected": {},
            "messages": [],
            "intent_history": [],
            "started_at": datetime.now(timezone.utc),
            "ended_at": None,
            "case_id": None,
            "metadata": {},
        }
        await db.chatbot_sessions.insert_one(session)
    return session


async def process_message(
    db: AsyncIOMotorDatabase,
    session_id: str,
    message: str,
    user_id: Optional[str],
    case_service_url: str,
    ip_address: str = "unknown",
) -> dict:
    session = await get_or_create_session(db, session_id, user_id)

    # FAQ search
    faq_results = await search_faq(db, message)

    # Remove MongoDB _id for passing to engine
    session_data = {k: v for k, v in session.items() if k != "_id"}

    # Get chatbot response
    result = get_response(message, session_data, faq_results)

    # Build message objects
    user_msg = {
        "role": "user",
        "content": message,
        "timestamp": datetime.now(timezone.utc).isoformat(),
    }
    bot_msg = {
        "role": "assistant",
        "content": result["reply"],
        "intent": result["intent"],
        "timestamp": datetime.now(timezone.utc).isoformat(),
    }

    # Handle case creation action
    case_id = session.get("case_id")
    if result.get("action") in ("create_case", "escalate") and result.get("case_payload"):
        try:
            async with httpx.AsyncClient(timeout=5.0) as client:
                payload = result["case_payload"]
                payload["source"] = "chatbot"
                # For guest users, use a placeholder customer mechanism
                resp = await client.post(
                    f"{case_service_url}/cases",
                    json=payload,
                    headers={"X-Internal-Service": "chatbot"},
                )
                if resp.status_code == 201:
                    case_data = resp.json()
                    case_id = case_data.get("id")
                    bot_msg["case_id"] = case_id
        except Exception as e:
            bot_msg["case_creation_error"] = str(e)

    # Determine final session status
    new_state = result.get("state", ConversationState.IDLE)
    session_status = "active"
    ended_at = None
    if new_state in (ConversationState.RESOLVED, ConversationState.ESCALATED):
        session_status = new_state
        ended_at = datetime.now(timezone.utc)

    # Update session in MongoDB
    await db.chatbot_sessions.update_one(
        {"session_id": session_id},
        {
            "$set": {
                "state": new_state,
                "status": session_status,
                "ended_at": ended_at,
                "case_id": case_id,
                "collected": result.get("collected", session.get("collected", {})),
            },
            "$push": {
                "messages": {"$each": [user_msg, bot_msg]},
                "intent_history": result["intent"],
            },
        }
    )

    return {
        "session_id": session_id,
        "reply": result["reply"],
        "intent": result["intent"],
        "state": new_state,
        "action": result.get("action"),
        "case_id": case_id,
        "faq_used": result.get("faq_used", False),
    }
