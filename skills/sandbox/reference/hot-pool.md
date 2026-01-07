# Hot Pool Reference

Use `SandboxManager` to maintain pre-warmed sandboxes for instant acquisition (~50ms vs ~30s cold start).

## When to Use Hot Pool

- AI code interpreters requiring instant response
- Interactive agent workflows with multiple executions
- High-throughput scenarios needing concurrent sandboxes
- Any use case where 30s latency is unacceptable

For one-off executions where startup time doesn't matter, use [Cold Sandbox](cold-sandbox.md) instead.

---

## Basic Pool Lifecycle

```python
from do_app_sandbox import SandboxManager

# 1. Initialize pool (sandboxes start provisioning)
manager = SandboxManager(
    pool_size=3,        # Number of pre-warmed sandboxes
    image="python"
)
manager.start()

# 2. Acquire sandbox instantly (~50ms)
sandbox = manager.acquire()

# 3. Use it
result = sandbox.exec("python3 -c 'print(2+2)'")
print(result.stdout)

# 4. Release back to pool
manager.release(sandbox)

# 5. Shutdown when done (cleans up all sandboxes)
manager.shutdown()
```

---

## Pool Configuration

```python
manager = SandboxManager(
    pool_size=5,                          # Number of sandboxes to maintain
    image="python",                       # "python" or "node"
    region="nyc",                         # Optional: region
    instance_size="apps-s-1vcpu-1gb"      # Optional: instance size
)
```

| Parameter | Default | Description |
|-----------|---------|-------------|
| `pool_size` | required | Number of pre-warmed sandboxes |
| `image` | required | `"python"` or `"node"` |
| `region` | `"nyc"` | Deployment region |
| `instance_size` | `"apps-s-1vcpu-1gb"` | Container size |

---

## Pool Sizing Guidance

| Use Case | Recommended Pool Size | Rationale |
|----------|----------------------|-----------|
| Single AI agent | 2-3 | One active + buffer for replenishment |
| Multiple concurrent users | users × 1.5 | Account for overlap |
| Burst workloads | peak_concurrent × 2 | Handle spikes |
| Development/testing | 1-2 | Minimize cost |

**Cost calculation:**
```
Pool cost = pool_size × instance_cost × hours_running
Example: 3 sandboxes × $0.02/hr × 8 hrs = $0.48/day
```

---

## Acquire/Release Pattern

### Basic Pattern

```python
sandbox = manager.acquire()
try:
    result = sandbox.exec("python3 script.py")
    # Process result
finally:
    manager.release(sandbox)
```

### Context Manager

```python
from contextlib import contextmanager

@contextmanager
def pooled_sandbox(manager):
    sandbox = manager.acquire()
    try:
        yield sandbox
    finally:
        manager.release(sandbox)

# Usage
with pooled_sandbox(manager) as sandbox:
    result = sandbox.exec("python3 -c 'print(42)'")
```

### Async Pattern

```python
import asyncio
from do_app_sandbox import SandboxManager

async def run_code(manager, code):
    sandbox = manager.acquire()
    try:
        result = sandbox.exec(f"python3 -c '{code}'")
        return result.stdout
    finally:
        manager.release(sandbox)

async def main():
    manager = SandboxManager(pool_size=3, image="python")
    manager.start()

    # Run multiple code snippets concurrently
    tasks = [
        run_code(manager, "print(1+1)"),
        run_code(manager, "print(2+2)"),
        run_code(manager, "print(3+3)")
    ]
    results = await asyncio.gather(*tasks)
    print(results)

    manager.shutdown()

asyncio.run(main())
```

---

## Pool Exhaustion Handling

When all sandboxes are in use:

```python
sandbox = manager.acquire(timeout=60)  # Wait up to 60s for available sandbox

if sandbox is None:
    # Pool exhausted, fall back to cold creation
    sandbox = Sandbox.create(image="python")
    is_pooled = False
else:
    is_pooled = True

try:
    result = sandbox.exec("python3 -c 'print(42)'")
finally:
    if is_pooled:
        manager.release(sandbox)
    else:
        sandbox.delete()
```

---

## State Management

**Important:** Sandboxes in a pool maintain state between uses. Clean up after each use:

```python
sandbox = manager.acquire()
try:
    # Install packages for this task
    sandbox.exec("pip install pandas")
    result = sandbox.exec("python3 analyze.py")
finally:
    # Clean up before releasing
    sandbox.exec("rm -rf /tmp/* /app/*")
    sandbox.exec("pip freeze | xargs pip uninstall -y 2>/dev/null || true")
    manager.release(sandbox)
```

Or configure the manager to reset sandboxes on release:

```python
manager = SandboxManager(
    pool_size=3,
    image="python",
    reset_on_release=True  # Cleans sandbox before returning to pool
)
```

---

## AI Agent Workflow Example

```python
from do_app_sandbox import SandboxManager

class CodeInterpreter:
    def __init__(self):
        self.manager = SandboxManager(pool_size=2, image="python")
        self.manager.start()

    def execute(self, code: str) -> dict:
        sandbox = self.manager.acquire()
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
            sandbox.exec("rm -f /tmp/user_code.py")
            self.manager.release(sandbox)

    def shutdown(self):
        self.manager.shutdown()

# Usage
interpreter = CodeInterpreter()
result = interpreter.execute("print('Hello from sandbox!')")
print(result)
interpreter.shutdown()
```

---

## Monitoring Pool Health

```python
# Check pool status
status = manager.status()
print(f"Available: {status['available']}")
print(f"In use: {status['in_use']}")
print(f"Total: {status['total']}")

# Scale pool dynamically
if status['available'] < 2:
    manager.scale(pool_size=status['total'] + 2)
```

---

## Graceful Shutdown

```python
import signal

manager = SandboxManager(pool_size=3, image="python")
manager.start()

def shutdown_handler(signum, frame):
    print("Shutting down pool...")
    manager.shutdown()
    exit(0)

signal.signal(signal.SIGINT, shutdown_handler)
signal.signal(signal.SIGTERM, shutdown_handler)

# Your application loop here
```
