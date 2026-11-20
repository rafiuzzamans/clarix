"""
ml/scripts/rerun_experiments.py

Re-runs all CLARIX experiments with a corrected evaluation protocol:
  1. Exact-duplicate narratives removed BEFORE splitting.
  2. Priority labels use ONLY information available at intake
     (keywords + narrative length). timely_response is NOT used.
     Keywords are matched as whole words/phrases (no substring hits,
     e.g. "court" no longer matches "courtesy").
  3. Stratified 80/20 split FIRST; class balancing only on the training part.
     The test set keeps the natural class distribution.
  4. All four models use the SAME TF-IDF settings as train.py.
  5. Hyperparameters chosen by 5-fold CV on the TRAINING set only.
  6. Reports accuracy, weighted F1, macro F1, per-class P/R/F1, confusion
     matrices, best params, CV score and training time for every model/task.

Production models in ml/models/ are NOT overwritten. Output goes to
ml/models_v2/ (evaluation_report_v2.json + the three LR pipelines).

Run from project root:
    python ml/scripts/rerun_experiments.py
Optional: --fast  (smaller grids, fewer RF trees; for a quick check only)
"""
import os, sys, re, json, time, argparse
import numpy as np
import pandas as pd
import joblib
from sklearn.pipeline import Pipeline
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.linear_model import LogisticRegression
from sklearn.svm import LinearSVC
from sklearn.naive_bayes import MultinomialNB
from sklearn.ensemble import RandomForestClassifier
from sklearn.model_selection import train_test_split, GridSearchCV, StratifiedKFold
from sklearn.metrics import (accuracy_score, f1_score, classification_report,
                             confusion_matrix)
from sklearn.utils import resample

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
import preprocess as pp   # reuses CATEGORY_MAP, clean_text, keyword sets, paths

ROOT    = pp.ROOT
OUT_DIR = os.path.join(ROOT, "ml", "models_v2")
os.makedirs(OUT_DIR, exist_ok=True)
SEED = 42


# ---------------------------------------------------------------- data ----
def _kw_regex(words):
    alts = sorted((re.escape(w) for w in words), key=len, reverse=True)
    return re.compile(r"\b(?:" + "|".join(alts) + r")\b")

URGENT_RE = _kw_regex(pp.URGENT_KEYWORDS)
HIGH_RE   = _kw_regex(pp.HIGH_KEYWORDS)

def assign_priority_intake(narrative: str) -> str:
    """Intake-only priority label: keywords, then length. No timely_response."""
    text = str(narrative).lower()
    if URGENT_RE.search(text) or HIGH_RE.search(text):
        return "high"                     # urgent merged into high, as before
    return "medium" if len(text.split()) > 200 else "low"


def load_cfpb(stats):
    df = pd.read_csv(pp.CFPB_CSV, usecols=["product", "consumer_complaint_narrative",
                                           "complaint_id"], dtype=str, low_memory=False)
    stats["raw_rows"] = len(df)
    df = df.dropna(subset=["consumer_complaint_narrative"])
    df = df[df["consumer_complaint_narrative"].str.strip().str.len() > 20]
    stats["after_narrative_filter"] = len(df)
    df["category"] = df["product"].str.lower().str.strip().map(pp.CATEGORY_MAP)
    df = df.dropna(subset=["category"])
    stats["after_category_mapping"] = len(df)
    df["cleaned_text"] = df["consumer_complaint_narrative"].apply(pp.clean_text)
    df = df[df["cleaned_text"].str.split().str.len() >= 5]
    stats["after_min_length"] = len(df)
    df = df.drop_duplicates(subset=["complaint_id"])
    df = df.drop_duplicates(subset=["cleaned_text"])
    stats["after_dedup"] = len(df)
    df["priority"] = df["consumer_complaint_narrative"].apply(assign_priority_intake)
    stats["category_counts"] = df["category"].value_counts().to_dict()
    stats["priority_counts"] = df["priority"].value_counts().to_dict()
    return df.reset_index(drop=True)


def load_fpb(stats):
    rows = []
    with open(pp.FPB_TXT, encoding="latin-1") as f:
        for line in f:
            line = line.strip()
            if "@" not in line:
                continue
            s, lab = line.rsplit("@", 1)
            lab = lab.strip().lower()
            if lab in ("positive", "negative", "neutral"):
                rows.append({"text": s.strip(), "sentiment": lab})
    df = pd.DataFrame(rows)
    stats["raw_sentences"] = len(df)
    df["cleaned_text"] = df["text"].apply(pp.clean_text)
    df = df[df["cleaned_text"].str.split().str.len() >= 3]
    stats["after_min_length"] = len(df)
    df = df.drop_duplicates(subset=["cleaned_text"])
    stats["after_dedup"] = len(df)
    stats["sentiment_counts"] = df["sentiment"].value_counts().to_dict()
    return df.reset_index(drop=True)


def balance_train(X, y, max_per_class, min_per_class):
    """Same rule as train.py's balance_classes(), applied to TRAINING data only:
    cap large classes (sampling without replacement), upsample small ones."""
    df = pd.DataFrame({"x": X.values, "y": y.values})
    parts = []
    for lab, sub in df.groupby("y"):
        if len(sub) < min_per_class:
            sub = resample(sub, replace=True, n_samples=min_per_class, random_state=SEED)
        elif len(sub) > max_per_class:
            sub = sub.sample(max_per_class, random_state=SEED)
        parts.append(sub)
    out = pd.concat(parts).sample(frac=1, random_state=SEED)
    return out["x"], out["y"]


# -------------------------------------------------------------- models ----
def tfidf():
    return TfidfVectorizer(ngram_range=(1, 2), max_features=15000, min_df=2,
                           sublinear_tf=True, strip_accents="unicode")

def model_grid(fast):
    lr_C  = [1.0, 5.0] if fast else [0.5, 1.0, 3.0, 5.0, 10.0]
    svc_C = [0.5] if fast else [0.1, 0.5, 1.0, 3.0]
    nb_a  = [0.5] if fast else [0.1, 0.5, 1.0]
    rf_n  = 50 if fast else 200
    return {
        "Logistic Regression": (
            LogisticRegression(max_iter=1000, class_weight="balanced",
                               solver="lbfgs", random_state=SEED),
            {"clf__C": lr_C}),
        "LinearSVC": (
            LinearSVC(class_weight="balanced", dual=False, random_state=SEED),
            {"clf__C": svc_C}),
        "Multinomial Naive Bayes": (MultinomialNB(), {"clf__alpha": nb_a}),
        "Random Forest": (
            RandomForestClassifier(n_estimators=rf_n, class_weight="balanced",
                                   n_jobs=-1, random_state=SEED),
            {"clf__max_features": ["sqrt"]}),   # fixed; RF is a reference model
    }


def evaluate(pipe, X_test, y_test, labels):
    y_pred = pipe.predict(X_test)
    rep = classification_report(y_test, y_pred, labels=labels,
                                output_dict=True, zero_division=0)
    return {
        "accuracy":    round(accuracy_score(y_test, y_pred), 4),
        "f1_weighted": round(f1_score(y_test, y_pred, average="weighted"), 4),
        "f1_macro":    round(f1_score(y_test, y_pred, average="macro"), 4),
        "per_class": {c: {k: round(rep[c][k], 4) for k in
                          ("precision", "recall", "f1-score")} | {"support": int(rep[c]["support"])}
                      for c in labels},
        "confusion_matrix": confusion_matrix(y_test, y_pred, labels=labels).tolist(),
        "labels": labels,
    }


def run_task(name, X, y, bal, fast, results):
    print(f"\n=== {name} ===")
    X_tr, X_te, y_tr, y_te = train_test_split(X, y, test_size=0.2,
                                              random_state=SEED, stratify=y)
    n_tr_before = len(X_tr)
    X_tr, y_tr = balance_train(X_tr, y_tr, *bal)
    labels = sorted(y.unique().tolist())
    task = {"n_train_before_balancing": n_tr_before,
            "n_train_after_balancing": len(X_tr),
            "train_counts_after_balancing": y_tr.value_counts().to_dict(),
            "n_test": len(X_te),
            "test_counts": y_te.value_counts().to_dict(),
            "models": {}}
    cv = StratifiedKFold(n_splits=3 if fast else 5, shuffle=True, random_state=SEED)
    for mname, (clf, grid) in model_grid(fast).items():
        pipe = Pipeline([("tfidf", tfidf()), ("clf", clf)])
        gs = GridSearchCV(pipe, grid, cv=cv, scoring="f1_weighted", n_jobs=-1, refit=True)
        t0 = time.time()
        gs.fit(X_tr, y_tr)
        secs = time.time() - t0
        m = evaluate(gs.best_estimator_, X_te, y_te, labels)
        m.update({"best_params": gs.best_params_,
                  "cv_f1_weighted_mean": round(gs.best_score_, 4),
                  "cv_f1_weighted_std": round(float(gs.cv_results_["std_test_score"][gs.best_index_]), 4),
                  "fit_seconds_incl_grid_search": round(secs, 1)})
        task["models"][mname] = m
        print(f"  {mname:<25} wF1={m['f1_weighted']:.4f} macroF1={m['f1_macro']:.4f} "
              f"best={gs.best_params_} ({secs:.0f}s)")
        if mname == "Logistic Regression":
            joblib.dump(gs.best_estimator_, os.path.join(OUT_DIR, f"{name}_model.pkl"))
    results[name] = task


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--fast", action="store_true")
    args = ap.parse_args()

    results = {"protocol": {
        "dedup": "exact duplicates on complaint_id and cleaned_text removed before split",
        "priority_labels": "keywords (whole-word) + length>200 words; timely_response not used",
        "split": "stratified 80/20, random_state=42, before balancing",
        "balancing": "training set only; cap without replacement, upsample with replacement",
        "tuning": "GridSearchCV on training set only, scoring=f1_weighted",
        "test_distribution": "natural (not balanced)",
        "fast_mode": args.fast}}

    cfpb_stats, fpb_stats = {}, {}
    cfpb = load_cfpb(cfpb_stats)
    fpb = load_fpb(fpb_stats)
    results["data"] = {"cfpb": cfpb_stats, "fpb": fpb_stats}
    print(json.dumps(results["data"], indent=2))

    run_task("category",  cfpb["cleaned_text"], cfpb["category"], (10000, 2000), args.fast, results)
    run_task("priority",  cfpb["cleaned_text"], cfpb["priority"], (10000, 2000), args.fast, results)
    run_task("sentiment", fpb["cleaned_text"],  fpb["sentiment"], (3000, 600),   args.fast, results)

    path = os.path.join(OUT_DIR, "evaluation_report_v2.json")
    with open(path, "w") as f:
        json.dump(results, f, indent=2, default=str)
    print(f"\nSaved -> {path}")


if __name__ == "__main__":
    main()
