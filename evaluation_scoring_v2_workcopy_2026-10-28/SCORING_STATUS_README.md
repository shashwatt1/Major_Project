# Key-fact scoring: status of reports in this folder

* **Final, authoritative:** `final_results_v2.1/FINAL_RESCORE_REPORT.md` and the frozen results in `final_results_v2.1/` (rules v2.1, rescore completed and approved 28 Oct 2026).
* **Historical, superseded:** `SCORING_V2_REPORT.md` is the pre-approval draft report for the v2 rules, written before the author decisions and before any rescore. It is kept unchanged as a record of the review process; its "DRAFT" and "No rescore has been run" statements describe that earlier stage.
* The copy of the rules file inside `final_results_v2.1/data/` is part of the frozen results and keeps its original status text ("final rescore NOT yet authorised"), which described the state at the time it was saved. Its rule content is identical to `data/key_fact_rules_v2.json`; only the `status` metadata string differs. Scoring code does not read the `status` field.
