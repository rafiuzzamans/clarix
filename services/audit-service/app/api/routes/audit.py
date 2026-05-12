from fastapi import APIRouter, Depends, Query
from motor.motor_asyncio import AsyncIOMotorDatabase
from pydantic import BaseModel
from typing import Optional
from datetime import datetime, timezone
import uuid
from app.core.database import get_db

router = APIRouter(prefix="/audit", tags=["Audit"])


class AuditLogCreate(BaseModel):
    actor_id: Optional[str] = None
    action: str
    resource_type: Optional[str] = None
    resource_id: Optional[str] = None
    description: Optional[str] = None
    ip_address: Optional[str] = None
    user_agent: Optional[str] = None
    metadata: Optional[dict] = {}


@router.post("/logs", status_code=201, summary="Create audit log entry")
async def create_log(body: AuditLogCreate, db: AsyncIOMotorDatabase = Depends(get_db)):
    doc = {
        "log_id": str(uuid.uuid4()),
        "actor_id": body.actor_id,
        "action": body.action,
        "resource_type": body.resource_type,
        "resource_id": body.resource_id,
        "description": body.description,
        "ip_address": body.ip_address,
        "user_agent": body.user_agent,
        "metadata": body.metadata or {},
        "timestamp": datetime.now(timezone.utc),
    }
    await db.audit_logs.insert_one(doc)
    return {"log_id": doc["log_id"], "status": "logged"}


@router.get("/logs", summary="Query audit logs")
async def list_logs(
    actor_id: Optional[str] = None,
    action: Optional[str] = None,
    resource_type: Optional[str] = None,
    resource_id: Optional[str] = None,
    limit: int = Query(50, le=200),
    skip: int = Query(0, ge=0),
    db: AsyncIOMotorDatabase = Depends(get_db),
):
    query = {}
    if actor_id:       query["actor_id"] = actor_id
    if action:         query["action"] = action
    if resource_type:  query["resource_type"] = resource_type
    if resource_id:    query["resource_id"] = resource_id

    cursor = db.audit_logs.find(query, {"_id": 0}).sort("timestamp", -1).skip(skip).limit(limit)
    logs = await cursor.to_list(length=limit)
    total = await db.audit_logs.count_documents(query)
    return {"logs": logs, "total": total, "skip": skip, "limit": limit}


@router.get("/logs/actor/{actor_id}", summary="Get all logs for a specific actor")
async def logs_by_actor(actor_id: str, limit: int = 50, db: AsyncIOMotorDatabase = Depends(get_db)):
    cursor = db.audit_logs.find({"actor_id": actor_id}, {"_id": 0}).sort("timestamp", -1).limit(limit)
    logs = await cursor.to_list(length=limit)
    return {"logs": logs, "actor_id": actor_id}


@router.get("/logs/resource/{resource_id}", summary="Get all logs for a resource")
async def logs_by_resource(resource_id: str, db: AsyncIOMotorDatabase = Depends(get_db)):
    cursor = db.audit_logs.find({"resource_id": resource_id}, {"_id": 0}).sort("timestamp", -1)
    logs = await cursor.to_list(length=100)
    return {"logs": logs}
