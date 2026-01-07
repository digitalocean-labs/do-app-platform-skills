---
name: app-platform-sandbox
description: Create and manage isolated container sandboxes for AI agent code execution. Use when you need ephemeral environments to run untrusted code, execute agent workflows, or test in isolation. NOT for debugging existing apps (use troubleshooting skill).
---

# Sandbox Skill

Isolated execution environments for AI agents and testing workflows.

## Philosophy

```
Lambda/Functions: Fast cold start, 15-min limit, stateless, per-ms billing
App Platform Sandbox: 30s cold start (or instant with pool), unlimited duration, stateful, per-hour billing

Sweet spot: Long-running, stateful, iterative workflows where agents need to
install packages, run code, check results, modify, repeat.
```

## Quick Decision

```
┌─────────────────────────────────────────────────────────────┐
│         Need isolated execution environment?                 │
└─────────────────────────────────────────────────────────────┘
                            │
              Is this for debugging an EXISTING app?
                            │
            ┌───────────────┴───────────────┐
            │                               │
           YES                              NO
            │                               │
            ▼                               ▼
   ┌─────────────────┐           ┌─────────────────┐
   │ troubleshooting │           │ Continue here   │
   │ skill           │           │                 │
   │                 │           │ Is low latency  │
   │ Sandbox.get_    │           │ critical?       │
   │ from_id()       │           │                 │
   └─────────────────┘           └────────┬────────┘
                                          │
                          ┌───────────────┴───────────────┐
                          │                               │
                         YES                              NO
                          │                               │
                          ▼                               ▼
                 ┌─────────────────┐           ┌─────────────────┐
                 │ HOT POOL        │           │ COLD SANDBOX    │
                 │ SandboxManager  │           │ Sandbox.create()│
                 │ ~50ms acquire   │           │ ~30s startup    │
                 └─────────────────┘           └─────────────────┘
```

---

## Prerequisites

```bash
# Verify doctl is installed and authenticated
doctl auth whoami

# Install the SDK (choose one)
uv pip install do-app-sandbox
# OR
pip install do-app-sandbox

# For Spaces support (large file transfers)
pip install "do-app-sandbox[spaces]"
```

**Requirements:**
- Python 3.10.12+
- `doctl` CLI installed and authenticated
- DigitalOcean account with App Platform access

---

## Quick Start: Cold Sandbox

Single sandbox creation with ~30s startup time:

```python
from do_app_sandbox import Sandbox

# Create sandbox with Python image
sandbox = Sandbox.create(
    image="python",           # or "node"
    name="my-sandbox",
    region="nyc",
    instance_size="apps-s-1vcpu-1gb"
)

# Execute code
result = sandbox.exec("python3 -c 'import sys; print(sys.version)'")
print(result.stdout)

# File operations
sandbox.filesystem.write_file("/tmp/script.py", "print('hello')")
result = sandbox.exec("python3 /tmp/script.py")

# Clean up
sandbox.delete()
```

**Full guide**: See [cold-sandbox.md](reference/cold-sandbox.md)

---

## Quick Start: Hot Pool

Pre-warmed sandboxes for instant acquisition (~50ms):

```python
from do_app_sandbox import SandboxManager

# Initialize pool with 3 pre-warmed sandboxes
manager = SandboxManager(pool_size=3, image="python")
manager.start()

# Acquire sandbox instantly
sandbox = manager.acquire()

# Use it
result = sandbox.exec("pip install pandas && python3 -c 'import pandas; print(pandas.__version__)'")
print(result.stdout)

# Release back to pool (or delete if exhausted)
manager.release(sandbox)

# Shutdown pool when done
manager.shutdown()
```

**Full guide**: See [hot-pool.md](reference/hot-pool.md)

---

## Quick Reference: When to Use Sandbox

| Scenario | Recommendation |
|----------|----------------|
| AI code interpreter | Hot Pool (instant response) |
| Multi-step agent workflow | Hot Pool (state persists) |
| One-off script test | Cold Sandbox (simple) |
| CI integration testing | Cold Sandbox (per-job) |
| Short tasks (< 30s) | Consider Lambda instead |
| High concurrency (1000+) | Consider Lambda instead |

---

## Quick Reference: Available Images

| Image | Registry | Use Case |
|-------|----------|----------|
| `python` | `ghcr.io/bikramkgupta/sandbox-python` | Python 3.12, pip, common libs |
| `node` | `ghcr.io/bikramkgupta/sandbox-node` | Node.js LTS, npm |

Custom images supported — any Docker image with HTTP server capability.

---

## Quick Reference: SDK Methods

| Method | Purpose |
|--------|---------|
| `Sandbox.create()` | Create new sandbox (cold) |
| `Sandbox.get_from_id()` | Connect to existing app (troubleshooting) |
| `sandbox.exec(cmd)` | Run shell command |
| `sandbox.filesystem.read_file()` | Read file contents |
| `sandbox.filesystem.write_file()` | Write file |
| `sandbox.filesystem.list_dir()` | List directory |
| `sandbox.delete()` | Clean up sandbox |
| `SandboxManager.start()` | Initialize hot pool |
| `SandboxManager.acquire()` | Get sandbox from pool |
| `SandboxManager.release()` | Return sandbox to pool |
| `SandboxManager.shutdown()` | Tear down pool |

---

## Reference Files

- **[cold-sandbox.md](reference/cold-sandbox.md)** — Single sandbox lifecycle, file ops, cleanup
- **[hot-pool.md](reference/hot-pool.md)** — Pool management, sizing, cost optimization
- **[use-cases.md](reference/use-cases.md)** — AI agent patterns, testing patterns
- **[positioning.md](reference/positioning.md)** — Lambda vs Sandbox decision guide

---

## Cost Considerations

```
Sandbox billing: ~$0.01-0.03/hour per container (apps-s-1vcpu-1gb)

Hot Pool trade-off:
- Pool of 5 sandboxes running 8 hours = ~$0.80-2.40/day
- Eliminates 30s cold start per request
- Worth it for interactive AI agents, not for batch jobs
```

---

## Integration with Other Skills

| Direction | Skill | When |
|-----------|-------|------|
| **→** | troubleshooting | Debug an existing sandbox (use `Sandbox.get_from_id()`) |
| **→** | designer | Include sandbox-compatible worker in app spec |
| **←** | deployment | Sandboxes are standalone, not part of main app deployment |
