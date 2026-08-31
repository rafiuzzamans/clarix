"""
ml/scripts/train.py
Trains all 3 classifiers on real CFPB + FinancialPhraseBank data:
  - category_model.pkl   (6-class: mortgage, debt_collection, etc.)
  - priority_model.pkl   (3-class: low, medium, high/urgent merged)
  - sentiment_model.pkl  (3-class: positive, neutral, negative)

Run from project root:
    python ml/scripts/train.py
"""
import os, json, sys
import joblib
import numpy as np
import pandas as pd
from sklearn.pipeline import Pipeline
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.linear_model import LogisticRegression
from sklearn.ensemble import GradientBoostingClassifier
from sklearn.svm import LinearSVC
from sklearn.model_selection import train_test_split, cross_val_score, StratifiedKFold
from sklearn.metrics import (
    classification_report, confusion_matrix, accuracy_score, f1_score
)
from sklearn.utils import resample

ROOT       = "/app"
DATA_DIR   = "/data/processed"
MODELS_DIR = "/app/models"
os.makedirs(MODELS_DIR, exist_ok=True)

CFPB_PATH  = os.path.join(DATA_DIR, "cfpb_clean.csv")
FPB_PATH   = os.path.join(DATA_DIR, "fpb_clean.csv")


def tfidf_pipeline(clf):
    return Pipeline([
        ("tfidf", TfidfVectorizer(
            ngram_range=(1, 2),
            max_features=15000,
            min_df=2,
            sublinear_tf=True,
            strip_accents="unicode",
        )),
        ("clf", clf),
    ])


def evaluate_and_save(pipeline, X_test, y_test, model_name, model_path, labels):
    y_pred = pipeline.predict(X_test)
    acc = accuracy_score(y_test, y_pred)
    f1  = f1_score(y_test, y_pred, average="weighted")
    report = classification_report(y_test, y_pred, output_dict=True)
    cm     = confusion_matrix(y_test, y_pred, labels=labels).tolist()

    print(f"\n{'='*52}")
    print(f"  {model_name.upper()} MODEL RESULTS")
    print(f"{'='*52}")
    print(f"  Accuracy       : {acc:.4f}")
    print(f"  Weighted F1    : {f1:.4f}")
    print(f"\n  Per-class F1:")
    for cls in labels:
        cls_f1 = report.get(cls, {}).get("f1-score", 0.0)
        flag   = "  << LOW" if cls_f1 < 0.60 else ""
        print(f"    {cls:<20} {cls_f1:.4f}{flag}")
    print(f"\n{classification_report(y_test, y_pred)}")

    joblib.dump(pipeline, model_path)
    print(f"  Model saved -> {model_path}")

    return {
        "accuracy": round(acc, 4),
        "f1_weighted": round(f1, 4),
        "per_class_f1": {
            cls: round(report.get(cls, {}).get("f1-score", 0.0), 4)
            for cls in labels
        },
        "confusion_matrix": cm,
        "labels": labels,
    }


def balance_classes(df, text_col, label_col, max_per_class=8000, min_per_class=500):
    """Upsample minority classes, cap majority classes."""
    frames = []
    for label in df[label_col].unique():
        subset = df[df[label_col] == label]
        n = len(subset)
        if n < min_per_class:
            subset = resample(subset, replace=True, n_samples=min_per_class, random_state=42)
        elif n > max_per_class:
            subset = subset.sample(max_per_class, random_state=42)
        frames.append(subset)
    return pd.concat(frames).sample(frac=1, random_state=42).reset_index(drop=True)


# â”€â”€ 1. Category Model â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€
def train_category():
    print("\n" + "="*52)
    print("  TRAINING: Category Classifier (CFPB Data)")
    print("="*52)

    df = pd.read_csv(CFPB_PATH, usecols=["cleaned_text", "category"])
    df = df.dropna(subset=["cleaned_text", "category"])
    print(f"  Loaded {len(df):,} rows")

    # Balance: cap debt_collection dominance, upsample student_loan
    df = balance_classes(df, "cleaned_text", "category",
                         max_per_class=10000, min_per_class=2000)
    print(f"  After balancing: {len(df):,} rows")
    print(df["category"].value_counts().to_string())

    X = df["cleaned_text"]
    y = df["category"]
    labels = sorted(y.unique().tolist())

    X_train, X_test, y_train, y_test = train_test_split(
        X, y, test_size=0.2, random_state=42, stratify=y
    )
    print(f"\n  Train: {len(X_train):,}  Test: {len(X_test):,}")

    # Train Logistic Regression (best for sparse TF-IDF, needed for SHAP)
    clf = LogisticRegression(
        max_iter=1000, C=5.0,
        class_weight="balanced",
        solver="lbfgs",
        random_state=42,
    )
    pipeline = tfidf_pipeline(clf)
    print("\n  Fitting LogisticRegression...")
    pipeline.fit(X_train, y_train)

    metrics = evaluate_and_save(
        pipeline, X_test, y_test,
        "Category",
        os.path.join(MODELS_DIR, "category_model.pkl"),
        labels,
    )
    return metrics


# â”€â”€ 2. Priority Model â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€
def train_priority():
    print("\n" + "="*52)
    print("  TRAINING: Priority Classifier (CFPB Data)")
    print("="*52)

    df = pd.read_csv(CFPB_PATH, usecols=["cleaned_text", "priority"])
    df = df.dropna(subset=["cleaned_text", "priority"])

    # Merge 'urgent' into 'high' for a cleaner 3-class problem
    df["priority"] = df["priority"].replace("urgent", "high")
    print(f"  Loaded {len(df):,} rows")
    print(df["priority"].value_counts().to_string())

    # Balance classes
    df = balance_classes(df, "cleaned_text", "priority",
                         max_per_class=10000, min_per_class=2000)
    print(f"  After balancing: {len(df):,} rows")

    X = df["cleaned_text"]
    y = df["priority"]
    labels = sorted(y.unique().tolist())

    X_train, X_test, y_train, y_test = train_test_split(
        X, y, test_size=0.2, random_state=42, stratify=y
    )

    # Use LogisticRegression (faster than GBC, still strong, SHAP-compatible)
    clf = LogisticRegression(
        max_iter=1000, C=3.0,
        class_weight="balanced",
        solver="lbfgs",
        random_state=42,
    )
    pipeline = tfidf_pipeline(clf)
    print("\n  Fitting LogisticRegression for priority...")
    pipeline.fit(X_train, y_train)

    # 5-fold CV
    cv = StratifiedKFold(n_splits=5, shuffle=True, random_state=42)
    cv_scores = cross_val_score(pipeline, X, y, cv=cv, scoring="f1_weighted")
    print(f"\n  5-fold CV F1: {cv_scores.mean():.4f} (+/- {cv_scores.std():.4f})")

    metrics = evaluate_and_save(
        pipeline, X_test, y_test,
        "Priority",
        os.path.join(MODELS_DIR, "priority_model.pkl"),
        labels,
    )
    metrics["cv_f1_mean"] = round(float(cv_scores.mean()), 4)
    metrics["cv_f1_std"]  = round(float(cv_scores.std()),  4)
    return metrics


# â”€â”€ 3. Sentiment Model â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€
def train_sentiment():
    print("\n" + "="*52)
    print("  TRAINING: Sentiment Classifier (FinancialPhraseBank)")
    print("="*52)

    df = pd.read_csv(FPB_PATH, usecols=["cleaned_text", "sentiment"])
    df = df.dropna(subset=["cleaned_text", "sentiment"])
    print(f"  Loaded {len(df):,} rows")
    print(df["sentiment"].value_counts().to_string())

    # Upsample negative (only 604 samples)
    df = balance_classes(df, "cleaned_text", "sentiment",
                         max_per_class=3000, min_per_class=600)

    X = df["cleaned_text"]
    y = df["sentiment"]
    labels = sorted(y.unique().tolist())

    X_train, X_test, y_train, y_test = train_test_split(
        X, y, test_size=0.2, random_state=42, stratify=y
    )
    print(f"\n  Train: {len(X_train):,}  Test: {len(X_test):,}")

    clf = LogisticRegression(
        max_iter=1000, C=1.0,
        class_weight="balanced",
        solver="lbfgs",
        random_state=42,
    )
    pipeline = tfidf_pipeline(clf)
    print("\n  Fitting LogisticRegression for sentiment...")
    pipeline.fit(X_train, y_train)

    metrics = evaluate_and_save(
        pipeline, X_test, y_test,
        "Sentiment",
        os.path.join(MODELS_DIR, "sentiment_model.pkl"),
        labels,
    )
    return metrics


# â”€â”€ Main â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€
def train_all():
    print("\n" + "="*52)
    print("  CLARIX â€” ML Training Pipeline")
    print("  CLARIX — ML Training Pipeline")
    print("  Real data: CFPB + FinancialPhraseBank")
    print("="*52)

    for path in [CFPB_PATH, FPB_PATH]:
        if not os.path.exists(path):
            print(f"ERROR: {path} not found. Run preprocess.py first.")
            sys.exit(1)

    from sklearn.feature_extraction.text import ENGLISH_STOP_WORDS as STOPWORDS
    results = {}
    results["category"]  = train_category()
    results["priority"]  = train_priority()
    results["sentiment"] = train_sentiment()

    # Save combined evaluation report
    report_path = os.path.join(MODELS_DIR, "evaluation_report.json")
    with open(report_path, "w") as f:
        json.dump(results, f, indent=2)

    print("\n" + "="*52)
    print("  TRAINING COMPLETE")
    print(f"  Category  F1: {results['category']['f1_weighted']}")
    print(f"  Priority  F1: {results['priority']['f1_weighted']}")
    print(f"  Sentiment F1: {results['sentiment']['f1_weighted']}")
    print(f"\n  All models -> {MODELS_DIR}")
    print(f"  Report    -> {report_path}")
    print("="*52)

    return results


if __name__ == "__main__":
    train_all()
