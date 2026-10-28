# Reference answer changes (working copy only)

| Date | Item | Before | After | Evidence | Files |
|---|---|---|---|---|---|
| 2026-10-28 | Q32 reference_answer | "Newton School of Technology charges ₹16–17 lakh in tuition for reported placements of ₹7–8 LPA, so the catalog suggests comparing lower-fee options." | "Newton School of Technology charges ₹16–17 lakh in tuition **for the full programme**, for reported placements of ₹7–8 LPA, so the catalog suggests comparing lower-fee options." | Catalogue p. 1, fee box: "Tuition, full programme ₹16–17 lakh, Academic fees only". The scope is stated explicitly in the catalogue, not inferred. | `rag_test_set.jsonl`, `data/rag_queries_v1.json` |

* Backups of both files before the change: `data/pre_q32_reference_fix/` (SHA-256 `53265782…` and `ad4a442b…`).
* Reason: the approved Q32 rule requires an explicit full-programme scope. The old reference did not state it, so the reference and the scorer used different definitions. After the change, both the production and audit scorers credit the reference with Q32-F1 and Q32-F2.
* Side effect: token F1 and BLEU use the reference text, so the Q32 rows change slightly (see the checkpoint report). Evidence quotes, key-fact lists, relevance labels, the author-review CSVs and the original package were not changed.
