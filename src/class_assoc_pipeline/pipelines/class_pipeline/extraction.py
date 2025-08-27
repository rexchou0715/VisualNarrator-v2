import os
import re
import pandas as pd

# Local imports from the project
from .extractors import extract_content_by_model
from class_assoc_pipeline.utils.text_utils import (
    clean_class_name,
    format_optional_line,
    remove_trailing_notes,
    flatten_or_variants,
    dedupe_preserve_optional_first,
    flatten_and_variants,
    flatten_comma_variants
)
from class_assoc_pipeline.utils.data_utils import deduplicate_list

from class_assoc_pipeline.config import (
     CLASS_INPUT_TEMPLATE,
     CLASS_EXTRACTED_DIR,
 )
from class_assoc_pipeline.config import MODELS, DATASETS
from pathlib import Path

# Process one file for a given model, dataset, and round
def process_file(model: str, dataset: str, exp_round: int) -> None:
    """
    Process a single raw text file by:
      1. Extracting model-specific content (header removal).
      2. Cleaning and separating mandatory and optional classes.
      3. Deduplicating and saving results to text and Excel.

    Paths are driven by config templates.
    """
    # === 1. Build input/output paths ===
    infile = CLASS_INPUT_TEMPLATE.format(model=model, dataset=dataset, round=exp_round)
    out_dir = Path(CLASS_EXTRACTED_DIR.format(model=model, dataset=dataset))
    out_dir.mkdir(parents=True, exist_ok=True)
    outfile = os.path.join(out_dir, f"extracted_class_round{exp_round}.txt")
    report  = os.path.join(out_dir, f"extracted_class.xlsx")

    # === 2. Read file ===
    try:
        raw = open(infile, encoding="utf-8").read()
    except FileNotFoundError:
        print(f"❌ Error: '{infile}' not found.")
        return

    # === 3. Extract relevant content (e.g., skip system headers) ===
    extracted = extract_content_by_model(raw, model, exp_round)
    if not extracted:
        print(f"⚠️ No content extracted for round {exp_round}.")
        return

    # === 4. Parse and clean lines ===
    lines = extracted.splitlines()
    mandatory, optional = [], []
    reading_mand = True  # Tracks when optional section starts

    for ln in lines:
        text = ln.strip()

        # Skip rationale sections (often not part of actual class lists)
        if re.match(r'^(?:\d+\.\s*|\*\s*|\-\s*)?\s*Rationale:', text, re.IGNORECASE):
            # print(f"{text}, Match")
            continue

        # Detect transition between mandatory and optional sections
        if reading_mand and text == "":
            reading_mand = False
            continue

        # Only process properly formatted list items
        if not re.match(r"^(?:\d+\.|\*)", ln):
            continue

        # Remove list numbering or bullets
        item = re.sub(r"^(?:\d+\.\s*|\*\s*|\-\s*)", "", ln)

        # Check if the line is marked optional
        is_opt = "(optional)" in item.lower()

        # Strip parenthetical notes unless they are special keywords
        core = re.sub(
            r"""
            (?!  # negative lookahead to protect "(optional)" etc.
                \( \s* optional \) |
                \( \s* or\b       |
                \( \s* and\b
            )
            \([^)]*\)
            """,
            "",
            item,
            flags=re.IGNORECASE|re.VERBOSE
        ).strip()
        core = remove_trailing_notes(core)

        # === 5. Handle variations in class grouping (comma, and, or) ===
        if ',' in core:
            raw_names = flatten_comma_variants(core)
            # print(raw_names)
        elif re.search(r'\band\b', core, flags=re.IGNORECASE):
            raw_names = flatten_and_variants(core)
            # print(raw_names)
        elif re.search(r'\(or\b', core, flags=re.IGNORECASE) or '/' in core:
            raw_names = [ flatten_or_variants(core) ]  # Single string
        else:
            raw_names = [ core ]

        # === 6. Final cleanup and classification ===
        for raw in raw_names:
            name = clean_class_name(raw)

            # Strip parentheses not related to meaning (e.g., acronyms)
            if not ('(optional)' in name.lower()) and ('(' in name):
                # print(f"before name: {name}")
                name = re.sub(r'\s*\([^)]*\)', '', name).strip()
                # print(f"after name: {name}")

            # Append to appropriate list (mandatory/optional)
            if reading_mand:
                if is_opt:
                    optional.append(format_optional_line(name))
                else:
                    mandatory.append(name)
            else:
                if is_opt:
                    optional.append(format_optional_line(name))

    # === 7. Deduplicate and combine ===
    mandatory = deduplicate_list(mandatory)
    optional  = deduplicate_list(optional)
    combined  = dedupe_preserve_optional_first(mandatory, optional)
    notes = [""] * len(combined)

    # Ensure output directory
    os.makedirs(out_dir, exist_ok=True)

    # === 8. Save as plain text ===
    with open(outfile, "w", encoding="utf-8") as f:
        f.write("\n".join(combined))

    # === 9. Save as Excel (with notes column) ===
    df = pd.DataFrame({"class": combined, "note": notes})
    df["class"] = df["class"].astype(str)
    df = df[~df['class'].str.lower().duplicated()].reset_index(drop=True)

    sheet_name  = f"Round{exp_round}"
    if not os.path.exists(report):
        with pd.ExcelWriter(report, engine='openpyxl') as writer:
            df.to_excel(writer, index=False, sheet_name=sheet_name)
    else:
        with pd.ExcelWriter(report, engine='openpyxl', mode='a', if_sheet_exists='replace') as writer:
            df.to_excel(writer, index=False, sheet_name=sheet_name)

    print(f"✅ Extracted {model} | {dataset} | Round {exp_round}. Data saved to {outfile} and {report}")

# === Helper: Loop through all rounds for a dataset ===
def process_dataset(model: str, dataset: str, rounds: int) -> None:
    """
    Loop over rounds for one dataset, using config-driven paths.
    """
    for r in range(1, rounds + 1):
        process_file(model, dataset, r)

# === Public entry point ===
def run_extraction_pipeline(model: str, dataset: str, rounds: int):
    """
    Public interface to run the whole extraction pipeline.
    """
    print(f"🔍 Extracting Class Conversation Log for {model} | {dataset.capitalize()} | {rounds} rounds")
    process_dataset(model, dataset, rounds)
