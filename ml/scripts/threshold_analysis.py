"""
ml/scripts/threshold_analysis.py

How many test complaints would CLARIX auto-resolve (category confidence > threshold),
and how accurate is the category prediction for those cases?

Uses exactly the same data, de-duplication and 80/20 split as rerun_experiments.py,
and the v2 category model. Output: ml/models_v2/threshold_report.json

Run from project root (after rerun_experiments.py):
    python ml/scripts/threshold_analysis.py
"""
import os, sys, json
import numpy as np
import joblib
from sklearn.model_selection import train_test_split

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
import rerun_experiments as rx

DEPLOYED = 0.85
SWEEP = [0.50, 0.60, 0.70, 0.75, 0.80, 0.85, 0.90, 0.95]


def main():
    cfpb = rx.load_cfpb({})
    _, X_te, _, y_te = train_test_split(cfpb["cleaned_text"], cfpb["category"],
                                        test_size=0.2, random_state=rx.SEED,
                                        stratify=cfpb["category"])
    model_path = os.path.join(rx.OUT_DIR, "category_model.pkl")
    pipe = joblib.load(model_path)
    proba = pipe.predict_proba(X_te)
    conf = proba.max(axis=1)
    pred = pipe.classes_[proba.argmax(axis=1)]
    y = y_te.to_numpy()
    correct = pred == y

    def at(t):
        auto = conf > t
        n_auto = int(auto.sum())
        return {"threshold": t,
                "n_auto": n_auto,
                "share_auto": round(n_auto / len(y), 4),
                "accuracy_auto": round(float(correct[auto].mean()), 4) if n_auto else None,
                "n_wrong_auto": int((~correct[auto]).sum()),
                "accuracy_human_routed": round(float(correct[~auto].mean()), 4) if n_auto < len(y) else None}

    report = {"model": model_path, "n_test": int(len(y)),
              "overall_accuracy": round(float(correct.mean()), 4),
              "deployed_threshold": at(DEPLOYED),
              "per_category_at_deployed": {},
              "sweep": [at(t) for t in SWEEP]}
    auto = conf > DEPLOYED
    for c in sorted(set(y)):
        m = y == c
        report["per_category_at_deployed"][c] = {
            "n_test": int(m.sum()),
            "share_auto": round(float(auto[m].mean()), 4),
            "accuracy_auto": round(float(correct[m & auto].mean()), 4) if (m & auto).any() else None}
    out = os.path.join(rx.OUT_DIR, "threshold_report.json")
    with open(out, "w") as f:
        json.dump(report, f, indent=2)
    print(json.dumps(report["deployed_threshold"], indent=2))
    print("Saved ->", out)


if __name__ == "__main__":
    main()
