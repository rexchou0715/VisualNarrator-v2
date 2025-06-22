import os
import pandas as pd
from typing import List, Dict
from pathlib import Path


def load_excel_sheets(input_excel_path: str) -> Dict[str, pd.DataFrame]:
    """
    Load all sheets from an Excel file.

    :param input_excel_path: Path to the Excel file.
    :return: Dictionary mapping sheet names to their corresponding DataFrames.
    """
    xls = pd.ExcelFile(input_excel_path)
    return {sheet: pd.read_excel(xls, sheet_name=sheet) for sheet in xls.sheet_names}


def write_experiment_log(output_dir: str, log_text: str) -> None:
    """
    Write the full matching log to a text file.

    :param output_dir: Directory to save the log file.
    :param log_text: Full log text to write.
    """
    os.makedirs(output_dir, exist_ok=True)
    log_path = os.path.join(output_dir, "experiment_log.txt")
    with open(log_path, "w", encoding="utf-8") as f:
        f.write(log_text)


def write_results_to_excel(
    output_dir: str,
    dataset: str,
    mand_results: List[dict],
    all_results: List[dict]
) -> None:
    """
    Write experiment results to an Excel file with two sheets:
    'mandatory' and 'including optional'.

    :param output_dir: Directory to save the Excel file.
    :param dataset: Dataset name (not used in filename but preserved for future extensibility).
    :param mand_results: List of dictionaries for mandatory metrics.
    :param all_results: List of dictionaries including optional metrics.
    """
    os.makedirs(output_dir, exist_ok=True)
    out_path = os.path.join(output_dir, "evaluation_results.xlsx")
    with pd.ExcelWriter(out_path) as writer:
        pd.DataFrame(mand_results).to_excel(writer, sheet_name="mandatory", index=False)
        pd.DataFrame(all_results).to_excel(writer, sheet_name="including optional", index=False)


def get_next_round_number(output_dir, pattern="*.txt"):
    output_path = Path(output_dir)
    if not output_path.exists():
        return 1  # First round if the folder doesn't exist yet

    # Count matching files (e.g., output text files)
    existing_files = list(output_path.glob(pattern))
    return len(existing_files) + 1