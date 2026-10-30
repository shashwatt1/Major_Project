"""Production key-fact evaluator, v2.1. Implements SCORING_SPEC.md using data/key_fact_rules_v2.json.

Questions listed in the rules file use the structured rules; all others keep the original phrase matcher
(metrics.key_fact_hit) on their existing key_facts. An independent re-implementation lives in
scripts/audit_recompute.py and must agree with this module (see scripts/check_audit_agreement.py).
"""
from __future__ import annotations

import json
import re
import unicodedata
from functools import lru_cache
from pathlib import Path

from metrics import key_fact_hit, normalize

RULES_PATH = Path(__file__).resolve().parents[1] / "data" / "key_fact_rules_v2.json"


@lru_cache(maxsize=1)
def spec() -> dict:
    s = json.loads(RULES_PATH.read_text(encoding="utf-8"))
    groups = s["groups"]

    def ex(x):
        return groups[x[1:]] if isinstance(x, str) and x.startswith("@") else x

    rules = {}
    for qid, rs in s["rules"].items():
        out = []
        for r in rs:
            r = dict(r)
            for k in ("subject", "competitors", "forbid", "alts", "sentence_forbid"):
                if k in r:
                    r[k] = ex(r[k])
            if "all" in r:
                r["all"] = [ex(g) for g in r["all"]]
            if "require_in_sentence" in r:
                r["require_in_sentence"] = [ex(g) for g in r["require_in_sentence"]]
            if "qualified" in r:
                r["qualified"] = [{k: (ex(v) if k != "terms" else v) for k, v in q.items()} for q in r["qualified"]]
            out.append(r)
        rules[qid] = out
    t = s["text"]
    rx = {k: re.compile(t[k]) for k in ("sentence_split_regex", "strong_delimiters_regex", "weak_delimiters_regex",
                                        "negation_regex", "uncertainty_regex", "contradiction_regex", "award_regex", "grade_regex")}
    return {"rules": rules, "text": t, "rx": rx}


def _prep(raw):
    t = unicodedata.normalize("NFKC", raw or "").lower().replace("’", "'").replace("‘", "'")
    t = re.sub(r"(?<=\d),(?=\d)", "", t)
    return re.sub(r"(?<=\w)'s\b", "", t)          # possessive: bennett's -> bennett


def sentences(raw):
    return [x for x in spec()["rx"]["sentence_split_regex"].split(_prep(raw)) if x and x.strip()]


def segments(sentence):
    return [x for x in spec()["rx"]["strong_delimiters_regex"].split(sentence) if x and x.strip()]


def seg_clauses(segment):
    return [x for x in spec()["rx"]["weak_delimiters_regex"].split(segment) if x and x.strip()]


def clauses(sentence):
    return [c for g in segments(sentence) for c in seg_clauses(g)]


def has(piece, terms):
    p = f" {normalize(piece)} "
    return any(normalize(t) and f" {normalize(t)} " in p for t in terms)


def negated(piece):
    rx = spec()["rx"]
    return bool(rx["negation_regex"].search(piece) or rx["uncertainty_regex"].search(piece))


def uncertain(sentence):
    return bool(spec()["rx"]["uncertainty_regex"].search(sentence))


_MONEY = None


def money_values(piece):
    global _MONEY
    if _MONEY is None:
        units = sorted([u for us in spec()["text"]["money_units"].values() for u in us], key=len, reverse=True)
        u = "|".join(re.escape(x) for x in units)
        _MONEY = re.compile(rf"\b(\d+(?:\.\d+)?)(?:\s+(?:{u}))?(?:\s+(?:to|and)\s+|\s+)(\d+(?:\.\d+)?)\s+({u})\b|\b(\d+(?:\.\d+)?)\s+({u})\b")
    cls = {x: k for k, us in spec()["text"]["money_units"].items() for x in us}
    out = []
    for m in _MONEY.finditer(normalize(piece)):
        if m.group(1):
            out.append((float(m.group(1)), float(m.group(2)), cls[m.group(3)]))
        else:
            out.append((float(m.group(4)), float(m.group(4)), cls[m.group(5)]))
    return out


def grades(piece):
    g = []
    for m in spec()["rx"]["grade_regex"].finditer(piece):
        s = re.sub(r"\s", "", m.group(0))
        g.append("A++" if s.endswith("++") else "A+" if s.endswith("+") else "A")
    return g


def _target(rule):
    v = rule["value"]
    return v["grade"] if "grade" in v else (float(v["lo"]), float(v["hi"]), v["unit"])


def _vals(rule, piece):
    if "grade" in rule["value"]:
        return grades(piece)
    return [v for v in money_values(piece) if v[2] == rule["value"]["unit"]]


def _bare(piece, subject):
    toks = normalize(piece).split()
    allowed = {t for s in subject for t in normalize(s).split()} | set(spec()["text"]["list_words"])
    return all(t in allowed for t in toks)


def eval_binding(rule, raw):
    tgt = _target(rule)
    is_grade = "grade" in rule["value"]
    for s in sentences(raw):
        if uncertain(s) or not all(has(s, g) for g in rule.get("require_in_sentence", [])):
            continue
        for seg in segments(s):
            for c in seg_clauses(seg):
                if not has(c, rule["subject"]) or negated(c) or has(c, rule.get("forbid", [])):
                    continue
                own = _vals(rule, c)
                if own:
                    if all(v == tgt for v in own) and not has(c, rule.get("competitors", [])):
                        return True
                    continue
                if money_values(c) or grades(c) or not _bare(c, rule["subject"]):
                    continue
                pool = [(cc, v) for cc in seg_clauses(seg) for v in _vals(rule, cc)] or \
                       [(cc, v) for cc in clauses(s) for v in _vals(rule, cc)]
                if len({v for _, v in pool}) != 1 or pool[0][1] != tgt:
                    continue
                vc = pool[0][0]
                if negated(vc) or has(vc, rule.get("forbid", [])):
                    continue
                if not is_grade and has(vc, rule.get("competitors", [])):
                    continue
                return True
    return False


def _qual_ok(term, unit_raw, sentence_raw, quals):
    q = next((q for q in quals if term in q["terms"]), None)
    if q is None:
        return True
    for c in clauses(unit_raw):
        if not has(c, [term]):
            continue
        if "require_any_in_clause" in q and not has(c, q["require_any_in_clause"]):
            continue
        if "forbid_any_in_clause" in q and has(c, q["forbid_any_in_clause"]):
            continue
        if "require_any_in_sentence" in q and not has(sentence_raw, q["require_any_in_sentence"]):
            continue
        return True
    return False


def _group_ok(group, unit_raw, sentence_raw, quals):
    return any(has(unit_raw, [t]) and _qual_ok(t, unit_raw, sentence_raw, quals) for t in group)


def eval_cooccur(rule, raw):
    quals = rule.get("qualified", [])
    for s in sentences(raw):
        if has(s, rule.get("sentence_forbid", [])):
            continue
        units = [s] if rule.get("scope") == "sentence" else clauses(s)
        for u in units:
            if negated(u) or has(u, rule.get("forbid", [])):
                continue
            ok = all(_group_ok(g, u, s, quals) for g in rule["all"])
            if not ok and rule.get("raw_regex_any") and len(rule["all"]) == 1:
                ok = any(re.search(x, u) for x in rule["raw_regex_any"])
            if ok:
                return True
    return False


def eval_degree_denial(rule, raw):
    t, rx = spec()["text"], spec()["rx"]
    for s in sentences(raw):
        if uncertain(s) or rx["contradiction_regex"].search(s):
            continue
        ns = normalize(s)
        if not (rx["award_regex"].search(ns) or "degree awarding" in ns or ns.startswith("no ")):
            continue
        toks = ns.split()
        for i, tok in enumerate(toks):
            if tok in t["denial_negators"]:
                if toks[i + 1:i + 2] == ["only"]:
                    continue
                win = toks[i + 1:i + 1 + t["denial_window_tokens"]]
                if "degree" in win or "degrees" in win:
                    return True
        if "not a degree awarding" in ns or "non degree" in ns:
            return True
    return False


def eval_phrase_guarded(rule, raw):
    quals = rule.get("qualified", [])
    for s in sentences(raw):
        if uncertain(s):
            continue
        for a in rule["alts"]:
            if key_fact_hit(s, [a]) and _qual_ok(a, s, s, quals):
                return True
    return False


EVAL = {"binding": eval_binding, "cooccur": eval_cooccur, "degree_denial": eval_degree_denial,
        "phrase_guarded": eval_phrase_guarded}


def fact_hits(answer, query_id, default_key_facts):
    rules = spec()["rules"]
    if query_id in rules:
        return [EVAL[r["type"]](r, answer or "") for r in rules[query_id]]
    return [key_fact_hit(answer, alts) for alts in default_key_facts]


def fact_ids(query_id, default_key_facts):
    rules = spec()["rules"]
    if query_id in rules:
        return [r["id"] for r in rules[query_id]]
    return [f"{query_id}-orig{i + 1}" for i in range(len(default_key_facts))]
