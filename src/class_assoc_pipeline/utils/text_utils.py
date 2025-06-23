import re
from typing import List, Tuple
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
    content = normalize_word(content)
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
    # line = re.sub(r"\([^)]*?Explanation:[^)]*\)", "", line, flags=re.IGNORECASE)
    core = line.split(' - ', 1)[0]
    parts = [normalize_word(seg.strip()) for seg in core.split('-')]
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
    if not lowered:
        return ''
    # Keywords to preserve as-is
    keywords = {"class",
                "process",
                "progress",
                "academic progress",
                "address",
                "delivery address",
                "deliveryaddres",
                "status",
                "order status",
                "business",}
    if lowered in keywords:
        return lowered
    # Attempt singularization; fallback to original lowercase
    return _p.singular_noun(lowered) or lowered

def normalize_assoc(assoc: list[str]) -> tuple[str,str]:
    """
    Normalize a two-element association pair by:
    1. Removing optional tags from the left element.
    2. Cleaning both left and right using class/association-specific functions.
    3. Lowercasing and sorting them alphabetically to produce a normalized 'X-Y' key.

    This is useful for deduplication because it ensures consistent formatting
    regardless of original order, case, or tag presence.
    """
    left, right = assoc
    left = re.sub(r'^\(Opt(?:ional)?\)\s*', '', left, flags=re.IGNORECASE)
    cleaned = [clean_class_name(left), clean_association_line(right)]
    return '-'.join(sorted(s.lower().strip() for s in cleaned))

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
    if m:
        return [
            f"{prefix}{m.group(1).strip()}",
            f"{prefix}{m.group(2).strip()}"
        ]

    # 3) **new** plain-and rule: e.g. "A and B" (no parentheses)
    m2 = re.match(r'^(.*?)\s+and\s+(.*?)$', entity, re.IGNORECASE)
    if m2:
        return [
            f"{prefix}{m2.group(1).strip()}",
            f"{prefix}{m2.group(2).strip()}"
        ]

    # 4) fallback: nothing to split on
    return [f"{prefix}{entity.strip()}"]

def deduplicate_associations(assocs: list[list[str]]) -> list[list[str]]:
    """
    Deduplicate a list of association pairs, treating 'A-B' and 'B-A' as equivalent.

    The function:
    - Uses normalized forms to detect duplicates.
    - Prefers mandatory associations when both optional and mandatory exist.
    - Retains the first-seen instance of each normalized key, unless replaced by a preferred version.
    """
    seen = dict()  # key -> index of the preferred version
    out = []
    mandatory = []
    optional = []

    for a in assocs:
        key = normalize_assoc(a)
        is_optional = any(re.search(r"\(opt(?:ional)?\)", s, flags=re.IGNORECASE) for s in a)

        if key not in seen:
            seen[key] = len(out)
            out.append(a)
            if is_optional:
                optional.append(a)
            else:
                mandatory.append(a)
        else:
            existing_index = seen[key]
            existing = out[existing_index]
            existing_is_optional = any(re.search(r"\(opt(?:ional)?\)", s, flags=re.IGNORECASE) for s in existing)

            # Prefer mandatory version if one exists
            if existing_is_optional and not is_optional:
                out[existing_index] = a  # replace optional with mandatory
                if existing in optional:
                    optional.remove(existing)
                mandatory.append(a)

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
    

def clean_brackets(item: str) -> str:
    """
    Remove all parenthetical expressions (e.g., acronyms or explanations) from a string,
    while preserving a leading '(optional)' marker, if present.
    """
    if not isinstance(item, str):
        return ""
    
    # If starting with (optioanl), record it
    prefix_optional = ''
    match = re.match(r'^\(optional\)\s*', item, flags=re.IGNORECASE)
    if match:
        prefix_optional = match.group(0).lower()  
        item = item[match.end():]  
    
    item = re.sub(r'\s*\([^)]*\)', '', item).strip()

    return f"{prefix_optional}{item}".strip()

def parse_association_line(line: str) -> list[list[str]]:
    """
    Parse a single raw association string into a list of individual association pairs.

    Supports:
    - Optional markers (e.g., "(optional) A-B").
    - Right-hand compound forms (e.g., A-B or C, D).
    - Normalization by removing quotes and whitespace.
    
    """
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


def combine_and_deduplicate_associations(
    refined: List[str], 
    optional: List[str]
) -> Tuple[List[str], List[str], List[str]]:
    """
    Combine refined and optional association lists, clean tags like (Optional)/(Opt),
    deduplicate (A-B == B-A), and return cleaned lists split into refined and optional.

    Args:
        refined: List of non-optional associations.
        optional: List of optional associations (may include (Optional)/(Opt) tags).

    Returns:
        final_refined: Subset of final_list originally from refined.
        final_optional: Subset of final_list originally from optional.
    """
    combined = refined + optional
    is_optional_mask = [False] * len(refined) + [True] * len(optional)

    # Clean optional tags (case-insensitive)
    cleaned = [
        re.sub(r'\((optional|opt)\)', '', item, flags=re.IGNORECASE).strip()
        for item in combined
    ]
    # Step 2: Normalize each side of the association
    normalized = []
    for assoc in cleaned:
        if assoc.startswith('- '):
            assoc = assoc[2:].strip()
        parts = assoc.split('-')
        if len(parts) == 2:
            left = normalize_word(parts[0])
            right = normalize_word(parts[1])
            normalized.append(f"{left}-{right}")
        else:
            normalized.append(assoc.lower().strip())  # fallback if malformed

    seen = set()
    final_list = []
    final_refined = []
    final_optional = []

    for item, is_optional in zip(normalized, is_optional_mask):
        key = '-'.join(sorted(item.split('-')))
        if key not in seen:
            seen.add(key)
            final_list.append(item)
            if is_optional:
                final_optional.append(f"(Optional) {item}")
            else:
                final_refined.append(item)

    final_refined = [re.sub(r'\(Optional\)\s*\*\s*', '(Optional)', item) for item in final_refined]
    final_optional = [re.sub(r'\(Optional\)\s*\*\s*', '(Optional)', item) for item in final_optional]

    final_refined = [
        clean_brackets(item) for item in final_refined
    ]
    final_optional = [
        clean_brackets(item) for item in final_optional
    ]

    return final_refined, final_optional
