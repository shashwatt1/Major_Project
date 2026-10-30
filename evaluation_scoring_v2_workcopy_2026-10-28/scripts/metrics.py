"""Metric definitions used across the evaluation.

Answer-level token F1 (QA-style, multiset overlap, SQuAD-like) — NOT the same thing as
the macro-F1 used for intent classification.

Normalisation policy (applied identically to predictions and references):
  1. Unicode NFKC, lowercase.
  2. Digit-group commas removed (1,200 -> 1200).
  3. Dashes / hyphens / slashes replaced by a space (16–17 -> 16 17, cut-off -> cut off).
  4. Every remaining Unicode punctuation (P*) or symbol (S*) character removed (₹, ', ., &, +).
  5. English articles a / an / the removed.
  6. Whitespace tokenisation.
Numbers are NOT converted between digits and words; contractions are not expanded.
"""
from __future__ import annotations

import re
import unicodedata
from collections import Counter

_DASHES = "-‐‑‒–—―−/"
_ARTICLES = {"a", "an", "the"}


def normalize(text: str) -> str:
    text = unicodedata.normalize("NFKC", text or "").lower()
    text = re.sub(r"(?<=\d),(?=\d)", "", text)
    for d in _DASHES:
        text = text.replace(d, " ")
    text = "".join("" if unicodedata.category(ch)[0] in ("P", "S") else ch for ch in text)
    tokens = [t for t in text.split() if t not in _ARTICLES]
    return " ".join(tokens)


def tokens(text: str) -> list[str]:
    return normalize(text).split()


def token_prf(prediction: str, reference: str) -> tuple[float, float, float]:
    """Multiset token overlap precision/recall/F1 (each token counted min(pred, ref) times)."""
    p, r = tokens(prediction), tokens(reference)
    if not p and not r:
        return 1.0, 1.0, 1.0
    if not p or not r:
        return 0.0, 0.0, 0.0
    common = Counter(p) & Counter(r)
    tp = sum(common.values())
    if tp == 0:
        return 0.0, 0.0, 0.0
    prec, rec = tp / len(p), tp / len(r)
    return prec, rec, 2 * prec * rec / (prec + rec)


def exact_match(prediction: str, reference: str) -> int:
    return int(normalize(prediction) == normalize(reference))


def key_fact_hit(answer: str, alternatives: list[str]) -> bool:
    """A key fact is present if any alternative appears in the answer.

    Alternatives containing '+' are matched on the raw lowercased answer (normalisation would
    delete the '+'); all others are matched as substrings of the normalised answer, padded with
    spaces at token boundaries unless the alternative is a prefix stem (e.g. 'graduat').
    """
    raw = unicodedata.normalize("NFKC", answer or "").lower()
    norm = " " + normalize(answer) + " "
    for alt in alternatives:
        if "+" in alt:
            if re.search(re.escape(alt) + r"(?!\+)", raw):
                return True
            continue
        a = normalize(alt)
        if not a:
            continue
        if f" {a} " in norm or (alt.endswith(("graduat",)) and a in norm):
            return True
    return False


def alnum(text: str) -> str:
    """Relevance-matching normalisation: lowercase, keep only letters and digits."""
    text = unicodedata.normalize("NFKC", text or "").lower()
    return "".join(ch for ch in text if ch.isalnum())


ABSTAIN_PATTERNS = [
    r"\bnot (?:explicitly |specifically |directly )?(?:mentioned|specified|provided|stated|available|listed|included|given|disclosed|covered|found|confirmed|present)\b",
    r"\b(?:does not|doesn't|do not|don't|did not|didn't) (?:explicitly |specifically )?(?:mention|specify|provide|state|include|contain|have|list|cover|disclose|give)\b",
    r"\bno (?:specific |explicit |such |direct )?(?:information|mention|data|details|figures?|record|reference)\b",
    r"\bi (?:don't|do not) have\b",
    r"\b(?:cannot|can't|can not|unable to|couldn't|could not) (?:find|determine|provide|answer|confirm|say|tell|locate|give)\b",
    r"\b(?:isn't|is not|aren't|are not|wasn't|was not) (?:explicitly )?(?:mentioned|specified|provided|stated|available|listed|included|covered|given|confirmed)\b",
    r"\bnot (?:sure|certain)\b",
    r"\bunknown\b",
    r"\b(?:check|verify|contact|visit) (?:with |the )?(?:the )?(?:official|university|college|institution|admissions?)\b",
    r"\bwhich (?:one|campus|university|institution|college) (?:do you|are you)\b",
    r"\b(?:could you|can you|please) (?:clarify|specify)\b",
]


def is_abstention(answer: str) -> bool:
    a = (answer or "").lower().replace("’", "'")
    return any(re.search(p, a) for p in ABSTAIN_PATTERNS)
