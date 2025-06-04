import os
from typing import List
import pandas as pd
import ast


def normalize_association_key(raw: str | tuple) -> tuple:
    if isinstance(raw, str):
        try:
            raw = ast.literal_eval(raw)  # safely convert string to tuple
        except Exception as e:
            print(f"⚠️ Could not parse: {raw} — {e}")
            return ("INVALID",)  # or raise

    return tuple(sorted([x.strip().lower() for x in raw]))


def aggregate_unmatched_results(
    experiment_type: str,
    models: List[str],
    base_dir: str = "output",
    output_root: str = "output/experiment/FP_data"
):
    """
    Read each model's unmatch.xlsx for every dataset under
      {base_dir}/{ExperimentType}/{model}/{dataset}/unmatch.xlsx
    and for each dataset produce a workbook with two sheets:
      - "Aggregated Result": total counts across models
      - "Individual Result": side-by-side per-model counts
    """

    et = experiment_type.lower()                  
    key_col = "class" if et == "class" else "association"

    template = os.path.join(
        f"{experiment_type.lower()}",
        "{model}",
        "{dataset}",
        "unmatched.xlsx"
    )

    # Discover datasets by listing the first model's extraction-dir
    first_model = models[0]
    first_base = f"output/{experiment_type.lower()}/{first_model}"
    # first_base now = "output/GPT-o1/Extracted_Class_Experiment/"
    datasets = [d for d in os.listdir(first_base) if not d.startswith(".")]

    # Prepare output folder
    agg_dir = os.path.join(output_root, et)
    os.makedirs(agg_dir, exist_ok=True)

    for dataset in datasets:
        df_ind = pd.DataFrame()
        for model in models:
            rel_path = template.format(model=model, dataset=dataset)
            full_path = os.path.join(base_dir, rel_path)
            df = pd.read_excel(full_path)
            if key_col == "association":
                df[key_col] = df[key_col].apply(normalize_association_key)
            # rename count column
            count_col = f"count_{model}"
            df = df.rename(columns={"count": count_col, key_col: key_col})
            # join side-by-side
            if df_ind.empty:
                df_ind = df.set_index(key_col)[[count_col]]
            else:
                df_ind = df_ind.join(df.set_index(key_col)[count_col], how="outer")

        df_all = df_ind.reset_index()
        # melt + sum to get aggregated totals
        df_agg = (
            df_all
            .melt(id_vars=[key_col], var_name="model", value_name="count")
            .groupby(key_col, as_index=False)["count"]
            .sum()
            .sort_values("count", ascending=False)
            .rename(columns={"count": "total_count"})
        )

        out_path = os.path.join(agg_dir, f"{dataset}_unmatched.xlsx")
        with pd.ExcelWriter(out_path, engine="openpyxl", mode="w") as writer:
            df_agg.to_excel(writer, sheet_name="Aggregated Result", index=False)
            df_all.to_excel(writer, sheet_name="Individual Result", index=False)

        print(f"→ Wrote {out_path}")
