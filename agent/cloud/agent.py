import os
from strands import Agent
from strands.models import BedrockModel
from tools import get_customer, get_order, cancel_order
from utils.shared import SYSTEM_PROMPT


def create_agent() -> Agent:
    model_id = os.environ["CLOUD_MODEL_NAME"]
    region = os.environ.get("AWS_REGION", "us-east-1")
    model = BedrockModel(model_id=model_id, region_name=region)
    return Agent(
        model=model,
        system_prompt=SYSTEM_PROMPT,
        tools=[get_customer, get_order, cancel_order],
    )
