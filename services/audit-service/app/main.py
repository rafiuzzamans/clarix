from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from contextlib import asynccontextmanager
from app.core.database import get_mongo_client
from app.api.routes import audit as audit_router


@asynccontextmanager
async def lifespan(app: FastAPI):
    get_mongo_client()
    yield


app = FastAPI(title="Audit & Logging Service", version="1.0.0", lifespan=lifespan)
app.add_middleware(CORSMiddleware, allow_origins=["http://localhost:3000", "http://localhost"], allow_credentials=True, allow_methods=["*"], allow_headers=["*"])
app.include_router(audit_router.router)


@app.get("/health")
async def health():
    return {"service": "audit-service", "status": "healthy"}

# Add audit event schema

# Store events in PostgreSQL

# Add pagination to audit log query

# Add filter by actor_id

# Add event type filter
