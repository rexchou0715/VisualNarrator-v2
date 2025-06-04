import pandas as pd
import numpy as np
import os
from pathlib import Path
from class_assoc_pipeline.config import (
    EXPERIMENT_OUTPUT_DIR,
    CLASS_EXTRACTED_DIR,
    ASSOC_EXTRACTED_DIR,
    MODELS
)
from class_assoc_pipeline.utils.aggregation_utils import aggregate_unmatched_results

def run_experiment_comparison(
    experiment_type="Class",
    main_cols=None,
    avg_sub_cols=None,
    variation_sub_cols=None,
    models=None,
    output_file=None
):
    """
    Aggregate and compare experiment results across datasets and models.

    :param experiment_type: Either "Class" or "Association". Determines folder paths.
    :param main_cols: List of model column labels (e.g. ["GPT-o1", "GPT-o1(Opt)", ...]).
    :param avg_sub_cols: Sub-columns to average (defaults to ["F-0.5", "F-1", "F-2"]).
    :param variation_sub_cols: Sub-columns to calculate variation (defaults to ["Precision", "Recall"]).
    :param models: List of model names to include (defaults to ["GPT-o1", "Llama 3 8B", "Qwen14B"]).
    :param output_file: Path to the final comparison Excel file.
    """
    # Set default main columns if not provided
    if main_cols is None:
        if experiment_type.lower() == "class":
            main_cols = [
                "GPT-o1", "GPT-o1(Opt)",
                "Llama3-8B", "Llama3-8B(Opt)",
                "Qwen-14B", "Qwen-14B(Opt)",
                "VN(Precision-Oriented)", "VN(Recall-Oriented)"
            ]
        else:
            main_cols = [
                "GPT-o1", "GPT-o1(Opt)",
                "Llama3-8B", "Llama3-8B(Opt)",
                "Qwen-14B", "Qwen-14B(Opt)"
            ]

    # Set default sub-columns for averages and variation
    if avg_sub_cols is None:
        avg_sub_cols = ["F-0.5", "F-1", "F-2"]
    if variation_sub_cols is None:
        variation_sub_cols = ["Precision", "Recall"]

    # Set default models
    if models is None:
        models = ["GPT-o1", "Llama3-8B", "Qwen-14B"]

    # Base directory for the "base" model to discover datasets

    base_path = "output/class/GPT-o1"

    # Discover all dataset folders
    datasets = [
        folder.lower()
        for folder in os.listdir(base_path)
        if folder != ".DS_Store"
    ]

    # Prepare multi‐indexed DataFrames for average and variation
    avg_columns = pd.MultiIndex.from_product([main_cols, avg_sub_cols])
    final_df_average = pd.DataFrame(np.nan, index=datasets, columns=avg_columns)

    var_columns = pd.MultiIndex.from_product([main_cols, variation_sub_cols])
    final_df_variation = pd.DataFrame(np.nan, index=datasets, columns=var_columns)

    # Process each model and dataset
    for model in models:
        experiment_type = experiment_type.lower()
        for dataset in os.listdir(f"output/{experiment_type}/{model}"):
            if dataset == ".DS_Store":
                continue

            dataset_lower = dataset.lower()
            input_file = f"output/{experiment_type}/{model}/{dataset}/experiment_results.xlsx"

            # Process both sheets: mandatory and including optional
            for sheet in ["mandatory", "including optional"]:
                df = pd.read_excel(input_file, sheet_name=sheet)
                # Drop the "Round" column
                metrics = df.drop(columns=["Round"])

                # Compute row‐wise average and standard deviation
                avg_vals = metrics.mean().round(3)
                std_vals = metrics.std().round(3)

                # Append AVG and STD-DEV rows to a combined DataFrame
                avg_row = pd.DataFrame([["AVG"] + avg_vals.tolist()], columns=df.columns)
                std_row = pd.DataFrame([["STD-DEV"] + std_vals.tolist()], columns=df.columns)
                combined = pd.concat([df, avg_row, std_row], ignore_index=True)

                # Write the aggregated sheet back to the dataset folder
                
                out_path = f"output/{experiment_type}/{model}/{dataset}/experiment_results_with_aggregation.xlsx"
                mode   = "a" if os.path.exists(out_path) else "w"

                if mode == "a":
                    # append to an existing file, replacing the sheet if it exists
                    with pd.ExcelWriter(
                        out_path,
                        engine="openpyxl",
                        mode="a",
                        if_sheet_exists="replace"
                    ) as writer:
                        combined.to_excel(writer, sheet_name=sheet, index=False)
                else:
                    # write a brand new file (no if_sheet_exists allowed)
                    with pd.ExcelWriter(
                        out_path,
                        engine="xlsxwriter",
                        mode="w"
                    ) as writer:
                        combined.to_excel(writer, sheet_name=sheet, index=False)

                # Extract averages and variations for the final comparison table
                avg_dict = avg_vals.to_dict()
                var_dict = std_vals.to_dict()
                for metric, value in avg_dict.items():
                    col_label = model if sheet == "mandatory" else f"{model}(Opt)"
                    final_df_average.at[dataset_lower, (col_label, metric)] = value
                for metric, value in var_dict.items():
                    col_label = model if sheet == "mandatory" else f"{model}(Opt)"
                    final_df_variation.at[dataset_lower, (col_label, metric)] = value

    # Compute between‐dataset average and variation
    between_avg = final_df_average.mean().to_frame().T.round(3)
    between_avg.index = ["AVG"]
    between_std = final_df_average.std().to_frame().T.round(3)
    between_std.index = ["STD-DEV"]
    final_df_average = pd.concat([final_df_average, between_avg, between_std])

    var_between_avg = final_df_variation.mean().to_frame().T.round(3)
    var_between_avg.index = ["AVG(STD)"]
    final_df_variation = pd.concat([final_df_variation, var_between_avg])

    # Write the final comparison workbook
    output_path = Path(f"output/experiment/{experiment_type}_experiment_comparison_result.xlsx")

    # If the file already exists on disk → append and replace sheets:
    if output_path.exists():
        with pd.ExcelWriter(
            output_path,
            engine="openpyxl",
            mode="a",
            if_sheet_exists="replace"
        ) as writer:
            final_df_average.to_excel(writer, sheet_name=f"{experiment_type}-Performance")
            final_df_variation.to_excel(writer, sheet_name=f"{experiment_type}-Variation")

    # Otherwise → write a new file (no if_sheet_exists allowed here)
    else:
        with pd.ExcelWriter(
            output_path,
            engine="xlsxwriter",
            mode="w"
        ) as writer:
            final_df_average.to_excel(writer, sheet_name=f"{experiment_type}-Performance")
            final_df_variation.to_excel(writer, sheet_name=f"{experiment_type}-Variation")


if __name__ == "__main__":
    # Run comparison for class experiments
    out_dir = Path(EXPERIMENT_OUTPUT_DIR)
    run_experiment_comparison(
        experiment_type="Association",
        output_file= out_dir / f"Association_experiment_comparison_result.xlsx",
        models=list(MODELS.keys())
    )
    # To compare association experiments
    # run_experiment_comparison(experiment_type="Association", output_file="Association_experiment_comparison_result.xlsx")
    aggregate_unmatched_results("association", models=list(MODELS.keys()))
