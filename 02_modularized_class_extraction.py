import re
import os
import pandas as pd

##############################
# Text Processing Functions
##############################
def clean_class_name(content: str) -> str:
    """
    Removes Markdown-style bold symbols (e.g., **Class**) and leading asterisks,
    then trims any extra surrounding whitespace.

    :param content: A string potentially containing bold markers (*) and extra spaces.
                    Example: "**Class Name**"
    :return: A cleaned string with formatting characters removed.
             Example return: "Class Name"
    """
    # content = re.sub(r'^\*+\s*', '', content)  # Remove leading '*'
    content = re.sub(r'\*{1,2}(.*?)\*{1,2}', r'\1', content) # Remove **bold** markers
    return content.strip()


def format_optional_line(content: str) -> str:
    """
    Cleans a class line by removing any trailing explanations after a dash ("-"),
    and normalizes the placement of the '(optional)' marker by moving it to the front if present.

    For example:
        Input: "Class A (optional) - required in some cases"
        Output: "(optional) Class A"

    :param content: A string potentially containing a dash-separated explanation and an '(optional)' tag.
    :return: A cleaned string with the optional marker (if any) at the beginning and explanation removed.
    """
    if re.search(r'\(optional\)', content, re.IGNORECASE):

        content_wo_optional = re.sub(r'\(optional\)', '', content, flags=re.IGNORECASE).strip()
        return f"(optional) {content_wo_optional}"
    return f"(optional) {content.strip()}"


def remove_trailing_notes(content_line: str) -> str:
    """
    Remove explanations or formatting characters such as ':', '-', and '`' from a content line.

    :param content_line: A raw line of text containing a potential class name and trailing explanations.
    :return: A cleaned version of the class name with trailing notes and special characters removed.
    """
    if ':' in content_line:
        content_line = content_line.split(':', 1)[0].strip()
    if '-' in content_line:
        content_line = content_line.split('-', 1)[0].strip()
    if '`' in content_line:
        content_line = content_line.replace('`', '')
    return content_line.strip()


def split_mandatory_entities(text: str):
    """
    Splits a class description string into individual class entities.

    The function performs the following steps:
      1. Splits the text using the word 'and' as a separator.
      2. For each part, trims any content after a parenthesis '(' or slash '/'.
      3. Splits the remaining part by commas to extract individual entities.
      4. Strips whitespace from each entity and filters out empty entries.

    Example:
        Input: "Class A and Class B, Class C / alternative (optional)"
        Output: ["Class A", "Class B", "Class C"]

    :param text: A string containing one or more class entities, possibly joined by 'and', '/', '(', or commas.
    :return: A list of cleaned class entity strings.
    """
    parts = re.split(r'\s+and\s+', text)
    result = []
    for part in parts:
        part = re.split(r'[\(/]', part)[0]
        subparts = [x.strip() for x in part.split(',')]
        result.extend([s for s in subparts if s])
    return result

##############################
# Data Management Function
##############################

def deduplicate_list(items: list[str]) -> list[str]:
    """
    Removes duplicate strings from a list while preserving the original order.
    Deduplication is case-insensitive, meaning 'Class A' and 'class a' are treated as duplicates.

    :param items: A list of strings, potentially containing duplicates.
    :return: A new list with duplicates removed, preserving the order of first appearance.
    """

    seen = set()
    deduped = []
    for item in items:
        item_lower = item.lower()  
        if item_lower not in seen:
            seen.add(item_lower)
            deduped.append(item)
    return deduped

######################################
# Header Extraction 
######################################
def extract_gpt_o1_content(content: str, exp_round: int) -> str:
    """
    Extract target content from GPT-o1 logs using structured header matching.

    :param content: Full log content to be processed.
    :param exp_round: The current experiment round, which may affect header structure or parsing logic.
    :return: Extracted section of the log corresponding to the GPT-o1 model.
    """
    header_pattern = r'GPT-o1'
    header_match = list(re.finditer(header_pattern, content, re.IGNORECASE))
    if len(header_match) < 2:
        print("⚠️ Could not find the second occurrence of GPT-o1")
        return ""
    second_match = header_match[1]
    content = content[second_match.end():].strip()

    header_pattern2 = r"step\s*3\s*:\s*.*?(final\s+(refined\s+)?(class(?:es)?|list(?:\s+of\s+classes)?|list of class candidates)).*?"
    header_match2 = re.search(header_pattern2, content, re.IGNORECASE)
    if not header_match2:
        print(f"⚠️ Warning: Could not locate the start of the first header in round {exp_round}.")
        return ""
    content = content[header_match2.end():].strip()
    print(f"[Round {exp_round}] After header_pattern2 extraction, content begins with:\n{content[:300]}\n")

    header_pattern3 = r'final\s+(refined list of class candidates|list of class candidates|list of classes|list|class(?:es)?)[\s:]*'
    header_match3 = re.search(header_pattern3, content, re.IGNORECASE)
    if exp_round == 1:
        print(f"[Round {exp_round}] header_match3 (direct matching): {header_match3}")
    if not header_match3:
        print(f"⚠️ Direct matching for header_pattern3 failed in round {exp_round}.")
        print(f"[Round {exp_round}] Content for header_pattern3 matching:\n{content[:300]}\n")
        fallback_pattern = r"(?:.*\d+\.\d+)? .*Numbered Format.*"
        header_match3 = re.search(fallback_pattern, content)
        if header_match3:
            print(f"🔍 Found a line matching 'Numbered Format' pattern in round {exp_round}.")
        else:
            print(f"⚠️ Warning: Could not locate the start of the second header in round {exp_round}.")
            return ""
    else:
        print(f"[Round {exp_round}] Found header_pattern3 match at index: {header_match3.start()} to {header_match3.end()}")
    
    extracted = content[header_match3.end():].strip()
    print(f"[Round {exp_round}] Extracted content begins with:\n{extracted[:300]}\n")
    return extracted


def extract_llama8b_content(content: str, exp_round: int) -> str:
    """
    Header extraction logic for Llama 3 8B model
    """
    # header_pattern = r'Step\s*3:.*?Final Class List.*?'
    # header_match = re.search(header_pattern, content, re.IGNORECASE)
    # if not header_match:
    #     print(f"⚠️ Warning: Could not locate the header using Llama 3 8B pattern in round {exp_round}.")
    #     return ""
    # content = content[header_match.end():].strip()

    header_pattern = r'Assistant :'
    header_match = list(re.finditer(header_pattern, content, re.IGNORECASE))
    if len(header_match) < 3:
        print("⚠️ Could not find three occurrences of Assistant")
        return ""
    start_index = header_match[2]
    content = content[start_index.end():].strip()
    header_pattern2 = r'(Here is the final list of classes:|#+\s*Final Class List|#+\s*Refined List of Classes|Here is the final class list in a structured format:)'
    # header_pattern2 = r'[#\*]*\s*(Step\s*3.*|' \
    #                r'Final Answer:\s*Refined List of Classes|' \
    #                r'Refined List of Classes|' \
    #                r'Final Class List|' \
    #                r'Final Refined Class List|' \
    #                r'Here\s+is\s+the\s+final\s+list\s+of\s+(class candidates|classes)(\s+in\s+.*format)?)' \
    #                r'\s*[:\*#]*' \
    #                r'Here is the final class list in a structured format:'
    header_match2 = re.search(header_pattern2, content, re.IGNORECASE)
    if not header_match2:
        print(f"⚠️ Warning: Could not locate the secondary header in round {exp_round} using Llama pattern.")
        return ""
    return content[header_match2.end():].strip()


def extract_qwen_content(content: str, exp_round: int) -> str:
    """
    Header extraction logic for Qwen model
    """

    header_pattern = r'Assistant :'
    header_match = list(re.finditer(header_pattern, content, re.IGNORECASE))
    if len(header_match) < 3:
        print("⚠️ Could not find three occurrences of Assistant")
        return ""
    start_index = header_match[2]
    content = content[start_index.end():].strip()

    # header_pattern = r'Step\s*3:\s*Present\s*the\s*Final\s*Class\s*List'
    # header_match = re.search(header_pattern, content, re.IGNORECASE)
    # if not header_match:
    #     print(f"⚠️ Warning: Could not locate the header using Qwen pattern in round {exp_round}.")
    #     return ""
    # content = content[header_match.end():].strip()

    header_pattern2 = r"</think>"
    header_match2 = re.search(header_pattern2, content, re.IGNORECASE)
    if not header_match2:
        print(f"⚠️ Warning: Could not locate the </think> header using Qwen pattern in round {exp_round}.")
        return ""
    content = content[header_match2.end():].strip()

    # header_pattern3 = r'[#\*]*\s*(Step\s*3.*|' \
    #                r'Final Answer:\s*Refined List of Classes|' \
    #                r'Refined List of Classes|' \
    #                r'Final Class List|' \
    #                r'Final Refined Class List|' \
    #                r'Here\s+is\s+the\s+final\s+list\s+of\s+(class candidates|classes)(\s+in\s+.*format)?)' \
    #                r'\s*[:\*#]*'
    header_pattern3 = r'(Here is the final list of classes:|#+\s*Final Class List|#+\s*Refined List of Classes)'
    # header_pattern3 = r'(Here is the final list of classes:|#+\s*Final Class List:?(\s*#+)?|#+\s*Refined List of Classes)'

    header_match3 = re.search(header_pattern3, content, re.IGNORECASE)
    if not header_match3:
        print(f"⚠️ Warning: Could not locate the third header in round {exp_round} using Qwen pattern.")
        return ""
    return content[header_match3.end():].strip()


def extract_content_by_model(content: str, model: str, exp_round: int) -> str:
    """
    Route content extraction to the corresponding model-specific function.

    :param content: Full text content to be processed.
    :param model: Name of the model to use for extraction logic.
    :param exp_round: The current experiment round (may influence extraction rules).
    :return: Extracted section of the content based on the model and round.
    """
    model = model.lower()
    if model == "gpt-o1":
        return extract_gpt_o1_content(content, exp_round)
    elif model == "llama 3 8b":
        return extract_llama8b_content(content, exp_round)
    elif model == "qwen14b":
        return extract_qwen_content(content, exp_round)
    else:
        print(f"⚠️ Warning: Unsupported model '{model}'. Returning original content.")
        return content


######################################
# File Processing Logic
######################################
def process_file(input_file: str, output_file: str, model: str, exp_round: int, dataset: str) -> None:
    """
    Process a single file by extracting model-specific content and saving structured results.

    Steps:
      1. Read content and extract section based on model.
      2. Parse and clean mandatory and optional classes.
      3. Save results to text and Excel files.

    :param input_file: Path to the input file to be processed.
    :param output_file: Path where the output files will be saved.
    :param model: Name of the model to extract sections for (e.g., 'GPT-o1', 'Llama 3 8B', 'Qwen14B').
    :param exp_round: Experiment round number.
    :param dataset: Name of the dataset being processed.
    :return: None
    """
    try:
        with open(input_file, "r", encoding="utf-8") as f:
            content = f.read()
            # content = content.replace("**", "")
    except FileNotFoundError:
        print(f"❌ Error: The file '{input_file}' was not found.")
        return
    
    content_after_header = extract_content_by_model(content, model, exp_round)
    if not content_after_header:
        print(f"⚠️ Warning: No content extracted for round {exp_round}.")
        return
    
    skip_keywords = [
        '**Class List:**', 
        '**Final Class List:**', 
        '[Class 1, Class 2, Class 3,...]', 
        'List:**',
        "**Refined List of Class Candidates:**",
        "**Rationale:**",
        "**Final Class List**",
        '**List**',
        'List**',
        '**Class List**'
        '**Rationale**',
        'Rationale: '
        '**Domain Entities:**',
        'Removed',
        'removed',
        'redundant',
        'irrelevant',
        'vague']

    lines = content_after_header.splitlines()
    found = False
    for i, line in enumerate(lines):
        if re.search(r'\d|\*', line):
            if any(keyword in line for keyword in [
                    '**Class List:**', 
                    '**Final Class List:**', 
                    '[Class 1, Class 2, Class 3,...]', 
                    'List:**',
                    "**Refined List of Class Candidates:**",
                    "**Rationale:**",
                    "**Final Class List**",
                    '**List**',
                    'List**',
                    '**Class List**'
                    '**Rationale**',
                    'Rationale: ']) or re.match(r'^\[.+\]$', line.strip()):
                continue
            lines = [line for line in lines if line.strip()]
            found = True
            break
    if not found:
        print(f"⚠️ No line matched number or * in round {exp_round}")
        return

    mandatory_class = []
    optional_class = []
    reading_mandatory = True
    for line in lines:
        line = line.strip()
        if any(kw in line for kw in skip_keywords):
            continue
        if reading_mandatory and line == '':
            reading_mandatory = False
            continue
        match = re.match(r'^(?:\d+\.\s+|\*\s+)(.*)', line)
        if not match:
            continue
        content_line = match.group(1)
        content_lower = content_line.lower()
        is_optional = False
        if '(optional)' in content_lower:
            is_optional = True
        content_line = remove_trailing_notes(content_line)
        if reading_mandatory:
            if is_optional:
            # if '(optional)' in content_lower:
                # content_line = remove_trailing_notes(content_line)
                cleaned = clean_class_name(content_line)
                optional_class.append(format_optional_line(cleaned))
            elif not any(re.search(rf'\b{re.escape(kw)}\b', content_lower) for kw in 
                         ['rationale', 'marked', 'reason', 'ensured', 'incorporated', 'conclusion']):
                # content_line = remove_trailing_notes(content_line)
                cleaned = clean_class_name(content_line)
                mandatory_class.append(cleaned)
        else:
            if '(optional)' in content_lower:
                content_line = remove_trailing_notes(content_line)
                cleaned = clean_class_name(content_line)
                optional_class.append(format_optional_line(cleaned))
    
    # clean_mandatory_class = []
    # for item in mandatory_class:
    #     clean_mandatory_class.extend(split_mandatory_entities(item))
    
    # combined = clean_mandatory_class + optional_class

    mandatory_class = deduplicate_list(mandatory_class)
    optional_class = deduplicate_list(optional_class)
    combined = mandatory_class + optional_class
    notes = [""] * len(combined)
    df = pd.DataFrame({"class": combined, "note": notes})
    df["class"] = df["class"].astype(str)
    df = df[~df['class'].str.lower().duplicated()].reset_index(drop=True)
    
    os.makedirs(os.path.dirname(output_file), exist_ok=True)
    with open(output_file, "w", encoding="utf-8") as out:
        out.write("\n".join(lines) + "\n\n" + "\n".join(mandatory_class) + "\n" + "\n".join(optional_class))
    
    output_dir = os.path.dirname(output_file)
    report_path = os.path.join(output_dir, f"class_report_{dataset}.xlsx")
    sheet_name = f"Round{exp_round}"
    if os.path.exists(report_path):
        with pd.ExcelWriter(report_path, engine="openpyxl", mode="a", if_sheet_exists="replace") as writer:
            df.to_excel(writer, index=False, sheet_name=sheet_name)
    else:
        with pd.ExcelWriter(report_path, engine="openpyxl") as writer:
            df.to_excel(writer, index=False, sheet_name=sheet_name)
    
    print(f"Processed round {exp_round} for model {model} and saved outputs.")


def process_dataset(model: str, dataset: str, rounds: int = 5) -> None:
    """
    Process multiple rounds of a dataset for a given model

    :param model: The name or identifier of the model (e.g., 'GPT-o1', 'Llama 3 8B', 'Qwen14B') to use.
    :param dataset: The dataset to process.
    :param rounds: Number of times to run the process (default is 5).
    :return: None

    """
    print(f"Processing: {dataset}")
    for exp_round in range(1, rounds + 1):
        if model == "Llama 3 8B":
            input_file = f"{model}/Class_Experiment/{dataset}/Log in Excel/R{exp_round}.txt"
        else:
            input_file = f"{model}/Class_Experiment/{dataset}/R{exp_round}.txt"
        output_file = f"{model}/Extracted_Class_Experiment/{dataset}/refined_class_round{exp_round}.txt"
        process_file(input_file, output_file, model, exp_round, dataset)


######################################
# Main Execution
######################################
if __name__ == "__main__":
    MODEL = "Llama 3 8B"
    experiment_rounds = 10
    # for MODEL in ["GPT-o1", "Llama 3 8B", "Qwen14B"]:
    for dataset in os.listdir(f"{MODEL}/Class_Experiment"):
    # for dataset in ["ticket"]:
        if dataset == ".DS_Store":
            continue
        if MODEL == "GPT-o1":
            experiment_rounds = 5
        process_dataset(MODEL, dataset, rounds=experiment_rounds)

