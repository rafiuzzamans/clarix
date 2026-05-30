from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from contextlib import asynccontextmanager
from app.core.database import engine, Base
from app.api.routes import notifications as notif_router


@asynccontextmanager
async def lifespan(app: FastAPI):
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    yield
    await engine.dispose()


app = FastAPI(title="Notification Service", version="1.0.0", lifespan=lifespan)
app.add_middleware(CORSMiddleware, allow_origins=["http://localhost:3000", "http://localhost"], allow_credentials=True, allow_methods=["*"], allow_headers=["*"])
app.include_router(notif_router.router)


@app.get("/health")
async def health():
    return {"service": "notification-service", "status": "healthy"}
