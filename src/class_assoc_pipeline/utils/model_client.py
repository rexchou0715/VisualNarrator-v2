from openai import OpenAI
from class_assoc_pipeline.api import API_1

def init_client(api_key=None, base_url=None):
    return OpenAI(
        api_key=API_1,
        base_url="https://router.huggingface.co/featherless-ai/v1"
    )
