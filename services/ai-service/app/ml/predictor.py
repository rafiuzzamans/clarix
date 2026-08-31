"""
predictor.py
Loads trained models at service startup and provides:
  - predict()  — category, priority, sentiment inference
  - explain()  — real SHAP LinearExplainer feature attribution

Models are LogisticRegression + TF-IDF pipelines trained on
CFPB Consumer Complaints + FinancialPhraseBank datasets.
"""
import os
import re
import time
import logging
import threading
import joblib
import numpy as np
from typing import Optional, Dict, Any, List

logger = logging.getLogger(__name__)

# ── Model paths ────────────────────────────────────────────────────────────────
# In Docker: /app/models  |  Local dev: ml/models/ from project root
_DEFAULT = os.path.join(
    os.path.dirname(__file__),          # ai-service/app/ml/
    "..", "..", "..", "..",              # up to project root
    "ml", "models"
)
MODELS_DIR = os.environ.get("MODELS_PATH", os.path.normpath(_DEFAULT))

# ── Text cleaning (must match preprocessing exactly) ──────────────────────────
from sklearn.feature_extraction.text import ENGLISH_STOP_WORDS as STOPWORDS

def clean_text(text: str) -> str:
    """Normalise text — must match ml/scripts/preprocess.py."""
    text = str(text).lower().strip()
    text = re.sub(r"http\S+|www\S+", " ", text)
    text = re.sub(r"xxxx+", " ", text)
    text = re.sub(r"[^a-z0-9\s]", " ", text)
    text = re.sub(r"\s+", " ", text)
    tokens = [t for t in text.split() if t not in STOPWORDS and len(t) > 1]
    return " ".join(tokens)


# ── Model Registry (singleton) ────────────────────────────────────────────────
class ModelRegistry:
    """Singleton — loads all models once at FastAPI startup."""
    _instance = None
    _lock = threading.Lock()  # Thread lock for safe concurrent inference

    def __new__(cls):
        if cls._instance is None:
            cls._instance = super().__new__(cls)
            cls._instance._loaded = False
        return cls._instance

    def load(self):
        if self._loaded:
            return
        try:
            logger.info("Loading ML models from %s", MODELS_DIR)
            self.category_model  = joblib.load(os.path.join(MODELS_DIR, "category_model.pkl"))
            self.priority_model  = joblib.load(os.path.join(MODELS_DIR, "priority_model.pkl"))
            self.sentiment_model = joblib.load(os.path.join(MODELS_DIR, "sentiment_model.pkl"))

            # ── Build SHAP explainers ─────────────────────────────────────────
            # Use a small background dataset for LinearExplainer
            # We need to pass the TF-IDF output (dense) as background
            try:
                import shap
                logger.info("Initialising SHAP explainers...")
                self._shap_cat_explainer  = self._build_shap_explainer(self.category_model)
                self._shap_sent_explainer = self._build_shap_explainer(self.sentiment_model)
                self._shap_pri_explainer  = self._build_shap_explainer(self.priority_model)
                self._shap_available = True
                logger.info("SHAP explainers ready")
            except ImportError:
                logger.warning("shap not installed — falling back to TF-IDF feature scores")
                self._shap_available = False
            except Exception as exc:
                logger.warning("SHAP init failed: %s — falling back", exc)
                self._shap_available = False

            self._loaded = True
            logger.info("All ML models loaded successfully")

        except FileNotFoundError as e:
            logger.warning("Models not found (%s) — run ml/scripts/train.py first", e)
            self.category_model = self.priority_model = self.sentiment_model = None
            self._shap_available = False

    def _build_shap_explainer(self, pipeline):
        """Build a SHAP LinearExplainer using a background sample."""
        import shap
        import pandas as pd

        vectorizer = pipeline.named_steps["tfidf"]
        clf        = pipeline.named_steps["clf"]

        # Transform background to dense matrix (SHAP requires dense)
        # Using a zero matrix as background ensures SHAP values exactly equal coef * TF-IDF value
        # This prevents the explainer from heavily weighting weird words just because they weren't in the background
        bg_dense = np.zeros((1, len(vectorizer.get_feature_names_out())))

        explainer = shap.LinearExplainer(clf, bg_dense)
        return explainer, vectorizer

    def is_ready(self) -> bool:
        return self._loaded and self.category_model is not None


registry = ModelRegistry()


# ── SHAP Explanation ───────────────────────────────────────────────────────────
def _shap_top_features(
    explainer_tuple,
    cleaned_text: str,
    predicted_class: str,
    top_n: int = 10,
) -> List[Dict]:
    """Return top-N SHAP feature attributions for the predicted class."""
    try:
        explainer, vectorizer = explainer_tuple
        feature_names = vectorizer.get_feature_names_out()

        # Transform to dense (LinearExplainer requires dense input)
        vec = vectorizer.transform([cleaned_text]).toarray()

        # shap_values returns shape (n_samples, n_features) for binary,
        # or list of (n_samples, n_features) for multiclass
        shap_vals = explainer.shap_values(vec)

        # Pick the values for the predicted class if multiclass
        if isinstance(shap_vals, list):
            # Find class index
            clf = None
            # Use first class as default, or find the right one
            try:
                class_list = list(explainer.model.classes_)
                cls_idx = class_list.index(predicted_class) if predicted_class in class_list else 0
                vals = shap_vals[cls_idx][0]
            except Exception:
                vals = shap_vals[0][0]
        else:
            # Binary or single output — shape (n_samples, n_features)
            vals = shap_vals[0]

        top_idx = np.argsort(np.abs(vals))[-top_n:][::-1]
        return [
            {
                "feature":    feature_names[i],
                "shap_value": round(float(vals[i]), 5),
                "direction":  "positive" if vals[i] > 0 else "negative",
            }
            for i in top_idx if abs(vals[i]) > 1e-6
        ]

    except Exception as exc:
        logger.warning("SHAP attribution failed: %s — using TF-IDF fallback", exc)
        return _tfidf_top_features(explainer_tuple[1], cleaned_text, top_n)


def _tfidf_top_features(vectorizer, cleaned_text: str, top_n: int = 10) -> List[Dict]:
    """Fallback: raw TF-IDF scores as proxy for feature importance."""
    try:
        feature_names = vectorizer.get_feature_names_out()
        scores = vectorizer.transform([cleaned_text]).toarray()[0]
        top_idx = scores.argsort()[-top_n:][::-1]
        return [
            {"feature": feature_names[i], "shap_value": round(float(scores[i]), 5),
             "direction": "positive"}
            for i in top_idx if scores[i] > 0
        ]
    except Exception:
        return []


# ── Inference ──────────────────────────────────────────────────────────────────
def predict(text: str) -> Dict[str, Any]:
    """
    Run full inference pipeline.
    Returns category, priority, sentiment predictions with SHAP explanation.
    Latency target: < 500ms.
    """
    start = time.perf_counter()

    if not registry.is_ready():
        return {
            "category":  {"label": "bank_account", "confidence": 0.0, "probabilities": {}},
            "priority":  {"label": "medium",        "confidence": 0.0, "probabilities": {}},
            "sentiment": {"label": "neutral",        "confidence": 0.0, "probabilities": {}},
            "explanation": {"top_features": [], "model_ready": False, "method": "none"},
            "label_category":  "bank_account",
            "label_priority":  "medium",
            "label_sentiment": "neutral",
            "confidence": 0.0,
        }

    cleaned = clean_text(text)

    def _classify(model, cleaned_text):
        proba   = model.predict_proba([cleaned_text])[0]
        classes = model.classes_
        idx     = proba.argmax()
        return {
            "label":         classes[idx],
            "confidence":    round(float(proba[idx]), 4),
            "probabilities": {cls: round(float(p), 4) for cls, p in zip(classes, proba)},
        }

    # Use a lock to prevent concurrent threads from corrupting sklearn model state
    with registry._lock:
        cat_result  = _classify(registry.category_model,  cleaned)
        pri_result  = _classify(registry.priority_model,   cleaned)
        sent_result = _classify(registry.sentiment_model,  cleaned)

        # ── SHAP or TF-IDF fallback ───────────────────────────────────────────────
        if registry._shap_available:
            top_features = _shap_top_features(
                registry._shap_cat_explainer,
                cleaned,
                cat_result["label"],
            )
            method = "shap_linear"
        else:
            top_features = _tfidf_top_features(
                registry.category_model.named_steps["tfidf"], cleaned
            )
            method = "tfidf_proxy"

    elapsed_ms = round((time.perf_counter() - start) * 1000, 1)
    if elapsed_ms > 500:
        logger.warning("Inference latency %.1fms exceeds 500ms SLA", elapsed_ms)

    return {
        "category":  cat_result,
        "priority":  pri_result,
        "sentiment": sent_result,
        "explanation": {
            "top_features":  top_features,
            "model_ready":   True,
            "method":        method,
            "input_cleaned": cleaned,
            "latency_ms":    elapsed_ms,
        },
        # Flat convenience fields for the case service
        "label_category":  cat_result["label"],
        "label_priority":  pri_result["label"],
        "label_sentiment": sent_result["label"],
        "confidence":      cat_result["confidence"],
    }
