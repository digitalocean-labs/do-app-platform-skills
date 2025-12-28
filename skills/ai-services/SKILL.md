---
name: ai-services
description: Configure DigitalOcean Gradient AI serverless inference and Agent Development Kit for App Platform applications
version: 1.0.0
author: Bikram Gupta
triggers:
  - "gradient"
  - "gradient ai"
  - "inference"
  - "serverless inference"
  - "LLM endpoint"
  - "AI platform"
  - "digitalocean ai"
  - "model access key"
  - "adk"
  - "agent development kit"
dependencies:
  - deployment (for API key via GitHub Secrets)
---

# AI Services Skill

Configure DigitalOcean Gradient AI Platform for App Platform applications.

---

## Quick Decision

| Need | Solution |
|------|----------|
| Simple LLM API calls | **Serverless Inference** (primary, below) |
| Agents with knowledge bases, RAG, guardrails, multi-agent routing | **Agent Development Kit** (brief section below) |

---

## Serverless Inference

Send API requests directly to foundation models without creating or managing agents. OpenAI-compatible API.

### Endpoints

| Endpoint | Verb | Description |
|----------|------|-------------|
| `https://inference.do-ai.run/v1/models` | GET | List available models and IDs |
| `https://inference.do-ai.run/v1/chat/completions` | POST | Send prompts, get responses |

### Model Access Keys

Create keys in: **Control Panel → Serverless Inference → Model Access Keys**

- Keys shown **only once** after creation—store securely
- Do NOT expose in front-end code
- Use secrets manager or environment variables

### App Spec Configuration

```yaml
services:
  - name: api
    envs:
      - key: MODEL_ACCESS_KEY
        scope: RUN_TIME
        type: SECRET
        value: ${MODEL_ACCESS_KEY}   # From GitHub Secrets
      - key: INFERENCE_ENDPOINT
        value: https://inference.do-ai.run
```

### Credential Setup

1. Create model access key: Control Panel → Serverless Inference → Model Access Keys
2. Add to GitHub Secrets: `MODEL_ACCESS_KEY`

---

## SDK Usage (OpenAI-Compatible)

### Python

```python
from openai import OpenAI
import os

client = OpenAI(
    base_url=os.environ["INFERENCE_ENDPOINT"] + "/v1",
    api_key=os.environ["MODEL_ACCESS_KEY"],
)

response = client.chat.completions.create(
    model="llama3.3-70b-instruct",
    messages=[{"role": "user", "content": "What is the capital of France?"}],
    temperature=0.7,
    max_tokens=100,
)
print(response.choices[0].message.content)
```

### Node.js

```javascript
const OpenAI = require('openai');

const client = new OpenAI({
  baseURL: process.env.INFERENCE_ENDPOINT + '/v1',
  apiKey: process.env.MODEL_ACCESS_KEY,
});

const response = await client.chat.completions.create({
  model: 'llama3.3-70b-instruct',
  messages: [{ role: 'user', content: 'What is the capital of France?' }],
  temperature: 0.7,
  max_tokens: 100,
});
console.log(response.choices[0].message.content);
```

### cURL

```bash
curl -X POST "https://inference.do-ai.run/v1/chat/completions" \
  -H "Authorization: Bearer ${MODEL_ACCESS_KEY}" \
  -H "Content-Type: application/json" \
  -d '{
    "model": "llama3.3-70b-instruct",
    "messages": [{"role": "user", "content": "What is the capital of France?"}],
    "temperature": 0.7,
    "max_tokens": 100
  }'
```

### List Available Models

```bash
curl -X GET "https://inference.do-ai.run/v1/models" \
  -H "Authorization: Bearer ${MODEL_ACCESS_KEY}" \
  -H "Content-Type: application/json"
```

---

## API Parameters

| Parameter | Type | Description |
|-----------|------|-------------|
| `model` | string | Model ID (get from `/v1/models`) |
| `messages` | array | Conversation history with `role` and `content` |
| `temperature` | float | 0.0-1.0, controls randomness |
| `max_tokens` | int | Maximum tokens in response |

### Response Format

```json
{
  "choices": [{
    "message": { "content": "The capital of France is Paris." }
  }],
  "usage": {
    "prompt_tokens": 43,
    "completion_tokens": 8,
    "total_tokens": 51
  }
}
```

Billing is per input/output token.

---

## Available Models

Check [Gradient AI Models](https://docs.digitalocean.com/products/gradient-ai-platform/details/models/) for current availability.

Common models:
- `llama3.3-70b-instruct`
- `llama3-8b`
- `mistral-7b`

---

## Agent Development Kit (ADK)

For users needing full AI agents with knowledge bases, RAG, guardrails, or multi-agent routing.

### When to Use ADK

- Need to ground responses in custom data (knowledge bases)
- Require guardrails or content filtering
- Building multi-agent workflows
- Need agent observability (traces, logs, evaluations)

### Prerequisites

- Python 3.13
- `gradient-adk` package: `pip install gradient-adk`
- Model access key: `GRADIENT_MODEL_ACCESS_KEY`
- Personal access token: `DIGITALOCEAN_API_TOKEN` (with genai CRUD + project read scopes)

### Key Concepts

Agent code requires an `@entrypoint` decorator:

```python
from gradient_adk import entrypoint

@entrypoint
def entry(payload, context):
    query = payload["prompt"]
    # Process and return response
    return result
```

### ADK Commands

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

### Agent Endpoint

Deployed agents available at:
```
https://agents.do-ai.run/v1/{workspace-id}/{deployment-name}/run
```

---

## doctl Commands

```bash
# List available models
doctl genai list-models

# List available regions
doctl genai list-regions

# Create an agent
doctl genai agent create --name "My Agent" \
  --project-id "..." \
  --model-id "..." \
  --region "nyc1" \
  --instruction "You are a helpful assistant."
```

---

## Partner Provider Keys

Commercial models (Anthropic Claude, OpenAI) require partner API keys from your provider account. Add keys in Control Panel → Agent Platform → Model Provider Keys.

See [Partner Provider Keys docs](https://docs.digitalocean.com/products/gradient-ai-platform/how-to/manage-model-keys/).

---

## Integration with Other Skills

### → deployment skill

Model access key stored in GitHub Secrets, referenced in app spec with `type: SECRET`.

### → sandbox skill

Sandboxes can use Gradient AI for code generation/analysis workflows.

---

## Documentation Links

- [Gradient AI Platform](https://docs.digitalocean.com/products/gradient-ai-platform/)
- [Available Models](https://docs.digitalocean.com/products/gradient-ai-platform/details/models/)
- [Serverless Inference](https://docs.digitalocean.com/products/gradient-ai-platform/how-to/serverless-inference/)
- [Agent Development Kit](https://docs.digitalocean.com/products/gradient-ai-platform/how-to/adk/)
- [API Reference](https://docs.digitalocean.com/reference/api/)
