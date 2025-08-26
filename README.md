# Visual Narrator 2.0

Transform user stories into domain-model elements—**classes** and **associations**—then evaluate extraction quality against a gold-standard reference.
 
---

## Setup & Usage

Setup & Usage

Before running the system, make sure you complete the following steps:

1. Install dependencies
```bash
pip install -r requirements.txt
```
2. Set your API key: Open **src/class_assoc_pipeline/api.py** and place your OpenAI API key inside.

3. Add src to Python path

```bash
export PYTHONPATH=src
```

Once these steps are done, you should be able to run the generation and evaluation commands without issues.

## Modules

| Module | Purpose |
| ------ | ------- |
| **Generation** | Prompt an LLM/SLM to extract classes **or** associations from user stories. |
| **Evaluation** | Parse the generated conversation, extract the predicted elements, and compute Precision, Recall, and F-measure. |

> **Note** This system **does not** produce visualized UML class diagrams; it outputs plain lists of classes or associations.

---

## Generation

### Inputs

* `--input` Path to a user-story text file (`.txt`)
* `--model` One of `Llama3-8B`, `Qwen-14B`, `GPT-o1`
* `--rounds` Number of repetition rounds (1-5, default = 1)

### Output

* Conversation log per round (`R1.txt`, `R2.txt`, …)

### Example commands

```bash
# Class extraction (2 rounds)
python src/class_assoc_pipeline/pipelines/class_pipeline/run_class_generation.py \
  --input data/user_stories/ticket.txt \
  --model Llama3-8B \
  --rounds 2

# Association extraction (3 rounds)
python src/class_assoc_pipeline/pipelines/association_pipeline/run_association_generation.py \
  --input data/user_stories/sports.txt \
  --model Llama3-8B \
  --rounds 3
```

---

## Evaluation

There are two modes in this module, including `extraction` and `evaluation`.

### Modes
* `extraction` — extract predicted elements into convenient files
* `evaluation` — compare predictions with gold standard and compute metrics
* `all` — run both

### Inputs

* For `extraction`: folder containing conversation logs 
* For `evaluation`: Excel file with extracted elements 

### Output
* For `extraction`: folder containing conversation logs 
    * Extracted elements (extracted_class_round{n}.txt) and combined Excel workbook (extracted_class.xlsx/ extracted_association.xlsx)
* For `evaluation`: Excel file with extracted elements 
    * Evaluation metrics workbook (evaluation_results.xlsx)
    * Experiment log (experiment_log.txt)
    * False-positive list (false_positive.xlsx)

### Example commands

```bash
# Run extraction + evaluation for classes
python src/class_assoc_pipeline/pipelines/class_pipeline/run_class_pipeline.py \
  --input data/raw/class/Llama3-8B/ticket \
  --mode all

# Run extraction only for associations
python src/class_assoc_pipeline/pipelines/association_pipeline/run_association_pipeline.py \
  --input data/raw/association/Llama3-8B/ticket \
  --mode extraction
```

---

### ⚠️ Known Issue: Model Output Formatting

It may occasionally take time to get valid outputs from all three models.  
If the evaluation module encounters issues during extraction, it's usually because the model outputs don't match the expected format. In such cases, manual transformation may be required to ensure compatibility with the extraction step.

---

## Related

- [Visual Narrator](https://github.com/MarcelRobeer/VisualNarrator) — The original system by Marcel Robeer that this project builds upon.
