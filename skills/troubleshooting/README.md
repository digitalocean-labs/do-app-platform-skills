# Troubleshooting Skill

Debug running App Platform applications by accessing containers, analyzing logs, running diagnostics, and applying fixes.

## What This Skill Does

- Provides **live shell access** to running containers via `do_app_sandbox` SDK
- Analyzes **build and runtime logs** for error patterns
- Deploys **debug containers** for infrastructure validation
- Offers quick fixes for common issues (502s, OOM, connection failures)

## Quick Start

```python
# Live troubleshooting with SDK
from do_app_sandbox import Sandbox

app = Sandbox.get_from_id(app_id="<app-id>", component="web")
app.exec("env | grep DATABASE")
app.exec("curl -v localhost:8080/health")
```

```bash
# Logs-only mode
doctl apps logs <app_id> <component> --type run
doctl apps logs <app_id> <component> --type build
```

## Key Decisions This Skill Makes

| Decision | Default | Rationale |
|----------|---------|-----------|
| Shell access | `do_app_sandbox` SDK | `doctl apps console` is interactive-only |
| Debug image | `ghcr.io/bikramkgupta/debug-python` | Pre-built with diagnostic tools |
| Log analysis | Pattern matching | Quick identification of common errors |

## Files

- `SKILL.md` — Complete skill documentation with decision tree
- `reference/live-troubleshooting.md` — SDK shell access workflows
- `reference/logs-analysis.md` — Log patterns and error codes
- `reference/debug-container.md` — Infrastructure validation
- `reference/networking-issues.md` — DNS, CORS, VPC diagnostics
- `reference/app-maintenance.md` — Archive/unarchive workflows
- `reference/diagnostic-scripts.md` — Helper scripts

## Integration

| Direction | Skill | Integration |
|-----------|-------|-------------|
| → | deployment | Deploy fixes after debugging |
| → | devcontainers | Reproduce issues locally |
| → | postgres | Database-specific troubleshooting |
| → | networking | Network diagnostics |

## Related Skills

- **deployment** — Redeploy after fixing issues
- **networking** — Diagnose routing and connectivity
- **postgres** — Database connection troubleshooting
