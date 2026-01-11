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
   │ troubleshooting │           │ Need real-time  │
   │ skill           │           │ streaming or    │
   │                 │           │ port exposure?  │
   │ Sandbox.get_    │           │                 │
   │ from_id()       │           └────────┬────────┘
   └─────────────────┘                    │
                          ┌───────────────┴───────────────┐
                          │                               │
                         YES                              NO
                          │                               │
                          ▼                               ▼
                 ┌─────────────────┐           ┌─────────────────┐
                 │ SERVICE MODE    │           │ Is low latency  │
                 │ exec_stream()   │           │ critical?       │
                 │ expose_port()   │           │                 │
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

Pre-warmed sandboxes for instant acquisition:

```python
import asyncio
from do_app_sandbox import SandboxManager, PoolConfig

async def main():
    # 1. Configure pool
    manager = SandboxManager(
        pools={"python": PoolConfig(target_ready=3)},
    )

    # 2. Start and warm up (blocks until pool is ready)
    await manager.start()
    await manager.warm_up(timeout=180)

    # 3. Acquire instantly (~500ms from pool vs 30s cold start)
    sandbox = await manager.acquire(image="python")
    result = sandbox.exec("python3 -c 'print(2+2)'")
    print(result.stdout)

    # 4. Delete when done - YOUR responsibility!
    sandbox.delete()

    # 5. Shutdown (cleans up pool, not acquired sandboxes)
    await manager.shutdown()

asyncio.run(main())
```

**Ownership model:** Once you `acquire()` a sandbox, you own it. Always call `sandbox.delete()` when done. The `shutdown()` only cleans up sandboxes still in the pool.

**Full guide**: See [hot-pool.md](reference/hot-pool.md)

---

## Quick Reference: When to Use Sandbox

| Scenario | Recommendation |
|----------|----------------|
| AI code interpreter | Hot Pool (instant response) |
| Multi-step agent workflow | Single sandbox (state persists within one sandbox) |
| One-off script test | Cold Sandbox (simple) |
| CI integration testing | Cold Sandbox (per-job) |
| Short tasks (< 30s) | Consider Lambda instead |
| High concurrency (1000+) | Consider Lambda instead |

---

## Quick Reference: Available Images

| Image | Registry | Use Case |
|-------|----------|----------|
| `python` | `ghcr.io/bikramkgupta/sandbox-python` | Python 3.13, uv, pip |
| `node` | `ghcr.io/bikramkgupta/sandbox-node` | Node.js 24, nvm |

Working directory: `/home/sandbox/app` (with `/app` symlink). Ports: 8080 (user apps), 9090 (health checks).

Custom images supported — any Docker image with HTTP server capability.

---

## Quick Reference: SDK Methods

| Method | Purpose |
|--------|---------|
| `Sandbox.create(image, mode=...)` | Create sandbox (WORKER or SERVICE mode) |
| `Sandbox.get_from_id()` | Connect to existing app |
| `sandbox.exec(cmd)` | Run shell command |
| `sandbox.exec_stream(cmd)` | Streaming output (SERVICE mode) |
| `sandbox.expose_port(port)` | Get public URL for port (SERVICE mode) |
| `sandbox.hibernate()` | Snapshot + delete for cost savings |
| `Sandbox.wake(hibernated)` | Restore hibernated sandbox |
| `sandbox.filesystem.read_file()` | Read file contents |
| `sandbox.filesystem.write_file()` | Write file |
| `sandbox.delete()` | Delete sandbox (always call when done) |
| `SandboxManager(pools={...})` | Configure hot pool |
| `manager.start()` | Start background pool management |
| `manager.warm_up(timeout)` | Block until pool reaches target (async) |
| `manager.acquire(image=...)` | Get sandbox from pool (async) |
| `manager.acquire_with_snapshot()` | Get sandbox with pre-configured state |
| `manager.shutdown()` | Tear down pool (cleans up pool only) |

---

## Reference Files

- **[cold-sandbox.md](reference/cold-sandbox.md)** — Single sandbox lifecycle, file ops, cleanup
- **[hot-pool.md](reference/hot-pool.md)** — Pool management, sizing, cost optimization
- **[service-mode.md](reference/service-mode.md)** — Streaming, port exposure, AI agent patterns
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
