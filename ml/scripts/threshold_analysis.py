"""
ml/scripts/threshold_analysis.py

Also reports the safeguard policy: auto-resolve only if category confidence > threshold
AND the priority model does not predict "high".

How many test complaints would CLARIX auto-resolve (category confidence > threshold),
and how accurate is the category prediction for those cases?

Uses exactly the same data, de-duplication and 80/20 split as rerun_experiments.py,
and the v2 category model. Output: ml/models_v2/threshold_report.json

Run from project root:
    python ml/scripts/threshold_analysis.py                          (v2 models)
    python ml/scripts/threshold_analysis.py --models-dir ml/models_v3 (v3 models)
"""
import os, sys, json, argparse
import numpy as np
import joblib
from sklearn.model_selection import train_test_split

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
import rerun_experiments as rx

DEPLOYED = 0.85
SWEEP = [0.50, 0.60, 0.70, 0.75, 0.80, 0.85, 0.90, 0.95]


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--models-dir", default="ml/models_v2", help="folder with category_model.pkl; output is written there too")
    mdir = os.path.join(rx.ROOT, ap.parse_args().models_dir)
    cfpb = rx.load_cfpb({})
    _, X_te, _, y_te = train_test_split(cfpb["cleaned_text"], cfpb["category"],
                                        test_size=0.2, random_state=rx.SEED,
                                        stratify=cfpb["category"])
    model_path = os.path.join(mdir, "category_model.pkl")
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

    # --- safeguard policy: exclude predicted-high-priority cases from auto-resolution
    pri_pipe = joblib.load(os.path.join(mdir, "priority_model.pkl"))
    pri_pred = pri_pipe.predict(X_te)
    pri_rule = cfpb.loc[X_te.index, "priority"].to_numpy()   # rule-derived label of the same complaints
    not_high = pri_pred != "high"

    def policy(t):
        base = conf > t
        elig = base & not_high
        out = {"threshold": t,
               "n_threshold_only": int(base.sum()),
               "n_excluded_predicted_high": int((base & ~not_high).sum()),
               "n_eligible": int(elig.sum()),
               "share_eligible": round(float(elig.mean()), 4),
               "accuracy_eligible": round(float(correct[elig].mean()), 4) if elig.any() else None,
               "n_wrong_eligible": int((~correct[elig]).sum()),
               "n_human_routed": int((~elig).sum()),
               "accuracy_human_routed": round(float(correct[~elig].mean()), 4) if (~elig).any() else None,
               "rule_high_auto_threshold_only": int((base & (pri_rule == "high")).sum()),
               "rule_high_auto_with_policy": int((elig & (pri_rule == "high")).sum())}
        return out

    report = {"model": model_path, "n_test": int(len(y)),
              "overall_accuracy": round(float(correct.mean()), 4),
              "deployed_threshold": at(DEPLOYED),
              "per_category_at_deployed": {},
              "sweep": [at(t) for t in SWEEP],
              "policy_conf_and_not_high_priority": {
                  "rule": "eligible = category confidence > threshold AND predicted priority != high",
                  "deployed_threshold": policy(DEPLOYED),
                  "sweep": [policy(t) for t in SWEEP]}}
    auto = conf > DEPLOYED
    for c in sorted(set(y)):
        m = y == c
        report["per_category_at_deployed"][c] = {
            "n_test": int(m.sum()),
            "share_auto": round(float(auto[m].mean()), 4),
            "accuracy_auto": round(float(correct[m & auto].mean()), 4) if (m & auto).any() else None}
    out = os.path.join(mdir, "threshold_report.json")
    with open(out, "w") as f:
        json.dump(report, f, indent=2)
    print(json.dumps(report["deployed_threshold"], indent=2))
    print(json.dumps(report["policy_conf_and_not_high_priority"]["deployed_threshold"], indent=2))
    print("Saved ->", out)


if __name__ == "__main__":
    main()
