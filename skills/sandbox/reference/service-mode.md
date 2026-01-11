# Service Mode Reference

Real-time streaming and port exposure for AI agents.

## When to Use Service Mode

- **Streaming output** — Show execution progress to users in real-time
- **Port exposure** — Give users preview URLs for apps running inside sandbox
- **Long-running commands** — Stream output while waiting for completion

For simple command execution without streaming, use WORKER mode (default).

---

## Mode Comparison

| Aspect | WORKER (default) | SERVICE |
|--------|------------------|---------|
| Execution | `doctl apps console` | HTTP API with SSE |
| Output | Returns when complete | Streams in real-time |
| Port access | Not available | `expose_port()` supported |
| Startup | ~30s | ~30s |
| Best for | Background tasks, batch jobs | Interactive AI agents |

---

## Basic Usage

```python
from do_app_sandbox import Sandbox, SandboxMode

# Create sandbox in service mode
sandbox = Sandbox.create(
    image="python",
    mode=SandboxMode.SERVICE
)

# Regular exec still works (returns when complete)
result = sandbox.exec("python3 --version")
print(result.stdout)

# Clean up
sandbox.delete()
```

---

## Streaming Execution

Stream stdout/stderr in real-time via SSE:

```python
from do_app_sandbox import Sandbox, SandboxMode

sandbox = Sandbox.create(image="python", mode=SandboxMode.SERVICE)

# Stream command output
for event in sandbox.exec_stream("pip install pandas numpy"):
    if event.type == "stdout":
        print(event.data, end="", flush=True)
    elif event.type == "stderr":
        print(f"[stderr] {event.data}", end="", flush=True)
    elif event.type == "exit":
        print(f"\nExited with code: {event.data}")

sandbox.delete()
```

### StreamEvent Types

| Type | Description |
|------|-------------|
| `stdout` | Standard output data |
| `stderr` | Standard error data |
| `exit` | Command completed, data is exit code |
| `error` | Execution error occurred |

---

## Port Exposure

Get a public URL for an internal service:

```python
from do_app_sandbox import Sandbox, SandboxMode

sandbox = Sandbox.create(image="python", mode=SandboxMode.SERVICE)

# Start a web server inside sandbox
sandbox.exec("python3 -m http.server 3000 &")

# Get public URL
port_info = sandbox.expose_port(3000)
print(f"Preview URL: {port_info.url}")
# https://sandbox-xxx.ondigitalocean.app/proxy/3000

sandbox.delete()
```

---

## AI Code Interpreter Pattern

Complete pattern for streaming code execution in an AI agent:

```python
from do_app_sandbox import Sandbox, SandboxMode, SandboxError

def execute_user_code(sandbox: Sandbox, code: str) -> dict:
    """Execute code and stream output to user."""

    # Write code to file
    sandbox.filesystem.write_file("/tmp/user_code.py", code)

    output = []
    exit_code = None

    try:
        for event in sandbox.exec_stream("python3 /tmp/user_code.py"):
            if event.type in ("stdout", "stderr"):
                output.append(event.data)
                # Stream to user in real-time here
                yield {"type": "output", "data": event.data}
            elif event.type == "exit":
                exit_code = int(event.data)
            elif event.type == "error":
                yield {"type": "error", "data": event.data}
                return
    except SandboxError as e:
        yield {"type": "error", "data": str(e)}
        return

    yield {
        "type": "complete",
        "exit_code": exit_code,
        "output": "".join(output)
    }


# Usage
sandbox = Sandbox.create(image="python", mode=SandboxMode.SERVICE)

for event in execute_user_code(sandbox, "print('Hello, world!')"):
    print(event)

sandbox.delete()
```

---

## Error Handling

```python
from do_app_sandbox import (
    Sandbox,
    SandboxMode,
    ServiceNotAvailableError,
    SandboxError
)

try:
    sandbox = Sandbox.create(image="python", mode=SandboxMode.SERVICE)

    for event in sandbox.exec_stream("python3 script.py"):
        print(event.data, end="")

except ServiceNotAvailableError:
    # exec_stream() called on WORKER mode sandbox
    print("Service mode required for streaming")
except SandboxError as e:
    print(f"Sandbox error: {e}")
finally:
    sandbox.delete()
```

---

## Limitations

- Service mode requires HTTP API inside container (built into default images)
- Port exposure works only for ports the container is listening on
- Streaming adds slight latency vs. buffered exec()
