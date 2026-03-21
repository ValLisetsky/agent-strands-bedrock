# PRD: agent_cancel_order

## 1. Overview

`agent_cancel_order` is an AI agent built with the [Strands](https://strandsagents.com) Python framework that handles an end-to-end order cancellation workflow. It identifies a customer by email, validates an order belongs to that customer, and processes the cancellation — returning an appropriate resolution to the user.

The agent supports two operating modes controlled by the `AGENT_MODE` environment variable:

| Mode | Model | Runtime |
|------|-------|---------|
| `local` | Ollama `qwen2.5:7b-instruct` (configured via `LOCAL_MODEL_NAME`) | Local machine |
| `cloud` | AWS Bedrock `Claude Haiku 4.5` (configured via `CLOUD_MODEL_NAME`) | AWS AgentCore |

The user interacts with the agent through a conversational terminal loop.

---

## 2. Environment Variables

All sensitive configuration lives in a `.env` file (gitignored). A `.env.example` template is committed.

| Variable | Required | Description | Example |
|----------|----------|-------------|---------|
| `AGENT_MODE` | Yes | Runtime mode | `local` or `cloud` |
| `LOCAL_MODEL_NAME` | local mode | Ollama model name | `qwen2.5:7b-instruct` |
| `CLOUD_MODEL_NAME` | cloud mode | Bedrock model ID | `anthropic.claude-haiku-4-5...` |
| `AWS_REGION` | cloud mode | AWS region for Bedrock | `us-east-1` |
| `AWS_ACCESS_KEY_ID` | cloud mode | AWS credentials | — |
| `AWS_SECRET_ACCESS_KEY` | cloud mode | AWS credentials | — |

---

## 3. Tool Response Schema

All tools return a consistent JSON envelope:

```json
{
  "result": {
    "content": { },
    "isError": false
  }
}
```

On **success**: `result.content` contains the operation payload; `isError` is `false`; no `errorDetail` field.

On **error**: `result.content` is `{}`; `isError` is `true`; `errorDetail` is present:

```json
{
  "result": {
    "content": {},
    "isError": true,
    "errorDetail": {
      "code": "ERROR_CODE",
      "retryable": false,
      "message": "Human-readable error description."
    }
  }
}
```

---

## 4. Tools Specification

### 4.1 `get_customer(email: str)`

Looks up a customer by email address.

**Mock data:**

```json
[
  { "email": "john.smith@gmail.com", "customerId": "10001", "firstName": "John",  "lastName": "Smith" },
  { "email": "jane.dow@yahoo.com",   "customerId": "10002", "firstName": "Jane",  "lastName": "Dow"   },
  { "email": "jack.black@gmail.com", "customerId": "10003", "firstName": "Jack",  "lastName": "Black" }
]
```

**Success response** (`result.content`):
```json
{ "customerId": "10001", "firstName": "John", "lastName": "Smith" }
```

**Not found** — empty content, no error:
```json
{ "result": { "content": {}, "isError": false } }
```

---

### 4.2 `get_order(customerId: str, orderId: str)`

Retrieves order details and validates that the given `orderId` belongs to the given `customerId`.

**Mock data:**

```json
[
  { "orderId": "20001", "customerId": "10001", "status": "SHIPPED"  },
  { "orderId": "20002", "customerId": "10002", "status": "DELIVERED" },
  { "orderId": "20003", "customerId": "10003", "status": "REFUNDED" }
]
```

**Success response** (`result.content`) — full order record:
```json
{ "orderId": "20001", "customerId": "10001", "status": "SHIPPED" }
```

**Not found / ownership mismatch** — empty content, no error:
```json
{ "result": { "content": {}, "isError": false } }
```

When an empty result is returned, the agent should ask the user to verify the order ID for possible typos.

---

### 4.3 `cancel_order(orderId: str)`

Processes the cancellation of a previously validated order.

> **Security constraint**: This tool must only be called after `get_order` has confirmed the order exists and belongs to the authenticated customer. The agent must never call `cancel_order` with an `orderId` supplied directly by the user without prior `get_order` validation.

Uses the same mock data as `get_order`. Resolution logic by order status:

| Order Status | `result.content` |
|---|---|
| `SHIPPED` | `{ "orderId": "...", "resolution": "CANCELLED" }` |
| `DELIVERED` | `{ "orderId": "...", "resolution": "REFUND" }` |
| `REFUNDED` | `{ "orderId": "...", "resolution": "ALREADY_REFUNDED" }` |

**Agent messaging per resolution:**

| Resolution | Agent response to user |
|---|---|
| `CANCELLED` | Confirm the order has been successfully cancelled. |
| `REFUND` | Inform the user the order was already delivered. Direct them to support line **555-123-4567** to initiate a refund. |
| `ALREADY_REFUNDED` | Inform the user the order has already been refunded. Suggest contacting support **555-123-4567** for additional clarifications. |

---

## 5. Agent Behavior & Workflow

### System Prompt Guidelines

The agent should:
- Identify itself as an order cancellation assistant
- Never expose internal tool names or implementation details
- Never call `cancel_order` with an orderId that was not first validated by `get_order`
- Ask clarifying questions politely when required information is missing
- Suggest support contact **555-123-4567** where applicable

### Conversation Workflow

```
1. Greet the user and ask for their email address
2. Call get_customer(email)
   ├─ Empty result → inform user no account found, ask to verify email
   └─ Found → proceed with customerId
3. Ask the user for their order ID
4. Call get_order(customerId, orderId)
   ├─ Empty result → ask user to double-check the order ID for typos
   └─ Found → proceed with validated orderId
5. Call cancel_order(orderId)
6. Respond to user based on resolution value
```

---

## 6. Project Structure

```
agent-strands-bedrock/
├── .env                      # gitignored — runtime secrets & config
├── .env.example              # committed template with placeholder values
├── .gitignore
├── LICENSE
├── PRD.md                    # this document
├── README.md
├── requirements.txt
├── main.py                   # entry point: starts conversational terminal loop
├── agent/
│   ├── __init__.py
│   ├── agent.py              # Agent instantiation and system prompt
│   └── model_factory.py      # returns BedrockModel or OllamaModel per AGENT_MODE
└── tools/
    ├── __init__.py
    ├── get_customer.py       # @tool: get_customer(email)
    ├── get_order.py          # @tool: get_order(customerId, orderId)
    └── cancel_order.py       # @tool: cancel_order(orderId)
```

---

## 7. Dependencies

| Package | Purpose |
|---------|---------|
| `strands-agents` | Core agent framework |
| `strands-agents[ollama]` | Ollama model provider (local mode) |
| `boto3` | AWS SDK for Bedrock (cloud mode) |
| `python-dotenv` | Load `.env` file |

> **Note**: Verify the correct extras/package name for Ollama support in `strands-agents` at implementation time, as the provider API may differ from Bedrock.

---

## 8. Out of Scope (v1)

- Persistent conversation history / session storage
- Real database or API integrations (all services are mocked)
- AWS AgentCore deployment infrastructure (Dockerfile, CDK, SAM)
- Multi-tenant or concurrent session support
- Authentication / authorization beyond email-based customer lookup
