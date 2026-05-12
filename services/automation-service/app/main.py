from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from app.api.routes import automation as auto_router

app = FastAPI(
    title="Automation / Workflow Service",
    description="Rule-based automation with 8 trigger handlers",
    version="1.0.0",
)

app.add_middleware(CORSMiddleware, allow_origins=["*"], allow_credentials=True, allow_methods=["*"], allow_headers=["*"])
app.include_router(auto_router.router)


@app.get("/health")
async def health():
    return {"service": "automation-service", "status": "healthy"}
