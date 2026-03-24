import os
from dotenv import load_dotenv
from bedrock_agentcore.memory import MemoryClient

load_dotenv()

client = MemoryClient(region_name=os.environ.get("AWS_REGION", "us-west-2"))
memory = client.create_memory(
    name="OrderCancellationAgentMemory",
    description="Short-term memory for order cancellation agent sessions",
)
memory_id = memory.get("id")
print(f"Created memory with ID: {memory_id}")
print(f"Add to .env:  AGENTCORE_MEMORY_ID={memory_id}")
