import os
from strands import Agent
from strands.models.ollama import OllamaModel
from tools import get_customer, get_order, cancel_order
from utils.shared import SYSTEM_PROMPT


def create_agent() -> Agent:
    model_id = os.environ.get("LOCAL_MODEL_NAME", "qwen2.5:7b-instruct")
    model = OllamaModel(host="http://localhost:11434", model_id=model_id)
    return Agent(
        model=model,
        system_prompt=SYSTEM_PROMPT,
        tools=[get_customer, get_order, cancel_order],
    )
