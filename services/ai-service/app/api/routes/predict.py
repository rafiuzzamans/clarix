import json
import os
from fastapi import APIRouter
from app.schemas.prediction import PredictRequest, PredictResponse, ModelStatusResponse, ReplyRequest, ReplyResponse
from app.ml.predictor import predict, registry, MODELS_DIR

router = APIRouter(prefix="/ai", tags=["AI Inference"])


@router.post("/predict", response_model=PredictResponse, summary="Run AI prediction on text")
async def run_prediction(body: PredictRequest):
    result = predict(body.text)
    return result


@router.post("/generate-reply", response_model=ReplyResponse, summary="Generate a smart template reply based on AI metrics")
async def generate_reply(body: ReplyRequest):
    category_friendly = body.category.replace("_", " ").title()
    
    # Simple smart template logic based on priority and sentiment
    greeting = "Hello, and thank you for reaching out to us."
    if body.sentiment == "negative":
        greeting = "Hello. We sincerely apologize for the frustration you've experienced regarding this matter."
    
    body_text = f"We have received your request regarding '{category_friendly}'. Our team is currently reviewing your case."
    if body.priority == "urgent":
        body_text += " Due to the urgent nature of your request, this case has been escalated and is being processed with the highest priority."
    elif body.priority == "high":
        body_text += " This case has been marked as high priority and our specialists will be in touch shortly."
    
    closing = "Please let us know if there is any further information you would like to provide.\n\nBest regards,\nCustomer Support Team"
    
    reply = f"{greeting}\n\n{body_text}\n\n{closing}"
    return {"generated_reply": reply}


@router.get("/status", response_model=ModelStatusResponse, summary="Model loading status")
async def model_status():
    available = []
    for name in ["category_model.pkl", "priority_model.pkl", "sentiment_model.pkl"]:
        if os.path.exists(os.path.join(MODELS_DIR, name)):
            available.append(name.replace("_model.pkl", ""))

    evaluation = None
    report_path = os.path.join(MODELS_DIR, "evaluation_report.json")
    if os.path.exists(report_path):
        with open(report_path) as f:
            evaluation = json.load(f)

    return {
        "models_loaded": registry.is_ready(),
        "models_available": available,
        "evaluation_report": evaluation,
    }


@router.post("/train", summary="Trigger model training (admin only)")
async def trigger_training():
    """Kicks off model training. In production this would be an async job."""
    try:
        from app.ml.train import train_all
        results = train_all()
        registry._loaded = False
        registry.load()
        return {"status": "trained", "metrics": results}
    except Exception as e:
        return {"status": "error", "detail": str(e)}
