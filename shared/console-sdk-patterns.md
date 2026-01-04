# Console SDK for AI Assistants

**CRITICAL**: AI assistants cannot use `doctl apps console` — it opens an interactive WebSocket session that requires human input. Use the `do-app-sandbox` Python package instead for programmatic shell access.

## Installation & Import

```python
# Install: pip install do-app-sandbox
from do_app_sandbox import Sandbox
```

## Quick Reference Patterns

### Connect to Any Running App Platform App

```python
# Get shell access to any component in an existing app
app = Sandbox.get_from_id(app_id="your-app-id", component="component-name")
result = app.exec("command-here")
print(result.stdout)
```

### Deploy and Connect to Debug Container

```python
# For troubleshooting: deploy the pre-built debug container
# Image: ghcr.io/bikramkgupta/do-app-debug-container-python:latest
# Then connect with Sandbox.get_from_id()
```

### Common Diagnostic Commands

```python
# Network diagnostics
app.exec("curl -I http://internal-service:8080/health")
app.exec("nc -zv db-host 5432")

# Environment inspection
app.exec("env | grep -E '^(DATABASE|REDIS|API)'")

# Database connectivity (from debug container)
app.exec("psql $DATABASE_URL -c 'SELECT 1'")
```

## When to Use

| Scenario | SDK Method |
|----------|------------|
| Debug a running app | `Sandbox.get_from_id(app_id, component)` |
| Test database connectivity | Deploy debug container → `Sandbox.get_from_id()` |
| Inspect VPC networking | Deploy debug container in same VPC → run `curl`/`nc` |
| Verify environment variables | `app.exec("env")` |

## Debug Container

For infrastructure validation, deploy the pre-built debug container:

```yaml
workers:
  - name: debug
    image:
      registry_type: GHCR
      registry: ghcr.io
      repository: bikramkgupta/do-app-debug-container-python
      tag: latest
    instance_size_slug: apps-s-1vcpu-2gb
    envs:
      - key: DATABASE_URL
        scope: RUN_TIME
        value: ${db.DATABASE_URL}
```

Then connect:

```python
from do_app_sandbox import Sandbox

app = Sandbox.get_from_id(app_id="<app-id>", component="debug")
app.exec("./validate-infra all")
```

→ See **troubleshooting** skill for complete debug container workflows.
