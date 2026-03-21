import os
from strands.models import BedrockModel
from strands.models.ollama import OllamaModel


def create_model():
    mode = os.environ.get("AGENT_MODE", "local").lower()

    if mode == "cloud":
        model_id = os.environ["CLOUD_MODEL_NAME"]
        region = os.environ.get("AWS_REGION", "us-east-1")
        return BedrockModel(model_id=model_id, region_name=region)

    if mode == "local":
        model_id = os.environ.get("LOCAL_MODEL_NAME", "DeepSeek-R1:8b")
        return OllamaModel(host="http://localhost:11434", model_id=model_id)

    raise ValueError(f"Unknown AGENT_MODE: '{mode}'. Must be 'local' or 'cloud'.")
