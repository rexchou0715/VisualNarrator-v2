from openai import OpenAI
from class_assoc_pipeline.api import API_HF, API_OpenAI

def init_client(api_key=None, base_url=None, model_name=None):
    if model_name.lower() == "gpt-o1":
        return OpenAI(
            api_key=API_OpenAI,
        )
    else:
        return OpenAI(
            api_key=API_HF,
            base_url="https://router.huggingface.co/featherless-ai/v1"
        )
