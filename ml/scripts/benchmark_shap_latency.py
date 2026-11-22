"""
ml/scripts/benchmark_shap_latency.py

Run AFTER rerun_experiments.py. Uses the v2 Logistic Regression pipelines.

Part A - Latency (in-process, model level; not the full HTTP/API path):
  * hardware/OS info
  * warm-up requests excluded
  * p50 / p95 / max for: prediction only, prediction + SHAP
  * SHAP with the explainer built once vs. rebuilt on every request
    (shows whether the ~180 ms in the paper comes from rebuilding it)
  * 1, 5 and 10 concurrent workers

Part B - SHAP baseline check on 30 test complaints (category model):
  zero (empty-document) background vs. training-mean background:
  overlap of the top-10 terms (Jaccard) and of the top-1 term.

Output: ml/models_v2/benchmark_report.json

Run from project root:
    python ml/scripts/benchmark_shap_latency.py                          (v2 models)
    python ml/scripts/benchmark_shap_latency.py --models-dir ml/models_v3 (v3 models)
"""
import os, sys, json, time, platform, argparse
from concurrent.futures import ThreadPoolExecutor
import numpy as np
import pandas as pd
import joblib
import shap

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
import preprocess as pp

MODELS = os.path.join(pp.ROOT, "ml", "models_v2")   # overridden by --models-dir
WARMUP, N_REQ, N_SHAP_CASES, TOP = 10, 200, 30, 10
rng = np.random.default_rng(42)


def system_info():
    info = {"os": platform.platform(), "python": platform.python_version(),
            "processor": platform.processor() or platform.machine(),
            "cpu_count_logical": os.cpu_count(), "shap": shap.__version__}
    try:
        import psutil
        info["ram_gb"] = round(psutil.virtual_memory().total / 1e9, 1)
        info["cpu_count_physical"] = psutil.cpu_count(logical=False)
    except ImportError:
        info["ram_gb"] = "install psutil to record RAM"
    try:
        import sklearn
        info["sklearn"] = sklearn.__version__
    except ImportError:
        pass
    return info


def pct(ms):
    a = np.array(ms)
    return {"n": len(a), "mean_ms": round(a.mean(), 1), "p50_ms": round(np.percentile(a, 50), 1),
            "p95_ms": round(np.percentile(a, 95), 1), "max_ms": round(a.max(), 1)}


def load():
    pipes = {t: joblib.load(os.path.join(MODELS, f"{t}_model.pkl"))
             for t in ("category", "priority", "sentiment")}
    texts = pd.read_csv(os.path.join(pp.OUT_DIR, "cfpb_clean.csv"),
                        usecols=["consumer_complaint_narrative"])["consumer_complaint_narrative"]
    texts = texts.dropna().sample(WARMUP + N_REQ + 50, random_state=42).tolist()
    return pipes, texts


def make_explainers(pipes):
    out = {}
    for t, p in pipes.items():
        n = len(p.named_steps["tfidf"].vocabulary_)
        out[t] = shap.LinearExplainer(p.named_steps["clf"], np.zeros((1, n)))
    return out


def one_request(raw, pipes, explainers, with_shap, rebuild):
    cleaned = pp.clean_text(raw)
    t0 = time.perf_counter()
    for t, p in pipes.items():
        pred = p.predict([cleaned])[0]
        if with_shap:
            vec = p.named_steps["tfidf"].transform([cleaned])
            clf = p.named_steps["clf"]
            exp = (shap.LinearExplainer(clf, np.zeros((1, vec.shape[1])))
                   if rebuild else explainers[t])
            sv = exp.shap_values(vec.toarray())
            k = list(clf.classes_).index(pred)
            sv = sv[k] if isinstance(sv, list) else (sv[..., k] if np.ndim(sv) == 3 else sv)
    return (time.perf_counter() - t0) * 1000


def latency(pipes, texts):
    ex = make_explainers(pipes)
    res = {}
    for label, ws, rb in [("predict_only", False, False),
                          ("predict_plus_shap_explainer_reused", True, False),
                          ("predict_plus_shap_explainer_rebuilt_each_request", True, True)]:
        for x in texts[:WARMUP]:
            one_request(x, pipes, ex, ws, rb)
        res[label] = pct([one_request(x, pipes, ex, ws, rb) for x in texts[WARMUP:WARMUP + N_REQ]])
        print(label, res[label])
    conc = {}
    for w in (1, 5, 10):
        batch = texts[WARMUP:WARMUP + N_REQ]
        t0 = time.perf_counter()
        with ThreadPoolExecutor(max_workers=w) as pool:
            ms = list(pool.map(lambda x: one_request(x, pipes, ex, True, False), batch))
        wall = time.perf_counter() - t0
        conc[f"{w}_workers"] = pct(ms) | {"throughput_req_per_s": round(len(batch) / wall, 1)}
        print(w, "workers", conc[f"{w}_workers"])
    res["concurrency_predict_plus_shap"] = conc
    return res


def top_terms(sv, names, k):
    idx = np.argsort(-np.abs(sv))[:k]
    return [names[i] for i in idx if sv[i] != 0]


def baseline_check(pipe, texts):
    tf, clf = pipe.named_steps["tfidf"], pipe.named_steps["clf"]
    names = tf.get_feature_names_out()
    bg_texts = [pp.clean_text(x) for x in texts[:2000]] if len(texts) >= 2000 else [pp.clean_text(x) for x in texts]
    mean_bg = np.asarray(tf.transform(bg_texts).mean(axis=0))
    ex0 = shap.LinearExplainer(clf, np.zeros((1, len(names))))
    exm = shap.LinearExplainer(clf, mean_bg)
    jacc, top1 = [], []
    for raw in texts[-N_SHAP_CASES:]:
        c = pp.clean_text(raw)
        v = tf.transform([c]).toarray()
        k = list(clf.classes_).index(pipe.predict([c])[0])
        def pick(sv):
            return sv[k][0] if isinstance(sv, list) else (sv[0, :, k] if np.ndim(sv) == 3 else sv[0])
        a = top_terms(pick(ex0.shap_values(v)), names, TOP)
        b = top_terms(pick(exm.shap_values(v)), names, TOP)
        if a and b:
            jacc.append(len(set(a) & set(b)) / len(set(a) | set(b)))
            top1.append(a[0] == b[0])
    return {"cases": len(jacc), "top_k": TOP,
            "mean_jaccard_topk": round(float(np.mean(jacc)), 3),
            "min_jaccard_topk": round(float(np.min(jacc)), 3),
            "same_top1_term_share": round(float(np.mean(top1)), 3),
            "mean_background_built_from_n_complaints": len(bg_texts)}


def main():
    global MODELS
    ap = argparse.ArgumentParser()
    ap.add_argument("--models-dir", default="ml/models_v2")
    MODELS = os.path.join(pp.ROOT, ap.parse_args().models_dir)
    pipes, texts = load()
    report = {"system": system_info(),
              "setup": {"warmup_excluded": WARMUP, "requests": N_REQ,
                        "scope": "in-process: clean_text + 3 predictions (+ SHAP); excludes HTTP, DB writes"}}
    report["latency"] = latency(pipes, texts)
    more = pd.read_csv(os.path.join(pp.OUT_DIR, "cfpb_clean.csv"),
                       usecols=["consumer_complaint_narrative"])["consumer_complaint_narrative"].dropna()
    report["shap_baseline_check"] = baseline_check(
        pipes["category"], more.sample(min(len(more), 2000 + N_SHAP_CASES), random_state=7).tolist())
    print(json.dumps(report["shap_baseline_check"], indent=2))
    path = os.path.join(MODELS, "benchmark_report.json")
    with open(path, "w") as f:
        json.dump(report, f, indent=2)
    print("Saved ->", path)


if __name__ == "__main__":
    main()
