from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
import asyncio
from app.api.routes import automation as auto_router
from app.workers.ai_agent import auto_resolve_cases

app = FastAPI(
    title="Automation / Workflow Service",
    description="Rule-based automation with 8 trigger handlers",
    version="1.0.0",
)

app.add_middleware(CORSMiddleware, allow_origins=["http://localhost:3000", "http://localhost"], allow_credentials=True, allow_methods=["*"], allow_headers=["*"])
app.include_router(auto_router.router)

@app.on_event("startup")
async def startup_event():
    asyncio.create_task(auto_resolve_cases())


@app.get("/health")
async def health():
    return {"service": "automation-service", "status": "healthy"}
