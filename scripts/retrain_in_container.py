"""
Retrain all 3 ML models inside the Docker container
using sklearn 1.4.2 (same version as the AI service).
This eliminates the InconsistentVersionWarning and NotFittedError.

Run with:
    docker exec cs_ai python /tmp/retrain_in_container.py
"""
import pandas as pd
import joblib
import os
from sklearn.pipeline import Pipeline
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.linear_model import LogisticRegression
from sklearn.model_selection import train_test_split
from sklearn.metrics import f1_score

MODELS_DIR = "/app/models"

print("Loading datasets...")
cfpb = pd.read_csv("/data/processed/cfpb_clean.csv").dropna(subset=["cleaned_text"])
sentiment_data = pd.read_csv("/data/processed/fpb_clean.csv").dropna(subset=["cleaned_text"])

def make_pipe():
    return Pipeline([
        ("tfidf", TfidfVectorizer(
            max_features=15000,
            ngram_range=(1, 2),
            sublinear_tf=True,
            min_df=2,
            strip_accents="unicode",
        )),
        ("clf", LogisticRegression(
            max_iter=1000,
            C=5.0,
            class_weight="balanced",
            solver="lbfgs",
            random_state=42,
        ))
    ])

# ── Category model ──────────────────────────────────────────────────────────
print("Training category model...")
X, y = cfpb["cleaned_text"], cfpb["category"]
Xtr, Xte, ytr, yte = train_test_split(X, y, test_size=0.2, random_state=42, stratify=y)
cat_model = make_pipe()
cat_model.fit(Xtr, ytr)
f1 = f1_score(yte, cat_model.predict(Xte), average="weighted")
print("  Category F1: {:.4f}".format(f1))
joblib.dump(cat_model, os.path.join(MODELS_DIR, "category_model.pkl"))

# ── Priority model ──────────────────────────────────────────────────────────
print("Training priority model...")
cfpb["priority_clean"] = cfpb["priority"].replace("urgent", "high")
X, y = cfpb["cleaned_text"], cfpb["priority_clean"]
Xtr, Xte, ytr, yte = train_test_split(X, y, test_size=0.2, random_state=42, stratify=y)
pri_model = make_pipe()
pri_model.fit(Xtr, ytr)
f1 = f1_score(yte, pri_model.predict(Xte), average="weighted")
print("  Priority F1: {:.4f}".format(f1))
joblib.dump(pri_model, os.path.join(MODELS_DIR, "priority_model.pkl"))

# ── Sentiment model ─────────────────────────────────────────────────────────
print("Training sentiment model...")
X, y = sentiment_data["cleaned_text"], sentiment_data["sentiment"]
Xtr, Xte, ytr, yte = train_test_split(X, y, test_size=0.2, random_state=42, stratify=y)
sent_model = make_pipe()
sent_model.fit(Xtr, ytr)
f1 = f1_score(yte, sent_model.predict(Xte), average="weighted")
print("  Sentiment F1: {:.4f}".format(f1))
joblib.dump(sent_model, os.path.join(MODELS_DIR, "sentiment_model.pkl"))

print("\nAll models saved to", MODELS_DIR)
print("Models trained with sklearn", __import__("sklearn").__version__)
