"""r4. BLEU means/SDs are recomputed at full precision with SacreBLEU from the frozen inputs (the stored 2-dp fields average rounded run scores and are NOT used). SD convention: sample SD (n-1) of the 3 run-level values, rounded once at the end.
Check that every number changed in this revision appears in the manuscript/response and equals the final
v2.1 results (evaluation_scoring_v2_workcopy_2026-10-28/final_results_v2.1). Read-only."""
import csv, json, sys, zipfile, re
from pathlib import Path
from lxml import etree
H = Path(__file__).resolve().parents[1]
import numpy as np, sacrebleu
F = H.parent / "evaluation_scoring_v2_workcopy_2026-10-28" / "final_results_v2.1"
x = etree.fromstring(zipfile.ZipFile(H / "revised_manuscript.docx").read("word/document.xml"))
doc = "".join(n.text or "" for n in x.iter() if etree.QName(n).localname == "t")
resp = (H / "submission" / "ICICAIEECE2027_Paper4_response_to_reviewers.md").read_text(encoding="utf-8")
bc = {(r["system"], r["metric"]): r for r in csv.DictReader(open(F / "baseline_comparison.csv")) if r.get("metric")}
_lines = open(F / "baseline_comparison.csv", encoding="utf-8").read().splitlines()
_end = next(i for i, l in enumerate(_lines[1:], 1) if not l.strip() or l.startswith("system,"))
cf = {r["config"]: r for r in csv.DictReader(_lines[:_end])}  # first table only (config-level means)
au = json.load(open(F / "audit/audit_results.json"))["statistics"]
st = {(t["system"], t["metric"]): t for t in au["tests"]}
fc = json.load(open(F / "fully_correct_final.json"))
ab = json.load(open(F / "ablation_threshold/ablation_summary.json"))
abp = {(p["system"], p["baseline"], p["metric"]): p for p in ab["paired"]}
f3 = lambda v: f"{float(v):.3f}"; f2 = lambda v: f"{float(v):.2f}"
_T = {json.loads(l)["id"]: json.loads(l) for l in open(F / "rag_test_set.jsonl", encoding="utf-8")}
_ids = [q for q, t in _T.items() if t["answerability"] == "answerable"]
_P = {(g["config"], g["run"], g["query_id"]): g for g in map(json.loads, open(F.parent / "raw_predictions.jsonl", encoding="utf-8"))}
def _bleu(c):
    r = [sacrebleu.corpus_bleu([(_P[(c, k, q)]["answer"] if _P[(c, k, q)]["status"] == "ok" else "") for q in _ids], [[_T[q]["reference_answer"] for q in _ids]], tokenize="13a", smooth_method="exp").score for k in (1, 2, 3)]
    a = np.array(r); return a.mean(), a.std(ddof=1)
BL = {c: _bleu(c) for c in ("rag_pdfkit", "no_rag", "rag_pypdf")}
checks = [
 ("A token F1", f3(cf["rag_pdfkit"]["token_f1_mean"]), "0.364"),
 ("B token F1", f3(cf["no_rag"]["token_f1_mean"]), "0.250"),
 ("C token F1", f3(cf["rag_pypdf"]["token_f1_mean"]), "0.306"),
 ("A BLEU mean (full precision)", f2(BL["rag_pdfkit"][0]), "8.14"), ("B BLEU mean", f2(BL["no_rag"][0]), "4.48"), ("C BLEU mean", f2(BL["rag_pypdf"][0]), "6.13"),
 ("A BLEU sd (n-1, full precision)", f2(BL["rag_pdfkit"][1]), "0.64"), ("B BLEU sd", f2(BL["no_rag"][1]), "0.38"), ("C BLEU sd", f2(BL["rag_pypdf"][1]), "1.33"),
 ("C F1 sd", f3(cf["rag_pypdf"]["token_f1_sd_runs"]), "0.006"),
 ("A kf", f3(cf["rag_pdfkit"]["key_fact_recall"]), "0.297"), ("B kf", f3(cf["no_rag"]["key_fact_recall"]), "0.054"), ("C kf", f3(cf["rag_pypdf"]["key_fact_recall"]), "0.155"),
 ("F1 diff", f3(st[("rag_pdfkit", "token_f1")]["mean_diff"]), "0.114"),
 ("F1 CI lo", f3(st[("rag_pdfkit", "token_f1")]["boot95"][0]), "0.050"), ("F1 CI hi", f3(st[("rag_pdfkit", "token_f1")]["boot95"][1]), "0.180"),
 ("F1 p exact", f"{st[('rag_pdfkit','token_f1')]['wilcoxon_p']:.4f}", "0.0006"),
 ("kf diff", f3(st[("rag_pdfkit", "key_fact_recall")]["mean_diff"]), "0.243"),
 ("kf CI", f"{f3(st[('rag_pdfkit','key_fact_recall')]['boot95'][0])},{f3(st[('rag_pdfkit','key_fact_recall')]['boot95'][1])}", "0.133,0.358"),
 ("BLEU diff", f2(au["bleu_paired_bootstrap"]["rag_pdfkit"]["observed_diff"]), "3.66"),
 ("BLEU CI", f"{f2(au['bleu_paired_bootstrap']['rag_pdfkit']['boot95'][0])},{f2(au['bleu_paired_bootstrap']['rag_pdfkit']['boot95'][1])}", "1.46,6.28"),
 ("A fully correct", str(fc["per_config"]["rag_pdfkit"]["verified_fully_correct"]), "21"),
 ("B fully correct", str(fc["per_config"]["no_rag"]["verified_fully_correct"]), "1"),
 ("C fully correct", str(fc["per_config"]["rag_pypdf"]["verified_fully_correct"]), "11"),
 ("N fully correct", str(fc["per_config"]["rag_pdfkit_nothreshold"]["verified_fully_correct"]), "33"),
 ("sign A-B", f'{fc["sign_tests_question_level"]["rag_pdfkit_vs_no_rag"]["better"]}/{fc["sign_tests_question_level"]["rag_pdfkit_vs_no_rag"]["worse"]} p={fc["sign_tests_question_level"]["rag_pdfkit_vs_no_rag"]["p_two_sided"]:.3f}', "8/0 p=0.008"),
 ("sign N-A", f'{fc["sign_tests_question_level"]["nothreshold_vs_rag_pdfkit"]["better"]}/{fc["sign_tests_question_level"]["nothreshold_vs_rag_pdfkit"]["worse"]} p={fc["sign_tests_question_level"]["nothreshold_vs_rag_pdfkit"]["p_two_sided"]:.2f}', "7/3 p=0.34"),
 ("A all-key hits", str(int(round(float(cf["rag_pdfkit"]["all_key_facts_correct"]) * 120))), "24"),
 ("N token F1", f3(ab["summary"]["rag_pdfkit_nothreshold"]["token_f1"]["mean"]), "0.404"),
 ("N kf", f3(ab["summary"]["rag_pdfkit_nothreshold"]["key_fact_recall"]["mean"]), "0.392"),
 ("N-A kf p", f"{abp[('rag_pdfkit_nothreshold','rag_pdfkit','key_fact_recall')]['wilcoxon_p']:.3f}", "0.078"),
 ("N-A allkey p", f"{abp[('rag_pdfkit_nothreshold','rag_pdfkit','all_key_facts')]['wilcoxon_p']:.3f}", "0.055"),
 ("N-A F1 CI includes 0", str(abp[('rag_pdfkit_nothreshold','rag_pdfkit','token_f1')]['boot95'][0] < 0), "True"),
]
bad = [(n, got, claimed) for n, got, claimed in checks if got != claimed]
for c in checks: print("OK " if c[1] == c[2] else "BAD", *c)
phr = ["0.250 to 0.364", "+0.114, 95% CI [+0.050, +0.180]", "8.14", "0.054 to 0.297", "+0.243, 95% CI [+0.133, +0.358]",
       "[+1.46, +6.28]", "against 1 of", "better on 8 questions", "= 0.008", "credited 24 RAG", "52% of cases", "3% otherwise",
       "0.364 to 0.404", "0.297 to 0.392", "21 to 33 of 120", "0.078 and 0.055", "= 0.34", "from 1 to 21", "0.364 ± 0.005",
       "8.14 ± 0.64", "4.48 ± 0.38", "6.13 ± 1.33", "sample SD (n − 1)", "refined after the outputs were inspected and is not human-validated", "in the same clause, or in a list naming it", "Key-fact recall uses rules refined after outputs were inspected", "0.306 ± 0.006", "1/120", "0.155", "53 sampled items", "14 corrected"]
miss = [p for p in phr if p not in doc]
stale = [p for p in ["0.365", "8.15", "4.48 ± 0.37", "one clause and reject", "0.318", "0.067", "0/120", "0.184", "6.12", "0.00057", "against none", "55%", "0.403", "0.401", "21 to 32", "without independent human verification", "Using the Template", "Duplicate the template"] if p in doc]
stale_resp = [p for p in ["0.365", "8.15", "0.00057", "0 of 120", "six RAG", "+0.115", "6.27]"] if p in resp]
print("phrases missing in manuscript:", miss); print("stale in manuscript:", stale); print("stale in response:", stale_resp)
sys.exit(1 if bad or miss or stale or stale_resp else 0)
