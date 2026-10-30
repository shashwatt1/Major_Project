# Round 4 change log (28 Oct 2026)

**Base:** round-3 files (`revised_manuscript_r3_BASE.docx`, `response_r3_BASE.md`; copies of `manuscript_revision_final_2026-10-28/submission/`). **Source of changes:** `build/content.py` (previous text: `build/content_r3_BEFORE_r4_edits.py`).

| # | Location | Change |
|---|---|---|
| E1 | Abstract | BLEU-4 "8.15" → "8.14" |
| E2 | Table I, A | "8.15 ± 0.64" → "8.14 ± 0.64" (SD unchanged at full precision) |
| E3 | Table I, B | "4.48 ± 0.37" → "4.48 ± 0.38" |
| E4 | V-A | BLEU-4 "8.15" → "8.14" |
| E5 | Conclusion | BLEU-4 "8.15" → "8.14" |
| E6 | V-A | Added: key-fact recall uses rules refined after outputs were inspected and is not human-validated (Section IV-B) |
| E7 | IV-B | "value and its subject in one clause" → "value to be bound to its subject (in the same clause, or in a list naming it)" |
| E8 | Table I note | SD convention stated (sample SD, n − 1, before rounding); key-fact disclosure appended |
| R1 | Response, Comment 1 | BLEU-4 "8.15" → "8.14" |
| R2 | Response, Comment 1 | Key-fact recall bullet carries the same disclosure |

Nothing else changed (text diff checked). **Checks:** `checks/verify_numbers.py` (33 values, BLEU at full precision), `checks/validate_pdf.py` (61 checks), `checks/pdf_pages/` (page images). Exports: LibreOffice 25.8.4.2. **Not validated in Microsoft Word.**
