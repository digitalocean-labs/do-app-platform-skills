---
name: ai-services
version: 1.0.0
min_doctl_version: "1.82.0"
description: Configure DigitalOcean Gradient AI serverless inference and Agent Development Kit. Use when adding LLM inference, model access keys, serverless AI endpoints, or building AI agents with ADK on App Platform.
related_skills: [designer, deployment]
deprecated: false
---

# AI Services Skill

Configure DigitalOcean Gradient AI Platform for App Platform applications.

> **Tip**: This is one specialized skill in the App Platform library. For complex multi-step projects, consider using the **planner** skill to generate a staged approach. For an overview of all available skills, see the [root SKILL.md](../../SKILL.md).

---

## Quick Decision

```
What do you need?
├── Simple LLM API calls → Serverless Inference
│   OpenAI-compatible API, no agent management
│
└── Full AI agents → Agent Development Kit (ADK)
    Knowledge bases, RAG, guardrails, multi-agent routing
```

| Need | Solution | Reference |
|------|----------|-----------|
| Call LLM models directly | Serverless Inference | [serverless-inference.md](reference/serverless-inference.md) |
| Build agents with knowledge bases | ADK | [agent-development-kit.md](reference/agent-development-kit.md) |
| Content filtering / guardrails | ADK | [agent-development-kit.md](reference/agent-development-kit.md) |
| Multi-agent workflows | ADK | [agent-development-kit.md](reference/agent-development-kit.md) |

---

## Credential Handling

Model access keys follow the standard credential hierarchy:

1. **GitHub Secrets** (recommended): User creates key → adds to GitHub Secrets → app spec references
2. **App Platform Secrets**: Set via `doctl apps update` with `type: SECRET`

```yaml
# App Spec pattern
envs:
  - key: MODEL_ACCESS_KEY
    scope: RUN_TIME
    type: SECRET
    value: ${MODEL_ACCESS_KEY}   # From GitHub Secrets
```

**Key creation**: Control Panel → Serverless Inference → Model Access Keys

> Keys shown **only once** after creation—store securely.

---

## Quick Start: Serverless Inference

```yaml
# .do/app.yaml
services:
  - name: api
    envs:
      - key: MODEL_ACCESS_KEY
        scope: RUN_TIME
        type: SECRET
        value: ${MODEL_ACCESS_KEY}
      - key: INFERENCE_ENDPOINT
        value: https://inference.do-ai.run
```

```python
# Python SDK (OpenAI-compatible)
from openai import OpenAI
import os

client = OpenAI(
    base_url=os.environ["INFERENCE_ENDPOINT"] + "/v1",
    api_key=os.environ["MODEL_ACCESS_KEY"],
)

response = client.chat.completions.create(
    model="llama3.3-70b-instruct",
    messages=[{"role": "user", "content": "Hello!"}],
)
```

**Full guide**: See [serverless-inference.md](reference/serverless-inference.md)

---

## Quick Start: Agent Development Kit

```bash
# Install and configure
pip install gradient-adk
gradient agent configure

# Run locally
gradient agent run
# → http://localhost:8080/run

# Deploy to DigitalOcean
gradient agent deploy
```

```python
# Agent entrypoint
from gradient_adk import entrypoint

@entrypoint
def entry(payload, context):
    query = payload["prompt"]
    return {"response": "Hello from agent!"}
```

**Full guide**: See [agent-development-kit.md](reference/agent-development-kit.md)

---

## Available Models

| Model | Use Case |
|-------|----------|
| `llama3.3-70b-instruct` | General purpose, high quality |
| `llama3-8b` | Faster, lower cost |
| `mistral-7b` | Efficient, multilingual |

```bash
# List all available models
doctl genai list-models
```

Check [Gradient AI Models](https://docs.digitalocean.com/products/gradient-ai-platform/details/models/) for current availability.

---

## Reference Files

- **[serverless-inference.md](reference/serverless-inference.md)** — SDK setup, API parameters, examples
- **[agent-development-kit.md](reference/agent-development-kit.md)** — ADK workflow, knowledge bases, guardrails

---

## Quick Troubleshooting

| Error | Cause | Fix |
|-------|-------|-----|
| `401 Unauthorized` | Invalid model access key | Verify key in GitHub Secrets |
| `Model not found` | Invalid model ID | Run `doctl genai list-models` |
| `Rate limit exceeded` | Too many requests | Implement exponential backoff |
| ADK deploy fails | Missing token scopes | Ensure `genai` CRUD + `project` read scopes |

---

## Integration with Other Skills

- **→ designer**: Add AI service environment variables to app spec
- **→ deployment**: Model access key stored in GitHub Secrets
- **→ devcontainers**: Test AI integrations locally before deployment
- **→ planner**: Plan AI-enabled app deployments

---

## Documentation Links

- [Gradient AI Platform](https://docs.digitalocean.com/products/gradient-ai-platform/)
- [Available Models](https://docs.digitalocean.com/products/gradient-ai-platform/details/models/)
- [Serverless Inference](https://docs.digitalocean.com/products/gradient-ai-platform/how-to/serverless-inference/)
- [Agent Development Kit](https://docs.digitalocean.com/products/gradient-ai-platform/how-to/adk/)
