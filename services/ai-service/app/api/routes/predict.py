import json
import os
from fastapi import APIRouter
from app.schemas.prediction import PredictRequest, PredictResponse, ModelStatusResponse
from app.ml.predictor import predict, registry, MODELS_DIR

router = APIRouter(prefix="/ai", tags=["AI Inference"])


@router.post("/predict", response_model=PredictResponse, summary="Run AI prediction on text")
async def run_prediction(body: PredictRequest):
    result = predict(body.text)
    return result


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
