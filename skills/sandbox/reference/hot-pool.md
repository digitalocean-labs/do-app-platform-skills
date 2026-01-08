# Hot Pool Reference

Use `SandboxManager` to maintain pre-warmed sandboxes for instant acquisition (~50ms vs ~30s cold start).

## Key Concept: Sandboxes Are Single-Use

**Critical understanding:** Sandboxes are ephemeral, single-use containers.

```
Pool maintains N pre-warmed sandboxes
       ↓
acquire() → You get a sandbox (removed from pool)
       ↓
Use it (exec commands, file ops, etc.)
       ↓
delete() → Sandbox destroyed permanently
       ↓
Pool auto-replenishes with NEW sandboxes
```

There is **no recycling**. You cannot "return" a sandbox to the pool. Always `delete()` when done.

---

## When to Use Hot Pool

- AI code interpreters requiring instant response
- High-throughput scenarios needing concurrent sandboxes
- Any use case where 30s cold-start latency is unacceptable

For one-off executions where startup time doesn't matter, use [Cold Sandbox](cold-sandbox.md) instead.

---

## Basic Pool Lifecycle

```python
import asyncio
from do_app_sandbox import SandboxManager, PoolConfig

async def main():
    # 1. Configure and start pool
    manager = SandboxManager(
        pools={"python": PoolConfig(target_ready=3)},
    )
    await manager.start()

    # 2. Acquire sandbox instantly (~50ms)
    sandbox = await manager.acquire(image="python")

    # 3. Use it
    result = sandbox.exec("python3 -c 'print(2+2)'")
    print(result.stdout)

    # 4. DELETE when done - sandboxes are single-use!
    sandbox.delete()

    # 5. Shutdown pool (destroys remaining warm sandboxes)
    await manager.shutdown()

asyncio.run(main())
```

---

## Pool Configuration

### PoolConfig Parameters

```python
from do_app_sandbox import PoolConfig

config = PoolConfig(
    target_ready=3,           # Target warm sandboxes when active
    max_ready=10,             # Maximum sandboxes in pool
    idle_timeout=60,          # Seconds before scaling down
    scale_down_delay=60,      # Seconds between destructions
    cooldown_after_acquire=120,  # Pause scale-down after acquire
    max_warm_age=1800,        # Max seconds a sandbox can wait in pool
    health_check_interval=60, # Health check frequency (0 to disable)
    on_empty="create",        # "create" (fallback) or "fail" (fast-fail)
    create_retries=3,         # Retry attempts for creation
)
```

| Parameter | Default | Description |
|-----------|---------|-------------|
| `target_ready` | 0 | Target warm sandboxes when pool is active |
| `max_ready` | 10 | Maximum sandboxes to keep in pool |
| `idle_timeout` | 60 | Seconds of no acquires before scaling down |
| `scale_down_delay` | 60 | Seconds between destructions during scale-down |
| `cooldown_after_acquire` | 120 | Pause scale-down after an acquire |
| `max_warm_age` | 1800 | Max seconds a sandbox can warm before cycling |
| `health_check_interval` | 60 | Seconds between health checks (0 to disable) |
| `on_empty` | `"create"` | `"create"` (cold fallback) or `"fail"` (raise error) |
| `create_retries` | 3 | Retry attempts for failed creation |

### SandboxManager Parameters

```python
manager = SandboxManager(
    pools={
        "python": PoolConfig(target_ready=3),
        "node": PoolConfig(target_ready=2),
    },
    default_pool_config=PoolConfig(target_ready=1),
    max_total_sandboxes=50,      # Global limit (cost ceiling)
    max_concurrent_creates=10,   # API rate limit protection
    sandbox_defaults={
        "region": "nyc",
        "instance_size": "apps-s-1vcpu-1gb",
    },
)
```

---

## Pool Sizing Guidance

| Use Case | Recommended Config | Rationale |
|----------|-------------------|-----------|
| Single AI agent | `target_ready=2` | One active + buffer |
| Multiple concurrent users | `target_ready=users * 1.5` | Account for overlap |
| Burst workloads | `target_ready=peak * 2` | Handle spikes |
| Development/testing | `target_ready=1` | Minimize cost |

**Cost calculation:**
```
Pool cost = target_ready × instance_cost × hours_running
Example: 3 sandboxes × $0.02/hr × 8 hrs = $0.48/day
```

---

## Acquire Pattern

### Basic Pattern (Always Delete)

```python
sandbox = await manager.acquire(image="python")
try:
    result = sandbox.exec("python3 script.py")
    # Process result
finally:
    sandbox.delete()  # Always delete!
```

### Context Manager (Recommended)

```python
from contextlib import asynccontextmanager

@asynccontextmanager
async def get_sandbox(manager, image="python"):
    sandbox = await manager.acquire(image=image)
    try:
        yield sandbox
    finally:
        sandbox.delete()

# Usage
async with get_sandbox(manager) as sandbox:
    result = sandbox.exec("python3 -c 'print(42)'")
```

### Handling Pool Exhaustion

```python
from do_app_sandbox import PoolExhaustedError

try:
    sandbox = await manager.acquire(image="python")
    try:
        result = sandbox.exec("python3 script.py")
    finally:
        sandbox.delete()
except PoolExhaustedError:
    # Pool empty and on_empty="fail"
    print("No sandboxes available")
```

With `on_empty="create"` (default), the manager falls back to cold creation (~30s) if the pool is empty.

---

## Adaptive Scaling

Pools automatically scale based on demand:

```
IDLE (0 warm) ←──── idle_timeout ──── ACTIVE (target_ready warm)
      │                                        ↑
      └──── acquire() triggers scale-up ───────┘
```

**Scale-down behavior:**
1. No acquires for `idle_timeout` seconds → start scaling down
2. Destroy 1 sandbox every `scale_down_delay` seconds
3. After any acquire, pause scale-down for `cooldown_after_acquire` seconds

This prevents paying for idle sandboxes while avoiding thrashing.

---

## Warm-Up Before Production Traffic

```python
manager = SandboxManager(
    pools={"python": PoolConfig(target_ready=5)},
)
await manager.start()

# Block until all pools reach target_ready
await manager.warm_up(timeout=120)

# Now safe to serve traffic with guaranteed low latency
print("Pool warmed up, ready to serve requests")
```

---

## Monitoring with Metrics

```python
# Get current metrics
metrics = manager.metrics()

for image, pool_metrics in metrics.items():
    print(f"{image}:")
    print(f"  Ready: {pool_metrics.ready}")
    print(f"  Creating: {pool_metrics.creating}")
    print(f"  In use: {pool_metrics.in_use}")
    print(f"  Pool hit rate: {pool_metrics.pool_hit_rate:.1%}")
    print(f"  Avg latency: {pool_metrics.avg_acquire_latency_ms:.0f}ms")
```

### Available Metrics

| Metric | Description |
|--------|-------------|
| `ready` | Sandboxes waiting in pool |
| `creating` | Sandboxes being created |
| `in_use` | Sandboxes currently acquired |
| `total_acquires` | Total acquisitions |
| `acquires_from_pool` | Instant acquisitions from pool |
| `acquires_cold_start` | Acquisitions requiring cold start |
| `pool_hit_rate` | Ratio of instant to total |
| `avg_acquire_latency_ms` | Average acquisition time |

---

## AI Agent Workflow Example

```python
import asyncio
from do_app_sandbox import SandboxManager, PoolConfig

class CodeInterpreter:
    def __init__(self):
        self.manager = SandboxManager(
            pools={"python": PoolConfig(target_ready=2)},
        )
        self._started = False

    async def start(self):
        await self.manager.start()
        self._started = True

    async def execute(self, code: str) -> dict:
        if not self._started:
            await self.start()

        sandbox = await self.manager.acquire(image="python")
        try:
            # Write code to file
            sandbox.filesystem.write_file("/tmp/user_code.py", code)

            # Execute with timeout
            result = sandbox.exec("python3 /tmp/user_code.py", timeout=30)

            return {
                "success": result.exit_code == 0,
                "output": result.stdout,
                "error": result.stderr if result.exit_code != 0 else None
            }
        finally:
            sandbox.delete()  # Always delete - single use!

    async def shutdown(self):
        await self.manager.shutdown()

# Usage
async def main():
    interpreter = CodeInterpreter()
    await interpreter.start()

    result = await interpreter.execute("print('Hello from sandbox!')")
    print(result)

    await interpreter.shutdown()

asyncio.run(main())
```

---

## Graceful Shutdown

```python
import asyncio
import signal

manager = SandboxManager(
    pools={"python": PoolConfig(target_ready=3)},
)

async def shutdown():
    print("Shutting down pool...")
    await manager.shutdown()

def signal_handler():
    asyncio.create_task(shutdown())

async def main():
    await manager.start()

    loop = asyncio.get_event_loop()
    loop.add_signal_handler(signal.SIGINT, signal_handler)
    loop.add_signal_handler(signal.SIGTERM, signal_handler)

    # Your application loop here
    while True:
        await asyncio.sleep(1)

asyncio.run(main())
```

---

## Error Handling

```python
from do_app_sandbox import (
    PoolExhaustedError,
    PoolShutdownError,
    WarmUpTimeoutError,
    SandboxCreationError,
)

try:
    sandbox = await manager.acquire(image="python")
    sandbox.delete()
except PoolExhaustedError:
    # Pool empty and on_empty="fail"
    pass
except PoolShutdownError:
    # Manager is shutting down
    pass

try:
    await manager.warm_up(timeout=60)
except WarmUpTimeoutError:
    # Pools didn't reach target in time
    pass
```

---

## High-Throughput Example

```python
from do_app_sandbox import SandboxManager, PoolConfig

async def run_agent_system():
    manager = SandboxManager(
        pools={
            "python": PoolConfig(
                target_ready=10,      # Keep 10 warm for burst handling
                max_ready=50,         # Never exceed 50 (cost ceiling)
                idle_timeout=60,      # Scale down after 1 min idle
                on_empty="create",    # Fall back to cold start if needed
            ),
        },
        max_total_sandboxes=100,      # Global limit across all images
        max_concurrent_creates=10,    # Don't overwhelm the API
        sandbox_defaults={
            "region": "nyc",
            "instance_size": "apps-s-1vcpu-2gb",
        },
    )

    await manager.start()
    await manager.warm_up(timeout=300)  # Wait for initial pool fill

    # Handle agent requests
    async def handle_agent_task(task):
        sandbox = await manager.acquire(image="python")
        try:
            result = sandbox.exec(f"python /app/run_task.py {task.id}")
            return result
        finally:
            sandbox.delete()  # Single-use: always delete

    # ... run your agent system ...

    await manager.shutdown()
```
