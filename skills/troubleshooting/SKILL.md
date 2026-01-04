---
name: app-platform-troubleshooting
description: Debug running App Platform applications by accessing containers, analyzing logs, running diagnostics, and applying fixes. Use when apps fail to deploy, crash at runtime, have connectivity issues, or need performance diagnosis.
---

# App Platform Troubleshooting Skill

Transform debugging from guessing to rapid diagnosis and fix.

## Philosophy

```
Traditional: See error → Guess → Change → Push → Wait 5-7 min → Repeat
With skill:  See error → Diagnose → Fix → Verify → Commit proper fix
```

## Quick Decision

```
Is the app deployed with running containers?
├── YES → Can we access the shell?
│         ├── YES → LIVE MODE (SDK shell access)
│         └── NO  → LOGS-ONLY MODE (fetch logs)
└── NO (build/deploy failed) → LOGS-ONLY MODE
```

---

## Mode 1: Live Troubleshooting (Quick Start)

```python
from do_app_sandbox import Sandbox

app = Sandbox.get_from_id(app_id="<app-id>", component="web")

# Diagnostics
app.exec("env | grep DATABASE")
app.exec("curl -v localhost:8080/health")
app.exec("ps aux | head -10")
```

**Full guide**: See [live-troubleshooting.md](reference/live-troubleshooting.md)

---

## Mode 2: Logs-Only (Quick Start)

```bash
# Runtime logs
doctl apps logs <app_id> <component> --type run

# Build logs
doctl apps logs <app_id> <component> --type build

# Crash logs
doctl apps logs <app_id> --type=run_restarted
```

**Full guide**: See [logs-analysis.md](reference/logs-analysis.md)

---

## Debug Container (Infrastructure Issues)

Deploy in ~30-45 seconds to isolate infrastructure from application:

```yaml
services:
  - name: debug
    image:
      registry_type: GHCR
      registry: ghcr.io
      repository: bikramkgupta/debug-python
      tag: latest
    http_port: 8080
    envs:
      - key: DATABASE_URL
        value: ${db.DATABASE_URL}
```

```bash
# Run validation suite
validate-infra all
validate-infra database
validate-infra kafka
```

**Full guide**: See [debug-container.md](reference/debug-container.md)

---

## Quick Reference: Exit Codes

| Code | Signal | Meaning |
|------|--------|---------|
| 0 | - | Clean exit (shouldn't exit) |
| 1 | - | General error |
| 127 | - | Command not found |
| 137 | SIGKILL | OOM killed |
| 143 | SIGTERM | Graceful shutdown |

---

## Quick Reference: Common Fixes

| Problem | Quick Fix |
|---------|-----------|
| App exits immediately | Check if listening on $PORT |
| 502 errors | Check health endpoint, verify running |
| Database connection fails | Use Debug Container, verify trusted sources |
| Build fails | Check dependencies, review build logs |
| OOM kills | Upgrade instance size |
| Health checks fail | Bind to 0.0.0.0, not localhost |
| Slow startup | Increase initial_delay_seconds |

---

## Reference Files

- **[live-troubleshooting.md](reference/live-troubleshooting.md)** — SDK shell access, diagnostics, hot fixes
- **[logs-analysis.md](reference/logs-analysis.md)** — Log patterns, error codes, health check config
- **[debug-container.md](reference/debug-container.md)** — Infrastructure validation, validation suite
- **[networking-issues.md](reference/networking-issues.md)** — DNS, CORS, VPC, routing
- **[app-maintenance.md](reference/app-maintenance.md)** — Archive/unarchive workflow
- **[diagnostic-scripts.md](reference/diagnostic-scripts.md)** — Scripts, testing strategy, performance

---

## When to Escalate

Contact DigitalOcean Support when:
- Internal error persists after redeploy
- Resource limit increases needed
- Multiple apps affected (platform issue)
- VPC/networking issues can't be diagnosed

**Before escalating, gather:**
```bash
doctl apps get <app_id> -o json > app_info.json
doctl apps logs <app_id> <component> --type run > runtime.log
doctl apps spec get <app_id> > app_spec.yaml
```

---

## Integration with Other Skills

- **→ deployment**: After fixing, deploy proper changes
- **→ devcontainers**: Reproduce issues locally
- **→ postgres**: Database-specific configuration
- **→ networking**: Comprehensive networking docs
