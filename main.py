import os
from dotenv import load_dotenv

load_dotenv()

from bedrock_agentcore.runtime import BedrockAgentCoreApp
from bedrock_agentcore.memory.integrations.strands.config import AgentCoreMemoryConfig
from bedrock_agentcore.memory.integrations.strands.session_manager import AgentCoreMemorySessionManager
from agent.cloud import create_agent

app = BedrockAgentCoreApp()


@app.entrypoint
def invoke(payload):
    user_message = payload.get("prompt", "")
    session_id = payload.get("sessionId", "default-session")
    actor_id = payload.get("actorId", "default-user")

    memory_id = os.environ.get("BEDROCK_AGENTCORE_MEMORY_ID")
    region = os.environ.get("AWS_REGION", "us-west-2")

    if memory_id:
        config = AgentCoreMemoryConfig(
            memory_id=memory_id,
            session_id=session_id,
            actor_id=actor_id,
        )
        with AgentCoreMemorySessionManager(
            agentcore_memory_config=config,
            region_name=region,
        ) as session_manager:
            agent = create_agent(session_manager=session_manager)
            result = agent(user_message)
    else:
        agent = create_agent()
        result = agent(user_message)

    return {"response": str(result)}


if __name__ == "__main__":
    app.run()
