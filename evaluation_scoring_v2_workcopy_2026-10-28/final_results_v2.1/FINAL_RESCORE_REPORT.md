# Final rescore: key-fact scoring v2.1 (28 Oct 2026)

**Where it ran and what was preserved.**
* Run in the isolated working copy `evaluation_scoring_v2_workcopy_2026-10-28/`.
* This folder holds the final outputs and logs.
* The pre-rescore results of the working copy (identical to the original package) are in `../pre_final_rescore_snapshot/`.
* The original package, `evaluation/`, the annotation files and the manuscript were not modified: 113/113 protected checksums OK (`logs/final_protected_checksums.log`).

**Inputs.**
* Rules: `data/key_fact_rules_v2.json` (v2.1), described in `SCORING_SPEC.md`.
* Q32 reference corrected (`REFERENCE_CHANGE_LOG.md`).
* Author judgements of the two newly credited answers: `author_judgements_newly_credited_2026-10-28.csv`. Both are correct. This file is separate from the original adjudication files, which were not edited.

**Checks (logs in `logs/`).**
* Unit tests: 88/88 OK.
* Production vs independent audit scorer: 0 disagreements.
* Sensitivity: all 4 injected faults detected.
* Audit recompute: 0 key-fact mismatches; token F1 max difference 5e-5; BLEU recomputed independently.
* Rescored files are byte-identical to the approved preview (`…_preview_run_2026-10-28_b`).

**Final metrics.** 40 answerable questions × 3 runs.

| | A RAG (PDFKit) | B no RAG | C RAG (pypdf) | No-threshold ablation |
|---|---|---|---|---|
| Token F1 | 0.3641 ± 0.0049 | 0.2500 ± 0.0152 | 0.3062 ± 0.0062 | 0.4037 |
| Corpus BLEU-4 | 8.15 ± 0.64 | 4.48 ± 0.37 | 6.13 ± 1.33 | – |
| Key-fact recall | 0.2972 | 0.0542 | 0.1549 | 0.3917 |
| All key facts (of 120) | 24 | 1 | 11 | 36 |
| Verified fully correct (of 120) | 21 | 1 | 11 | 33 |

**Fully-correct counts.** These are human judgements, not rule output (`fully_correct_final.json`):
* A: all 27 judgements author-confirmed.
* B: 2 judgements author-confirmed, plus 1 author judgement.
* C: AI-only.
* Ablation: AI-only, plus 1 author judgement.

**Significance.** Question = unit. Bootstrap uses 10,000 resamples (seed 42). Wilcoxon p values are exact and unrounded (audit). Sign tests are on question-level fully-correct counts.

| Comparison | Token F1 | Key-fact recall | All key facts | Fully-correct sign test |
|---|---|---|---|---|
| A vs B | +0.114 [0.050, 0.180], p = 0.0006 | +0.243 [0.133, 0.358], p = 0.0005 | +0.192 [0.092, 0.300], p = 0.0029 | 8/0, p = 0.0078 |
| C vs B | +0.056 [0.002, 0.114], p = 0.068 | +0.101 [0.019, 0.194], p = 0.045 | +0.083 [0.017, 0.167], p = 0.041 | 4/0, p = 0.125 |
| No-threshold vs A | +0.040 [−0.007, 0.091], p = 0.35 | +0.094 [0.007, 0.192], p = 0.078 | +0.100 [0.008, 0.208], p = 0.055 | 7/3, p = 0.34 |

BLEU paired bootstrap (1,000 resamples): A − B = +3.66 [1.46, 6.28]; C − B = +1.65 [−0.48, 4.37].

**Limitations.**
1. One catalogue, 52 questions, one hardware platform.
2. **Annotation and judgement.** Annotations and judgements were drafted by a single AI annotator. An author reviewed 53 sampled items and two later judgements. The intent and abstention labels, most annotations, and the C and ablation judgements are not human-verified. No inter-annotator agreement was measured.
3. **Post-hoc rules.** The relation-aware rules (12 questions) were refined after the outputs were seen.
4. **Matcher limits.** The other questions use phrase matching. Three A credits (Q14, Q18) are known to be wrong; removing them does not change any conclusion (`sensitivity_judged_wrong_credits.json`).
5. **Lower bounds.** Fact-level scores cannot detect added false claims. Fully-correct counts are lower bounds, because answers the rules did not credit were not re-read.
6. **Ablation.** The no-threshold ablation is exploratory and borderline.
7. **Unseeded generation.** Three runs give only a rough estimate of variability.
8. **ASR.** ASR accuracy on real speech was not evaluated.
