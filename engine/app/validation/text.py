"""Text normalisation and OCR confusable correction (number fields only)."""
import re

# Letter -> digit in digit positions; digit -> letter in letter positions.
TO_DIGIT = {"O": "0", "D": "0", "Q": "0", "U": "0", "I": "1", "L": "1", "|": "1", "!": "1", "T": "1", "Z": "2",
            "S": "5", "B": "8", "G": "6", "A": "4"}
TO_LETTER = {"0": "O", "1": "I", "2": "Z", "5": "S", "8": "B", "6": "G", "4": "A"}

_NON_ALNUM = re.compile(r"[^A-Z0-9]")
_NON_ALPHA = re.compile(r"[^A-Z]")


def squash(s: str) -> str:
    """Uppercase alphanumerics only ('R. Karthik' -> 'RKARTHIK')."""
    return _NON_ALNUM.sub("", (s or "").upper())


def letters(s: str) -> str:
    return _NON_ALPHA.sub("", (s or "").upper())


def digit_ratio(s: str) -> float:
    s = squash(s)
    return sum(c.isdigit() for c in s) / len(s) if s else 0.0


def to_digits(s: str) -> tuple[str, int]:
    """Map confusable letters to digits. Returns (digits-only string, substitutions made)."""
    out, subs = [], 0
    for ch in (s or "").upper():
        if ch.isdigit():
            out.append(ch)
        elif ch in TO_DIGIT:
            out.append(TO_DIGIT[ch])
            subs += 1
    return "".join(out), subs


def correct_pattern(raw: str, pattern: str) -> tuple[str, int]:
    """Positional correction. pattern uses 'A' for letter, '9' for digit (e.g. PAN 'AAAAA9999A')."""
    s = squash(raw)
    if len(s) != len(pattern):
        return s, 0
    out, subs = [], 0
    for ch, kind in zip(s, pattern):
        if kind == "9" and not ch.isdigit() and ch in TO_DIGIT:
            out.append(TO_DIGIT[ch])
            subs += 1
        elif kind == "A" and ch.isdigit() and ch in TO_LETTER:
            out.append(TO_LETTER[ch])
            subs += 1
        else:
            out.append(ch)
    return "".join(out), subs


def clean_name(s: str) -> str:
    """Uppercase letters, dots and single spaces; 'R.KARTHIK' -> 'R. KARTHIK'."""
    s = re.sub(r"[^A-Z. ]", " ", (s or "").upper())
    s = re.sub(r"\.(?=[A-Z])", ". ", s)
    return re.sub(r"\s+", " ", s).strip(" .")


def respace(name: str, father: str | None) -> str:
    """Restore a dropped space using the father's name printed on the same card.

    Tamil Nadu naming: the surname/initial is the father's name, so 'KARTHIKRAJENDRAN' with father
    'RAJENDRAN' -> 'KARTHIK RAJENDRAN', and 'KARTHIKR' -> 'KARTHIK R'.
    """
    name = clean_name(name)
    f = letters(father or "")
    if not name or not f or " " in name:
        return name
    sq = name.replace(".", "")
    if len(sq) > len(f) + 2 and sq.endswith(f):
        return f"{sq[:-len(f)]} {f}"
    if len(sq) > len(f) + 2 and sq.startswith(f):
        return f"{f} {sq[len(f):]}"
    if len(sq) >= 4 and sq[-1] == f[0]:
        return f"{sq[:-1]} {sq[-1]}"
    return name
