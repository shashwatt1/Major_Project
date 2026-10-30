"""Step 3: score raw_predictions.jsonl.

Outputs
  answer_level_f1_results.csv   per config x run x query: token P/R/F1, EM, key-fact recall, abstention
  bleu_results.json             corpus BLEU-4 (SacreBLEU) per config and run, answerable queries only
  retrieval_results.csv         per query x k: retrieved chunk IDs, relevance, P@k, R@k (rag configs)
  baseline_comparison.csv       config-level means and paired A-vs-B statistics
  results/rag_summary.json      everything above in one machine-readable file

Eligibility (fixed before scoring): token F1 / EM / BLEU / key-fact recall use the 40 'answerable'
queries. Unanswerable (7) and ambiguous (5) queries are scored only for abstention. Errored
generations are kept and scored as empty answers (F1 = 0), and counted in the report.
"""
from __future__ import annotations

import csv
import json
import statistics as st
from collections import defaultdict

import numpy as np

from common import EVAL_DIR, RESULTS_DIR, now, read_jsonl
from keyfact_rules import fact_hits  # key-fact rules v2.1 (author-approved; final rescore completed 2026-10-28)
from metrics import exact_match, is_abstention, key_fact_hit, token_prf

KS = (1, 3, 5, 10)


def _np(o):
    return o.item() if hasattr(o, "item") else str(o)


def mean_sd(xs):
    xs = list(xs)
    return (float(np.mean(xs)) if xs else float("nan"), float(np.std(xs, ddof=1)) if len(xs) > 1 else 0.0)


def paired_bootstrap(a, b, n=10000, seed=42):
    rng = np.random.default_rng(seed)
    a, b = np.asarray(a), np.asarray(b)
    idx = rng.integers(0, len(a), size=(n, len(a)))
    diffs = (a[idx] - b[idx]).mean(axis=1)
    return float(np.percentile(diffs, 2.5)), float(np.percentile(diffs, 97.5))


def main() -> None:
    import sacrebleu
    from scipy.stats import wilcoxon

    tests = {q["id"]: q for q in read_jsonl(EVAL_DIR / "rag_test_set.jsonl")}
    preds = [p for p in read_jsonl(EVAL_DIR / "raw_predictions.jsonl")]
    configs = sorted({p["config"] for p in preds}, key=["rag_pdfkit", "no_rag", "rag_pypdf"].index)
    runs = sorted({p["run"] for p in preds})

    # ---------- answer-level scores ----------
    rows = []
    for p in preds:
        q = tests[p["query_id"]]
        ans = p.get("answer", "") if p["status"] == "ok" else ""
        row = {"config": p["config"], "run": p["run"], "query_id": q["id"], "category": q["category"],
               "answerability": q["answerability"], "status": p["status"],
               "n_retrieved": len(p.get("retrieved", [])), "abstained": int(is_abstention(ans))}
        if q["answerability"] == "answerable":
            pr, rc, f1 = token_prf(ans, q["reference_answer"])
            facts = fact_hits(ans, q["id"], q["key_facts"])
            row.update(token_precision=round(pr, 4), token_recall=round(rc, 4), token_f1=round(f1, 4),
                       exact_match=exact_match(ans, q["reference_answer"]),
                       key_fact_recall=round(sum(facts) / len(facts), 4), all_key_facts=int(all(facts)))
        rows.append(row)
    fields = ["config", "run", "query_id", "category", "answerability", "status", "n_retrieved", "token_precision",
              "token_recall", "token_f1", "exact_match", "key_fact_recall", "all_key_facts", "abstained"]
    with open(EVAL_DIR / "answer_level_f1_results.csv", "w", newline="", encoding="utf-8") as f:
        w = csv.DictWriter(f, fieldnames=fields)
        w.writeheader()
        for r in rows:
            w.writerow({k: r.get(k, "") for k in fields})

    by = defaultdict(list)
    for r in rows:
        by[(r["config"], r["run"])].append(r)

    summary = {"generated": now(), "configs": configs, "runs": runs, "n_queries": len(tests),
               "n_answerable": sum(q["answerability"] == "answerable" for q in tests.values()),
               "per_config": {}}

    # ---------- BLEU ----------
    bleu_out = {"library": f"sacrebleu {sacrebleu.__version__}", "metric": "corpus BLEU-4",
                "settings": {"tokenize": "13a", "smooth_method": "exp", "lowercase": False, "max_ngram_order": 4,
                             "references_per_segment": 1},
                "eligible_queries": "answerable only (n=40); unanswerable/ambiguous excluded",
                "reference_construction": "one hand-written reference answer per query, grounded in the PDF (rag_test_set.jsonl)",
                "error_handling": "errored generations are scored as empty hypotheses",
                "results": {}}
    answerable_ids = [qid for qid, q in tests.items() if q["answerability"] == "answerable"]
    for cfg in configs:
        bleu_out["results"][cfg] = {}
        for run in runs:
            pmap = {p["query_id"]: (p.get("answer", "") if p["status"] == "ok" else "")
                    for p in preds if p["config"] == cfg and p["run"] == run}
            hyps = [pmap.get(qid, "") for qid in answerable_ids]
            refs = [tests[qid]["reference_answer"] for qid in answerable_ids]
            b = sacrebleu.metrics.BLEU(tokenize="13a", smooth_method="exp")
            score = b.corpus_score(hyps, [refs])
            bleu_out["results"][cfg][f"run{run}"] = {"bleu": round(score.score, 2), "precisions": [round(x, 2) for x in score.precisions],
                                                     "bp": round(score.bp, 4), "sys_len": score.sys_len, "ref_len": score.ref_len,
                                                     "n": len(hyps)}
            bleu_out["signature"] = str(b.get_signature())
        vals = [bleu_out["results"][cfg][f"run{r}"]["bleu"] for r in runs]
        m, s = mean_sd(vals)
        bleu_out["results"][cfg]["mean_over_runs"] = round(m, 2)
        bleu_out["results"][cfg]["sd_over_runs"] = round(s, 2)
    (EVAL_DIR / "bleu_results.json").write_text(json.dumps(bleu_out, indent=2, default=_np), encoding="utf-8")

    # ---------- config-level aggregates ----------
    for cfg in configs:
        agg = {}
        for metric in ("token_f1", "token_precision", "token_recall", "exact_match", "key_fact_recall", "all_key_facts"):
            per_run = [np.mean([r[metric] for r in by[(cfg, run)] if r["answerability"] == "answerable"]) for run in runs]
            m, s = mean_sd(per_run)
            agg[metric] = {"mean": round(m, 4), "sd_over_runs": round(s, 4), "per_run": [round(float(x), 4) for x in per_run]}
        f1_all = [r["token_f1"] for run in runs for r in by[(cfg, run)] if r["answerability"] == "answerable"]
        agg["token_f1_median_all_runs"] = round(float(np.median(f1_all)), 4)
        agg["token_f1_quartiles_all_runs"] = [round(float(x), 4) for x in np.percentile(f1_all, [25, 50, 75])]
        for ans_type in ("unanswerable", "ambiguous", "answerable"):
            per_run = [np.mean([r["abstained"] for r in by[(cfg, run)] if r["answerability"] == ans_type]) for run in runs]
            m, s = mean_sd(per_run)
            agg[f"abstention_rate_{ans_type}"] = {"mean": round(m, 4), "sd_over_runs": round(s, 4)}
        cats = sorted({q["category"] for q in tests.values() if q["answerability"] == "answerable"})
        agg["token_f1_by_category"] = {}
        agg["key_fact_recall_by_category"] = {}
        for c in cats:
            vals = [r for run in runs for r in by[(cfg, run)] if r["category"] == c and r["answerability"] == "answerable"]
            agg["token_f1_by_category"][c] = {"n_queries": len(vals) // len(runs), "mean": round(float(np.mean([v["token_f1"] for v in vals])), 4)}
            agg["key_fact_recall_by_category"][c] = round(float(np.mean([v["key_fact_recall"] for v in vals])), 4)
        agg["errors"] = sum(1 for p in preds if p["config"] == cfg and p["status"] != "ok")
        agg["generations"] = sum(1 for p in preds if p["config"] == cfg)
        if cfg != "no_rag":
            nr = [r["n_retrieved"] for run in runs for r in by[(cfg, run)]]
            agg["mean_chunks_passed_to_llm"] = round(float(np.mean(nr)), 3)
            agg["share_queries_with_zero_chunks_after_threshold"] = round(float(np.mean([x == 0 for x in nr])), 4)
            ans_nr = [r["n_retrieved"] for run in runs for r in by[(cfg, run)] if r["answerability"] == "answerable"]
            agg["answerable_share_zero_chunks"] = round(float(np.mean([x == 0 for x in ans_nr])), 4)
        lat_r = [p["retrieval_seconds"] for p in preds if p["config"] == cfg and p["status"] == "ok"]
        lat_g = [p["generation_seconds"] for p in preds if p["config"] == cfg and p["status"] == "ok"]
        agg["latency_seconds"] = {
            "retrieval_plus_prompt_build": {"mean": round(st.mean(lat_r), 4), "sd": round(st.stdev(lat_r), 4),
                                             "p50": round(float(np.percentile(lat_r, 50)), 4), "p95": round(float(np.percentile(lat_r, 95)), 4), "n": len(lat_r)},
            "llm_generation": {"mean": round(st.mean(lat_g), 3), "sd": round(st.stdev(lat_g), 3),
                               "p50": round(float(np.percentile(lat_g, 50)), 3), "p95": round(float(np.percentile(lat_g, 95)), 3), "n": len(lat_g)}}
        summary["per_config"][cfg] = agg

    # ---------- paired comparison vs baseline ----------
    comparisons = []
    for cfg in [c for c in configs if c != "no_rag"]:
        for metric in ("token_f1", "key_fact_recall", "all_key_facts"):
            def per_query(c):
                return [np.mean([r[metric] for run in runs for r in by[(c, run)] if r["query_id"] == qid]) for qid in answerable_ids]
            a, b = per_query(cfg), per_query("no_rag")
            diff = float(np.mean(a) - np.mean(b))
            lo, hi = paired_bootstrap(a, b)
            nz = [x - y for x, y in zip(a, b) if abs(x - y) > 1e-12]
            p = float(wilcoxon(a, b).pvalue) if len(nz) >= 1 else 1.0
            comparisons.append({"system": cfg, "baseline": "no_rag", "metric": metric, "n_queries": len(a),
                                "system_mean": round(float(np.mean(a)), 4), "baseline_mean": round(float(np.mean(b)), 4),
                                "mean_difference": round(diff, 4), "bootstrap95_lo": round(lo, 4), "bootstrap95_hi": round(hi, 4),
                                "wilcoxon_p": round(p, 6), "queries_system_better": sum(x > y for x, y in zip(a, b)),
                                "queries_baseline_better": sum(x < y for x, y in zip(a, b)), "ties": sum(x == y for x, y in zip(a, b))})
    summary["paired_comparisons"] = comparisons

    with open(EVAL_DIR / "baseline_comparison.csv", "w", newline="", encoding="utf-8") as f:
        w = csv.writer(f)
        w.writerow(["config", "description", "n_answerable", "runs", "token_f1_mean", "token_f1_sd_runs", "exact_match",
                    "key_fact_recall", "all_key_facts_correct", "corpus_bleu_mean", "corpus_bleu_sd_runs",
                    "abstention_unanswerable", "abstention_ambiguous", "false_abstention_answerable", "llm_errors"])
        desc = {"rag_pdfkit": "A: app RAG pipeline, PDF text via PDFKit (proposed)",
                "no_rag": "B: same LLM + app prompt template, retrieval disabled (baseline)",
                "rag_pypdf": "C: app RAG pipeline, PDF text via pypdf (extraction ablation)"}
        for cfg in configs:
            a = summary["per_config"][cfg]
            w.writerow([cfg, desc[cfg], summary["n_answerable"], len(runs), a["token_f1"]["mean"], a["token_f1"]["sd_over_runs"],
                        a["exact_match"]["mean"], a["key_fact_recall"]["mean"], a["all_key_facts"]["mean"],
                        bleu_out["results"][cfg]["mean_over_runs"], bleu_out["results"][cfg]["sd_over_runs"],
                        a["abstention_rate_unanswerable"]["mean"], a["abstention_rate_ambiguous"]["mean"],
                        a["abstention_rate_answerable"]["mean"], a["errors"]])
        w.writerow([])
        w.writerow(list(comparisons[0].keys()))
        for c in comparisons:
            w.writerow(list(c.values()))

    # ---------- retrieval ----------
    ret_rows, ret_summary = [], {}
    for cfg in [c for c in configs if c != "no_rag"]:
        corpus = "pdfkit" if cfg == "rag_pdfkit" else "pypdf"
        recs = {p["query_id"]: p for p in preds if p["config"] == cfg and p["run"] == runs[0] and p["status"] == "ok"}
        # retrieval is deterministic: verify identical chunk lists across runs
        det = all([x["chunk_id"] for x in p["retrieved"]] == [x["chunk_id"] for x in recs[p["query_id"]]["retrieved"]]
                  for p in preds if p["config"] == cfg and p["status"] == "ok" and p["query_id"] in recs)
        stats = defaultdict(list)
        n_excluded = 0
        for qid in answerable_ids:
            q = tests[qid]
            groups = [g for g in q["relevant_chunks"][corpus] if g["found"]]
            if not groups or qid not in recs:
                n_excluded += 1
                ret_rows.append({"config": cfg, "query_id": qid, "k": "", "note": "excluded: evidence not present in this extraction" if not groups else "excluded: generation error"})
                continue
            relevant = set().union(*[set(g["relevant_chunk_ids"]) for g in groups])
            rec = recs[qid]
            lists = {f"raw@{k}": [x["chunk_id"] for x in rec["raw_top10"][:k]] for k in KS}
            lists["app@3"] = [x["chunk_id"] for x in rec["retrieved"]]
            for name, ids in lists.items():
                k = 3 if name == "app@3" else int(name.split("@")[1])
                rel_flags = [int(i in relevant) for i in ids]
                covered = sum(any(i in g["relevant_chunk_ids"] for i in ids) for g in groups)
                prec = sum(rel_flags) / k
                prec_returned = (sum(rel_flags) / len(ids)) if ids else 0.0
                recall = covered / len(groups)
                hit = int(any(rel_flags))
                stats[(name, "precision")].append(prec)
                stats[(name, "precision_over_returned")].append(prec_returned)
                stats[(name, "recall")].append(recall)
                stats[(name, "hit")].append(hit)
                stats[(name, "n_returned")].append(len(ids))
                ret_rows.append({"config": cfg, "query_id": qid, "category": q["category"], "k": name,
                                 "retrieved_chunk_ids": " ".join(ids), "relevance_flags": " ".join(map(str, rel_flags)),
                                 "scores_sq_l2": " ".join(str(x["sq_l2"]) for x in rec["raw_top10"][:len(ids)]) if name != "app@3" else
                                 " ".join(str(next(r["sq_l2"] for r in rec["raw_top10"] if r["chunk_id"] == i)) for i in ids),
                                 "relevant_chunk_ids": " ".join(sorted(relevant)), "evidence_groups": len(groups),
                                 "groups_covered": covered, "precision_at_k": round(prec, 4), "recall_at_k": round(recall, 4),
                                 "hit_at_k": hit, "note": ""})
        ret_summary[cfg] = {"n_queries_scored": len(answerable_ids) - n_excluded, "n_excluded": n_excluded,
                            "deterministic_across_runs": det,
                            "metrics": {name: {m: round(float(np.mean(stats[(name, m)])), 4) for m in ("precision", "precision_over_returned", "recall", "hit", "n_returned")}
                                        for name in [f"raw@{k}" for k in KS] + ["app@3"]}}
        rl = [p["retrieval_seconds"] for p in preds if p["config"] == cfg and p["status"] == "ok"]
        ret_summary[cfg]["retrieval_latency_ms"] = {"mean": round(1000 * st.mean(rl), 2), "sd": round(1000 * st.stdev(rl), 2),
                                                    "p50": round(1000 * float(np.percentile(rl, 50)), 2), "p95": round(1000 * float(np.percentile(rl, 95)), 2), "n": len(rl)}
    fields = ["config", "query_id", "category", "k", "retrieved_chunk_ids", "relevance_flags", "scores_sq_l2", "relevant_chunk_ids",
              "evidence_groups", "groups_covered", "precision_at_k", "recall_at_k", "hit_at_k", "note"]
    with open(EVAL_DIR / "retrieval_results.csv", "w", newline="", encoding="utf-8") as f:
        w = csv.DictWriter(f, fieldnames=fields)
        w.writeheader()
        for r in ret_rows:
            w.writerow({k: r.get(k, "") for k in fields})
    summary["retrieval"] = ret_summary
    summary["bleu"] = bleu_out["results"]
    (RESULTS_DIR / "rag_summary.json").write_text(json.dumps(summary, indent=2, default=_np), encoding="utf-8")
    print(json.dumps({c: {"f1": summary["per_config"][c]["token_f1"]["mean"], "kf": summary["per_config"][c]["key_fact_recall"]["mean"],
                          "bleu": bleu_out["results"][c]["mean_over_runs"]} for c in configs}, indent=1))
    print(json.dumps(ret_summary, indent=1))


if __name__ == "__main__":
    main()
