from class_assoc_pipeline.utils.text_utils import normalize_word, remove_trailing_notes_association
from class_assoc_pipeline.utils.data_utils import expand_synonym_mapping, generate_candidates
from class_assoc_pipeline.utils.metrics import perform_matching_associations, compute_metrics
from class_assoc_pipeline.config import (
    ASSOC_INPUT_TEMPLATE,
    ASSOC_EXTRACTED_DIR,
    GOLD_STANDARD_ASSOCIATION,
    SILVER_STANDARD_ASSOCIATION,
    SYNONYM_DICT_CLASS
)

from ...utils.file_io import (
    load_excel_sheets,
    write_results_to_excel,
    write_experiment_log,
)

from collections import Counter
from pathlib import Path
import pandas as pd
import os


def evaluation_experiment(model: str, dataset: str) -> None:
    """
    Process a given model's association extraction results across all datasets and rounds:
    1. Load refined associations from Excel sheets.
    2. Normalize and label associations as optional or mandatory.
    3. Match extracted associations with gold/silver standards using synonyms.
    4. Compute evaluation metrics.
    5. Write logs, metrics, and unmatched associations to files.
    """
    # for dataset in DATASETS:
    ds = dataset.lower()
    # out_dir = ASSOC_EXTRACTED_DIR.format(model=model, dataset=ds)
    out_dir = ASSOC_EXTRACTED_DIR.format(model=model, dataset=ds)
    os.makedirs(out_dir, exist_ok=True)

    report_path = os.path.join(out_dir, f"extracted_associaiton.xlsx")
    sheets = load_excel_sheets(report_path)

    # Load gold and silver standards, and prepare synonym mapping
    gold_raw = GOLD_STANDARD_ASSOCIATION[ds]
    silver_raw = SILVER_STANDARD_ASSOCIATION.get(ds, [])
    gold_set = {frozenset(map(normalize_word, pair)) for pair in gold_raw}
    silver_set = {frozenset(map(normalize_word, pair)) for pair in silver_raw}
    syn_map = expand_synonym_mapping(SYNONYM_DICT_CLASS[ds])

    full_log = ""
    mand_results = []
    all_results = []
    all_unmatched = []

    for round_idx, (sheet_name, df_raw) in enumerate(sheets.items()):
        # Normalize input associations and identify optional ones
        df = df_raw.copy()
        df["X"] = df["X"].map(normalize_word)
        df["Y"] = df["Y"].map(normalize_word)
        df["opt"] = df["X"].str.contains(r'^\((?:opt|optional)\)', case=False, regex=True)
        df["X"] = df["X"].str.replace(r'^\(opt\)\s*', "", regex=True)

        pairs = [
            tuple(sorted((x, y)))
            for x, y in df[["X", "Y"]].itertuples(index=False, name=None)
        ]
        # print(pairs)
        is_option = df["opt"].tolist()

        # Perform matching and collect results
        m_matched, o_matched, m_un, o_un, log, remaining_gold_man, remaining_gold_all = perform_matching_associations(
            pairs,
            is_option,
            gold_set,
            silver_set,
            syn_map
        )

        all_unmatched.append(m_un + o_un)

        mand_metrics = compute_metrics(m_matched, m_un, remaining_gold_man, round_idx)
        all_metrics = compute_metrics(m_matched + o_matched, m_un + o_un, remaining_gold_all, round_idx)

        full_log += f"\n\n=== Round {round_idx + 1} ({sheet_name}) ===\n" + log
        mand_results.append(mand_metrics)
        all_results.append(all_metrics)

    # Write unmatched associations summary to Excel
    flat_unmatched = [assoc for round_list in all_unmatched for assoc in round_list]
    counter = Counter(flat_unmatched)
    df_unmatched_log = pd.DataFrame({
        'association': list(counter.keys()),
        'count': list(counter.values())
    })
    df_unmatched_log.sort_values(by=["count"], ascending=False, inplace=True)
    df_unmatched_log.to_excel(os.path.join(out_dir, "false_positives.xlsx"), index=False)

    # Write experiment log and results
    write_experiment_log(out_dir, full_log)
    write_results_to_excel(out_dir, ds, mand_results, all_results)


def run_evaluation_pipeline(model, dataset, rounds):
    print(f"🔍 Evaluating Association Extraction for {model} | {dataset.capitalize()} | {rounds} Rounds")
    evaluation_experiment(
        model,
        dataset
    )
    print(f"✅ Done Evaluation of Association for {model} | {dataset.capitalize()} | {rounds} Rounds")

