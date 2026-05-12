from fastapi import APIRouter
from pydantic import BaseModel
from typing import Optional, Dict, Any
from app.services.rule_engine import dispatch_trigger

router = APIRouter(prefix="/automation", tags=["Automation"])


class TriggerRequest(BaseModel):
    trigger_type: str
    reference_id: str
    metadata: Optional[Dict[str, Any]] = {}


@router.post("/trigger", summary="Fire an automation trigger")
async def trigger_automation(body: TriggerRequest):
    result = await dispatch_trigger(body.trigger_type, body.reference_id, body.metadata or {})
    return result


@router.get("/triggers", summary="List available automation triggers")
async def list_triggers():
    from app.services.rule_engine import TRIGGER_HANDLERS
    return {"triggers": list(TRIGGER_HANDLERS.keys())}
