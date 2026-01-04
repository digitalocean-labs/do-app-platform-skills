# Agent Development Kit (ADK)

Build full AI agents with knowledge bases, RAG, guardrails, or multi-agent routing.

## When to Use ADK

| Use Case | ADK Required? |
|----------|---------------|
| Simple LLM API calls | No — use Serverless Inference |
| Ground responses in custom data (knowledge bases) | Yes |
| Content filtering / guardrails | Yes |
| Multi-agent workflows | Yes |
| Agent observability (traces, logs, evaluations) | Yes |

---

## Prerequisites

- Python 3.13
- `gradient-adk` package: `pip install gradient-adk`
- Model access key: `GRADIENT_MODEL_ACCESS_KEY`
- Personal access token: `DIGITALOCEAN_API_TOKEN` (with genai CRUD + project read scopes)

---

## Key Concepts

Agent code requires an `@entrypoint` decorator:

```python
from gradient_adk import entrypoint

@entrypoint
def entry(payload, context):
    query = payload["prompt"]
    # Process and return response
    return result
```

---

## ADK Commands

```bash
# Configure project
gradient agent configure

# Run locally (exposes localhost:8080/run)
gradient agent run

# Deploy to DigitalOcean
gradient agent deploy

# View traces and logs
gradient agent traces
gradient agent logs
```

---

## Agent Endpoint

Deployed agents available at:
```
https://agents.do-ai.run/v1/{workspace-id}/{deployment-name}/run
```

---

## doctl Commands

```bash
# Create an agent
doctl genai agent create --name "My Agent" \
  --project-id "..." \
  --model-id "..." \
  --region "nyc1" \
  --instruction "You are a helpful assistant."

# List agents
doctl genai agent list

# Get agent details
doctl genai agent get <agent-id>
```

---

## App Spec Configuration

```yaml
services:
  - name: agent-api
    envs:
      - key: GRADIENT_MODEL_ACCESS_KEY
        scope: RUN_TIME
        type: SECRET
        value: ${GRADIENT_MODEL_ACCESS_KEY}
      - key: DIGITALOCEAN_API_TOKEN
        scope: RUN_TIME
        type: SECRET
        value: ${DIGITALOCEAN_API_TOKEN}
```

---

## Local Development

```bash
# Install ADK
pip install gradient-adk

# Initialize project
gradient agent init

# Run locally
gradient agent run
# → http://localhost:8080/run

# Test with curl
curl -X POST http://localhost:8080/run \
  -H "Content-Type: application/json" \
  -d '{"prompt": "Hello, agent!"}'
```

---

## Knowledge Bases

ADK supports attaching knowledge bases for RAG:

```python
from gradient_adk import entrypoint, KnowledgeBase

kb = KnowledgeBase.from_id("kb-xxxx")

@entrypoint
def entry(payload, context):
    query = payload["prompt"]
    # Search knowledge base
    results = kb.search(query, top_k=5)
    # Use results in response
    return {"response": "...", "sources": results}
```

---

## Guardrails

Add content filtering:

```python
from gradient_adk import entrypoint, Guardrail

guardrail = Guardrail(
    block_topics=["violence", "illegal"],
    pii_redaction=True
)

@entrypoint
def entry(payload, context):
    # Input is automatically filtered
    query = payload["prompt"]
    return {"response": "..."}
```

---

## Documentation Links

- [Agent Development Kit](https://docs.digitalocean.com/products/gradient-ai-platform/how-to/adk/)
- [ADK Quickstart](https://docs.digitalocean.com/products/gradient-ai-platform/getting-started/adk-quickstart/)
- [Knowledge Bases](https://docs.digitalocean.com/products/gradient-ai-platform/how-to/knowledge-bases/)
