# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Overview

An order cancellation AI agent built with [Strands Agents](https://strandsagents.com/). It supports two execution modes: **cloud** (AWS Bedrock) and **local** (Ollama). The agent guides users through cancelling orders by verifying identity, validating orders, and processing cancellations.

## Running

```bash
# Cloud mode (AWS Bedrock)
python main.py

# Local mode (Ollama)
python local.py
```

Type `exit` or `quit` to stop the agent.

## Environment Variables

Create a `.env` file (loaded via `python-dotenv`):

```
CLOUD_MODEL_NAME=<bedrock-model-id>   # required for cloud mode
AWS_REGION=us-east-1                  # optional, defaults to us-east-1
LOCAL_MODEL_NAME=qwen2.5:7b-instruct  # optional, defaults to qwen2.5:7b-instruct
```

For cloud mode, AWS credentials must also be configured (via `~/.aws/credentials` or environment variables).

## Architecture

```
main.py          → cloud mode entry point
local.py         → local mode entry point

agent/
  cloud/agent.py → creates Agent with BedrockModel
  local/agent.py → creates Agent with OllamaModel

tools/           → Strands @tool-decorated functions
  get_customer   → look up customer by email
  get_order      → validate order belongs to customer
  cancel_order   → process cancellation (returns CANCELLED / REFUND / ALREADY_REFUNDED)

utils/shared.py  → ORDERS data (in-memory), SYSTEM_PROMPT
```

**Data flow**: Both entry points call `create_agent()` from the relevant `agent/` subpackage. The agent receives the same three tools and system prompt regardless of mode — only the underlying model differs. All data (customers, orders) is in-memory in `tools/get_customer.py` and `utils/shared.py`.

**Tool sequence enforced by prompt**: `get_customer` → `get_order` → `cancel_order`. The agent must never skip identity verification.

**Tool return format**: All tools return a JSON envelope `{"result": {"content": {...}, "isError": bool}}`.

## Dependencies

Install with:
```bash
pip install -r requirements.txt
```

Key packages: `strands-agents`, `strands-agents[ollama]`, `boto3`, `python-dotenv`.
