# agent-strands-bedrock

configure: `agentcore configure --entrypoint main.py`
deploy: `agentcore deploy --env CLOUD_MODEL_NAME=us.anthropic.claude-haiku-4-5-20251001-v1:0`

`agentcore invoke '{"prompt":"Hi, I need to cancel my order 20001","sessionId":"sess-abcd","actorId":"user-43"}'`