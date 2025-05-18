# src/class_assoc_pipeline/pipelines/class_pipeline/extraction.py

import os
import re
import pandas as pd

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

def process_file(model: str, dataset: str, exp_round: int) -> None:
    """
    Process a single raw text file by:
      1. Extracting model-specific content (header removal).
      2. Cleaning and separating mandatory and optional classes.
      3. Deduplicating and saving results to text and Excel.

    Paths are driven by config templates.
    """
    # Build paths from config
    infile = CLASS_INPUT_TEMPLATE.format(model=model, dataset=dataset, round=exp_round)
    out_dir = CLASS_EXTRACTED_DIR.format(model=model, dataset=dataset)
    outfile = os.path.join(out_dir, f"refined_class_round{exp_round}.txt")
    report  = os.path.join(out_dir, f"class_report_{dataset}(refined).xlsx")

    # 1. Read
    try:
        raw = open(infile, encoding="utf-8").read()
    except FileNotFoundError:
        print(f"❌ Error: '{infile}' not found.")
        return

    # 2. Extract headers
    extracted = extract_content_by_model(raw, model, exp_round)
    if not extracted:
        print(f"⚠️ No content extracted for round {exp_round}.")
        return

    # 3. Clean lines
    # lines = [ln.strip() for ln in extracted.splitlines() if ln.strip()] # Remove all new lines
    lines = extracted.splitlines()
    mandatory, optional = [], []
    reading_mand = True

    for ln in lines:
        text = ln.strip()
        # Drop any “Rationale” (or similar) lines outright
        if re.match(r'^(?:\d+\.\s*|\*\s*|\-\s*)?\s*Rationale:', text, re.IGNORECASE):
            print(f"{text}, Match")
            continue
        if reading_mand and text == "":
            reading_mand = False
            continue
        # only numbered or bulleted items
        if not re.match(r"^(?:\d+\.|\*)", ln):
            continue

        item = re.sub(r"^(?:\d+\.\s*|\*\s*|\-\s*)", "", ln)
        is_opt = "(optional)" in item.lower()
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

        # -- handle "and", "or" 
        if ',' in core:
            raw_names = flatten_comma_variants(core)
            print(raw_names)
        elif re.search(r'\band\b', core, flags=re.IGNORECASE):
            raw_names = flatten_and_variants(core)
            print(raw_names)
        elif re.search(r'\(or\b', core, flags=re.IGNORECASE) or '/' in core:
            # flatten_or_variants returns a single string
            raw_names = [ flatten_or_variants(core) ]
        else:
            raw_names = [ core ]

        # clean & append each
        for raw in raw_names:
            name = clean_class_name(raw)
            # —— strip generic parentheses (e.g. acronyms) —— 
            # if not re.search(r'^\(optional\)', name, re.IGNORECASE) \
            #     and '(' in name:
            if not ('(optional)' in name.lower()) and ('(' in name):
                # remove the first (...) group
                print(f"before name: {name}")
                name = re.sub(r'\s*\([^)]*\)', '', name).strip()
                print(f"after name: {name}")
            if reading_mand:
                if is_opt:
                    optional.append(format_optional_line(name))
                else:
                    mandatory.append(name)
            else:
                if is_opt:
                    optional.append( format_optional_line(name) )

    # 4. Dedupe
    mandatory = deduplicate_list(mandatory)
    optional  = deduplicate_list(optional)
    combined  = dedupe_preserve_optional_first(mandatory, optional)
    notes = [""] * len(combined)
    # ensure output dir
    os.makedirs(out_dir, exist_ok=True)

    # 5. Save text
    with open(outfile, "w", encoding="utf-8") as f:
        f.write("\n".join(combined))

    # 6. Save Excel
    df = pd.DataFrame({"class": combined, "note": notes})
    df["class"] = df["class"].astype(str)
    df = df[~df['class'].str.lower().duplicated()].reset_index(drop=True)
    # report_path = os.path.join(out_dir, f"class_report_{dataset}.xlsx")
    sheet_name  = f"Round{exp_round}"
    # If file doesn't exist yet, write fresh; otherwise append/replace
    if not os.path.exists(report):
        with pd.ExcelWriter(report, engine='openpyxl') as writer:
            df.to_excel(writer, index=False, sheet_name=sheet_name)
    else:
        with pd.ExcelWriter(report, engine='openpyxl', mode='a', if_sheet_exists='replace') as writer:
            df.to_excel(writer, index=False, sheet_name=sheet_name)
    print(f"✅ Processed {model} | {dataset} | Round {exp_round}")

def process_dataset(model: str, dataset: str, rounds: int) -> None:
    """
    Loop over rounds for one dataset, using config-driven paths.
    """
    for r in range(1, rounds + 1):
        process_file(model, dataset, r)

if __name__ == "__main__":
    # example usage
    # for mdl, rnds in MODELS.items():
    #     for ds in DATASETS:
    #         process_dataset(mdl, ds, rnds)

    MODEL = "Qwen-14B"
    ROUNDS = MODELS.get(MODEL, 5)  # falls back to 5 if for some reason it’s missing

    for ds in DATASETS:
        process_dataset(MODEL, ds, ROUNDS)