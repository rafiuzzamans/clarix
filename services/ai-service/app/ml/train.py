"""
ML Pipeline — Text preprocessing, feature engineering, model training.
Trains category, priority, and sentiment classifiers on support ticket data.
Saves models to /models directory for the AI service to load.
"""
import os
import json
import joblib
import numpy as np
import pandas as pd
from sklearn.pipeline import Pipeline
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.linear_model import LogisticRegression
from sklearn.ensemble import RandomForestClassifier, GradientBoostingClassifier
from sklearn.model_selection import train_test_split, cross_val_score
from sklearn.metrics import (
    classification_report, confusion_matrix, accuracy_score, f1_score
)
from sklearn.preprocessing import LabelEncoder
import re
import string

MODELS_DIR = os.path.join(os.path.dirname(__file__), "..", "..", "models")
os.makedirs(MODELS_DIR, exist_ok=True)

# ─── Text Preprocessing ──────────────────────────────────────
STOPWORDS = {
    "i", "me", "my", "we", "our", "you", "your", "he", "she", "it", "they",
    "is", "are", "was", "were", "be", "been", "being", "have", "has", "had",
    "do", "does", "did", "will", "would", "could", "should", "may", "might",
    "a", "an", "the", "and", "but", "or", "so", "in", "on", "at", "to", "for",
    "of", "with", "that", "this", "these", "those", "from", "by", "about",
}


def clean_text(text: str) -> str:
    """Lowercase, remove punctuation, strip stopwords."""
    text = str(text).lower().strip()
    text = re.sub(r"http\S+|www\S+", " ", text)         # remove URLs
    text = re.sub(r"[^a-z0-9\s]", " ", text)            # keep alphanumeric
    text = re.sub(r"\s+", " ", text)                    # collapse whitespace
    tokens = [t for t in text.split() if t not in STOPWORDS and len(t) > 1]
    return " ".join(tokens)


# ─── Synthetic Data Generation ───────────────────────────────
def generate_synthetic_dataset(n_samples: int = 3000) -> pd.DataFrame:
    """Generate realistic synthetic support ticket data."""
    categories = {
        "billing": [
            "I was charged twice for my subscription this month",
            "My invoice shows an incorrect amount",
            "I need a refund for the duplicate charge",
            "My payment was declined but money left my account",
            "I want to cancel my subscription and get a refund",
            "I can't update my credit card information",
            "Why was I charged more than I expected",
            "My bank account shows a charge but no confirmation",
        ],
        "technical_support": [
            "The app crashes every time I open it",
            "I cannot log in to my account",
            "The website is showing an error 500",
            "My data is not syncing between devices",
            "The feature is not working as expected",
            "I am getting a server error when I try to submit",
            "The mobile app is very slow and keeps freezing",
            "I cannot upload files through the platform",
        ],
        "account": [
            "I forgot my password and cannot reset it",
            "I need to change my email address",
            "My account has been locked out",
            "I want to delete my account and all my data",
            "I cannot verify my email address",
            "Please help me update my profile information",
            "I need to merge two accounts",
            "My account was hacked and I need help",
        ],
        "shipping": [
            "My order has not arrived after 2 weeks",
            "I received the wrong item in my package",
            "The tracking number is not updating",
            "My package was marked delivered but I did not receive it",
            "I need to change my delivery address",
            "How long will my order take to arrive",
            "Can I expedite my shipping",
            "My order was returned to sender",
        ],
        "returns": [
            "I want to return a product I bought last week",
            "How do I initiate a return for a damaged item",
            "I received a defective product and need a replacement",
            "My return was rejected but the item was faulty",
            "How long do refunds take to process",
            "I want to exchange my item for a different size",
            "The return window was missed due to shipping delays",
            "I have not received my refund after 2 weeks",
        ],
        "product_inquiry": [
            "Does this product come with a warranty",
            "What are the specifications of your premium plan",
            "Is this service available in my country",
            "Can I use the product on multiple devices",
            "What is the difference between plan A and plan B",
            "Do you have a free trial available",
            "How does the cancellation policy work",
            "What features are included in the enterprise tier",
        ],
        "complaint": [
            "I am very unhappy with the service I received",
            "Your agent was extremely rude and unhelpful",
            "This is the third time I have had this problem",
            "I am considering switching to a competitor",
            "Your service has gone downhill significantly",
            "I have been waiting 10 days for a resolution",
            "Nobody is responding to my previous emails",
            "I am furious about how my case was handled",
        ],
        "feedback": [
            "I love the new interface you released this week",
            "The customer support team was incredibly helpful",
            "I have a suggestion for improving the checkout process",
            "Your platform is one of the best I have used",
            "I think the mobile app needs a dark mode",
            "Overall great experience but the loading is a bit slow",
            "Would love to see monthly billing as an option",
            "Thank you for resolving my issue so quickly",
        ],
    }

    sentiments = {
        "complaint": "negative",
        "billing":   "negative",
        "returns":   "negative",
        "technical_support": "neutral",
        "account":        "neutral",
        "shipping":       "negative",
        "product_inquiry": "positive",
        "feedback":       "positive",
    }

    priorities = {
        "complaint": "high",
        "billing":   "high",
        "technical_support": "high",
        "account":   "medium",
        "shipping":  "medium",
        "returns":   "low",
        "product_inquiry": "low",
        "feedback":  "low",
    }

    rows = []
    rng = np.random.default_rng(42)

    for _ in range(n_samples):
        cat = rng.choice(list(categories.keys()))
        templates = categories[cat]
        base_text = rng.choice(templates)

        # Add some noise / variation
        suffixes = [
            "", " Please help me.", " This is urgent.",
            " I have been waiting for days.", " Thank you in advance.",
            " I am very frustrated.", " Can someone assist me?",
        ]
        text = base_text + rng.choice(suffixes)

        # Vary sentiment slightly
        base_sent = sentiments[cat]
        sent = rng.choice(
            [base_sent, "neutral"],
            p=[0.75, 0.25]
        )

        # Vary priority slightly
        base_pri = priorities[cat]
        all_pris = ["low", "medium", "high", "urgent"]
        base_idx = all_pris.index(base_pri)
        shift = rng.integers(-1, 2)
        pri_idx = max(0, min(3, base_idx + shift))
        pri = all_pris[pri_idx]

        rows.append({
            "text": text,
            "category": cat,
            "sentiment": sent,
            "priority": pri,
        })

    df = pd.DataFrame(rows)
    df["cleaned_text"] = df["text"].apply(clean_text)
    return df


# ─── Model Training ──────────────────────────────────────────
def build_pipeline(clf) -> Pipeline:
    return Pipeline([
        ("tfidf", TfidfVectorizer(
            ngram_range=(1, 2),
            max_features=10000,
            min_df=2,
            sublinear_tf=True,
        )),
        ("clf", clf),
    ])


def train_and_evaluate(X_train, X_test, y_train, y_test, clf, label: str) -> dict:
    pipeline = build_pipeline(clf)
    pipeline.fit(X_train, y_train)
    y_pred = pipeline.predict(X_test)

    acc = accuracy_score(y_test, y_pred)
    f1 = f1_score(y_test, y_pred, average="weighted")
    report = classification_report(y_test, y_pred, output_dict=True)
    cm = confusion_matrix(y_test, y_pred).tolist()

    print(f"\n{'='*50}")
    print(f"  {label.upper()} MODEL")
    print(f"{'='*50}")
    print(f"  Accuracy:  {acc:.4f}")
    print(f"  F1 (weighted): {f1:.4f}")
    print(classification_report(y_test, y_pred))

    return {
        "model": pipeline,
        "metrics": {
            "accuracy": acc,
            "f1_weighted": f1,
            "report": report,
            "confusion_matrix": cm,
        }
    }


def train_all():
    print("Generating synthetic dataset...")
    df = generate_synthetic_dataset(3000)
    df.to_csv(os.path.join(MODELS_DIR, "training_data.csv"), index=False)

    X = df["cleaned_text"]
    results = {}

    # ── Category model ───────────────────────────────────────
    y_cat = df["category"]
    X_train, X_test, y_train, y_test = train_test_split(X, y_cat, test_size=0.2, random_state=42, stratify=y_cat)
    cat_result = train_and_evaluate(
        X_train, X_test, y_train, y_test,
        LogisticRegression(max_iter=1000, C=5, class_weight="balanced"),
        "Category"
    )
    joblib.dump(cat_result["model"], os.path.join(MODELS_DIR, "category_model.pkl"))
    results["category"] = cat_result["metrics"]

    # ── Priority model ───────────────────────────────────────
    y_pri = df["priority"]
    X_train, X_test, y_train, y_test = train_test_split(X, y_pri, test_size=0.2, random_state=42, stratify=y_pri)
    pri_result = train_and_evaluate(
        X_train, X_test, y_train, y_test,
        GradientBoostingClassifier(n_estimators=100, random_state=42),
        "Priority"
    )
    joblib.dump(pri_result["model"], os.path.join(MODELS_DIR, "priority_model.pkl"))
    results["priority"] = pri_result["metrics"]

    # ── Sentiment model ──────────────────────────────────────
    y_sent = df["sentiment"]
    X_train, X_test, y_train, y_test = train_test_split(X, y_sent, test_size=0.2, random_state=42, stratify=y_sent)
    sent_result = train_and_evaluate(
        X_train, X_test, y_train, y_test,
        LogisticRegression(max_iter=1000, C=3, class_weight="balanced"),
        "Sentiment"
    )
    joblib.dump(sent_result["model"], os.path.join(MODELS_DIR, "sentiment_model.pkl"))
    results["sentiment"] = sent_result["metrics"]

    # Save metrics report
    with open(os.path.join(MODELS_DIR, "evaluation_report.json"), "w") as f:
        json.dump(results, f, indent=2)

    print("\n✅ All models trained and saved to:", MODELS_DIR)
    return results


if __name__ == "__main__":
    train_all()
