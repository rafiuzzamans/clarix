from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from contextlib import asynccontextmanager
from app.ml.predictor import registry
from app.api.routes import predict as predict_router

CORS_ORIGINS = ["http://localhost:3000", "http://localhost:80"]


@asynccontextmanager
async def lifespan(app: FastAPI):
    registry.load()
    yield


app = FastAPI(
    title="AI Inference Service",
    description="Category, priority, and sentiment prediction with explainability",
    version="1.0.0",
    lifespan=lifespan,
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=CORS_ORIGINS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(predict_router.router)


@app.get("/health", tags=["Health"])
async def health():
    return {
        "service": "ai-service",
        "status": "healthy",
        "models_ready": registry.is_ready()
    }

# Lazy-load models on first request

# Add model version endpoint

# Cache predictions for duplicate messages

# Return structured confidence scores

# Add prediction audit logging

# Handle empty message gracefully

# Add SHAP explanation to auto-routed cases
