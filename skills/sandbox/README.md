# Sandbox Skill

Create and manage isolated container environments on DigitalOcean App Platform for AI agent code execution and testing workflows.

## What This Skill Does

- Creates ephemeral sandbox containers for running untrusted code
- Manages hot pools of pre-warmed sandboxes for low-latency execution
- Provides SDK patterns for AI agent workflows (code interpreters, iterative development)

## When to Use This Skill

Use **sandbox** when you need to:
- Execute untrusted code in isolation (AI code interpreters)
- Run long-running or stateful agent workflows
- Test in isolated environments before production

**NOT** for debugging existing apps — use the **troubleshooting** skill for that.

## Quick Start

```python
from do_app_sandbox import Sandbox

# Create a sandbox
sandbox = Sandbox.create(image="python")
result = sandbox.exec("python3 -c 'print(2+2)'")
print(result.stdout)  # 4
sandbox.delete()
```

## Key Decisions

| Decision | Choice | Rationale |
|----------|--------|-----------|
| SDK over CLI | Python SDK only | AI agents use programmatic access |
| Hot pool default | SandboxManager | Eliminates 30s cold start for agents |
| Image choice | python, node | Pre-built at ghcr.io/bikramkgupta |

## Files

- **SKILL.md** — Full documentation with decision trees and patterns
- **reference/cold-sandbox.md** — Single sandbox creation patterns
- **reference/hot-pool.md** — SandboxManager for pre-warmed pools
- **reference/use-cases.md** — AI agent and testing patterns
- **reference/positioning.md** — When to use sandbox vs Lambda

## Integration

- **← troubleshooting**: Different use case (debug existing vs create new)
- **→ designer**: Can include sandbox-compatible images in app specs
