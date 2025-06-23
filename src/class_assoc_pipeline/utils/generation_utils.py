from pathlib import Path

# Determine the next available round number by counting existing output files
def get_next_round_number(output_dir, pattern="*.txt"):
    output_path = Path(output_dir)
    if not output_path.exists():
        return 1  # First round if the folder doesn't exist yet

    # Count matching files (e.g., output text files)
    existing_files = list(output_path.glob(pattern))
    return len(existing_files) + 1

# Execute a multi-step prompt process with a given model client
def process_steps(instructions, user_text, client, model, max_tokens, task, identified_classes=None, dataset_name=None):
    conversation = []
    responses = []

    # Step 0: Add initial system prompt
    conversation.append({"role": "system", "content": instructions[0]})

    # Step 1: Add first user prompt based on task type
    if task == "class":
        conversation.append({"role": "user", "content": user_text})
    else:
        # Include user stories and identified classes for association tasks
        conversation.append({
            "role": "user", 
            "content": f""" Here is the list of user stories:
            {user_text}
            
            Here is the list of classes identified from these user stories. Only create associations based on the classes shown in this list. Do not invent any other class.
            {identified_classes}
            """
        })

    # Step 1: Send conversation to model API
    try:
        response = client.chat.completions.create(
            model=model,
            messages=conversation,
            max_tokens=max_tokens
        )
    except Exception as e:
        print(f"[Error] Step 1: {e}")
        return conversation, responses

    # Append model's reply to conversation and response list
    response_message = response.choices[0].message
    conversation.append({"role": response_message.role, "content": response_message.content})
    responses.append(response)
    if dataset_name:
        print(f"{dataset_name} Step 1 completed")

    # Iterate over remaining instruction steps (Step 2+)
    for step, instruction in enumerate(instructions[1:], start=2):
        conversation.append({"role": "user", "content": instruction})
        try:
            response = client.chat.completions.create(
                model=model,
                messages=conversation,
                max_tokens=max_tokens
            )
        except Exception as e:
            print(f"[Error] Step {step}: {e}")
            break  # Stop further processing on failure

        # Append model's reply to conversation and response list
        response_message = response.choices[0].message
        conversation.append({"role": response_message.role, "content": response_message.content})
        responses.append(response)
        if dataset_name:
            print(f"{dataset_name} Step {step} completed")

    # Return full conversation and collected responses
    return conversation, responses
