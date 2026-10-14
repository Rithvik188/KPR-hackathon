"""Cross-document checks: three-tier name matching (DOB tie-breaker), DOB agreement, Aadhaar back present.

Name comparison is space-insensitive because OCR often drops spaces ('KARTHIKRAJENDRAN').
Tamil Nadu initials: 'R. KARTHIK' vs 'KARTHIK RAJENDRAN' -> drop the initial R and the full word starting
with R, compare the rest. Such a match is at most `likely_match`, and only if the DOBs agree.
"""
import re

from rapidfuzz import fuzz

from app.validation.messages import make_issue
from app.validation.text import clean_name, letters
from app.validation.thresholds import get_thresholds
from app.validation.types import ConsistencyResult, ExtractedDoc

_RELATION = re.compile(r"^(S/O|D/O|W/O|C/O|SO|DO)\b[\s.:]*")
TIER_RANK = {"mismatch": 0, "likely_match": 1, "match": 2}


def normalize_name(name: str) -> list[str]:
    """Uppercase tokens without punctuation or relation prefixes; single letters are initials."""
    s = _RELATION.sub("", (name or "").upper().strip())
    return [tok for tok in clean_name(s).replace(".", " ").split() if tok]


def _initial_expansion(short: str, short_tokens: list[str], long: str, min_ratio: float) -> str | None:
    """'R'+'KARTHIK' vs 'KARTHIKRAJENDRAN' -> 'R→RAJENDRAN'. Strings are squashed letters."""
    cands: list[tuple[str, str, str]] = []  # (initial, rest, position)
    if len(short_tokens) > 1:
        for i, tok in enumerate(short_tokens):
            if len(tok) == 1:
                rest = "".join(short_tokens[:i] + short_tokens[i + 1:])
                cands.append((tok, rest, "start" if i == 0 else "end"))
    else:  # spaces lost: the initial can only be the first or the last letter
        cands += [(short[0], short[1:], "start"), (short[-1], short[:-1], "end")]
    for init, rest, _pos in cands:
        if len(rest) < 3:
            continue
        # long = rest + WORD (initial expands at the end) or WORD + rest (at the start)
        if len(long) - len(rest) >= 3:
            head, tail = long[:len(rest)], long[len(rest):]
            if tail[0] == init and fuzz.ratio(head, rest) >= min_ratio:
                return f"{init}→{tail}"
            head2, tail2 = long[:len(long) - len(rest)], long[len(long) - len(rest):]
            if head2[0] == init and fuzz.ratio(tail2, rest) >= min_ratio:
                return f"{init}→{head2}"
    return None


def compare_names(a: str, b: str, dob_match: bool | None, t: dict | None = None) -> tuple[str, float, dict]:
    """-> (tier, name_score, evidence)."""
    t = t or get_thresholds()
    ta, tb = normalize_name(a), normalize_name(b)
    sa, sb = "".join(ta), "".join(tb)
    score = float(fuzz.token_sort_ratio(" ".join(ta), " ".join(tb)))
    sim = float(fuzz.ratio(sa, sb))  # space-insensitive
    evidence: dict = {"name_score": round(score, 1), "squashed_similarity": round(sim, 1)}
    if not sa or not sb:
        return "mismatch", score, evidence
    if sim >= t["name_match_min"]:
        return "match", max(score, sim), evidence

    candidate = False
    short, short_t, long = (sa, ta, sb) if len(sa) <= len(sb) else (sb, tb, sa)
    expanded = _initial_expansion(short, short_t, long, t["name_match_min"])
    if expanded:
        candidate = True
        evidence["initial_expanded"] = expanded
    elif max(score, sim) >= t["name_likely_min"]:
        candidate = True

    evidence["dob_match"] = dob_match
    if candidate and dob_match is not False:
        return "likely_match", score, evidence  # DOB agrees (or is unreadable): officer confirms
    if candidate:
        evidence["reason"] = "names similar but DOB differs"
    return "mismatch", score, evidence


def _slot(d: ExtractedDoc) -> str:
    return d.declared_type or d.doc_type


def check_consistency(docs: list[ExtractedDoc]) -> ConsistencyResult:
    t = get_thresholds()
    issues = []
    slots = {_slot(d) for d in docs}
    if "aadhaar_front" in slots and "aadhaar_back" not in slots:
        issues.append(make_issue("AADHAAR_BACK_MISSING", {"documents": sorted(slots)}))

    dobs = [(d, d.dob) for d in docs if d.dob]
    dob_match: bool | None = None
    if len(dobs) >= 2:
        dob_match = len({dob for _, dob in dobs}) == 1
        if not dob_match:
            issues.append(make_issue("DOB_MISMATCH", {"dobs": {_slot(d): dob for d, dob in dobs}}))

    named = [d for d in docs if d.name and letters(d.name)]
    if len(named) < 2:
        return ConsistencyResult(name_tier="not_enough_data", dob_match=dob_match, issues=issues)

    anchor = next((d for d in named if _slot(d) == "aadhaar_front"), named[0])
    worst = None
    for other in (d for d in named if d is not anchor):
        pair_dob = None if not (anchor.dob and other.dob) else anchor.dob == other.dob
        tier, score, ev = compare_names(anchor.name, other.name, pair_dob, t)
        if worst is None or TIER_RANK[tier] < TIER_RANK[worst[0]]:
            worst = (tier, score, ev, other)
    tier, score, ev, other = worst
    if tier == "likely_match":
        issues.append(make_issue("NAME_LIKELY_MATCH", ev))
    elif tier == "mismatch":
        issues.append(make_issue("NAME_MISMATCH", ev))
    return ConsistencyResult(name_tier=tier, name_score=round(score, 1), names_compared=[anchor.name, other.name],
                             dob_match=dob_match, issues=issues)
