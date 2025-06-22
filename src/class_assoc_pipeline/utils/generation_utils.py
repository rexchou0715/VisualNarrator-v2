from pathlib import Path

def get_next_round_number(output_dir, pattern="*.txt"):
    output_path = Path(output_dir)
    if not output_path.exists():
        return 1  # First round if the folder doesn't exist yet

    # Count matching files (e.g., output text files)
    existing_files = list(output_path.glob(pattern))
    return len(existing_files) + 1

def process_steps(instructions, user_text, client, model, max_tokens, task, identified_classes=None, dataset_name=None):
    conversation = []
    responses = []

    conversation.append({"role": "system", "content": instructions[0]})
    if task == "class":
        conversation.append({"role": "user", "content": user_text})
    else:
        conversation.append({
            "role": "user", 
            "content": f""" Here is the list of user stories:
            {user_text}
            
            Here is the list of classes identified from these user stories. Only create associations based on the classes shown in this list. Do not invent any other class.
            {identified_classes}
            """
        })


    # Step 1 API call
    try:
        response = client.chat.completions.create(
            model=model,
            messages=conversation,
            max_tokens=max_tokens
        )
    except Exception as e:
        print(f"[Error] Step 1: {e}")
        return conversation, responses

    response_message = response.choices[0].message
    conversation.append({"role": response_message.role, "content": response_message.content})
    responses.append(response)
    if dataset_name:
        print(f"{dataset_name} Step 1 completed")

    # Process subsequent steps (starting from Step 2)
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
            break
        response_message = response.choices[0].message
        conversation.append({"role": response_message.role, "content": response_message.content})
        responses.append(response)
        if dataset_name:
            print(f"{dataset_name} Step {step} completed")

    return conversation, responses
