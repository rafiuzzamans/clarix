import uuid
from typing import Optional
from fastapi import APIRouter, Depends, Request
from motor.motor_asyncio import AsyncIOMotorDatabase
from pydantic import BaseModel
from app.core.database import get_db
from app.services.session_manager import process_message

router = APIRouter(prefix="/chatbot", tags=["Chatbot"])

CASE_SERVICE_URL = "http://case-service:8003"


class ChatRequest(BaseModel):
    session_id: Optional[str] = None
    message: str
    user_id: Optional[str] = None


class SessionHistoryRequest(BaseModel):
    session_id: str


@router.post("/message", summary="Send a message to the chatbot")
async def chat_message(
    body: ChatRequest,
    request: Request,
    db: AsyncIOMotorDatabase = Depends(get_db),
):
    session_id = body.session_id or str(uuid.uuid4())
    ip = request.headers.get("X-Forwarded-For", "unknown")
    return await process_message(
        db=db,
        session_id=session_id,
        message=body.message,
        user_id=body.user_id,
        case_service_url=CASE_SERVICE_URL,
        ip_address=ip,
    )


@router.get("/session/{session_id}", summary="Get chat session history")
async def get_session(
    session_id: str,
    db: AsyncIOMotorDatabase = Depends(get_db),
):
    session = await db.chatbot_sessions.find_one(
        {"session_id": session_id},
        {"_id": 0}
    )
    if not session:
        return {"error": "Session not found"}
    return session


@router.get("/faq/search", summary="Search FAQ knowledge base")
async def search_faq_endpoint(
    q: str,
    db: AsyncIOMotorDatabase = Depends(get_db),
):
    from app.services.session_manager import search_faq
    results = await search_faq(db, q)
    return [{"question": r["question"], "answer": r["answer"], "tags": r.get("tags", [])}
            for r in results]
