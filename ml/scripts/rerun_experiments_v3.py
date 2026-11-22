"""
ml/scripts/rerun_experiments_v3.py

Same data, de-duplication, priority labels and 80/20 split as rerun_experiments.py,
with these additions requested in review:

  1. Class balancing happens INSIDE each cross-validation training fold
     (imblearn Pipeline), so validation folds never contain resampled copies.
     The final model is refit on the whole training partition, balanced the same way.
  2. 95% bootstrap confidence intervals (1,000 resamples of the test set) for
     weighted and macro F1 of every model.
  3. Calibration of the Logistic Regression category model (Brier score, ECE,
     reliability bins), relevant to the 0.85 auto-resolution threshold.
  4. SHAP faithfulness test: removing the top-k attributed terms vs k random
     terms present in the complaint, and the effect on the predicted-class logit.
  5. Near-duplicate check: share of test complaints whose nearest training
     complaint has TF-IDF cosine similarity >= 0.9, and accuracy without them.
  6. Model provenance: SHA-256 of each saved pipeline and library versions.

Output: ml/models_v3/evaluation_report_v3.json and the three LR pipelines.
Production models are not touched.

Requires:  pip install imbalanced-learn
Run from project root:
    python ml/scripts/rerun_experiments_v3.py          (full)
    python ml/scripts/rerun_experiments_v3.py --fast   (quick check only)
"""
import os, sys, json, time, hashlib, argparse, platform
import numpy as np
import pandas as pd
import joblib
import sklearn
from sklearn.model_selection import train_test_split, GridSearchCV, StratifiedKFold
from sklearn.metrics import f1_score
from imblearn.pipeline import Pipeline as ImbPipeline
from imblearn import FunctionSampler

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
import rerun_experiments as rx       # data loading, labels, models, metrics (unchanged)

OUT_DIR = os.path.join(rx.ROOT, "ml", "models_v3")
os.makedirs(OUT_DIR, exist_ok=True)
SEED = rx.SEED
BALANCE = {"category": (10000, 2000), "priority": (10000, 2000), "sentiment": (3000, 600)}


# ------------------------------------------------ balancing inside folds ----
def _balance(X, y, max_per_class, min_per_class):
    X = np.asarray(X, dtype=object); y = np.asarray(y)
    rng = np.random.RandomState(SEED)
    idx = []
    for lab in np.unique(y):
        li = np.where(y == lab)[0]
        if len(li) < min_per_class:
            li = rng.choice(li, size=min_per_class, replace=True)
        elif len(li) > max_per_class:
            li = rng.choice(li, size=max_per_class, replace=False)
        idx.append(li)
    idx = rng.permutation(np.concatenate(idx))
    return X[idx], y[idx]


def make_pipe(clf, bal):
    sampler = FunctionSampler(func=_balance, validate=False,
                              kw_args={"max_per_class": bal[0], "min_per_class": bal[1]})
    return ImbPipeline([("balance", sampler), ("tfidf", rx.tfidf()), ("clf", clf)])


# ------------------------------------------------------------ analyses ----
def bootstrap_ci(y_true, y_pred, n=1000):
    rng = np.random.RandomState(SEED)
    y_true = np.asarray(y_true); y_pred = np.asarray(y_pred)
    w, m = [], []
    for _ in range(n):
        i = rng.randint(0, len(y_true), len(y_true))
        w.append(f1_score(y_true[i], y_pred[i], average="weighted"))
        m.append(f1_score(y_true[i], y_pred[i], average="macro"))
    q = lambda a: [round(float(np.percentile(a, 2.5)), 4), round(float(np.percentile(a, 97.5)), 4)]
    return {"f1_weighted_95ci": q(w), "f1_macro_95ci": q(m), "resamples": n}


def calibration(pipe, X_te, y_te, bins=15):
    proba = pipe.predict_proba(X_te)
    classes = list(pipe.classes_)
    y = np.asarray(y_te)
    onehot = np.array([[1.0 if c == t else 0.0 for c in classes] for t in y])
    brier = float(np.mean(np.sum((proba - onehot) ** 2, axis=1)))
    conf = proba.max(axis=1)
    correct = np.array(classes)[proba.argmax(axis=1)] == y
    edges = np.linspace(0, 1, bins + 1)
    ece, table = 0.0, []
    for lo, hi in zip(edges[:-1], edges[1:]):
        mk = (conf > lo) & (conf <= hi)
        if mk.any():
            acc, cf = float(correct[mk].mean()), float(conf[mk].mean())
            ece += mk.mean() * abs(acc - cf)
            table.append({"bin": [round(lo, 3), round(hi, 3)], "n": int(mk.sum()),
                          "mean_confidence": round(cf, 4), "accuracy": round(acc, 4)})
    return {"brier_multiclass": round(brier, 4), "ece": round(float(ece), 4), "bins": table}


def faithfulness(pipe, X_te, k=5, n_cases=300):
    """Zero the top-k attributed features vs k random present features
    (in TF-IDF space, no re-normalisation) and measure the drop in the
    predicted-class logit and the share of predictions that change."""
    tf, clf = pipe.named_steps["tfidf"], pipe.named_steps["clf"]
    rng = np.random.RandomState(SEED)
    sample = rng.choice(len(X_te), size=min(n_cases, len(X_te)), replace=False)
    V = tf.transform(np.asarray(X_te, dtype=object)[sample]).toarray()
    W, b = clf.coef_, clf.intercept_
    top_drop, rnd_drop, top_flip, rnd_flip, used = [], [], [], [], 0
    for v in V:
        present = np.flatnonzero(v)
        if len(present) <= k:
            continue
        logits = W @ v + b
        c = int(np.argmax(logits))
        phi = W[c] * v                       # exact SHAP, zero background
        top = present[np.argsort(-phi[present])[:k]]
        rnd = rng.choice(present, size=k, replace=False)
        for idx, drops, flips in ((top, top_drop, top_flip), (rnd, rnd_drop, rnd_flip)):
            v2 = v.copy(); v2[idx] = 0
            l2 = W @ v2 + b
            drops.append(float(logits[c] - l2[c]))
            flips.append(int(np.argmax(l2) != c))
        used += 1
    return {"cases": used, "k": k,
            "mean_logit_drop_top_k": round(float(np.mean(top_drop)), 4),
            "mean_logit_drop_random_k": round(float(np.mean(rnd_drop)), 4),
            "prediction_change_rate_top_k": round(float(np.mean(top_flip)), 4),
            "prediction_change_rate_random_k": round(float(np.mean(rnd_flip)), 4),
            "note": "features zeroed in TF-IDF space without re-normalisation; predicted class (positive-attribution terms)"}


def near_duplicates(pipe, X_tr, X_te, y_te, thr=0.9, chunk=500):
    tf = pipe.named_steps["tfidf"]
    A = tf.transform(np.asarray(X_tr, dtype=object))
    B = tf.transform(np.asarray(X_te, dtype=object))
    best = np.zeros(B.shape[0])
    for s in range(0, B.shape[0], chunk):
        sims = (B[s:s + chunk] @ A.T).max(axis=1).toarray().ravel()
        best[s:s + chunk] = sims
    near = best >= thr
    pred = pipe.predict(np.asarray(X_te, dtype=object))
    y = np.asarray(y_te)
    out = {"threshold_cosine": thr, "n_test": int(len(y)), "n_near_duplicates": int(near.sum()),
           "share_near_duplicates": round(float(near.mean()), 4),
           "f1_weighted_all": round(float(f1_score(y, pred, average="weighted")), 4)}
    if (~near).any():
        out["f1_weighted_without_near_duplicates"] = round(float(f1_score(y[~near], pred[~near], average="weighted")), 4)
    return out


def sha256(path):
    h = hashlib.sha256()
    with open(path, "rb") as f:
        for blk in iter(lambda: f.read(1 << 20), b""):
            h.update(blk)
    return h.hexdigest()


# ---------------------------------------------------------------- main ----
def run_task(name, X, y, fast, results):
    print(f"\n=== {name} ===")
    X_tr, X_te, y_tr, y_te = train_test_split(X, y, test_size=0.2, random_state=SEED, stratify=y)
    labels = sorted(y.unique().tolist())
    bal = BALANCE[name]
    task = {"n_train": len(X_tr), "n_test": len(X_te), "test_counts": y_te.value_counts().to_dict(),
            "balancing": f"inside each CV training fold and for the final refit: max {bal[0]}, min {bal[1]} per class",
            "models": {}}
    cv = StratifiedKFold(n_splits=3 if fast else 5, shuffle=True, random_state=SEED)
    for mname, (clf, grid) in rx.model_grid(fast).items():
        gs = GridSearchCV(make_pipe(clf, bal), grid, cv=cv, scoring="f1_weighted", n_jobs=-1, refit=True)
        t0 = time.time(); gs.fit(X_tr, y_tr); secs = time.time() - t0
        best = gs.best_estimator_
        m = rx.evaluate(best, X_te, y_te, labels)
        pred = best.predict(X_te)
        m.update({"best_params": gs.best_params_,
                  "cv_f1_weighted_mean": round(gs.best_score_, 4),
                  "cv_f1_weighted_std": round(float(gs.cv_results_["std_test_score"][gs.best_index_]), 4),
                  "fit_seconds_incl_grid_search": round(secs, 1),
                  "bootstrap": bootstrap_ci(y_te, pred, n=200 if fast else 1000)})
        print(f"  {mname:<25} wF1={m['f1_weighted']:.4f} {m['bootstrap']['f1_weighted_95ci']} "
              f"macro={m['f1_macro']:.4f} best={gs.best_params_} ({secs:.0f}s)")
        if mname == "Logistic Regression":
            # save the plain sklearn pipeline (tfidf + clf) used for inference
            from sklearn.pipeline import Pipeline as SkPipeline
            deploy = SkPipeline([("tfidf", best.named_steps["tfidf"]), ("clf", best.named_steps["clf"])])
            path = os.path.join(OUT_DIR, f"{name}_model.pkl")
            joblib.dump(deploy, path)
            m["artifact"] = {"path": os.path.relpath(path, rx.ROOT), "sha256": sha256(path)}
            m["faithfulness"] = faithfulness(deploy, X_te)
            if name == "category":
                m["calibration"] = calibration(deploy, X_te, y_te)
                m["near_duplicates"] = near_duplicates(deploy, X_tr, X_te, y_te)
            print("   faithfulness:", {k: v for k, v in m["faithfulness"].items() if k != "note"})
        task["models"][mname] = m
    results[name] = task


def main():
    ap = argparse.ArgumentParser(); ap.add_argument("--fast", action="store_true")
    args = ap.parse_args()
    import imblearn, shap
    results = {"protocol": {
        "base": "same data, de-duplication, intake-only priority labels and stratified 80/20 split (seed 42) as rerun_experiments.py",
        "balancing": "inside each CV training fold (imblearn Pipeline); validation folds and test set untouched",
        "tuning": "GridSearchCV on training partition, scoring=f1_weighted",
        "fast_mode": args.fast},
        "environment": {"python": platform.python_version(), "sklearn": sklearn.__version__,
                        "imblearn": imblearn.__version__, "shap": shap.__version__, "os": platform.platform()}}
    cfpb = rx.load_cfpb({}); fpb = rx.load_fpb({})
    run_task("category", cfpb["cleaned_text"], cfpb["category"], args.fast, results)
    run_task("priority", cfpb["cleaned_text"], cfpb["priority"], args.fast, results)
    run_task("sentiment", fpb["cleaned_text"], fpb["sentiment"], args.fast, results)
    path = os.path.join(OUT_DIR, "evaluation_report_v3.json")
    with open(path, "w") as f:
        json.dump(results, f, indent=2, default=str)
    print("\nSaved ->", path)


if __name__ == "__main__":
    main()
