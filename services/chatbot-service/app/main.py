from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from contextlib import asynccontextmanager
from app.core.database import get_mongo_client
from app.api.routes import chatbot as chatbot_router


@asynccontextmanager
async def lifespan(app: FastAPI):
    get_mongo_client()  # Ensure connection on startup
    yield


app = FastAPI(
    title="Chatbot Service",
    description="Hybrid chatbot with FAQ, intent detection, case creation and escalation",
    version="1.0.0",
    lifespan=lifespan,
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000", "http://localhost"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(chatbot_router.router)


@app.get("/health", tags=["Health"])
async def health():
    return {"service": "chatbot-service", "status": "healthy"}

# Add conversation history storage

# Add intent classification step

# Add knowledge base lookup

# Handle session timeout gracefully

# Add CSAT survey after resolution

# Add typing indicator event

# Sanitize user input

# Add escalation trigger detection

# Add /health endpoint
