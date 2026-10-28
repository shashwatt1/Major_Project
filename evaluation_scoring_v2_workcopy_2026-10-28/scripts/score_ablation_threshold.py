"""Score the exploratory relevance-threshold ablation against the frozen original runs.

Compared configurations (same questions, model, prompt template, top_k=3, Ollama defaults, 3 runs):
  rag_pdfkit              original app behaviour (filter: keep chunk only if squared L2 < 1.0)  [from raw_predictions.jsonl]
  rag_pdfkit_nothreshold  filter disabled; all top-3 chunks enter the prompt                     [ablation_threshold/raw_predictions_nothreshold.jsonl]
  no_rag                  reference point                                                        [from raw_predictions.jsonl]

Uses the same metric functions (scripts/metrics.py) and BLEU settings as score_rag.py.
Paired unit = question (3 runs averaged per question). Writes only into ablation_threshold/.
"""
from __future__ import annotations

import csv
import json
from collections import defaultdict

import numpy as np

from common import EVAL_DIR, now, read_jsonl
from keyfact_rules import fact_hits  # key-fact rules v2.1 (author-approved; final rescore completed 2026-10-28)
from metrics import is_abstention, key_fact_hit, token_prf

ABL = EVAL_DIR / "ablation_threshold"
CFGS = ["rag_pdfkit", "rag_pdfkit_nothreshold", "no_rag"]


def main():
    import sacrebleu
    from scipy.stats import binomtest, wilcoxon

    tests = {q["id"]: q for q in read_jsonl(EVAL_DIR / "rag_test_set.jsonl")}
    orig = [p for p in read_jsonl(EVAL_DIR / "raw_predictions.jsonl") if p["config"] in ("rag_pdfkit", "no_rag")]
    new = read_jsonl(ABL / "raw_predictions_nothreshold.jsonl")
    preds = orig + new
    P = {(p["config"], p["run"], p["query_id"]): p for p in preds}
    ans = [q for q, t in tests.items() if t["answerability"] == "answerable"]
    una = [q for q, t in tests.items() if t["answerability"] == "unanswerable"]
    amb = [q for q, t in tests.items() if t["answerability"] == "ambiguous"]
    R = {}

    # integrity
    R["integrity"] = {"new_generations": len(new), "expected": 52 * 3, "errors": sum(p["status"] != "ok" for p in new),
                      "missing": [f"{r}/{q}" for r in (1, 2, 3) for q in tests if ("rag_pdfkit_nothreshold", r, q) not in P],
                      "same_ranking_as_original": sum(
                          [x["chunk_id"] for x in P[("rag_pdfkit_nothreshold", r, q)]["raw_top10"]] ==
                          [x["chunk_id"] for x in P[("rag_pdfkit", r, q)]["raw_top10"]] for r in (1, 2, 3) for q in tests
                          if ("rag_pdfkit_nothreshold", r, q) in P),
                      "threshold_recorded": sorted({p.get("relevance_threshold") for p in new})}

    # per-generation scores
    rows = []
    for (c, r, q), p in sorted(P.items()):
        if c not in CFGS:
            continue
        a = p["answer"] if p["status"] == "ok" else ""
        row = {"config": c, "run": r, "query_id": q, "answerability": tests[q]["answerability"],
               "n_chunks_in_prompt": len(p.get("retrieved", [])), "abstained_auto": int(is_abstention(a))}
        if q in ans:
            pr, rc, f1 = token_prf(a, tests[q]["reference_answer"])
            facts = fact_hits(a, q, tests[q]["key_facts"])
            rel = set().union(*[set(g["relevant_chunk_ids"]) for g in tests[q]["relevant_chunks"]["pdfkit"] if g["found"]])
            ids = [x["chunk_id"] for x in p.get("retrieved", [])]
            groups = [g for g in tests[q]["relevant_chunks"]["pdfkit"] if g["found"]]
            row.update(token_precision=pr, token_recall=rc, token_f1=f1, key_fact_recall=sum(facts) / len(facts),
                       all_key_facts=int(all(facts)), evidence_hit=int(any(i in rel for i in ids)),
                       evidence_recall=sum(any(i in g["relevant_chunk_ids"] for i in ids) for g in groups) / len(groups))
        rows.append(row)
    fields = ["config", "run", "query_id", "answerability", "n_chunks_in_prompt", "token_precision", "token_recall", "token_f1",
              "key_fact_recall", "all_key_facts", "evidence_hit", "evidence_recall", "abstained_auto"]
    with open(ABL / "per_generation_scores.csv", "w", newline="", encoding="utf-8") as f:
        w = csv.DictWriter(f, fieldnames=fields)
        w.writeheader()
        for r in rows:
            w.writerow({k: (round(v, 6) if isinstance(v, float) else v) for k, v in ((k, r.get(k, "")) for k in fields)})

    by = defaultdict(dict)
    for r in rows:
        by[(r["config"], r["run"])][r["query_id"]] = r

    def runmean(c, m, ids):
        vals = [np.mean([by[(c, r)][q][m] for q in ids]) for r in (1, 2, 3)]
        return {"mean": round(float(np.mean(vals)), 4), "sd_over_runs": round(float(np.std(vals, ddof=1)), 4), "per_run": [round(float(v), 4) for v in vals]}

    summ = {}
    for c in CFGS:
        s = {m: runmean(c, m, ans) for m in ("token_f1", "token_precision", "token_recall", "key_fact_recall", "all_key_facts", "evidence_hit", "evidence_recall")}
        bl = []
        for r in (1, 2, 3):
            hyps = [by[(c, r)][q] and (P[(c, r, q)]["answer"] if P[(c, r, q)]["status"] == "ok" else "") for q in ans]
            refs = [tests[q]["reference_answer"] for q in ans]
            bl.append(sacrebleu.corpus_bleu(hyps, [refs], tokenize="13a", smooth_method="exp").score)
        s["corpus_bleu4"] = {"mean": round(float(np.mean(bl)), 2), "sd_over_runs": round(float(np.std(bl, ddof=1)), 2), "per_run": [round(b, 2) for b in bl]}
        s["abstention_auto_unanswerable"] = runmean(c, "abstained_auto", una)
        s["abstention_auto_ambiguous"] = runmean(c, "abstained_auto", amb)
        s["false_abstention_auto_answerable"] = runmean(c, "abstained_auto", ans)
        s["mean_chunks_in_prompt_answerable"] = round(float(np.mean([by[(c, r)][q]["n_chunks_in_prompt"] for r in (1, 2, 3) for q in ans])), 3)
        summ[c] = s
    R["summary"] = summ

    # paired comparisons, unit = question
    def qv(c, m):
        return np.array([np.mean([by[(c, r)][q][m] for r in (1, 2, 3)]) for q in ans])
    rng = np.random.default_rng(42)
    idx = rng.integers(0, len(ans), size=(10000, len(ans)))
    comps = []
    for a_c, b_c in (("rag_pdfkit_nothreshold", "rag_pdfkit"), ("rag_pdfkit_nothreshold", "no_rag")):
        for m in ("token_f1", "key_fact_recall", "all_key_facts", "evidence_hit"):
            a, b = qv(a_c, m), qv(b_c, m)
            d = a - b
            bd = d[idx].mean(axis=1)
            nz = d[np.abs(d) > 1e-12]
            wp = float(wilcoxon(a, b).pvalue) if len(nz) else 1.0
            comps.append({"system": a_c, "baseline": b_c, "metric": m, "n_questions": len(ans), "mean_diff": round(float(d.mean()), 4),
                          "boot95": [round(float(np.percentile(bd, 2.5)), 4), round(float(np.percentile(bd, 97.5)), 4)],
                          "wilcoxon_p": round(wp, 5), "n_nonzero": int(len(nz)), "better": int((d > 1e-12).sum()), "worse": int((d < -1e-12).sum())})
        # BLEU paired bootstrap (question resampling, runs averaged)
        def bm(c, ix):
            return float(np.mean([sacrebleu.corpus_bleu([P[(c, r, ans[i])]["answer"] for i in ix], [[tests[ans[i]]["reference_answer"] for i in ix]],
                                                        tokenize="13a", smooth_method="exp").score for r in (1, 2, 3)]))
        bix = np.random.default_rng(7).integers(0, len(ans), size=(1000, len(ans)))
        diffs = np.array([bm(a_c, ix) - bm(b_c, ix) for ix in bix])
        comps.append({"system": a_c, "baseline": b_c, "metric": "corpus_bleu4", "n_questions": len(ans),
                      "mean_diff": round(bm(a_c, range(len(ans))) - bm(b_c, range(len(ans))), 3),
                      "boot95": [round(float(np.percentile(diffs, 2.5)), 3), round(float(np.percentile(diffs, 97.5)), 3)],
                      "wilcoxon_p": None, "n_nonzero": None, "better": None, "worse": None})
    R["paired"] = comps
    R["generated"] = now()
    R["status"] = "EXPLORATORY: the threshold was singled out after inspecting retrieval on these same 52 questions; no held-out set."
    (ABL / "ablation_summary.json").write_text(json.dumps(R, indent=2), encoding="utf-8")
    print(json.dumps(R, indent=1)[:9000])


if __name__ == "__main__":
    main()
