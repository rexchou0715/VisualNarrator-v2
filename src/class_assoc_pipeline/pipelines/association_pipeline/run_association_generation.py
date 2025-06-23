# run_class_generation.py

import argparse
from pathlib import Path
from datetime import datetime
import time

from class_assoc_pipeline.utils.prompts import INSTRCTION_ASSOC_SLM, INSTRUCTIONS_ASSOC_LLM
from class_assoc_pipeline.utils.model_client  import init_client
from class_assoc_pipeline.utils.generation_utils import process_steps, get_next_round_number
from class_assoc_pipeline.config import GOLD_STANDARD_CLASS

FIXED_MAX_TOKENS = 3000

def parse_args():
    """
    Handle and validate command-line arguments.
    """
    parser = argparse.ArgumentParser(description="Run class identification")
    parser.add_argument('--input', type=str, required=True, help='Input file path')
    parser.add_argument('--model', type=str, required=True, help='Model name')
    # parser.add_argument('--output', type=str, required=True, help='Output folder name')
    parser.add_argument('--rounds', type=int, default=1, help='Number of rounds (suggested max=5)')
    args = parser.parse_args()

    valid_models = ["llama3-8b", "qwen-14b", "gpt-o1"]
    if args.model.lower() not in valid_models:
        parser.error(f"Invalid model name. Please choose from: {', '.join(valid_models)}")

    return args



def main():
    args = parse_args()
    client = init_client(model_name= args.model)
    input_path = Path(args.input)
    dataset_name = input_path.stem

    if dataset_name not in GOLD_STANDARD_CLASS:
        print(f"⚠️ No gold standard found for dataset: '{dataset_name}'")
        print(f"Available Datasets: {list(GOLD_STANDARD_CLASS.keys())}")
        raise SystemExit(1)
    
    output_dir = Path(f"data/raw/association/{args.model}/{dataset_name}")
    output_dir.mkdir(parents=True, exist_ok=True)

    with open(input_path, "r", encoding="utf-8") as f:
        user_stories = f.read()

    # Determine next available round number (e.g., R3 → start from 4)
    print(output_dir)
    round_num = get_next_round_number(output_dir)
    print(f"🔁 Experiment Round ID: {round_num}")

    # Choose prompt instruction based on model type
    if args.model.lower() == "gpt-o1":
        instruction = INSTRUCTIONS_ASSOC_LLM
    else:
        instruction = INSTRCTION_ASSOC_SLM

    # Map CLI model name to actual model ID used by the client
    if args.model.lower() == "llama3-8b":
        model = "meta-llama/Meta-Llama-3-8B-Instruct"
    elif args.model.lower() == "qwen-14b":
        model = "deepseek-ai/DeepSeek-R1-Distill-Qwen-14B"
    else:
        model = "o1-2024-12-17"

    # Run experiment rounds
    for r in range(args.rounds):
        conversation, responses = process_steps(
            instructions=instruction,
            user_text=user_stories,
            client=client,
            model=model,
            max_tokens=FIXED_MAX_TOKENS,
            task="association",
            dataset_name=dataset_name,
            identified_classes=GOLD_STANDARD_CLASS[dataset_name]
        )

        # Format output path and save interaction logs
        output_filename = f"R{round_num+r}.txt"
        output_path = output_dir / output_filename

        with open(output_path, "w", encoding="utf-8") as out_file:
            for msg in conversation:
                out_file.write(f"{msg['role'].upper()} :\n\n{msg['content']}\n\n")

        print(f"✅ Round {r + 1} completed for {dataset_name}")

    print("🎉 All rounds completed.")


if __name__ == "__main__":
    main()
