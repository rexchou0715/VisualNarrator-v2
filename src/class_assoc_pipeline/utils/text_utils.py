import re
from typing import List
import inflect

_p = inflect.engine()

def clean_class_name(content: str) -> str:
    """
    Removes Markdown-style bold symbols (e.g., **Class**) and leading asterisks,
    then trims any extra surrounding whitespace.
    """
    # Remove Markdown bold markers (**...**) and any single '*' around text
    content = re.sub(r"\*{1,2}(.*?)\*{1,2}", r"\1", content)
    # Remove leading '*' characters
    content = re.sub(r"^\*+\s*", "", content)
    return content.strip()


def format_optional_line(content: str) -> str:
    """
    Normalizes a class or association line by ensuring the '(optional)' marker
    appears at the start. It retains any trailing notes after a dash.
    """
    # Detect '(optional)' tag
    if re.search(r"\(optional\)", content, re.IGNORECASE):
        # Remove all '(optional)' instances, then strip extra whitespace
        base = re.sub(r"\(optional\)", "", content, flags=re.IGNORECASE).strip()
        return f"(optional) {base}"
    return remove_trailing_notes(content.strip())


def remove_trailing_notes(line: str) -> str:
    """
    Strips trailing notes or formatting characters such as ':', '-', and '`' from a line.
    """
    # Split and keep only the part before ':', '-', '–' (- and – are different), and '`'
    for sep in [":", "-", "–"]:
        if sep in line:
            line = line.split(sep, 1)[0]

    # ASCII and typographic quotes:
    line = re.sub(r"[`“”‘’]", "", line)
    return line.strip()


def remove_trailing_notes_association(line: str) -> str:
    """
    Strips leading/trailing formatting and trailing notes from an association line.

    1. Trim whitespace.
    2. Remove Markdown bold markers (“**”).
    3. Normalize any “ - ” to “-”.
    4. Drop everything after the first colon.
    5. Remove ASCII and typographic quotes.
    """
    # 1) Trim and remove bold markers, 2) normalize " - " → "-"
    line = line.strip().replace("**", "").replace(" - ", "-")

    # 3) Drop any trailing notes after a colon
    if ":" in line:
        line = line.split(":", 1)[0]

    # 4) Remove any backticks or typographic quotes
    line = re.sub(r"[`“”‘’]", "", line)

    return line.strip()


def clean_association_line(line: str, force_optional: bool = False) -> str:
    """
    Normalize one association line:
      - Remove leading bullets/numbers
      - Strip Explanation(...) parentheticals
      - Keep only the first and last parts around '-'
      - Remove any leftover parentheses
      - Prefix '(optional)' if needed
    """
    # 1) strip leading “1. ”, “* ” or “- ”
    line = re.sub(r"^(\d+\.\s*|\*\s*|\-\s*)", "", line)
    # 2) detect optional
    opt = force_optional or ("(optional" in line.lower()) or ("(opt)" in line.lower())
    # 3) remove Explanation(...) groups
    line = re.sub(r"\(Explanation:.*?\)", "", line, flags=re.IGNORECASE)
    # 4) split on hyphen, keep first & last segment
    parts = [p.strip() for p in line.split('-')]
    cleaned = f"{parts[0]}-{parts[-1]}" if len(parts) >= 2 else line.strip()
    # 5) strip any remaining parentheses
    cleaned = re.sub(r"\([^)]*\)", "", cleaned).strip()
    # 6) prefix “(optional) ”
    return f"(optional) {cleaned}" if opt else cleaned



def split_mandatory_entities(text: str) -> list[str]:
    """
    Splits a combined class description into individual entities by 'and', commas, and
    strips off any parenthetical or slash segments.
    """
    parts = re.split(r"\s+and\s+", text)
    result = []
    for part in parts:
        # Remove anything after '(' or '/'
        part = re.split(r"[\(/]", part)[0]
        # Split by commas and strip whitespace
        for item in part.split(','):
            item = item.strip()
            if item:
                result.append(item)
    return result


def clean_association_line(line: str, force_optional: bool = False) -> str:
    """
    Cleans and normalizes an association line:
    - Remove leading numbering or bullets
    - Strip explanatory parentheses
    - Keep only the core 'X-Y' association
    - Drop any trailing notes after ' - '
    - Optionally prefix '(optional)'
    """
    line = re.sub(r"^(?:\d+\.\s*|\*\s*|\-\s*)", "", line)
    is_opt = force_optional or bool(re.search(r"\(opt(?:ional)?\)", line, re.IGNORECASE))
    line = re.sub(r"\(opt(?:ional)?\)", "", line, flags=re.IGNORECASE).strip()
    line = re.sub(r"\([^)]*?Explanation:[^)]*\)", "", line, flags=re.IGNORECASE)
    core = line.split(' - ', 1)[0]
    parts = [seg.strip() for seg in core.split('-')]
    if len(parts) >= 2:
        cleaned = f"{parts[0]}-{parts[-1]}"
    else:
        cleaned = core
    if is_opt:
        return f"(optional) {cleaned.strip()}"
    return cleaned.strip()

def expand_or_variants(entity: str) -> list[str]:
    """
    Given an entity like:
       "Group (or “CampGroup”)"
       "Activity (or “Event” / “Task”)"
       "AttendanceRecord (or simply “Attendance”)"

    Yield a list of the stripped variants:
       ["Group", "CampGroup"]
       ["Activity", "Event", "Task"]
       ["AttendanceRecord", "Attendance"]
    """
    # 1) Remove outer quotes and normalize parentheses
    text = entity.strip()
    # capture the head before any '('
    head, *rest = re.split(r'\(', text, 1)
    variants = [head.strip()]
    
    if rest:
        # take inside the first parentheses
        inside = rest[0].rstrip(')')
        # remove leading "or" or "or simply"
        inside = re.sub(r'^(?:or|or simply)\s*', '', inside, flags=re.IGNORECASE)
        # split on slash or literal " / "
        parts = re.split(r'\s*/\s*|\s+or\s+', inside, flags=re.IGNORECASE)
        for p in parts:
            cleaned = p.strip().strip('“”"\'')
            if cleaned:
                variants.append(cleaned)
    return variants


def flatten_or_variants(entity: str) -> str:
    """
    Transform strings like:
        "(Optional) Profile (or “Account”)"
    Into:
        "(Optional) Profile/Account"
    """
    # Detect and remove leading "(Optional)"
    opt_match = re.match(r'^\(\s*optional\)\s*', entity, flags=re.IGNORECASE)
    is_optional = bool(opt_match)
    if is_optional:
        # strip off the exact prefix we matched
        entity = entity[opt_match.end():]

    # Split off at the first "("
    head, *rest = re.split(r'\(', entity, 1)
    # Clean up any Markdown bold around the head
    head = re.sub(r'\*{1,2}(.*?)\*{1,2}', r'\1', head).strip()
    variants = [head]

    if rest:
        inside = rest[0].rstrip(')')
        inside = re.sub(r'^(?:or\s*simply|or|often)\s*', '', inside, flags=re.IGNORECASE)
        parts = re.split(r'\s*/\s*|\s+or\s+', inside, flags=re.IGNORECASE)

        for p in parts:
            cleaned = p.strip().strip('“”"\' ')
            if cleaned:
                variants.append(cleaned.replace(" ", ""))

    joined = "/".join(variants)
    # 3) Re-add the "(Optional)" prefix if needed
    return f"(Optional) {joined}" if is_optional else joined


def normalize_word(word: str) -> str:
    """
    Normalize a word to its lowercase singular form, preserving certain keywords.
    """
    if not isinstance(word, str):
        return ""
    lowered = word.lower().strip()
    # Keywords to preserve as-is
    keywords = {"class", "process", "progress", "academic progress", "address"}
    if lowered in keywords:
        return lowered
    # Attempt singularization; fallback to original lowercase
    return _p.singular_noun(lowered) or lowered


def normalize_assoc(assoc: list[str]) -> tuple[str,str]:
    left, right = assoc
    left = re.sub(r'^\(Opt\)\s*', '', left, flags=re.IGNORECASE)
    left = clean_class_name(left)
    right = clean_association_line(right)
    return left, right


def flatten_and_variants(entity: str) -> List[str]:
    """
    Only handles strings of the form:
        "(Optional) X (and Y)"
    Returns:
        ["(Optional) X", "(Optional) Y"]
    """
    # 1) pull off an "(optional)" prefix if it’s there
    opt_match = re.match(r'^\(\s*optional\)\s*', entity, flags=re.IGNORECASE)
    prefix = ""
    if opt_match:
        prefix = opt_match.group(0).strip() + " "
        entity = entity[opt_match.end():]

    # 2) first, the parenthesized-and rule: e.g. "X (and Y)"
    m = re.match(r'^(.*?)\s*\(\s*and\s*(.*?)\s*\)\s*$', entity, re.IGNORECASE)
    print(f"m {m}")
    if m:
        return [
            f"{prefix}{m.group(1).strip()}",
            f"{prefix}{m.group(2).strip()}"
        ]

    # 3) **new** plain-and rule: e.g. "A and B" (no parentheses)
    m2 = re.match(r'^(.*?)\s+and\s+(.*?)$', entity, re.IGNORECASE)
    print(f"m2 {m2}, prefix: {prefix}")
    if m2:
        return [
            f"{prefix}{m2.group(1).strip()}",
            f"{prefix}{m2.group(2).strip()}"
        ]

    # 4) fallback: nothing to split on
    return [f"{prefix}{entity.strip()}"]

def deduplicate_associations(assocs: list[list[str]]) -> list[list[str]]:
    seen = set()
    out = []
    for a in assocs:
        key = normalize_assoc(a)
        if key not in seen:
            seen.add(key)
            out.append(a)
    return out

def dedupe_preserve_optional_first(mandatory: list[str], optional: list[str]) -> list[str]:
    """
    Merge mandatory + optional lists, but if an item appears in both (ignoring "(optional) "),
    only keep whichever came first in the combined sequence.
    """
    seen = set()
    combined = []
    for item in (mandatory + optional):
        # strip off the optional prefix for the purpose of deduplication
        key = item.lower().replace("(optional)", "").strip()
        if key not in seen:
            seen.add(key)
            combined.append(item)
    return combined

def flatten_comma_variants(entity: str) -> List[str]:
    """
    Given a comma-separated list, possibly prefixed by ANY (...) group,
    return each item as its own entity, preserving that exact prefix.

    Examples:
        "(optional) A, B, C"    -> ["(optional) A", " (optional) B", "(optional) C"]
        "(Opt) X, Y, Z"         -> ["(Opt) X", "(Opt) Y", "(Opt) Z"]
        "(Foo) 1, 2, 3"         -> ["(Foo) 1", "(Foo) 2", "(Foo) 3"]
        "Alpha, Beta, Gamma"    -> ["Alpha", "Beta", "Gamma"]
    """
    # 1) extract any leading "(...)" prefix (not just "optional"):
    m = re.match(r'^\(\s*[^)]+\)\s*', entity)
    if m:
        prefix = m.group(0).strip() # e.g. "(optional)" or "(Opt)" or "(Foo)"
        rest = entity[m.end():]
    else:
        prefix = ""
        rest = entity

    # 2) split on commas
    parts = [p.strip() for p in rest.split(',') if p.strip()]

    # 3) re-attach the exact prefix (if any) to each
    if prefix:
        return [f"{prefix} {p}" for p in parts]
    else:
        return parts
    


def parse_association_line(line: str) -> list[list[str]]:
    line = line.strip()
    if not line or '-' not in line:
        return []
    is_opt = bool(re.match(r'^\((?:optional|opt)\)', line, re.IGNORECASE))
    if is_opt:
        line = re.sub(r'^\((?:optional|opt)\)\s*', '', line, flags=re.IGNORECASE)
    line = line.replace('"','').strip()
    left, right = [p.strip() for p in line.split('-',1)]
    # split on or/and
    parts = re.split(r'\s+or\s+|\s+and\s+', right, flags=re.IGNORECASE)
    pairs = []
    for part in parts:
        # handle commas
        for sub in [s.strip() for s in part.split(',')]:
            tag_left = f"(Opt) {left}" if is_opt else left
            pairs.append([ tag_left, sub ])
    return deduplicate_associations(pairs)
