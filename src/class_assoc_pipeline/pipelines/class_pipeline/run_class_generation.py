# run_class_generation.py

import argparse
from pathlib import Path
from datetime import datetime
import time

from class_assoc_pipeline.utils.prompts import INSTRUCTIONS_CLASS_SLM, INSTRUCTIONS_LLM
from class_assoc_pipeline.utils.model_client  import init_client
from class_assoc_pipeline.utils.generation_utils import process_steps, get_next_round_number

FIXED_MAX_TOKENS = 3000

def parse_args():
    parser = argparse.ArgumentParser(description="Run class identification")
    parser.add_argument('--input', type=str, required=True, help='Input file path')
    parser.add_argument('--model', type=str, required=True, help='Model name')
    # parser.add_argument('--output', type=str, required=True, help='Output folder name')
    parser.add_argument('--rounds', type=int, default=1, help='Number of rounds (max=5)')
    args = parser.parse_args()

    if args.rounds > 5:
        parser.error("Maximum number of rounds is 5.")

    valid_models = ["llama3-8b", "qwen-14b", "gpt-o1"]

    if args.model.lower() not in valid_models:
        parser.error(f"Invalid model name. Please choose from: {', '.join(valid_models)}")

    return args

def main():
    args = parse_args()
    client = init_client()
    input_path = Path(args.input)
    dataset_name = input_path.stem
    output_dir = Path(f"/Users/rexchou/Documents/GitHub/thesis_github/data/raw/class_test/{args.model}/{dataset_name}")
    output_dir.mkdir(parents=True, exist_ok=True)

    with open(input_path, "r", encoding="utf-8") as f:
        user_stories = f.read()

    # total_round_num = get_experiment_round()

    round_num = get_next_round_number(output_dir)
    print(f"🔁 Experiment Round ID: {round_num}")

    if args.model.lower() == "gpt-o1":
        instruction = INSTRUCTIONS_LLM
    else:
        instruction = INSTRUCTIONS_CLASS_SLM
    
    print(args.model.lower())
    if args.model.lower() == "llama3-8b":
        model="meta-llama/Meta-Llama-3-8B-Instruct"
    elif args.model.lower() == "qwen-14b":
        model="..."
    else:
        model="..."

    for r in range(args.rounds):
        conversation, responses = process_steps(
            instructions=instruction,
            user_text=user_stories,
            client=client,
            model=model,
            max_tokens=FIXED_MAX_TOKENS,
            task="class",
            dataset_name=dataset_name
        )

        # output_filename = f"{now.date()}_{args.model}_{dataset_name}_class_identification_round{round_num + r}.txt"
        output_filename = f"R{round_num+r}.txt"
        output_path = output_dir / output_filename

        with open(output_path, "w", encoding="utf-8") as out_file:
            for msg in conversation:
                out_file.write(f"{msg['role'].upper()} :\n\n{msg['content']}\n\n")
        print(f"✅ Round {r + 1} completed for {dataset_name}")
        time.sleep(1)

    print("🎉 All rounds completed.")

if __name__ == "__main__":
    main()
