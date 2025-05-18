import re


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
    # Split and keep only the part before ':', '-', or '`'
    for sep in [":", "-"]:
        if sep in line:
            line = line.split(sep, 1)[0]
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

