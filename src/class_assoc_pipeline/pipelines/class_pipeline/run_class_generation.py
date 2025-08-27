import argparse
from pathlib import Path
from datetime import datetime
import time

from class_assoc_pipeline.utils.prompts import INSTRUCTIONS_CLASS_SLM, INSTRUCTIONS_CLASS_LLM
from class_assoc_pipeline.utils.model_client  import init_client
from class_assoc_pipeline.utils.generation_utils import process_steps, get_next_round_number

FIXED_MAX_TOKENS = 3000  # Cap on token size to avoid runaway completions

def parse_args():
    """
    Handle and validate command-line arguments.
    """
    parser = argparse.ArgumentParser(description="Run class identification")
    parser.add_argument('--input', type=str, required=True, help='Input file path')
    parser.add_argument('--model', type=str, required=True, help='Model name')
    parser.add_argument('--rounds', type=int, default=1, help='Number of rounds (suggested max=5)')
    args = parser.parse_args()

    # Ensure model is supported
    valid_models = ["llama3-8b", "qwen-14b", "gpt-o1"]
    if args.model.lower() not in valid_models:
        parser.error(f"Invalid model name. Please choose from: {', '.join(valid_models)}")

    return args

def main():
    # --- Parse and validate input arguments ---
    args = parse_args()

    # --- Initialize model client (e.g., OpenAI, HuggingFace) ---
    client = init_client(model_name=args.model.lower())
    input_path = Path(args.input)
    dataset_name = input_path.stem  # Get filename without extension
    output_dir = Path(f"data/raw/class/{args.model}/{dataset_name}")
    output_dir.mkdir(parents=True, exist_ok=True)

    # --- Load user stories from file ---
    with open(input_path, "r", encoding="utf-8") as f:
        user_stories = f.read()

    # --- Determine next available round number ---
    round_num = get_next_round_number(output_dir)
    print(f"🔁 Experiment Round ID: {round_num}")

    # --- Select prompt instruction based on model type ---
    if args.model.lower() == "gpt-o1":
        instruction = INSTRUCTIONS_CLASS_LLM
    else:
        instruction = INSTRUCTIONS_CLASS_SLM

    # --- Map CLI model name to internal model ID (for client) ---
    if args.model.lower() == "llama3-8b":
        model = "meta-llama/Meta-Llama-3-8B-Instruct:novita"
    elif args.model.lower() == "qwen-14b":
        model = "deepseek-ai/DeepSeek-R1-Distill-Qwen-14B:novita"
    else:
        model = "o1-2024-12-17"

    # --- Run class identification for N rounds ---
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
        # --- Format and save response to file ---
        output_filename = f"R{round_num + r}.txt"
        output_path = output_dir / output_filename

        with open(output_path, "w", encoding="utf-8") as out_file:
            for msg in conversation:
                out_file.write(f"{msg['role'].upper()} :\n\n{msg['content']}\n\n")

        print(f"✅ Round {r + 1} completed for {dataset_name}. The data is saved to {output_path}")
        time.sleep(1)  # Prevent API flooding

    print("🎉 All rounds completed.")

if __name__ == "__main__":
    main()
