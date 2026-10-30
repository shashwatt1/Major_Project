"""Final fully-correct counts = saved human judgements (read-only) + separate author judgements of newly
credited answers. Original annotation files are not modified. Writes final_results_v2.1/fully_correct_final.json."""
import csv, json
from pathlib import Path
from scipy.stats import binomtest
R = Path(__file__).resolve().parents[1]
def tsv(p): return {(r["config"], int(r["run"]), r["query_id"]): int(r["verified_correct"]) for r in csv.DictReader(open(p, encoding="utf-8"), delimiter="\t")}
J = tsv(R / "audit/manual_keyfact_adjudication_v1.tsv"); JA = tsv(R / "ablation_threshold/manual_keyfact_adjudication.tsv")
add = {(r["config"], int(r["run"]), r["query_id"]): int(r["AUTHOR_verified_correct (1/0)"]) for r in csv.DictReader(open(R / "author_judgements_newly_credited_2026-10-28.csv", encoding="utf-8"))}
for k, v in add.items(): (JA if k[0].endswith("nothreshold") else J)[k] = v
qs = [json.loads(l)["id"] for l in open(R / "rag_test_set.jsonl", encoding="utf-8") if json.loads(l)["answerability"] == "answerable"]
qv = lambda JX, c: {q: int(any(JX.get((c, r, q)) == 1 for r in (1, 2, 3))) for q in qs}
def sign(a, b):
    bt, wr = sum(a[q] > b[q] for q in qs), sum(a[q] < b[q] for q in qs)
    return {"better": bt, "worse": wr, "ties": len(qs) - bt - wr, "p_two_sided": round(binomtest(bt, bt + wr).pvalue, 5) if bt + wr else None}
cnt = lambda JX, c: sum(v for k, v in JX.items() if k[0] == c)
A, B, C, N = qv(J, "rag_pdfkit"), qv(J, "no_rag"), qv(J, "rag_pypdf"), qv(JA, "rag_pdfkit_nothreshold")
out = {"method": "Fully correct = every requested fact stated correctly and nothing contradicting the PDF. Judged only for answers credited with all key facts by the automatic rule (original v1 rule, plus answers newly credited by v2.1); answers not credited were not re-read, so counts are lower bounds. Judgements: single AI annotator (Claude) after outputs were seen, with 53 sampled items reviewed by the author (S001-S053) and 2 newly credited answers judged by the author (2026-10-28).",
       "author_judgements_added": [f"{k[0]} run{k[1]} {k[2]} = {v}" for k, v in add.items()],
       "per_config": {c: {"verified_fully_correct": cnt(JX, c), "of_generations": 120, "rate": round(cnt(JX, c) / 120, 4), "questions_with_>=1_verified_run": sum(qv(JX, c).values())}
                      for c, JX in (("rag_pdfkit", J), ("no_rag", J), ("rag_pypdf", J), ("rag_pdfkit_nothreshold", JA))},
       "sign_tests_question_level": {"rag_pdfkit_vs_no_rag": sign(A, B), "rag_pypdf_vs_no_rag": sign(C, B), "nothreshold_vs_rag_pdfkit": sign(N, A)}}
(R / "final_results_v2.1").mkdir(exist_ok=True)
(R / "final_results_v2.1/fully_correct_final.json").write_text(json.dumps(out, indent=2, ensure_ascii=False), encoding="utf-8")
print(json.dumps(out, indent=1, ensure_ascii=False))
