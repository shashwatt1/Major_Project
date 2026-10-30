# Errata: BLEU-4 rounding in earlier reports (28 Oct 2026)

**Status.** This note records the issue. Historical reports and the frozen result files were **not** rewritten.

## What happened
`evaluation_scoring_v2_workcopy_2026-10-28/scripts/score_rag.py` (lines 105–112) rounds each run's corpus BLEU-4 to 2 decimals and then averages and takes the SD of the **rounded** run scores. The stored fields `bleu_results.json → results.*.mean_over_runs / sd_over_runs` therefore differ slightly from the exact values:

| Config | Stored (from rounded runs) | Exact (from unrounded runs) | Used in r4 paper |
|---|---|---|---|
| A. RAG (PDFKit) | 8.15 ± 0.64 | 8.1440 ± 0.6353 | **8.14 ± 0.64** |
| B. No-RAG | 4.48 ± 0.37 | 4.4805 ± 0.3753 | **4.48 ± 0.38** |
| C. RAG (pypdf) | 6.13 ± 1.33 | 6.1327 ± 1.3341 | 6.13 ± 1.33 (unchanged) |

Exact run scores, A: 8.406464, 8.606092, 7.419536. B: 4.068943, 4.803851, 4.568707. C: 7.553540, 5.937687, 4.906738.

**Not affected:**
* The paired BLEU difference and its bootstrap interval (+3.66 [1.46, 6.28]), which were computed from unrounded scores.
* All other metrics.

## SD convention (used consistently in the paper)
The sample standard deviation (n − 1) of the three run-level scores, computed from unrounded values and rounded once at the end. Token-F1 SDs follow the same convention (`np.std(ddof=1)`; verified against `per_run`).

**A correction to my proposal of 28 Oct.** I had proposed "8.14 ± 0.63" for A. That SD was taken from the audit's 3-decimal run scores (0.6349). At full precision it is 0.6353, which rounds to 0.64, so A's SD stays 0.64.

## Earlier documents repeating the rounded values (left unchanged)
* `evaluation_scoring_v2_workcopy_2026-10-28/final_results_v2.1/FINAL_RESCORE_REPORT.md`: "8.15 ± 0.64" and "4.48 ± 0.37".
* `evaluation_scoring_v2_preview_run_2026-10-28_b/CHECKPOINT_REPORT.md`: same values.
* `bleu_results.json`, `baseline_comparison.csv` and `results/rag_summary.json` (frozen results and package copies): rounded-run values, by design of the script.
* `manuscript_revision_final_2026-10-28/` (round 3): states 8.15, superseded by this folder.

**Where the exact values come from.**
* `final_results_v2.1/audit/audit_results.json → bleu.*.runs[].independent` (3-decimal, from independent code and SacreBLEU's API).
* A full-precision recomputation from the frozen inputs, done by `checks/verify_numbers.py` on every run.

**No rerun** of the evaluation or scoring was needed or done.
