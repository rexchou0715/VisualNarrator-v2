import re
import os
import pandas as pd

from class_assoc_pipeline.config import MODELS, DATASETS, ASSOC_INPUT_TEMPLATE, ASSOC_EXTRACTED_DIR
from class_assoc_pipeline.utils.text_utils import (
    remove_trailing_notes_association,
    clean_association_line,
    parse_association_line,
)

# === Extractor functions for different model outputs ===

def extract_gpt_o1_associations(content: str) -> tuple[list[str], list[str]]:
    """
    Extract mandatory and optional associations from GPT-o1 raw output.
    """
    assistants = list(re.finditer(r'ASSISTANT :', content, re.IGNORECASE))
    if len(assistants) < 2:
        return [], []
    content = content[assistants[1].end():].strip()

    m2 = re.search(r"Step\s*3:.*?Associations? in 'X-Y'", content, re.IGNORECASE)
    if not m2:
        return [], []
    content = content[m2.end():].strip()

    m3 = re.search(r"Here is the final list of associations?:", content, re.IGNORECASE)
    if not m3:
        return [], []
    content = content[m3.end():].strip()

    lines = content.splitlines()
    refined, optional = [], []
    reading_mand = True

    complex_pat = re.compile(r"^[\d\*\-\.\s]*[\w\s()]+-\([\w\s&]+\)-[\w\s()]+$")
    simple_pat = re.compile(r"^[\d\*\-\.\s]*[\w\s()]+-[\w\s()]+$")

    for ln in lines:
        ln = remove_trailing_notes_association(ln)
        if ln == "":
            reading_mand = False
            continue
        if complex_pat.match(ln) or simple_pat.match(ln):
            if "(optional" in ln.lower() or "(opt)" in ln.lower():
                optional.append(ln)
            elif reading_mand:
                refined.append(ln)
            else:
                optional.append(ln)

    return refined, optional


def extract_llama3_8b_associations(content: str) -> tuple[list[str], list[str]]:
    """
    Extract mandatory and optional associations from Llama 3 8B raw output.
    """
    assistants = list(re.finditer(r'Assistant?:', content, re.IGNORECASE))
    if len(assistants) < 3:
        print("⚠️ Less than 3 'Assistant:' markers")
        return [], []
    content = content[assistants[2].end():].strip()

    m = re.search(r"Here is the final list of associations?:", content, re.IGNORECASE)
    if not m:
        return [], []
    lines = content[m.end():].strip().splitlines()

    refined, optional = [], []
    reading_mand = True
    xy_pat = re.compile(r"^[\d\*\-\.\s]*[\w\s()]+-[\w\s()]+$")

    for ln in lines:
        ln = remove_trailing_notes_association(ln)
        if ln == "":
            reading_mand = False
            continue
        if reading_mand and xy_pat.match(ln):
            refined.append(ln)
        elif "(optional" in ln.lower() and xy_pat.match(ln):
            optional.append(ln)

    return refined, optional


def extract_qwen14b_associations(content: str) -> tuple[list[str], list[str]]:
    """
    Extract mandatory and optional associations from Qwen14B raw output.
    """
    assistants = list(re.finditer(r'Assistant :', content, re.IGNORECASE))
    if len(assistants) < 3:
        print("⚠️ Less than 3 'Assistant :' markers")
        return [], []
    content = content[assistants[2].end():].strip()

    m2 = re.search(r"</think>", content, re.IGNORECASE)
    if not m2:
        print("⚠️ Missing '</think>' marker")
        return [], []
    content = content[m2.end():].strip()

    m3 = re.search(r"Here is the final list of associations?:", content, re.IGNORECASE)
    if not m3:
        print("⚠️ Missing 'final list of associations' marker")
        return [], []
    lines = content[m3.end():].strip().splitlines()

    refined, optional = [], []
    reading_mand = True
    xy_pat = re.compile(r"^[\d\*\-\.\s]*[\w\s()]+-[\w\s()]+$")

    for ln in lines:
        ln = remove_trailing_notes_association(ln)
        if ln == "":
            reading_mand = False
            continue
        if reading_mand and xy_pat.match(ln):
            refined.append(ln)
        elif "(optional" in ln.lower() and xy_pat.match(ln):
            optional.append(ln)

    return refined, optional


# Mapping from model name to corresponding extractor
EXTRACTORS = {
    "gpt-o1": extract_gpt_o1_associations,
    "llama3-8b": extract_llama3_8b_associations,
    "qwen-14b": extract_qwen14b_associations,
}


def extract_associations_by_model(content: str, model: str) -> tuple[list[str], list[str]]:
    """
    Route content to the correct model-specific extractor function.
    """
    fn = EXTRACTORS.get(model.lower())
    if not fn:
        print(f"⚠️ Unsupported model '{model}' for association extraction.")
        return [], []
    return fn(content)


def process_file(input_file: str, output_file: str, model: str) -> None:
    """
    Read raw model output, extract associations, and write cleaned associations to file.
    """
    try:
        content = open(input_file, encoding="utf-8").read()
    except FileNotFoundError:
        print(f"❌ File not found: {input_file}")
        return

    refined, optional = extract_associations_by_model(content, model)
    if not refined and not optional:
        print(f"⚠️ No associations found in {input_file}")
        return

    os.makedirs(os.path.dirname(output_file), exist_ok=True)
    with open(output_file, "w", encoding="utf-8") as out:
        for ln in refined:
            out.write(clean_association_line(ln) + "\n")
        for ln in optional:
            out.write(clean_association_line(ln, force_optional=True) + "\n")


def process_dataset(model: str, dataset: str) -> None:
    """
    Process all rounds of a specific (model, dataset) pair.
    """
    rounds = MODELS.get(model, 5)
    for r in range(1, rounds + 1):
        inp = ASSOC_INPUT_TEMPLATE.format(model=model, dataset=dataset, round=r)
        outd = ASSOC_EXTRACTED_DIR.format(model=model, dataset=dataset)
        outp = os.path.join(outd, f"refined_associations_round{r}.txt")
        process_file(inp, outp, model)


def process_round_file(input_file: str) -> list[list[str]]:
    """
    Read one refined .txt file and parse each association line into a list of [X, Y].
    """
    out = []
    try:
        with open(input_file, encoding='utf-8') as f:
            for ln in f:
                out.extend(parse_association_line(ln))
    except FileNotFoundError:
        print(f"❌ Error: File '{input_file}' not found.")
    return out


def convert_dataset_to_excel(model: str, dataset: str, num_rounds: int = 10) -> None:
    """
    Convert all rounds of one dataset to an Excel file, each round as a sheet.
    """
    out_xlsx_dir = ASSOC_EXTRACTED_DIR.format(model=model, dataset=dataset)
    out_xlsx_path = os.path.join(out_xlsx_dir, f"association_report_{dataset}.xlsx")
    writer = pd.ExcelWriter(out_xlsx_path, engine="xlsxwriter")

    for r in range(1, num_rounds + 1):
        txt_path = os.path.join(out_xlsx_dir, f"refined_associations_round{r}.txt")
        pairs = process_round_file(txt_path)
        if not pairs:
            continue
        df = pd.DataFrame(pairs, columns=["X", "Y"])

        # Move optional associations to the bottom
        mask = df["X"].str.contains(r'\(Opt\)', case=False)
        df = pd.concat([df[~mask], df[mask]], ignore_index=True)
        df.to_excel(writer, sheet_name=f"Round{r}", index=False)

    writer.close()
    print(f"✅ Wrote Excel report for {model}/{dataset}")


def process_all_datasets(model: str) -> None:
    """
    Process and convert all datasets for a given model into Excel reports.
    """
    path = f"output/association/{model}"
    for ds in os.listdir(path):
        if ds.startswith("."):
            continue
        rounds = MODELS.get(model, 5)
        convert_dataset_to_excel(model, ds, num_rounds=rounds)


if __name__ == "__main__":
    for MODEL in list(MODELS.keys()):
        for ds in DATASETS:
            process_dataset(MODEL, ds)
        process_all_datasets(MODEL)
