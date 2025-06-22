from class_assoc_pipeline.pipelines.association_pipeline.extraction import run_extraction_pipeline
from class_assoc_pipeline.pipelines.association_pipeline.matching import run_evaluation_pipeline
import argparse
from pathlib import Path



def parse_args():
    parser = argparse.ArgumentParser(description="Run class identification")
    parser.add_argument('--input', type=str, required=True, help='Input folder')
    # parser.add_argument('--model', type=str, required=True, help='Model name (llama3-8b, qwen-14b, gpt-o1, or all)')
    # parser.add_argument('--output', type=str, required=True, help='Output folder name')
    parser.add_argument('--mode', type=str, default="all", help="Pipeline mode (extraction, evaluation, all)")
    args = parser.parse_args()

    # valid_models = ["llama3-8b", "qwen-14b", "gpt-o1", "all"]
    # if args.model.lower() not in valid_models:
    #     parser.error(f"Invalid model name. Please choose from: {', '.join(valid_models)}")

    valid_modes = ["evaluation", "extraction", "all"]
    if args.mode.lower() not in valid_modes:
        parser.error(f"Invalid mode. Choose from: {', '.join(valid_modes)}")
    
    return args

def extract_model_and_dataset(input_path: str):
    path = Path(input_path)
    dataset = path.stem if path.is_file() else path.name
    model = path.parent.name
    return model, dataset

def main():
    args = parse_args()
    mode = args.mode
    in_dir = Path(args.input)
    # Get the number of files in the given dir, which is an important argument for the extraction task.
    pattern = "*.txt"
    existing_files = list(in_dir.glob(pattern))
    total_number_files = len(existing_files)
    # Get the dataset and model
    model, dataset = extract_model_and_dataset(in_dir)

    if mode == "extraction":
        run_extraction_pipeline(model, dataset, rounds=total_number_files)
    elif mode == "evaluation":
        run_evaluation_pipeline(model, dataset, rounds=total_number_files)
    else:
        run_extraction_pipeline(model, dataset, rounds=total_number_files)
        run_evaluation_pipeline(model, dataset, rounds=total_number_files)

if __name__ == "__main__":
    main()