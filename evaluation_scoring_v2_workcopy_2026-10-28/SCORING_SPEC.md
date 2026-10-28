# Key-fact scoring specification v2.1 (shared by production and audit)

Data: `data/key_fact_rules_v2.json`. Production implementation: `scripts/keyfact_rules.py`. Independent audit implementation: `scripts/audit_recompute.py` (section "v2 key facts"), which does not import the production evaluator or `metrics.key_fact_hit`.

## 1. Text handling
1. **Prepare:** Unicode NFKC, lower-case, curly → straight apostrophes, remove commas between digits (`3,000` → `3000`), and remove a possessive `'s` after a word character (`Bennett's` → `Bennett`).
2. **Sentences:** split prepared text on `text.sentence_split_regex`.
3. **Segments:** split each sentence on `strong_delimiters_regex`.
4. **Clauses:** split each segment on `weak_delimiters_regex`. Empty pieces are dropped.
5. **Normalised form** of any piece is the existing answer normalisation: NFKC, lower-case, digit commas removed, dashes and `/` → space, punctuation and symbols deleted, articles a/an/the removed, whitespace tokens.
6. **Term match:** a term matches a piece if `" " + norm(term) + " "` occurs in `" " + norm(piece) + " "` (token-bounded).
7. **Negated piece:** the raw piece matches `negation_regex` or `uncertainty_regex`. **Uncertain sentence:** it matches `uncertainty_regex`.

## 2. Values
* **Money:** a range or single number followed by a unit, in normalised text. The form is `A [unit] (to|and)? B unit` or `A unit`. Units: `lpa`, `lakh per annum`, `lakhs per annum` → class `lpa`; `lakh`, `lakhs` → class `lakh`. A value is `(lo, hi, class)`.
* **NAAC grade:** matches of `grade_regex` on the raw piece: `A++`, `A+` or plain `NAAC A`. "A+" never equals "A++".

## 3. Rule types
* **cooccur** (`scope` = clause or sentence): the fact is hit if some unit (clause or sentence) satisfies all of the following:
  * it is not negated;
  * it contains no `forbid` term;
  * its sentence contains no `sentence_forbid` term;
  * every group in `all` matches the unit.
  * **Qualified terms:** a group satisfied only through a qualified term counts only if some clause of the unit contains that term **and** that clause satisfies the qualification: `require_any_in_clause` (one term in the same clause), `require_any_in_sentence` (one term in the sentence), and `forbid_any_in_clause` (none in the same clause).
  * `raw_regex_any` (single-group rules only) is an extra alternative tested on the prepared raw unit.
* **binding** (subject → target value): for each sentence that is not uncertain and contains every `require_in_sentence` group, for each clause `c` that contains a subject term, is not negated, and has no `forbid` term:
  1. If `c` holds values of the target class, it is a hit iff all of them equal the target **and** `c` contains no competitor term.
  2. Else, if `c` holds any money value or grade of another class, no hit from `c`.
  3. Else, if `c` is **bare** (every token belongs to a subject term or `list_words`), take the values of the target class in the clause's segment; if there are none, take those in the sentence. It is a hit iff there is exactly one distinct value, it equals the target, the clause holding it (the first such clause in text order) is not negated and has no forbid term, and (for money rules only) that clause contains no competitor term.
* **degree_denial** (Q06): skip sentences matching `uncertainty_regex` or `contradiction_regex`. A sentence is a hit if:
  * it contains an award verb (`award_regex`), or "degree awarding", or starts with "no "; **and**
  * either a `denial_negators` token is followed within `denial_window_tokens` tokens by "degree"/"degrees" (unless the next token is "only"), or the sentence contains "not a degree awarding" or "non degree".
* **phrase_guarded:** a sentence that is not uncertain contains any alternative, using the token-bounded match on the normalised sentence (with "+"-containing terms matched on the raw sentence). Qualified alternatives additionally need their qualification satisfied in the clause that contains them.

## 4. Group references
A string `"@NAME"` in a rule refers to `groups.NAME`.

## 5. Questions without rules
They keep their original key facts, scored with the original phrase matcher (`metrics.key_fact_hit`). The audit re-implements that matcher independently, as it already did.

## 6. How the two implementations differ (by design)
* **Production** (`keyfact_rules.py`) matches terms as padded substrings of `metrics.normalize` output and finds money values with one regular expression.
* **Audit** (`audit_recompute.py`, `kf_v2`) matches terms as contiguous token sub-lists of its own `norm_ind` tokenizer, finds money values with a token scanner (longest unit first), classifies grades by counting `+`, and re-implements the v1 phrase matcher (`orig_hit`).
* Both read the same JSON file. Agreement is checked by `scripts/check_audit_agreement.py` (unit cases, all saved generations, references, cited page text, and every generation sentence × every rule question).
