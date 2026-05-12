from pydantic import BaseModel
from typing import Optional, Dict, Any, List


class PredictRequest(BaseModel):
    text: str
    case_id: Optional[str] = None


class FeatureScore(BaseModel):
    feature: str
    score: float


class ClassResult(BaseModel):
    label: str
    confidence: float
    probabilities: Dict[str, float]


class ExplanationResult(BaseModel):
    top_features: List[FeatureScore]
    model_ready: bool
    input_cleaned: Optional[str] = None


class PredictResponse(BaseModel):
    category: ClassResult
    priority: ClassResult
    sentiment: ClassResult
    explanation: ExplanationResult
    # Flat convenience fields
    label_category: str
    label_priority: str
    label_sentiment: str
    confidence: float


class ModelStatusResponse(BaseModel):
    models_loaded: bool
    models_available: List[str]
    evaluation_report: Optional[Dict[str, Any]] = None
