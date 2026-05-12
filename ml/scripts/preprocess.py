"""
ml/scripts/preprocess.py
Loads real CFPB + FinancialPhraseBank datasets and produces clean CSVs
ready for model training.

Run from project root:
    python ml/scripts/preprocess.py
"""
import os
import re
import pandas as pd
import numpy as np

# â”€â”€ Paths â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€
ROOT       = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
CFPB_CSV   = os.path.join(ROOT, "extracted_3", "consumer_complaints.csv")
FPB_TXT    = os.path.join(ROOT, "extracted_5", "FinancialPhraseBank", "Sentences_50Agree.txt")
OUT_DIR    = os.path.join(ROOT, "ml", "data", "processed")
os.makedirs(OUT_DIR, exist_ok=True)

# â”€â”€ CFPB Product â†’ 6-class category map â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€
CATEGORY_MAP = {
    # Mortgage
    "mortgage":                                                    "mortgage",
    # Debt collection
    "debt collection":                                             "debt_collection",
    # Credit reporting
    "credit reporting":                                            "credit_reporting",
    "credit reporting, credit repair services, or other personal consumer reports": "credit_reporting",
    "credit report":                                               "credit_reporting",
    # Bank account / services
    "checking or savings account":                                 "bank_account",
    "bank account or service":                                     "bank_account",
    "money transfer, virtual currency, or money service":          "bank_account",
    "money transfers":                                             "bank_account",
    "prepaid card":                                                "bank_account",
    "payday loan, title loan, or personal loan":                   "bank_account",
    "payday loan":                                                 "bank_account",
    "vehicle loan or lease":                                       "bank_account",
    # Credit card
    "credit card":                                                 "credit_card",
    "credit card or prepaid card":                                 "credit_card",
    # Student loan
    "student loan":                                                "student_loan",
}

# â”€â”€ Urgency keywords that bump priority to high/urgent â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€
URGENT_KEYWORDS = {
    "fraud", "fraudulent", "identity theft", "unauthorized", "stolen",
    "scam", "illegal", "threatening", "harassment", "lawsuit", "court",
}
HIGH_KEYWORDS = {
    "urgent", "immediately", "emergency", "asap", "critical", "deadline",
    "eviction", "foreclosure", "repossession", "bankruptcy",
}

# â”€â”€ Stop words (fast custom set, no NLTK dependency) â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€
STOPWORDS = {
    "i","me","my","we","our","you","your","he","she","it","they","is","are",
    "was","were","be","been","being","have","has","had","do","does","did",
    "will","would","could","should","may","might","a","an","the","and","but",
    "or","so","in","on","at","to","for","of","with","that","this","these",
    "those","from","by","about","not","no","nor","as","if","then","than",
    "too","very","just","also","up","out","into","over","after",
}


def clean_text(text: str) -> str:
    """Normalise complaint narrative for TF-IDF vectorisation."""
    text = str(text).lower().strip()
    text = re.sub(r"http\S+|www\S+", " ", text)          # remove URLs
    text = re.sub(r"xxxx+", " ", text)                    # CFPB redacts PII with X's
    text = re.sub(r"[^a-z0-9\s]", " ", text)             # keep alphanumeric
    text = re.sub(r"\s+", " ", text)                      # collapse whitespace
    tokens = [t for t in text.split() if t not in STOPWORDS and len(t) > 1]
    return " ".join(tokens)


def assign_priority(row: pd.Series) -> str:
    """
    Derive priority label from timely_response flag and urgency keywords
    in the complaint narrative.
    """
    narrative = str(row.get("consumer_complaint_narrative", "")).lower()
    timely    = str(row.get("timely_response", "Yes")).strip().lower()

    # Check urgency keywords first (highest signal)
    for kw in URGENT_KEYWORDS:
        if kw in narrative:
            return "urgent"
    for kw in HIGH_KEYWORDS:
        if kw in narrative:
            return "high"

    # Use timely_response as secondary signal
    if timely == "no":
        return "high"

    # Default based on narrative length (longer = more complex = higher priority)
    word_count = len(narrative.split())
    if word_count > 200:
        return "medium"
    return "low"


# â”€â”€ CFPB Preprocessing â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€
def preprocess_cfpb() -> pd.DataFrame:
    print("Loading CFPB Consumer Complaints CSV...")
    df = pd.read_csv(
        CFPB_CSV,
        usecols=["product", "consumer_complaint_narrative",
                 "timely_response", "complaint_id"],
        dtype=str,
        low_memory=False,
    )
    print(f"  Raw rows: {len(df):,}")

    # 1. Filter rows with no complaint narrative
    df = df.dropna(subset=["consumer_complaint_narrative"])
    df = df[df["consumer_complaint_narrative"].str.strip().str.len() > 20]
    print(f"  After narrative filter: {len(df):,}")

    # 2. Map product â†’ category
    df["product_lower"] = df["product"].str.lower().str.strip()
    df["category"] = df["product_lower"].map(CATEGORY_MAP)
    df = df.dropna(subset=["category"])
    print(f"  After category mapping: {len(df):,}")
    print("\n  Category distribution:")
    print(df["category"].value_counts().to_string())

    # 3. Engineer priority label
    print("\n  Engineering priority labels...")
    df["priority"] = df.apply(assign_priority, axis=1)
    print("\n  Priority distribution:")
    print(df["priority"].value_counts().to_string())

    # 4. Clean text
    print("\n  Cleaning complaint narratives...")
    df["cleaned_text"] = df["consumer_complaint_narrative"].apply(clean_text)

    # 5. Remove rows where cleaned text is too short
    df = df[df["cleaned_text"].str.split().str.len() >= 5]
    print(f"  Final CFPB rows: {len(df):,}")

    # 6. Keep only needed columns
    result = df[["complaint_id", "consumer_complaint_narrative",
                 "cleaned_text", "category", "priority"]].reset_index(drop=True)

    out_path = os.path.join(OUT_DIR, "cfpb_clean.csv")
    result.to_csv(out_path, index=False)
    print(f"\n  Saved -> {out_path}")
    return result


# â”€â”€ FinancialPhraseBank Preprocessing â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€
def preprocess_fpb() -> pd.DataFrame:
    print("\nLoading FinancialPhraseBank (Sentences_50Agree)...")

    rows = []
    with open(FPB_TXT, encoding="latin-1") as f:
        for line in f:
            line = line.strip()
            if not line:
                continue
            # Format: "sentence text@sentiment"
            if "@" not in line:
                continue
            parts = line.rsplit("@", 1)
            if len(parts) != 2:
                continue
            sentence, sentiment = parts[0].strip(), parts[1].strip().lower()
            if sentiment not in ("positive", "negative", "neutral"):
                continue
            rows.append({"text": sentence, "sentiment": sentiment})

    df = pd.DataFrame(rows)
    print(f"  Raw sentences: {len(df):,}")
    print("\n  Sentiment distribution:")
    print(df["sentiment"].value_counts().to_string())

    df["cleaned_text"] = df["text"].apply(clean_text)
    df = df[df["cleaned_text"].str.split().str.len() >= 3]
    print(f"  After cleaning: {len(df):,}")

    out_path = os.path.join(OUT_DIR, "fpb_clean.csv")
    df.to_csv(out_path, index=False)
    print(f"\n  Saved â†’ {out_path}")
    return df


# â”€â”€ Entry Point â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€
if __name__ == "__main__":
    print("=" * 55)
    print("  CLARIX â€” Dataset Preprocessing Pipeline")
    print("=" * 55)

    cfpb = preprocess_cfpb()
    fpb  = preprocess_fpb()

    print("\n" + "=" * 55)
    print("  Preprocessing complete.")
    print(f"  CFPB rows:  {len(cfpb):,}")
    print(f"  FPB rows:   {len(fpb):,}")
    print(f"  Output dir: {OUT_DIR}")
    print("=" * 55)
