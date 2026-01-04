# AI Services Skill

Configure DigitalOcean Gradient AI Platform for App Platform applications.

## What This Skill Does

- Configures **Serverless Inference** for direct LLM API calls
- Sets up **Agent Development Kit (ADK)** for full AI agents
- Handles model access key credential patterns
- Provides SDK examples (Python, Node.js, cURL)

## Quick Start

```yaml
# Add to .do/app.yaml
envs:
  - key: MODEL_ACCESS_KEY
    scope: RUN_TIME
    type: SECRET
    value: ${MODEL_ACCESS_KEY}
  - key: INFERENCE_ENDPOINT
    value: https://inference.do-ai.run
```

## Key Decisions This Skill Makes

| Decision | Default | Rationale |
|----------|---------|-----------|
| API compatibility | OpenAI SDK | Industry standard, easy migration |
| Credential storage | GitHub Secrets | Secure, AI never sees keys |
| Default model | `llama3.3-70b-instruct` | Best quality/speed balance |

## Files

- `SKILL.md` — Complete skill documentation with decision tree
- `reference/serverless-inference.md` — SDK setup and API reference
- `reference/agent-development-kit.md` — ADK workflow and features

## Integration

| Direction | Skill | Integration |
|-----------|-------|-------------|
| → | designer | Add AI env vars to app spec |
| → | deployment | Store model keys in GitHub Secrets |
| → | devcontainers | Test AI locally |

## Related Skills

- **designer** — Create app specs with AI components
- **deployment** — Deploy AI-enabled applications
