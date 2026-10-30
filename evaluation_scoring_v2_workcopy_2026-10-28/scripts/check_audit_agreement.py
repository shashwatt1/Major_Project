"""Agreement check: production key-fact evaluator (scripts/keyfact_rules.py) vs the independent audit
implementation (kf_v2 in scripts/audit_recompute.py), on identical inputs. Read-only on all inputs.

Input sets
  1. unit-test CASES (also checked against the hand-written expected values)
  2. every saved generation in raw_predictions.jsonl (answerable questions, all configs and runs)
  3. every saved generation in ablation_threshold/raw_predictions_nothreshold.jsonl
  4. reference answers and cited catalogue page text for each answerable question
  5. stress set: every sentence of every saved generation, scored against every rule question

Writes agreement/agreement_report.json and prints a summary. Exit code 1 on any disagreement.
"""
from __future__ import annotations

import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "scripts"))
sys.path.insert(0, str(ROOT / "tests"))

from keyfact_rules import fact_hits, spec  # noqa: E402  production
from audit_recompute import kf_v2, _sents  # noqa: E402  independent audit
from test_keyfact_rules import CASES  # noqa: E402


def jl(p):
    return [json.loads(l) for l in open(p, encoding="utf-8") if l.strip()]


def main():
    tests = {q["id"]: q for q in jl(ROOT / "rag_test_set.jsonl")}
    ans_ids = [q for q, t in tests.items() if t["answerability"] == "answerable"]
    rule_q = sorted(spec()["rules"])
    report, dis = {}, []

    def cmp(setname, key, text, qid, facts):
        p = fact_hits(text, qid, facts)
        a = kf_v2(text, qid, facts)
        if p != a:
            dis.append({"set": setname, "key": key, "qid": qid, "production": p, "audit": a, "text": text[:400]})
        return p, a

    # 1. unit-test cases
    exp_fail = {"production": [], "audit": []}
    for i, (qid, text, exp, cat) in enumerate(CASES):
        p, a = cmp("unit_cases", i, text, qid, [])
        if p != exp:
            exp_fail["production"].append(i)
        if a != exp:
            exp_fail["audit"].append(i)
    report["unit_cases"] = {"n": len(CASES), "production_vs_expected_failures": exp_fail["production"],
                            "audit_vs_expected_failures": exp_fail["audit"]}

    # 2-3. saved generations
    gens = []
    for src, path in (("raw_predictions", ROOT / "raw_predictions.jsonl"),
                      ("ablation_nothreshold", ROOT / "ablation_threshold" / "raw_predictions_nothreshold.jsonl")):
        n = facts_n = 0
        for g in jl(path):
            q = g["query_id"]
            if q not in ans_ids:
                continue
            text = g["answer"] if g["status"] == "ok" else ""
            p, _ = cmp(src, f'{g["config"]}|{g["run"]}|{q}', text, q, tests[q]["key_facts"])
            n += 1
            facts_n += len(p)
            gens.append(text)
        report[src] = {"generations": n, "fact_decisions": facts_n,
                       "rule_question_generations": sum(1 for g in jl(path) if g["query_id"] in rule_q)}

    # 4. references and cited page text
    pages = json.load(open(ROOT / "source" / "pages_pdfkit.json", encoding="utf-8"))
    nref = 0
    for q in ans_ids:
        cmp("reference", q, tests[q]["reference_answer"], q, tests[q]["key_facts"])
        cmp("page_text", q, " ".join(pages[p - 1] for p in tests[q]["source_pages"]), q, tests[q]["key_facts"])
        nref += 2
    report["references_and_pages"] = {"inputs": nref}

    # 5. stress set: each generation sentence against every rule question
    sents = sorted({s for g in gens for s in _sents(g)})
    nd = 0
    for s in sents:
        for q in rule_q:
            p, _ = cmp("stress_sentence_x_rule", q, s, q, tests[q]["key_facts"])
            nd += len(p)
    report["stress"] = {"unique_sentences": len(sents), "rule_questions": len(rule_q), "fact_decisions": nd}

    report["disagreements"] = dis
    report["n_disagreements"] = len(dis)
    out = ROOT / "agreement"
    out.mkdir(exist_ok=True)
    (out / "agreement_report.json").write_text(json.dumps(report, indent=2, ensure_ascii=False), encoding="utf-8")
    print(json.dumps({k: v for k, v in report.items() if k != "disagreements"}, indent=1))
    for d in dis[:40]:
        print("DISAGREE", d["set"], d["key"], d["qid"], "prod", d["production"], "audit", d["audit"], "|", d["text"][:200])
    return 1 if dis or exp_fail["production"] or exp_fail["audit"] else 0


if __name__ == "__main__":
    sys.exit(main())
