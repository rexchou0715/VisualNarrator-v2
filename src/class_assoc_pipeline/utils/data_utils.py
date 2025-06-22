import re
import inflect

# Initialize inflect engine for singularization
_p = inflect.engine()


def normalize_word(word: str) -> str:
    """
    Normalize a word to its lowercase singular form, preserving certain keywords.
    """
    if not isinstance(word, str):
        return ""
    lowered = word.lower().strip()
    # Keywords to preserve as-is
    keywords = {"class",
                "process",
                "progress",
                "academic progress",
                "address",
                "delivery address",
                "deliveryaddresnormalize_word",
                "status",
                "order status",
                "business",
                "scheduling process",
                "payment process",
                "hiring process"}
    if lowered in keywords:
        return lowered
    # Attempt singularization; fallback to original lowercase
    return _p.singular_noun(lowered) or lowered


def expand_synonym_mapping(compact_dict: dict) -> dict:
    """
    Expand a compact synonym dictionary into a flat mapping of synonym->standard term.
    """
    flat = {}
    for standard, synonyms in compact_dict.items():
        norm_standard = normalize_word(standard)
        for syn in synonyms:
            norm_syn = normalize_word(syn)
            flat[norm_syn] = norm_standard
    return flat


def generate_candidates(element: str, mapping: dict) -> set[str]:
    """
    Generate a set of candidate strings by applying synonym replacements.
    """
    if not isinstance(element, str):
        return set()
    candidates = {element}
    for key, val in mapping.items():
        new_set = set(candidates)
        for cand in candidates:
            if key in cand:
                replaced = cand.replace(key, val).strip()
                new_set.add(replaced)
        candidates = new_set
    return candidates


def deduplicate_list(items: list[str]) -> list[str]:
    """
    Deduplicate a list of strings (case-insensitive), preserving order.
    """
    seen = set()
    result = []
    for item in items:
        key = item.lower() if isinstance(item, str) else item
        if key not in seen:
            seen.add(key)
            result.append(item)
    return result


def deduplicate_associations(associations: list[list[str]]) -> list[list[str]]:
    """
    Deduplicate (X,Y) pairs, ignoring an optional prefix on X, preserving the first occurrence.
    """
    def _normalize(assoc: list[str]) -> tuple:
        left, right = assoc
        # remove '(opt)' or '(optional)' prefix (case-insensitive)
        left_norm = re.sub(r"^\(opt(?:ional)?\)\s*", "", left, flags=re.IGNORECASE).strip().lower()
        return (left_norm, right.lower().strip())

    seen = set()
    result = []
    for assoc in associations:
        norm = _normalize(assoc)
        if norm not in seen:
            seen.add(norm)
            result.append(assoc)
    return result
