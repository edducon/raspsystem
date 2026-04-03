import re


_GROUP_SUFFIX_RE = re.compile(r"\s*(п/г|гр\.|подгруппа)\s*\d+", re.IGNORECASE)
_TRAILING_NUMBER_RE = re.compile(r"\s+\d+$")
_TRAILING_PUNCT_RE = re.compile(r"[,;.]+$")


def clean_subject_name(name: str) -> str:
    cleaned = _GROUP_SUFFIX_RE.sub("", name)
    cleaned = _TRAILING_NUMBER_RE.sub("", cleaned)
    cleaned = _TRAILING_PUNCT_RE.sub("", cleaned)
    return cleaned.strip()


def normalize_for_compare(name: str) -> str:
    return " ".join(clean_subject_name(name).lower().split())


def levenshtein(a: str, b: str) -> int:
    if a == b:
        return 0
    if not a:
        return len(b)
    if not b:
        return len(a)

    previous = list(range(len(b) + 1))
    for i, char_a in enumerate(a, start=1):
        current = [i]
        for j, char_b in enumerate(b, start=1):
            insert_cost = current[j - 1] + 1
            delete_cost = previous[j] + 1
            replace_cost = previous[j - 1] + (0 if char_a == char_b else 1)
            current.append(min(insert_cost, delete_cost, replace_cost))
        previous = current

    return previous[-1]


def fuzzy_match(a: str, b: str, threshold: int | None = None) -> bool:
    normalized_a = normalize_for_compare(a)
    normalized_b = normalize_for_compare(b)
    if normalized_a == normalized_b:
        return True

    max_len = max(len(normalized_a), len(normalized_b))
    if max_len == 0:
        return True

    effective_threshold = threshold if threshold is not None else int(max_len * 0.15)
    return levenshtein(normalized_a, normalized_b) <= effective_threshold
