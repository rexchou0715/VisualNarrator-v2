# src/class_assoc_pipeline/pipelines/class_pipeline/extractors.py

import re

def extract_gpt_o1_content(content: str, exp_round: int) -> str:
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
    # print(f"[Round {exp_round}] After header_pattern2 extraction, content begins with:\n{content[:300]}\n")
    print(f"[Round {exp_round}]")

    header_pattern3 = r'final\s+(refined list of class candidates|list of class candidates|list of classes|list|class(?:es)?)[\s:]*'
    header_match3 = re.search(header_pattern3, content, re.IGNORECASE)
    if exp_round == 1:
        print(f"[Round {exp_round}] header_match3 (direct matching): {header_match3}")
    if not header_match3:
        print(f"⚠️ Direct matching for header_pattern3 failed in round {exp_round}.")
        print(f"[Round {exp_round}] Content for header_pattern3 matching:\n{content[:300]}\n")
        fallback_pattern = r"(?:.*\d+\.\d+)?\s*Numbered Format.*"
        header_match3 = re.search(fallback_pattern, content)
        if header_match3:
            print(f"🔍 Found a line matching 'Numbered Format' pattern in round {exp_round}.")
        else:
            print(f"⚠️ Warning: Could not locate the start of the second header in round {exp_round}\n{content[:300]}\n .")
            return ""
    else:
        print(f"[Round {exp_round}] Found header_pattern3 match at index: {header_match3.start()} to {header_match3.end()}")
    
    extracted = content[header_match3.end():].strip()
    # print(f"[Round {exp_round}] Extracted content begins with:\n{extracted[:300]}\n")
    print(f"[Round {exp_round}]")
    return extracted


def extract_llama3_8b_content(content: str, exp_round: int) -> str:
    header_pattern = r'Assistant :'
    header_match = list(re.finditer(header_pattern, content, re.IGNORECASE))
    if len(header_match) < 3:
        print("⚠️ Could not find three occurrences of Assistant")
        return ""
    start_index = header_match[2]
    content = content[start_index.end():].strip()
    header_pattern2 = r'(Here is the final list of classes:|#+\s*Final Class List|#+\s*Refined List of Classes|Here is the final class list in a structured format:)'
    header_match2 = re.search(header_pattern2, content, re.IGNORECASE)
    if not header_match2:
        print(f"⚠️ Warning: Could not locate the secondary header in round {exp_round} using Llama pattern.")
        return ""
    return content[header_match2.end():].strip()

def extract_qwen14b_content(content: str, exp_round: int) -> str:
    header_pattern = r'Assistant :'
    header_match = list(re.finditer(header_pattern, content, re.IGNORECASE))
    if len(header_match) < 3:
        print("⚠️ Could not find three occurrences of Assistant")
        return ""
    start_index = header_match[2]
    content = content[start_index.end():].strip()

    header_pattern2 = r"</think>"
    header_match2 = re.search(header_pattern2, content, re.IGNORECASE)
    if not header_match2:
        print(f"⚠️ Warning: Could not locate the </think> header using Qwen pattern in round {exp_round}.")
        return ""
    content = content[header_match2.end():].strip()

    header_pattern3 = r'(Here is the final list of classes:|#+\s*Final Class List|#+\s*Refined List of Classes)'
    
    header_match3 = re.search(header_pattern3, content, re.IGNORECASE)
    if not header_match3:
        print(f"⚠️ Warning: Could not locate the third header in round {exp_round} using Qwen pattern.")
        return ""
    return content[header_match3.end():].strip()

EXTRACTORS = {
    "gpt-o1": extract_gpt_o1_content,
    "llama3-8b": extract_llama3_8b_content,
    "qwen-14b": extract_qwen14b_content,
}

def extract_content_by_model(content: str, model: str, exp_round: int) -> str:
    fn = EXTRACTORS.get(model.lower())
    if not fn:
        print(f"⚠️ Unsupported model '{model}'")
        return content
    return fn(content, exp_round)
