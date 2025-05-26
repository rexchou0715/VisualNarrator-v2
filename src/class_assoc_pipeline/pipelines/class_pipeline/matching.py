
import os
from pathlib import Path
import pandas as pd
from collections import Counter
import re

from class_assoc_pipeline.config import (
    CLASS_EXTRACTED_DIR,
    MODELS,
    DATASETS,
    GOLD_STANDARD_CLASS,
    SILVER_STANDARD_CLASS,
    SYNONYM_DICT_CLASS,
    NON_PUNISH_CLASS,
)
from ...utils.file_io import (
    load_excel_sheets,
    write_results_to_excel,
    write_experiment_log
)
from class_assoc_pipeline.utils.data_utils import (
    normalize_word,
    expand_synonym_mapping,
)
from class_assoc_pipeline.utils.metrics import (
    perform_matching,
    compute_metrics,
    remove_non_punished_from_unmatched
)

def run_experiment(
    model: str,
    dataset: str,
    gold_standard_dict: dict,
    silver_standard_dict: dict,
    synonym_dict: dict,
    non_punish_dict: dict,
):
    """
    1) load each round’s refined class-report Excel
    2) preprocess and normalize
    3) match against gold & silver
    4) compute metrics, accumulate logs
    5) write out experiment_log.txt and aggregated experiment_results.xlsx
    """
    # — prepare standards & synonyms —
    dataset_key = dataset.lower()
    gold_standard   = { normalize_word(x) for x in gold_standard_dict[dataset_key] }
    silver_standard = { normalize_word(x) for x in silver_standard_dict.get(dataset_key, []) }
    synonym_mapping = expand_synonym_mapping(synonym_dict[dataset_key])

    # — I/O paths —
    out_dir = Path(CLASS_EXTRACTED_DIR.format(model=model, dataset=dataset_key))
    in_path = out_dir / f"class_report_{dataset_key}(refined).xlsx"
    unmatched_output_path = out_dir / "unmatched.xlsx"
    os.makedirs(out_dir, exist_ok=True)

    # load all rounds
    sheets = load_excel_sheets(in_path)

    full_log = ""
    mand_results = []
    all_results  = []
    all_unmatched_class = []
    # remaining_gold = set(gold_standard)  # we’ll shrink this each round

    for round_idx, (sheet_name, df_raw) in enumerate(sheets.items()):
        # normalize the incoming df
        # assume df_raw has columns ["class","note"], optional marker already in “(optional)”
        # we need class_for_match & is_optional_flag:
        df = df_raw.dropna(subset=["class"]).copy()
        df["is_opt"] = df["class"].str.contains(r"^\((?:opt|optional)\)", case=False)
        df["class_clean"] = df["class"].str.replace(
            r"(?i)^\((?:opt|optional)\)\s*", "", regex=True
        )
        df["class_for_match"] = (
            df["class_clean"]
              .str.replace(r"\([^)]*\)", "", regex=True)
              .str.strip()
              .map(normalize_word)
        )

        words       = df["class_for_match"].tolist()
        is_opts     = df["is_opt"].tolist()

        # run the two‐phase matching
        m_matched, o_matched, m_un, o_un, log, remaining_gold_man, remaining_gold_all = perform_matching(
            words, is_opts, gold_standard, silver_standard, synonym_mapping
        )

        updated_m_un, log = remove_non_punished_from_unmatched(m_un,
                                                               m_matched,
                                                               non_punish_dict,
                                                               dataset,
                                                               log)
        
        updated_all_un, log = remove_non_punished_from_unmatched(m_un + o_un,
                                                                 m_matched + o_matched,
                                                                 non_punish_dict,
                                                                 dataset,
                                                                 log)

        # compute metrics for this round
        # note: remaining_gold was modified inside perform_matching
        mand_metrics = compute_metrics(m_matched, updated_m_un, remaining_gold_man, round_idx)
        all_metrics  = compute_metrics(m_matched+o_matched, updated_all_un, remaining_gold_all, round_idx)

        mand_results.append(mand_metrics)
        all_results .append(all_metrics)

        full_log   += f"\n\n=== Round {round_idx+1} ({sheet_name}) ===\n" + log

        # deal with unmathed list
        all_unmatched_class.append(updated_all_un)
        # print(all_unmatched_class)

    # Clean unmatched classes
    all_unmatched_log_flat = [
        re.sub(r'^\(opt\)', '', entity, flags=re.IGNORECASE).strip() 
        for round in all_unmatched_class 
        for entity in round
    ]
    class_counter = Counter(all_unmatched_log_flat)
    df_unmatched_class = pd.DataFrame({
        'class': list(class_counter.keys()),
        'count': list(class_counter.values())
    })

    df_unmatched_class.sort_values(by='count', ascending=False, inplace=True)
    df_unmatched_class.to_excel(unmatched_output_path, index=False)

    # write logs and results
    write_experiment_log(out_dir, full_log)
    write_results_to_excel(out_dir, dataset_key, mand_results, all_results)

    # print(m_un + o_un)

def process_dataset(model: str, rounds: int):
    """
    Iterate over all DATASETS for one model.
    """
    for ds in DATASETS:
        if ds.lower() == ".ds_store":
            continue
        print(ds)
        run_experiment(
            model,
            ds,
            GOLD_STANDARD_CLASS,
            SILVER_STANDARD_CLASS,
            SYNONYM_DICT_CLASS,
            NON_PUNISH_CLASS,
        )

if __name__ == "__main__":
    # only run GPT-o1 for now
    for MODEL, ROUNDS in MODELS.items():
        # MODEL = "Qwen-14B"
        # ROUNDS = MODELS.get(MODEL, 5)
        print(f"▶ Running class‐matching for {MODEL} ({ROUNDS} rounds)…")
        process_dataset(MODEL, ROUNDS)
