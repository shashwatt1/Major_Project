"""Deadline audit: recompute every reported metric from the saved raw files with independent code
and compare with the saved results. Writes audit/audit_results.json. Read-only on all existing files.

Independence: token F1, BLEU n-gram statistics, macro-F1 and P@k/R@k are re-implemented here and do
not import scripts/metrics.py or scripts/score_rag.py. sacrebleu is used only for its 13a tokenizer
and as a second reference value. Key facts (v2.1, SCORING_SPEC.md) are scored by kf_v2 below, which does
not import scripts/keyfact_rules.py or metrics.key_fact_hit.
"""
from __future__ import annotations

import csv
import json
import math
import re
import sys
import unicodedata
from collections import Counter, defaultdict
from pathlib import Path

import numpy as np

EVAL = Path(__file__).resolve().parents[1]
OUT = EVAL / "audit"
OUT.mkdir(exist_ok=True)
sys.path.insert(0, str(EVAL / "scripts"))
import common  # noqa: E402,F401  (adds backend/ to sys.path)


def jl(p):
    return [json.loads(l) for l in open(p, encoding="utf-8") if l.strip()]


# ---------------------------------------------------------------- independent token F1
def norm_ind(t: str) -> list[str]:
    t = unicodedata.normalize("NFKC", t or "").lower()
    t = re.sub(r"(\d),(\d)", r"\1\2", t)
    t = re.sub(r"(\d),(\d)", r"\1\2", t)  # second pass for 1,00,000 style
    t = re.sub(r"[-‐‑‒–—―−/]", " ", t)
    t = "".join(c for c in t if unicodedata.category(c)[0] not in "PS")
    return [w for w in t.split() if w not in {"a", "an", "the"}]


def f1_ind(pred: str, ref: str):
    p, r = norm_ind(pred), norm_ind(ref)
    if not p or not r:
        return (1.0, 1.0, 1.0) if p == r else (0.0, 0.0, 0.0)
    tp = sum((Counter(p) & Counter(r)).values())
    if tp == 0:
        return 0.0, 0.0, 0.0
    P, R = tp / len(p), tp / len(r)
    return P, R, 2 * P * R / (P + R)


# ---------------------------------------------------------------- independent corpus BLEU-4
def bleu_ind(hyps: list[str], refs: list[str]) -> float:
    from sacrebleu.tokenizers.tokenizer_13a import Tokenizer13a
    tok = Tokenizer13a()
    match, total = [0] * 4, [0] * 4
    hl = rl = 0
    for h, r in zip(hyps, refs):
        ht, rt = tok(h.strip()).split(), tok(r.strip()).split()
        hl, rl = hl + len(ht), rl + len(rt)
        for n in range(1, 5):
            hc = Counter(tuple(ht[i:i + n]) for i in range(len(ht) - n + 1))
            rc = Counter(tuple(rt[i:i + n]) for i in range(len(rt) - n + 1))
            match[n - 1] += sum((hc & rc).values())
            total[n - 1] += max(len(ht) - n + 1, 0)
    # sacrebleu 'exp' smoothing: the k-th zero-match order gets 1 / 2^k
    precs, k = [], 1
    for m, t in zip(match, total):
        if t == 0:
            return 0.0
        if m == 0:
            k *= 2
            precs.append(100.0 / (k * t))
        else:
            precs.append(100.0 * m / t)
    bp = 1.0 if hl > rl else (math.exp(1 - rl / hl) if hl > 0 else 0.0)
    return bp * math.exp(sum(math.log(p) for p in precs) / 4)


# ---------------------------------------------------------------- independent key-fact scoring (v1 matcher + v2.1 rules)
# Implements SCORING_SPEC.md from data/key_fact_rules_v2.json. Does NOT import scripts/keyfact_rules.py or
# metrics.key_fact_hit. Term matching is done on token lists (norm_ind) and money values are found by a
# token scanner instead of the production regex.
def orig_hit(ans: str, alts: list[str]) -> bool:
    """Original (v1) phrase matcher, re-implemented."""
    raw = unicodedata.normalize("NFKC", ans or "").lower()
    n = " " + " ".join(norm_ind(ans)) + " "
    for a in alts:
        if "+" in a:
            if re.search(re.escape(a) + r"(?!\+)", raw):
                return True
            continue
        na = " ".join(norm_ind(a))
        if na and (f" {na} " in n or (a.endswith("graduat") and na in n)):
            return True
    return False


_KF = {}


def _kspec():
    if not _KF:
        s = json.load(open(EVAL / "data" / "key_fact_rules_v2.json", encoding="utf-8"))
        g = s["groups"]

        def res(x):  # resolve "@GROUP" references, recursively through lists
            if isinstance(x, str):
                return g[x[1:]] if x.startswith("@") else x
            if isinstance(x, list):
                return [res(y) for y in x]
            if isinstance(x, dict):
                return {k: (v if k == "terms" else res(v)) for k, v in x.items()}
            return x

        _KF["rules"] = {q: [res(r) for r in rs] for q, rs in s["rules"].items()}
        t = s["text"]
        _KF["t"] = t
        _KF["rx"] = {k[:-6] if k.endswith("_regex") else k: re.compile(v) for k, v in t.items() if k.endswith("_regex")}
        _KF["unit_of"] = [(norm_ind(u), cls) for cls, us in t["money_units"].items() for u in us]
        _KF["unit_of"].sort(key=lambda x: -len(" ".join(x[0])))  # longest unit first
    return _KF


def _ind_prepare(raw):
    t = unicodedata.normalize("NFKC", raw or "").lower()
    t = t.replace("’", "'").replace("‘", "'")
    t = re.sub(r"(\d),(?=\d)", r"\1", t)
    return re.sub(r"(\w)'s\b", r"\1", t)


def _split(rxname, text):
    return [p for p in _kspec()["rx"][rxname].split(text) if p and p.strip()]


def _sents(raw):
    return _split("sentence_split", _ind_prepare(raw))


def _segs(sentence):
    return _split("strong_delimiters", sentence)


def _cls_of_seg(seg):
    return _split("weak_delimiters", seg)


def _all_clauses(sentence):
    out = []
    for g in _segs(sentence):
        out.extend(_cls_of_seg(g))
    return out


def _contains(piece, term):
    hay, needle = norm_ind(piece), norm_ind(term)
    if not needle:
        return False
    L = len(needle)
    return any(hay[i:i + L] == needle for i in range(len(hay) - L + 1))


def _any(piece, terms):
    return any(_contains(piece, x) for x in (terms or []))


def _neg(piece):
    rx = _kspec()["rx"]
    return rx["negation"].search(piece) is not None or rx["uncertainty"].search(piece) is not None


def _unc(sentence):
    return _kspec()["rx"]["uncertainty"].search(sentence) is not None


def _unit_at(toks, i):
    for u, cls in _kspec()["unit_of"]:
        if toks[i:i + len(u)] == u:
            return len(u), cls
    return 0, None


def _money(piece):
    """Token scanner for 'A [unit] (to|and)? B unit' and 'A unit'; leftmost, non-overlapping."""
    toks, out, i = norm_ind(piece), [], 0
    num = re.compile(r"^\d+$")
    while i < len(toks):
        if not num.match(toks[i]):
            i += 1
            continue
        a, found = float(toks[i]), None
        j0 = i + 1
        lu, _ = _unit_at(toks, j0)
        for skip_unit in ([lu, 0] if lu else [0]):          # optional unit after A (greedy first)
            j = j0 + skip_unit
            for sep in ([1, 0] if j < len(toks) and toks[j] in ("to", "and") else [0]):
                k = j + sep
                if k < len(toks) and num.match(toks[k]):
                    lu2, cls2 = _unit_at(toks, k + 1)
                    if lu2:
                        found = ((a, float(toks[k]), cls2), k + 1 + lu2)
                        break
            if found:
                break
        if not found and lu:
            found = ((a, a, _unit_at(toks, j0)[1]), j0 + lu)
        if found:
            out.append(found[0])
            i = found[1]
        else:
            i += 1
    return out


def _grades(piece):
    res = []
    for m in _kspec()["rx"]["grade"].finditer(piece):
        res.append({2: "A++", 1: "A+"}.get(m.group(0).count("+"), "A"))
    return res


def _target_vals(rule, piece):
    v = rule["value"]
    if "grade" in v:
        return _grades(piece)
    return [x for x in _money(piece) if x[2] == v["unit"]]


def _target(rule):
    v = rule["value"]
    return v["grade"] if "grade" in v else (float(v["lo"]), float(v["hi"]), v["unit"])


def _is_bare(piece, subject):
    ok = set(_kspec()["t"]["list_words"])
    for s in subject:
        ok.update(norm_ind(s))
    return all(w in ok for w in norm_ind(piece))


def ind_binding(rule, raw):
    tgt, grade_rule = _target(rule), "grade" in rule["value"]
    subj, forbid, comp = rule["subject"], rule.get("forbid", []), rule.get("competitors", [])
    for s in _sents(raw):
        if _unc(s):
            continue
        if any(not _any(s, grp) for grp in rule.get("require_in_sentence", [])):
            continue
        for seg in _segs(s):
            for c in _cls_of_seg(seg):
                if not _any(c, subj) or _neg(c) or _any(c, forbid):
                    continue
                own = _target_vals(rule, c)
                if own:                                         # step 1
                    if set(own) == {tgt} and not _any(c, comp):
                        return True
                    continue
                if _money(c) or _grades(c):                     # step 2
                    continue
                if not _is_bare(c, subj):
                    continue
                pool = [(cc, v) for cc in _cls_of_seg(seg) for v in _target_vals(rule, cc)]   # step 3
                if not pool:
                    pool = [(cc, v) for cc in _all_clauses(s) for v in _target_vals(rule, cc)]
                if not pool or {v for _, v in pool} != {tgt}:
                    continue
                holder = pool[0][0]
                if _neg(holder) or _any(holder, forbid) or (not grade_rule and _any(holder, comp)):
                    continue
                return True
    return False


def _qualification_met(term, unit, sentence, quals):
    q = None
    for cand in quals:
        if term in cand["terms"]:
            q = cand
            break
    if q is None:
        return True
    for c in _all_clauses(unit):
        if not _contains(c, term):
            continue
        if "require_any_in_clause" in q and not _any(c, q["require_any_in_clause"]):
            continue
        if "forbid_any_in_clause" in q and _any(c, q["forbid_any_in_clause"]):
            continue
        if "require_any_in_sentence" in q and not _any(sentence, q["require_any_in_sentence"]):
            continue
        return True
    return False


def ind_cooccur(rule, raw):
    quals = rule.get("qualified", [])
    for s in _sents(raw):
        if _any(s, rule.get("sentence_forbid", [])):
            continue
        for u in ([s] if rule.get("scope") == "sentence" else _all_clauses(s)):
            if _neg(u) or _any(u, rule.get("forbid", [])):
                continue
            ok = True
            for grp in rule["all"]:
                if not any(_contains(u, t) and _qualification_met(t, u, s, quals) for t in grp):
                    ok = False
                    break
            if not ok and len(rule["all"]) == 1:
                ok = any(re.search(x, u) for x in rule.get("raw_regex_any", []))
            if ok:
                return True
    return False


def ind_degree_denial(rule, raw):
    t, rx = _kspec()["t"], _kspec()["rx"]
    negs, W = set(t["denial_negators"]), t["denial_window_tokens"]
    for s in _sents(raw):
        if _unc(s) or rx["contradiction"].search(s):
            continue
        toks = norm_ind(s)
        ns = " ".join(toks)
        if not (rx["award"].search(ns) or "degree awarding" in ns or (toks and toks[0] == "no")):
            continue
        for i, w in enumerate(toks):
            if w not in negs or (i + 1 < len(toks) and toks[i + 1] == "only"):
                continue
            if {"degree", "degrees"} & set(toks[i + 1:i + 1 + W]):
                return True
        if "not a degree awarding" in ns or "non degree" in ns:
            return True
    return False


def ind_phrase_guarded(rule, raw):
    quals = rule.get("qualified", [])
    for s in _sents(raw):
        if _unc(s):
            continue
        if any(orig_hit(s, [a]) and _qualification_met(a, s, s, quals) for a in rule["alts"]):
            return True
    return False


_IND = {"binding": ind_binding, "cooccur": ind_cooccur, "degree_denial": ind_degree_denial,
        "phrase_guarded": ind_phrase_guarded}


def kf_v2(answer, qid, default_key_facts):
    rules = _kspec()["rules"].get(qid)
    if rules is None:
        return [orig_hit(answer, alts) for alts in default_key_facts]
    return [_IND[r["type"]](r, answer or "") for r in rules]


def main():
    import sacrebleu
    from scipy.stats import wilcoxon, binomtest

    tests = {q["id"]: q for q in jl(EVAL / "rag_test_set.jsonl")}
    preds = jl(EVAL / "raw_predictions.jsonl")
    saved_rows = list(csv.DictReader(open(EVAL / "answer_level_f1_results.csv", encoding="utf-8")))
    saved_bleu = json.load(open(EVAL / "bleu_results.json"))
    saved_sum = json.load(open(EVAL / "results/rag_summary.json"))
    A = {}
    issues = []

    # ------------------------------------------------ 1. data integrity
    configs = ["rag_pdfkit", "no_rag", "rag_pypdf"]
    keys = Counter((p["config"], p["run"], p["query_id"]) for p in preds)
    expected = {(c, r, q) for c in configs for r in (1, 2, 3) for q in tests}
    A["integrity"] = {
        "n_generations": len(preds), "expected": len(expected),
        "duplicate_keys": [k for k, v in keys.items() if v > 1],
        "missing_keys": sorted(map(str, expected - set(keys))),
        "status_counts": dict(Counter(p["status"] for p in preds)),
        "empty_answers": sum(1 for p in preds if p["status"] == "ok" and not p["answer"].strip()),
        "n_test_questions": len(tests),
        "by_answerability": dict(Counter(q["answerability"] for q in tests.values())),
        "duplicate_question_texts": [q for q, c in Counter(t["question"].strip().lower() for t in tests.values()).items() if c > 1],
        "reference_or_label_text_in_any_prompt": sum(1 for p in preds if p["status"] == "ok" and
                                                     any(tests[p["query_id"]]["reference_answer"] in p["prompt"] for _ in [0])),
        "question_text_matches_test_set": all(p["question"] == tests[p["query_id"]]["question"] for p in preds),
    }
    # near-duplicate questions (token Jaccard > 0.7)
    qs = list(tests.values())
    near = []
    for i in range(len(qs)):
        for j in range(i + 1, len(qs)):
            a, b = set(norm_ind(qs[i]["question"])), set(norm_ind(qs[j]["question"]))
            if len(a & b) / len(a | b) > 0.6:
                near.append((qs[i]["id"], qs[j]["id"], round(len(a & b) / len(a | b), 2)))
    A["integrity"]["near_duplicate_questions_jaccard_gt_0.6"] = near

    # ------------------------------------------------ 2. token F1 recomputation
    ans_ids = [q for q, t in tests.items() if t["answerability"] == "answerable"]
    saved = {(r["config"], int(r["run"]), r["query_id"]): r for r in saved_rows}
    maxdiff, mism = 0.0, []
    per = defaultdict(dict)  # (cfg, run) -> qid -> f1
    for p in preds:
        if p["query_id"] not in ans_ids:
            continue
        P, R, F = f1_ind(p["answer"] if p["status"] == "ok" else "", tests[p["query_id"]]["reference_answer"])
        per[(p["config"], p["run"])][p["query_id"]] = (P, R, F)
        s = saved[(p["config"], p["run"], p["query_id"])]
        d = max(abs(P - float(s["token_precision"])), abs(R - float(s["token_recall"])), abs(F - float(s["token_f1"])))
        maxdiff = max(maxdiff, d)
        if d > 1e-3:
            mism.append((p["config"], p["run"], p["query_id"], round(F, 4), s["token_f1"]))
    f1 = {}
    for c in configs:
        run_means = [np.mean([per[(c, r)][q][2] for q in ans_ids]) for r in (1, 2, 3)]
        f1[c] = {"mean_of_run_means": round(float(np.mean(run_means)), 4), "sd_over_runs": round(float(np.std(run_means, ddof=1)), 4),
                 "per_run": [round(float(x), 4) for x in run_means],
                 "precision": round(float(np.mean([np.mean([per[(c, r)][q][0] for q in ans_ids]) for r in (1, 2, 3)])), 4),
                 "recall": round(float(np.mean([np.mean([per[(c, r)][q][1] for q in ans_ids]) for r in (1, 2, 3)])), 4),
                 "saved": saved_sum["per_config"][c]["token_f1"]["mean"]}
    A["token_f1"] = {"n_rows_compared": sum(len(v) for v in per.values()), "max_abs_diff_vs_saved": maxdiff,
                     "mismatches_gt_1e-3": mism, "by_config": f1}

    # ------------------------------------------------ 3. BLEU recomputation (independent + sacrebleu functional API)
    bl = {}
    for c in configs:
        runs = []
        for r in (1, 2, 3):
            pm = {p["query_id"]: (p["answer"] if p["status"] == "ok" else "") for p in preds if p["config"] == c and p["run"] == r}
            hyps = [pm[q] for q in ans_ids]
            refs = [tests[q]["reference_answer"] for q in ans_ids]
            ind = bleu_ind(hyps, refs)
            sb = sacrebleu.corpus_bleu(hyps, [refs], tokenize="13a", smooth_method="exp").score
            runs.append({"run": r, "independent": round(ind, 3), "sacrebleu_functional": round(sb, 3),
                         "saved": saved_bleu["results"][c][f"run{r}"]["bleu"]})
        bl[c] = {"runs": runs, "mean_independent": round(float(np.mean([x["independent"] for x in runs])), 3),
                 "saved_mean": saved_bleu["results"][c]["mean_over_runs"]}
    A["bleu"] = bl

    # ------------------------------------------------ 4. key facts: independent reimplementation + reference self-check
    # v2.1 rules via the independent implementation above (kf_v2); v1 matcher (orig_hit) for page-text check.
    kf_hit = orig_hit
    kf = defaultdict(dict)
    kmis = 0
    for p in preds:
        if p["query_id"] not in ans_ids:
            continue
        facts = kf_v2(p["answer"] if p["status"] == "ok" else "", p["query_id"], tests[p["query_id"]]["key_facts"])
        kf[(p["config"], p["run"])][p["query_id"]] = (sum(facts) / len(facts), int(all(facts)))
        s = saved[(p["config"], p["run"], p["query_id"])]
        if abs(kf[(p["config"], p["run"])][p["query_id"]][0] - float(s["key_fact_recall"])) > 1e-3 or kf[(p["config"], p["run"])][p["query_id"]][1] != int(s["all_key_facts"]):
            kmis += 1
    ref_self = [q for q in ans_ids if not all(kf_v2(tests[q]["reference_answer"], q, tests[q]["key_facts"]))]
    # key facts present in the cited page text (PDFKit extraction)?
    pages = json.load(open(EVAL / "source/pages_pdfkit.json", encoding="utf-8"))
    not_in_page = []
    for q in ans_ids:
        txt = " ".join(pages[p - 1] for p in tests[q]["source_pages"])
        for alts in tests[q]["key_facts"]:
            if not kf_hit(txt, alts):
                not_in_page.append((q, alts))
    A["key_facts"] = {"rows_mismatching_saved": kmis, "references_missing_own_key_facts": ref_self,
                      "key_facts_not_found_in_cited_page_text": not_in_page,
                      "by_config": {c: {"key_fact_recall": round(float(np.mean([np.mean([kf[(c, r)][q][0] for q in ans_ids]) for r in (1, 2, 3)])), 4),
                                        "all_key_facts": round(float(np.mean([np.mean([kf[(c, r)][q][1] for q in ans_ids]) for r in (1, 2, 3)])), 4)}
                                    for c in configs}}

    # ------------------------------------------------ 5. statistics: unit = question (run-averaged), paired
    def qmeans(c, which):
        if which == "token_f1":
            return np.array([np.mean([per[(c, r)][q][2] for r in (1, 2, 3)]) for q in ans_ids])
        idx = 0 if which == "key_fact_recall" else 1
        return np.array([np.mean([kf[(c, r)][q][idx] for r in (1, 2, 3)]) for q in ans_ids])
    rng = np.random.default_rng(42)
    boot_idx = rng.integers(0, len(ans_ids), size=(10000, len(ans_ids)))
    stats, pvals = [], []
    for sysc in ("rag_pdfkit", "rag_pypdf"):
        for m in ("token_f1", "key_fact_recall", "all_key_facts"):
            a, b = qmeans(sysc, m), qmeans("no_rag", m)
            d = a - b
            bd = d[boot_idx].mean(axis=1)
            w = wilcoxon(a, b)  # zero_method='wilcox' (zero differences dropped), two-sided
            nz = d[np.abs(d) > 1e-12]
            sign = binomtest(int((nz > 0).sum()), len(nz), 0.5).pvalue if len(nz) else 1.0
            stats.append({"system": sysc, "metric": m, "n_questions": len(d), "n_nonzero_diffs": int(len(nz)),
                          "mean_diff": round(float(d.mean()), 4), "boot95": [round(float(np.percentile(bd, 2.5)), 4), round(float(np.percentile(bd, 97.5)), 4)],
                          "wilcoxon_p": float(w.pvalue), "sign_test_p": float(sign)})
            pvals.append(float(w.pvalue))
    # Holm correction across the 6 Wilcoxon tests
    order = np.argsort(pvals)
    holm = [None] * len(pvals)
    running = 0.0
    for rank, i in enumerate(order):
        running = max(running, min(1.0, (len(pvals) - rank) * pvals[i]))
        holm[i] = running
    for s, h in zip(stats, holm):
        s["wilcoxon_p_holm6"] = round(h, 6)
    saved_cmp = {(c["system"], c["metric"]): c for c in saved_sum["paired_comparisons"]}
    for s in stats:
        sc = saved_cmp[(s["system"], s["metric"])]
        s["saved_mean_diff"], s["saved_boot95"], s["saved_wilcoxon_p"] = sc["mean_difference"], [sc["bootstrap95_lo"], sc["bootstrap95_hi"]], sc["wilcoxon_p"]
    # paired bootstrap for BLEU (new): resample questions, corpus BLEU per run, average runs
    def bleu_mean(c, idx):
        out = []
        for r in (1, 2, 3):
            pm = {p["query_id"]: p["answer"] for p in preds if p["config"] == c and p["run"] == r}
            hyps = [pm[ans_ids[i]] for i in idx]
            refs = [tests[ans_ids[i]]["reference_answer"] for i in idx]
            out.append(sacrebleu.corpus_bleu(hyps, [refs], tokenize="13a", smooth_method="exp").score)
        return float(np.mean(out))
    bb_idx = np.random.default_rng(7).integers(0, len(ans_ids), size=(1000, len(ans_ids)))
    bleu_boot = {}
    for sysc in ("rag_pdfkit", "rag_pypdf"):
        diffs = np.array([bleu_mean(sysc, ix) - bleu_mean("no_rag", ix) for ix in bb_idx])
        bleu_boot[sysc] = {"observed_diff": round(bleu_mean(sysc, range(len(ans_ids))) - bleu_mean("no_rag", range(len(ans_ids))), 3),
                           "boot95": [round(float(np.percentile(diffs, 2.5)), 3), round(float(np.percentile(diffs, 97.5)), 3)],
                           "resamples": 1000, "unit": "question (all 3 runs of a question move together)", "seed": 7}
    A["statistics"] = {"design": "40 answerable questions; per question the 3 runs are averaged first, so the paired unit is the question (n=40), not the 120 generations.",
                       "bootstrap": "percentile, 10,000 resamples of questions with replacement, numpy default_rng(42)",
                       "wilcoxon": "scipy.stats.wilcoxon two-sided, zero_method='wilcox' (ties at zero dropped); assumes independent questions and a symmetric distribution of differences",
                       "tests": stats, "bleu_paired_bootstrap": bleu_boot}

    # ------------------------------------------------ 6. retrieval recomputation
    chunks = {r["chunk_id"]: r for r in jl(EVAL / "results/chunks_pdfkit.jsonl")}
    from metrics import alnum as _alnum  # only used to re-verify relevance labels against chunk text
    label_err = []
    for q in ans_ids:
        for g in tests[q]["relevant_chunks"]["pdfkit"]:
            for cid in g["relevant_chunk_ids"]:
                if not any(_alnum(qt) in _alnum(chunks[cid]["text"]) for qt in g["matched_quotes"]) or g["page"] not in chunks[cid]["pages"]:
                    label_err.append((q, cid))
    ret = {}
    for c, corpus in (("rag_pdfkit", "pdfkit"), ("rag_pypdf", "pypdf")):
        recs = {(p["run"], p["query_id"]): p for p in preds if p["config"] == c}
        consist = 0
        for p in recs.values():  # app list must equal raw top-3 filtered by sq_l2 < 1.0
            exp = [x["chunk_id"] for x in p["raw_top10"][:3] if x["sq_l2"] < 1.0]
            consist += exp == [x["chunk_id"] for x in p["retrieved"]]
        res = {}
        for name in ("raw@1", "raw@3", "raw@5", "raw@10", "app@3"):
            P_, R_, H_, n = [], [], [], 0
            for q in ans_ids:
                groups = [g for g in tests[q]["relevant_chunks"][corpus] if g["found"]]
                if not groups:
                    continue
                n += 1
                rel = set().union(*[set(g["relevant_chunk_ids"]) for g in groups])
                p = recs[(1, q)]
                k = 3 if name == "app@3" else int(name.split("@")[1])
                ids = [x["chunk_id"] for x in p["retrieved"]] if name == "app@3" else [x["chunk_id"] for x in p["raw_top10"][:k]]
                P_.append(sum(i in rel for i in ids) / k)
                R_.append(sum(any(i in g["relevant_chunk_ids"] for i in ids) for g in groups) / len(groups))
                H_.append(int(any(i in rel for i in ids)))
            res[name] = {"n": n, "P": round(float(np.mean(P_)), 4), "R": round(float(np.mean(R_)), 4), "Hit": round(float(np.mean(H_)), 4),
                         "saved": saved_sum["retrieval"][c]["metrics"][name]}
        zero = np.mean([len(recs[(r, q)]["retrieved"]) == 0 for r in (1, 2, 3) for q in ans_ids])
        ret[c] = {"app_list_consistent_with_raw_top3_and_threshold": f"{consist}/{len(recs)}", "metrics": res,
                  "answerable_zero_chunk_share": round(float(zero), 4)}
    A["retrieval"] = {"relevance_label_errors": label_err, "by_config": ret,
                      "note": "P@k fixed denominator k; R@k = evidence groups covered / groups; retrieval identical across runs (checked in score_rag)."}

    # ------------------------------------------------ 7. intent: independent macro-F1 + re-run classifier
    from modules.intent_classifier import classify_intent
    ip = jl(EVAL / "results/intent_predictions.jsonl")
    rerun_diff = [r["id"] for r in ip if classify_intent(r["utterance"]) != r["predicted"]]
    def macro(rows):
        out = {}
        for c in ("command", "query"):
            tp = sum(r["label"] == c and r["predicted"] == c for r in rows)
            fp = sum(r["label"] != c and r["predicted"] == c for r in rows)
            fn = sum(r["label"] == c and r["predicted"] != c for r in rows)
            P = tp / (tp + fp) if tp + fp else 0.0
            R = tp / (tp + fn) if tp + fn else 0.0
            out[c] = {"tp": tp, "fp": fp, "fn": fn, "P": round(P, 4), "R": round(R, 4), "F1": round(2 * P * R / (P + R), 4) if P + R else 0.0}
        return {"n": len(rows), "per_class": out, "macro_f1": round((out["command"]["F1"] + out["query"]["F1"]) / 2, 4),
                "accuracy": round(sum(r["label"] == r["predicted"] for r in rows) / len(rows), 4)}
    core = {"canonical", "polite", "general", "rag"}
    saved_int = json.load(open(EVAL / "intent_classification_results.json"))
    A["intent"] = {"rerun_prediction_differences": rerun_diff, "duplicate_utterances": [u for u, c in Counter(r["utterance"].lower() for r in ip).items() if c > 1],
                   "full": macro(ip), "core": macro([r for r in ip if r["category"] in core]),
                   "challenge": macro([r for r in ip if r["category"] not in core]),
                   "by_category": {c: f"{sum(r['correct'] for r in ip if r['category'] == c)}/{sum(1 for r in ip if r['category'] == c)}" for c in sorted({r['category'] for r in ip})},
                   "saved_macro": {k: saved_int[k]["macro"]["f1"] for k in ("full_set", "core_subset", "challenge_subset")}}

    # ------------------------------------------------ 8. automation: re-run dry run (intercepted) and compare
    import run_automation_eval as rae
    fresh = {r["case_id"]: (r["outcome"], r["resolved_type"], r["resolved_target"]) for r in rae.dry_run()}
    old = {r["case_id"]: (r["outcome"], r["resolved_type"], r["resolved_target"]) for r in csv.DictReader(open(EVAL / "results/automation_dry_run.csv"))}
    A["automation"] = {"dry_run_reproduced_identically": fresh == old, "differences": {k: (old.get(k), v) for k, v in fresh.items() if old.get(k) != v},
                       "safety_cases": {k: fresh[k] for k in ("A31", "A34", "A35", "A36", "A38")},
                       "live": [{k: r[k] for k in ("case_id", "app", "outcome", "process_seen_after_s")} for r in csv.DictReader(open(EVAL / "results/automation_live_run.csv"))]}

    (OUT / "audit_results.json").write_text(json.dumps(A, indent=2, ensure_ascii=False, default=lambda o: o.item() if hasattr(o, "item") else str(o)), encoding="utf-8")
    print(json.dumps({k: (v if k not in ("statistics",) else v["tests"]) for k, v in A.items()}, indent=1, ensure_ascii=False, default=str)[:12000])
    print(json.dumps(A["statistics"]["bleu_paired_bootstrap"], indent=1))


if __name__ == "__main__":
    main()
