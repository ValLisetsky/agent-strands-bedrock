# AgentCore Migration Plan

## Context

The project currently runs the cloud agent locally (calling AWS Bedrock directly from your machine via `main.py`). The goal is to deploy the cloud agent to **AWS AgentCore Runtime** — a serverless, containerized execution environment — with **short-term memory (STM)** so users can have multi-turn conversations across invocations within the same session. The existing `main.py` will be replaced by the AgentCore entry point. `local.py` and `agent/local/` are unaffected.

---

## Phase 1: AWS Account Preparation

### 1.1 Enable Bedrock Model Access

1. Go to **AWS Console → Amazon Bedrock → Model access** (in your target region, e.g. `us-west-2`)
2. Click **Manage model access**
3. Request access to your target model (e.g. `anthropic.claude-haiku-4-5-20251001-v1:0`)
4. Wait for access to be granted (usually instant for on-demand models)

### 1.2 Create IAM Role — AgentCore Runtime Execution Role

This role is assumed by the running AgentCore container.

**Create role** in IAM Console with:
- **Trust policy principal**: `bedrock-agentcore.amazonaws.com`
- **Name**: `AgentCoreRuntimeRole` (or similar)
- **Inline permissions**:

```json
{
  "Version": "2012-10-17",
  "Statement": [
    {
      "Sid": "BedrockInvoke",
      "Effect": "Allow",
      "Action": "bedrock:InvokeModel",
      "Resource": "arn:aws:bedrock:*::foundation-model/*"
    },
    {
      "Sid": "AgentCoreMemory",
      "Effect": "Allow",
      "Action": [
        "bedrock-agentcore:GetMemory",
        "bedrock-agentcore:PutMemory",
        "bedrock-agentcore:RetrieveMemoryRecords",
        "bedrock-agentcore:IngestMemoryRecords",
        "bedrock-agentcore:ListMemoryRecords",
        "bedrock-agentcore:DeleteMemoryRecords"
      ],
      "Resource": "*"
    },
    {
      "Sid": "CloudWatchLogs",
      "Effect": "Allow",
      "Action": [
        "logs:CreateLogGroup",
        "logs:CreateLogStream",
        "logs:PutLogEvents"
      ],
      "Resource": "arn:aws:logs:*:*:*"
    }
  ]
}
```

> Save the role ARN — you will need it for deployment: `arn:aws:iam::<account-id>:role/AgentCoreRuntimeRole`

### 1.3 Ensure Developer Credentials Have Deployment Permissions

#### Setting Up Local AWS Credentials

The AWS CLI and SDKs (boto3, agentcore toolkit) read credentials from `~/.aws/credentials`. Set them up via the AWS CLI:

```bash
# Install AWS CLI if not already installed
pip install awscli

# Configure credentials interactively
aws configure
# Prompts for:
#   AWS Access Key ID:      <from IAM user → Security credentials → Access keys>
#   AWS Secret Access Key:  <same location>
#   Default region name:    us-west-2
#   Default output format:  json
```

This writes to `~/.aws/credentials` and `~/.aws/config`. Alternatively, set environment variables:

```bash
export AWS_ACCESS_KEY_ID=AKIA...
export AWS_SECRET_ACCESS_KEY=...
export AWS_REGION=us-west-2
```

Or add them to `.env` (already supported via `python-dotenv` in the project).

> The IAM user whose credentials you use here must have the permissions listed below attached (either directly or via a group/role).

#### Required Permissions for Deployment

Your local AWS credentials (used by `agentcore launch`) need:

```json
{
  "Version": "2012-10-17",
  "Statement": [
    {
      "Effect": "Allow",
      "Action": [
        "bedrock-agentcore:CreateAgentRuntime",
        "bedrock-agentcore:UpdateAgentRuntime",
        "bedrock-agentcore:GetAgentRuntime",
        "bedrock-agentcore:ListAgentRuntimes",
        "bedrock-agentcore:DeleteAgentRuntime",
        "bedrock-agentcore:CreateMemory",
        "bedrock-agentcore:GetMemory",
        "bedrock-agentcore:PutMemory",
        "bedrock-agentcore:RetrieveMemoryRecords",
        "bedrock-agentcore:IngestMemoryRecords",
        "bedrock-agentcore:ListMemoryRecords",
        "bedrock-agentcore:DeleteMemoryRecords"
      ],
      "Resource": "*"
    },
    {
      "Effect": "Allow",
      "Action": [
        "ecr:CreateRepository",
        "ecr:GetAuthorizationToken",
        "ecr:BatchCheckLayerAvailability",
        "ecr:PutImage",
        "ecr:InitiateLayerUpload",
        "ecr:UploadLayerPart",
        "ecr:CompleteLayerUpload",
        "ecr:DescribeRepositories"
      ],
      "Resource": "*"
    },
    {
      "Effect": "Allow",
      "Action": "iam:PassRole",
      "Resource": "arn:aws:iam::<account-id>:role/AgentCoreRuntimeRole"
    }
  ]
}
```

### 1.4 Create AgentCore Memory Resource (one-time setup)

Run `setup_memory.py` (created in Phase 2) once to provision the memory resource:

```bash
python setup_memory.py
# Outputs: Created memory with ID: <memory-id>
# Copy the ID into your .env
```

---

## Phase 2: Code Changes

### 2.1 File Changes Overview

| File | Change |
|------|--------|
| `requirements.txt` | Add `bedrock-agentcore[strands-agents]`, `bedrock-agentcore-starter-toolkit` |
| `.env.example` | Add `AGENTCORE_MEMORY_ID`, `AGENTCORE_RUNTIME_ROLE_ARN` |
| `agent/cloud/agent.py` | Accept optional `session_manager` parameter |
| `main.py` | Replace CLI loop with `BedrockAgentCoreApp` entry point |
| `setup_memory.py` | New: one-time script to create AgentCore Memory resource |

### 2.2 `requirements.txt`

```
strands-agents
strands-agents[ollama]
bedrock-agentcore[strands-agents]
bedrock-agentcore-starter-toolkit
boto3
python-dotenv
```

### 2.3 `.env.example` — add new variables

```
AGENTCORE_MEMORY_ID=              # from setup_memory.py output
AGENTCORE_RUNTIME_ROLE_ARN=       # arn:aws:iam::<account-id>:role/AgentCoreRuntimeRole
```

### 2.4 `agent/cloud/agent.py` — accept session_manager

```python
import os
from strands import Agent
from strands.models import BedrockModel
from tools import get_customer, get_order, cancel_order
from utils.shared import SYSTEM_PROMPT


def create_agent(session_manager=None) -> Agent:
    model_id = os.environ["CLOUD_MODEL_NAME"]
    region = os.environ.get("AWS_REGION", "us-west-2")
    model = BedrockModel(model_id=model_id, region_name=region)
    return Agent(
        model=model,
        system_prompt=SYSTEM_PROMPT,
        tools=[get_customer, get_order, cancel_order],
        session_manager=session_manager,
    )
```

### 2.5 `main.py` — replace with AgentCore entry point

```python
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

    memory_id = os.environ["AGENTCORE_MEMORY_ID"]
    region = os.environ.get("AWS_REGION", "us-west-2")

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
        return {"response": str(result)}


if __name__ == "__main__":
    app.run()
```

### 2.6 `setup_memory.py` — new one-time script

```python
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
```

### 2.7 Install packages in venv

```bash
python -m venv venv
venv\Scripts\activate          # Windows
pip install -r requirements.txt
```

---

## Phase 3: Deployment Steps

### 3.1 Configure the starter toolkit

```bash
agentcore configure --entrypoint main.py
```

When prompted, provide:
- **Execution role ARN**: value of `AGENTCORE_RUNTIME_ROLE_ARN` from `.env`
- **Region**: `us-west-2` (or your target region)

This creates `agentcore.yaml` in the project root.

### 3.2 (Optional) Local container test

```bash
agentcore launch --local
curl -X POST http://localhost:8080/invocations \
  -H "Content-Type: application/json" \
  -d '{"prompt": "Hi, I want to cancel an order", "sessionId": "test-session-1", "actorId": "user-1"}'
```

### 3.3 Deploy to AWS

```bash
agentcore launch
```

Starter toolkit will:
- Build a linux/arm64 container image
- Push to ECR
- Create the AgentCore Runtime
- Output the **Agent Runtime ARN**

### 3.4 Test deployed agent

```bash
agentcore invoke '{"prompt": "Hi, I want to cancel an order", "sessionId": "sess-001", "actorId": "user-001"}'
```

---

## Phase 4: Multi-turn Usage Example

The `sessionId` ties turns together. Use the same `sessionId` across calls within a conversation. STM loads prior turns from AgentCore Memory automatically.

```bash
# Turn 1 — greet
agentcore invoke '{"prompt":"Hi, I need to cancel an order","sessionId":"sess-abc","actorId":"user-42"}'
# Agent: "Hello! I'd be happy to help you cancel your order. Could you provide me with your email address?"

# Turn 2 — provide email
agentcore invoke '{"prompt":"john.smith@gmail.com","sessionId":"sess-abc","actorId":"user-42"}'
# Agent: "Thank you, John. Could you please provide your order ID?"

# Turn 3 — provide order
agentcore invoke '{"prompt":"Order 20001","sessionId":"sess-abc","actorId":"user-42"}'
# Agent: "Your order 20001 has been successfully cancelled."
```

The same pattern works via boto3:

```python
import boto3, json

client = boto3.client("bedrock-agentcore", region_name="us-west-2")
agent_runtime_arn = "arn:aws:bedrock-agentcore:us-west-2:<account>:agent-runtime/<id>"
session_id = "sess-abc"
actor_id = "user-42"

def chat(prompt: str):
    payload = json.dumps({"prompt": prompt, "sessionId": session_id, "actorId": actor_id}).encode()
    response = client.invoke_agent_runtime(
        agentRuntimeArn=agent_runtime_arn,
        runtimeSessionId=session_id,
        payload=payload,
    )
    return json.loads(response["payload"].read())["response"]

print(chat("Hi, I need to cancel an order"))
print(chat("john.smith@gmail.com"))
print(chat("Order 20001"))
```
