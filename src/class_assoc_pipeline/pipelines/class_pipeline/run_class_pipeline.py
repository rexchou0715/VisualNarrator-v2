from class_assoc_pipeline.pipelines.class_pipeline.extraction import run_extraction_pipeline
from class_assoc_pipeline.pipelines.class_pipeline.matching import run_evaluation_pipeline
import argparse
from pathlib import Path

def parse_args():
    """
    Parse CLI arguments and validate the selected pipeline mode.
    """
    parser = argparse.ArgumentParser(description="Run class identification")
    parser.add_argument('--input', type=str, required=True, help='Input folder')
    parser.add_argument('--mode', type=str, default="all", help="Pipeline mode (extraction, evaluation, all)")
    args = parser.parse_args()

    valid_modes = ["evaluation", "extraction", "all"]
    if args.mode.lower() not in valid_modes:
        parser.error(f"Invalid mode. Choose from: {', '.join(valid_modes)}")
    
    return args

def extract_model_and_dataset(input_path: str):
    """
    Given a file or directory path, infer model and dataset names.
    e.g., for .../llama3-8b/my_dataset → model: llama3-8b, dataset: my_dataset
    """
    path = Path(input_path)
    dataset = path.stem if path.is_file() else path.name
    model = path.parent.name
    return model, dataset

def main():
    args = parse_args()
    mode = args.mode
    in_dir = Path(args.input)

    # Count how many R*.txt files exist — used to determine number of rounds
    pattern = "*.txt"
    existing_files = list(in_dir.glob(pattern))
    total_number_files = len(existing_files)
    print(total_number_files)

    # Infer model and dataset from folder structure
    model, dataset = extract_model_and_dataset(in_dir)

    # Pipeline dispatch based on mode
    if mode == "extraction":
        run_extraction_pipeline(model, dataset, rounds=total_number_files)
    elif mode == "evaluation":
        run_evaluation_pipeline(model, dataset, rounds=total_number_files)
    else:
        run_extraction_pipeline(model, dataset, rounds=total_number_files)
        run_evaluation_pipeline(model, dataset, rounds=total_number_files)

if __name__ == "__main__":
    main()
