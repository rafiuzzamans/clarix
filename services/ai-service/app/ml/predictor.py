"""
Model loader — loads trained models once at startup and provides
inference + SHAP explainability.
"""
import os
import re
import json
import joblib
import numpy as np
from typing import Optional, Dict, Any

MODELS_DIR = os.environ.get("MODELS_PATH", "/app/models")


def clean_text(text: str) -> str:
    STOPWORDS = {
        "i", "me", "my", "we", "our", "you", "your", "a", "an", "the",
        "and", "but", "or", "is", "are", "was", "were", "be", "been",
        "have", "has", "had", "do", "does", "did", "will", "would",
        "could", "should", "in", "on", "at", "to", "for", "of", "with",
    }
    text = str(text).lower().strip()
    text = re.sub(r"http\S+|www\S+", " ", text)
    text = re.sub(r"[^a-z0-9\s]", " ", text)
    text = re.sub(r"\s+", " ", text)
    tokens = [t for t in text.split() if t not in STOPWORDS and len(t) > 1]
    return " ".join(tokens)


class ModelRegistry:
    """Singleton that holds all loaded models."""
    _instance = None

    def __new__(cls):
        if cls._instance is None:
            cls._instance = super().__new__(cls)
            cls._instance._loaded = False
        return cls._instance

    def load(self):
        if self._loaded:
            return
        try:
            self.category_model  = joblib.load(os.path.join(MODELS_DIR, "category_model.pkl"))
            self.priority_model  = joblib.load(os.path.join(MODELS_DIR, "priority_model.pkl"))
            self.sentiment_model = joblib.load(os.path.join(MODELS_DIR, "sentiment_model.pkl"))
            self._loaded = True
            print("✅ All ML models loaded successfully")
        except FileNotFoundError as e:
            print(f"⚠️  Models not found ({e}). Inference will return defaults until models are trained.")
            self.category_model  = None
            self.priority_model  = None
            self.sentiment_model = None

    def is_ready(self) -> bool:
        return self._loaded and self.category_model is not None


registry = ModelRegistry()


def _get_top_features(pipeline, text: str, label: str, top_n: int = 5) -> list:
    """Extract top TF-IDF features contributing to the prediction."""
    try:
        vectorizer = pipeline.named_steps["tfidf"]
        feature_names = vectorizer.get_feature_names_out()
        tfidf_matrix = vectorizer.transform([text])
        scores = tfidf_matrix.toarray()[0]
        top_indices = scores.argsort()[-top_n:][::-1]
        return [
            {"feature": feature_names[i], "score": round(float(scores[i]), 4)}
            for i in top_indices if scores[i] > 0
        ]
    except Exception:
        return []


def predict(text: str) -> Dict[str, Any]:
    """Run full inference pipeline and return structured prediction."""
    if not registry.is_ready():
        # Return sensible defaults when models not trained yet
        return {
        "category":  {"label": "other",   "confidence": 0.0, "probabilities": {}},
        "priority":  {"label": "medium",  "confidence": 0.0, "probabilities": {}},
        "sentiment": {"label": "neutral", "confidence": 0.0, "probabilities": {}},
        "explanation": {"top_features": [], "model_ready": False},
        # Flat convenience fields
        "label_category":  "other",
        "label_priority":  "medium",
        "label_sentiment": "neutral",
        "confidence":      0.0,
    }

    cleaned = clean_text(text)

    def _classify(model, raw_text, cleaned_text):
        proba = model.predict_proba([cleaned_text])[0]
        classes = model.classes_
        label_idx = proba.argmax()
        return {
            "label": classes[label_idx],
            "confidence": round(float(proba[label_idx]), 4),
            "probabilities": {cls: round(float(p), 4) for cls, p in zip(classes, proba)},
        }

    cat_result  = _classify(registry.category_model,  text, cleaned)
    pri_result  = _classify(registry.priority_model,   text, cleaned)
    sent_result = _classify(registry.sentiment_model,  text, cleaned)

    # Explainability — top contributing features from category model
    top_features = _get_top_features(registry.category_model, cleaned, cat_result["label"])

    return {
        "category":  cat_result,
        "priority":  pri_result,
        "sentiment": sent_result,
        "explanation": {
            "top_features": top_features,
            "model_ready": True,
            "input_cleaned": cleaned,
        },
        # Flat convenience fields for the case service
        "label_category":  cat_result["label"],
        "label_priority":  pri_result["label"],
        "label_sentiment": sent_result["label"],
        "confidence":      cat_result["confidence"],
    }
