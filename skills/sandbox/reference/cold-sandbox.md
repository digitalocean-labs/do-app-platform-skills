# Cold Sandbox Reference

Create individual sandboxes with `Sandbox.create()`. Each sandbox takes ~30 seconds to provision.

## When to Use Cold Sandbox

- One-off script execution
- CI/CD integration testing (one sandbox per job)
- Simple use cases where 30s startup is acceptable
- When you don't need multiple sandboxes concurrently

For interactive AI agents requiring instant response, use [Hot Pool](hot-pool.md) instead.

---

## Basic Lifecycle

```python
from do_app_sandbox import Sandbox

# 1. Create (~30 seconds)
sandbox = Sandbox.create(
    image="python",                    # or "node"
    name="test-sandbox",               # optional, auto-generated if omitted
    region="nyc",                      # nyc, sfo, ams, sgp, etc.
    instance_size="apps-s-1vcpu-1gb"   # see shared/instance-sizes.yaml
)

# 2. Use
result = sandbox.exec("python3 --version")
print(f"Exit code: {result.exit_code}")
print(f"Output: {result.stdout}")
print(f"Errors: {result.stderr}")

# 3. Clean up (important!)
sandbox.delete()
```

---

## Create Options

```python
sandbox = Sandbox.create(
    image="python",              # Required: "python" or "node"
    name="my-sandbox",           # Optional: custom name
    region="nyc",                # Optional: default nyc
    instance_size="apps-s-1vcpu-1gb"  # Optional: instance size
)
```

| Parameter | Required | Default | Options |
|-----------|----------|---------|---------|
| `image` | Yes | — | `"python"`, `"node"` |
| `name` | No | auto-generated | any string |
| `region` | No | `"nyc"` | `nyc`, `sfo`, `ams`, `sgp`, etc. |
| `instance_size` | No | `apps-s-1vcpu-1gb` | see instance-sizes.yaml |

---

## Command Execution

### Basic Execution

```python
result = sandbox.exec("ls -la /tmp")
print(result.stdout)
```

### With Working Directory

```python
result = sandbox.exec("python3 script.py", cwd="/app")
```

### With Timeout

```python
result = sandbox.exec("sleep 60", timeout=30)  # Timeout in seconds
```

### Chained Commands

```python
# Install and use in one command
result = sandbox.exec("pip install requests && python3 -c 'import requests; print(requests.__version__)'")
```

---

## File Operations

### Write File

```python
sandbox.filesystem.write_file("/tmp/script.py", """
import json
data = {"hello": "world"}
print(json.dumps(data))
""")

result = sandbox.exec("python3 /tmp/script.py")
```

### Read File

```python
content = sandbox.filesystem.read_file("/tmp/output.txt")
print(content)
```

### List Directory

```python
files = sandbox.filesystem.list_dir("/tmp")
for f in files:
    print(f"{f['name']} ({f['type']})")
```

### Download File

```python
# Download to local machine
sandbox.filesystem.download_file("/tmp/results.json", "./local-results.json")
```

### Upload File

```python
# Upload from local machine
sandbox.filesystem.upload_file("./local-script.py", "/tmp/script.py")
```

---

## Error Handling

```python
from do_app_sandbox import Sandbox, SandboxError

try:
    sandbox = Sandbox.create(image="python")
    result = sandbox.exec("python3 script.py")

    if result.exit_code != 0:
        print(f"Command failed: {result.stderr}")

except SandboxError as e:
    print(f"Sandbox error: {e}")
finally:
    if sandbox:
        sandbox.delete()
```

---

## Context Manager Pattern

```python
from contextlib import contextmanager
from do_app_sandbox import Sandbox

@contextmanager
def sandbox_context(image="python"):
    sandbox = Sandbox.create(image=image)
    try:
        yield sandbox
    finally:
        sandbox.delete()

# Usage
with sandbox_context() as sandbox:
    result = sandbox.exec("python3 -c 'print(42)'")
    print(result.stdout)
# Automatically cleaned up
```

---

## Common Patterns

### Install Package and Run

```python
sandbox.exec("pip install pandas numpy")
result = sandbox.exec("""python3 -c '
import pandas as pd
import numpy as np
df = pd.DataFrame(np.random.rand(5, 3))
print(df.describe())
'""")
```

### Run Multi-file Project

```python
# Upload project files
sandbox.filesystem.write_file("/app/main.py", main_code)
sandbox.filesystem.write_file("/app/utils.py", utils_code)
sandbox.filesystem.write_file("/app/requirements.txt", "requests\npandas")

# Install and run
sandbox.exec("pip install -r /app/requirements.txt", cwd="/app")
result = sandbox.exec("python3 main.py", cwd="/app")
```

### Capture Structured Output

```python
import json

sandbox.filesystem.write_file("/tmp/analyze.py", """
import json
result = {"status": "success", "count": 42}
print(json.dumps(result))
""")

result = sandbox.exec("python3 /tmp/analyze.py")
data = json.loads(result.stdout)
print(data["count"])  # 42
```
