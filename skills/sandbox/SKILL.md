---
name: app-platform-sandbox
description: Create and manage disposable cloud sandboxes on DigitalOcean App Platform for AI agents, code execution, and parallel experimentation
version: 1.0.0
author: Bikram Gupta
source_of_truth: https://github.com/bikramkgupta/do-app-sandbox
triggers:
  - "sandbox"
  - "create sandbox"
  - "disposable environment"
  - "execute code remotely"
  - "parallel experiments"
  - "app platform sandbox"
  - "agentic workflow"
  - "isolated environment"
---

# App Platform Sandbox Skill

## Overview

This skill enables AI agents to create, manage, and use disposable cloud sandboxes on DigitalOcean App Platform. Sandboxes provide isolated execution environments for running code, processing data, and conducting parallel experiments without affecting local systems.

**Source of Truth**: [do-app-sandbox repository](https://github.com/bikramkgupta/do-app-sandbox)

### What is a Sandbox?

A sandbox is a disposable, isolated container running on App Platform that you can:
- Create on demand (30-45 seconds)
- Execute arbitrary commands
- Upload/download files
- Run background processes
- Delete when finished

### Architecture

```
Agent/SDK → Executor (pexpect) → doctl apps console → Container
                                                          │
                                                    ┌─────┴─────┐
                                                    │ Port 8080 │ (user apps)
                                                    │ Port 9090 │ (health server)
                                                    └───────────┘
```

---

## Opinionated Defaults

| Setting | Default | Rationale |
|---------|---------|-----------|
| Python version manager | **uv** | Fast, modern, handles venvs automatically |
| Node version manager | **nvm** | Industry standard for Node.js version management |
| Working directory | `/home/sandbox/app` (symlinked to `/app`) | Consistent, predictable location |
| Default region | `atl1` | Low latency for US-based operations |
| Instance size | `apps-s-1vcpu-1gb` | Cost-effective for most workloads |
| Component type | `service` | Provides HTTP endpoint; use `worker` for background jobs |
| Large file threshold | ~250KB | Files larger use Spaces for transfer |
| Presigned URL expiry | 15 minutes | Security-conscious default |

---

## Prerequisites

| Requirement | Purpose | Installation |
|-------------|---------|--------------|
| Python 3.10+ | SDK runtime | System package manager |
| doctl | App Platform operations | `brew install doctl` / [docs.digitalocean.com](https://docs.digitalocean.com/reference/doctl/how-to/install/) |
| doctl auth | Authentication | `doctl auth init` |

### Optional: Spaces for Large Files

```bash
export SPACES_ACCESS_KEY="your-access-key"
export SPACES_SECRET_KEY="your-secret-key"
export SPACES_BUCKET="your-bucket-name"
export SPACES_REGION="nyc3"  # or: sfo3, ams3, sgp1, fra1
```

---

## Installation

```bash
# From PyPI
pip install do-app-sandbox

# From source with uv (recommended)
uv pip install -e ".[spaces]"

# Run without installing
uv sync && uv run python -m do_app_sandbox --help
```

---

## Core Workflows

### Workflow 1: Create and Use a Sandbox

**SDK (Sync)**

```python
from do_app_sandbox import Sandbox

# Create sandbox (uses GHCR public images by default)
sandbox = Sandbox.create(image="python", name="my-sandbox")

# Execute commands
result = sandbox.exec("python3 --version")
print(result.stdout)  # Python 3.13.x

# File operations
sandbox.filesystem.write_file("/app/script.py", "print('Hello World')")
result = sandbox.exec("python3 /app/script.py")
print(result.stdout)  # Hello World

# Clean up
sandbox.delete()
```

**SDK (Async)**

```python
import asyncio
from do_app_sandbox import AsyncSandbox

async def main():
    sandbox = await AsyncSandbox.create(image="python")
    result = await sandbox.exec("echo 'Hello from async!'")
    print(result.stdout)
    await sandbox.delete()

asyncio.run(main())
```

**CLI**

```bash
# Create
sandbox create --image python --name my-sandbox

# Execute
sandbox exec my-sandbox "python3 --version"

# Delete
sandbox delete my-sandbox
```

---

### Workflow 2: Context Manager (Auto-Cleanup)

```python
from do_app_sandbox import Sandbox

with Sandbox.create(image="python") as sandbox:
    result = sandbox.exec("python3 -c 'print(42)'")
    print(result.stdout)
# Sandbox automatically deleted on exit
```

---

### Workflow 3: Connect to Existing Sandbox

Reuse sandboxes to avoid 30-45 second creation time:

```python
from do_app_sandbox import Sandbox

# Connect by App ID
sandbox = Sandbox.get_from_id(app_id="a1b2c3d4-e5f6-7890-abcd-ef1234567890")

# Now use it like normal
result = sandbox.exec("whoami")
print(result.stdout)
```

---

### Workflow 4: Python Development Pattern

Python requires virtual environments with uv:

```python
# Upload application files
sandbox.filesystem.write_file("/app/app.py", '''
from flask import Flask
app = Flask(__name__)

@app.route('/')
def hello():
    return 'Hello World!'

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=8080)
''')

sandbox.filesystem.write_file("/app/requirements.txt", "flask>=2.0")

# Create venv and install dependencies
sandbox.exec("cd /app && uv venv .venv")
sandbox.exec("cd /app && source .venv/bin/activate && uv pip install -r requirements.txt")

# Run application
pid = sandbox.launch_process(
    "cd /app && source .venv/bin/activate && python app.py",
    cwd="/app"
)

print(f"App running at: {sandbox.get_url()}")
```

---

### Workflow 5: Node.js Development Pattern

Node.js works with npm/yarn directly (nvm pre-installed):

```python
# Upload application
sandbox.filesystem.write_file("/app/app.js", '''
const express = require('express');
const app = express();

app.get('/', (req, res) => res.send('Hello World!'));

app.listen(8080, () => console.log('Server running on port 8080'));
''')

sandbox.filesystem.write_file("/app/package.json", '''{
  "name": "my-app",
  "dependencies": { "express": "^4.18.0" }
}''')

# Install and run
sandbox.exec("cd /app && npm install")
pid = sandbox.launch_process("node /app/app.js", cwd="/app")

print(f"App running at: {sandbox.get_url()}")
```

---

### Workflow 6: Bulk File Upload

For 10+ files, use zip for efficiency:

```python
import shutil

# Local: Create zip excluding unnecessary files
shutil.make_archive("/tmp/app", "zip", "/path/to/your/project")

# Upload single zip
sandbox.filesystem.upload_file("/tmp/app.zip", "/home/sandbox/app.zip")

# Remote: Unzip in sandbox
sandbox.exec("cd /home/sandbox && unzip -o app.zip -d app && rm app.zip")
```

---

### Workflow 7: Large File Transfers (Spaces)

Files ≥250KB use Spaces as intermediary:

```python
# Configure Spaces at creation
sandbox = Sandbox.create(
    image="python",
    spaces_config={
        "bucket": "my-bucket",
        "region": "nyc3",
        "access_key": "...",
        "secret_key": "..."
    }
)

# Upload large file (uses presigned URLs, no credentials in container)
sandbox.filesystem.upload_large("./large_model.bin", "/models/model.bin")

# Download large results
sandbox.filesystem.download_large("/output/results.tar.gz", "./results.tar.gz")
```

**How it works**:
1. SDK uploads to Spaces via boto3
2. Generates presigned URL (15 min expiry)
3. Sandbox downloads via curl
4. Spaces object deleted after transfer

---

### Workflow 8: Background Processes

Run long-running jobs:

```python
# Launch background process
pid = sandbox.launch_process("python train.py", cwd="/app")
print(f"Training started with PID: {pid}")

# Monitor progress
import time
while True:
    output = sandbox.process_manager.get_output(pid)
    print(output[-500:])  # Last 500 chars
    
    if not sandbox.process_manager.is_running(pid):
        print("Complete!")
        break
    time.sleep(30)

# Kill if needed
sandbox.kill_process(pid)
# Or kill all
sandbox.kill_all_processes()
```

---

### Workflow 9: Worker Sandbox (No HTTP Endpoint)

For background tasks that don't need public URLs:

```python
worker = Sandbox.create(image="python", component_type="worker")

result = worker.exec("python batch_job.py")
print(result.stdout)

# worker.get_url() returns None
```

---

## API Reference

### Sandbox Class

| Method | Parameters | Returns |
|--------|------------|---------|
| `Sandbox.create()` | `image*`, `name?`, `region?`, `instance_size?`, `component_type?`, `wait_ready?`, `timeout?`, `spaces_config?` | `Sandbox` |
| `Sandbox.get_from_id()` | `app_id*`, `component?`, `spaces_config?` | `Sandbox` |
| `sandbox.exec()` | `command*`, `env?`, `cwd?`, `timeout?` | `CommandResult` |
| `sandbox.launch_process()` | `command*`, `cwd?`, `env?` | `int` (PID) |
| `sandbox.list_processes()` | `pattern?` | `list[ProcessInfo]` |
| `sandbox.kill_process()` | `pid*` | `bool` |
| `sandbox.kill_all_processes()` | — | `int` (count) |
| `sandbox.get_url()` | — | `str` or `None` |
| `sandbox.delete()` | — | `None` |
| `sandbox.is_ready()` | — | `bool` |
| `sandbox.wait_ready()` | `timeout?` | `None` |

### FileSystem Class

| Method | Parameters | Returns |
|--------|------------|---------|
| `read_file()` | `path*`, `binary?` | `str` or `bytes` |
| `write_file()` | `path*`, `content*`, `binary?` | `None` |
| `upload_file()` | `local_path*`, `remote_path*` | `None` |
| `download_file()` | `remote_path*`, `local_path*` | `None` |
| `upload_large()` | `local_path*`, `remote_path*`, `progress_callback?`, `cleanup?` | `None` |
| `download_large()` | `remote_path*`, `local_path*`, `progress_callback?`, `cleanup?` | `None` |
| `list_dir()` | `path?` | `list[FileInfo]` |
| `mkdir()` | `path*`, `recursive?` | `None` |
| `rm()` | `path*`, `recursive?`, `force?` | `None` |
| `exists()` | `path*` | `bool` |
| `is_file()` | `path*` | `bool` |
| `is_dir()` | `path*` | `bool` |
| `copy()` | `src*`, `dst*`, `recursive?` | `None` |
| `move()` | `src*`, `dst*` | `None` |
| `has_spaces` | — | `bool` (property) |

### CommandResult

```python
@dataclass
class CommandResult:
    stdout: str
    stderr: str
    exit_code: int
    
    @property
    def success(self) -> bool:
        return self.exit_code == 0
```

---

## CLI Reference

```bash
# Create sandbox
sandbox create --image <python|node> [--name NAME] [--region REGION] [--instance-size SIZE] [--type <service|worker>] [--no-wait]

# List sandboxes
sandbox list [--json]

# Execute command
sandbox exec <name> "<command>" [--id APP_ID] [--timeout SECONDS]

# Delete sandbox
sandbox delete <name> [--id APP_ID] [--all] [--force]
```

---

## Environment Variables

| Variable | Required | Default | Description |
|----------|----------|---------|-------------|
| `DIGITALOCEAN_TOKEN` | No | — | API token (optional if doctl authenticated) |
| `GHCR_OWNER` | No | `bikramkgupta` | GHCR image namespace |
| `GHCR_REGISTRY` | No | `ghcr.io` | GHCR registry host |
| `APP_SANDBOX_REGION` | No | `atl1` | Default region |
| `SPACES_ACCESS_KEY` | For large files | — | Spaces access key |
| `SPACES_SECRET_KEY` | For large files | — | Spaces secret key |
| `SPACES_BUCKET` | For large files | — | Default bucket |
| `SPACES_REGION` | For large files | — | Spaces region |
| `SANDBOX_LARGE_FILE_THRESHOLD` | No | ~250KB | Bytes threshold for Spaces |

---

## Available Images

| Image | Contents |
|-------|----------|
| `python` | Ubuntu 24.04 + Python 3.13 + uv + curl, git, lsof, jq, procps |
| `node` | Ubuntu 24.04 + Node.js 24 + nvm + curl, git, lsof, jq, procps |

Working directory: `/home/sandbox/app` (with `/app` as symlink)

---

## Ports

| Port | Purpose |
|------|---------|
| **8080** | User applications (Flask, Express, etc.) |
| **9090** | Internal health server (handled by sandbox) |

**Important**: Your app MUST listen on port 8080. No health endpoint needed—the sandbox handles health checks on port 9090.

---

## Known Limitations

| Limitation | Details |
|------------|---------|
| Deployment time | 30-45 seconds to create |
| Static port | User apps must use port 8080 |
| Per-command console | Each command opens new session |
| No persistent storage | Data lost when sandbox deleted |
| No GPU support | CPU-only workloads |

---

## Streaming Logs

Use doctl directly for real-time logs:

```bash
doctl apps logs -f <APP_ID> sandbox --type run    # Runtime logs
doctl apps logs -f <APP_ID> sandbox --type build  # Build logs
doctl apps logs -f <APP_ID> sandbox --type deploy # Deploy logs
```

---

## Error Handling

```python
from do_app_sandbox.exceptions import (
    SandboxCreationError,
    SandboxNotFoundError,
    SandboxNotReadyError,
    CommandTimeoutError,
    SpacesNotConfiguredError,
    FileOperationError
)

try:
    sandbox = Sandbox.create(image="python", timeout=60)
except SandboxCreationError as e:
    print(f"Failed to create: {e}")

try:
    result = sandbox.exec("long_command", timeout=30)
except CommandTimeoutError:
    print("Command timed out")

if not sandbox.filesystem.has_spaces:
    print("Configure Spaces for large file transfers")
```

---

## Integration with Other Skills

| From Skill | To Sandbox | Use Case |
|------------|------------|----------|
| **designer** | Generate app spec → test in sandbox | Validate architecture before deployment |
| **migration** | Convert app → test in sandbox | Verify migration works |
| **deployment** | After deploy → sandbox for staging | Pre-production testing |

### Handoff Protocol

When creating a sandbox for testing:

1. Create sandbox with same image as production
2. Upload application code
3. Install dependencies
4. Run tests or manual validation
5. Delete sandbox when done

---

## Security Considerations

1. **No credentials in sandbox**: Spaces uses presigned URLs
2. **Short-lived URLs**: Default 15 min expiry
3. **Isolated containers**: Each sandbox is independent
4. **Auto-cleanup**: Use context managers for guaranteed deletion
5. **doctl required**: All operations go through authenticated doctl

---

## Common Patterns

### Data Processing Pipeline

```python
with Sandbox.create(image="python") as sandbox:
    # Setup
    sandbox.exec("pip install pandas pyarrow")
    
    # Upload data
    sandbox.filesystem.upload_large("./large_dataset.parquet", "/data/input.parquet")
    
    # Process
    sandbox.filesystem.write_file("/app/process.py", '''
import pandas as pd
df = pd.read_parquet("/data/input.parquet")
result = df.groupby("category").sum()
result.to_parquet("/data/output.parquet")
print(f"Processed {len(df)} rows")
''')
    
    result = sandbox.exec("python /app/process.py")
    print(result.stdout)
    
    # Download results
    sandbox.filesystem.download_large("/data/output.parquet", "./output.parquet")
# Auto-deleted
```

### Parallel Experiments

```python
import asyncio
from do_app_sandbox import AsyncSandbox

async def run_experiment(config):
    async with await AsyncSandbox.create(image="python") as sandbox:
        await sandbox.filesystem.write_file("/app/config.json", json.dumps(config))
        result = await sandbox.exec("python /app/experiment.py")
        return json.loads(result.stdout)

# Run 5 experiments in parallel
configs = [{"lr": 0.01}, {"lr": 0.001}, {"lr": 0.0001}, ...]
results = await asyncio.gather(*[run_experiment(c) for c in configs])
```

---

## Next Steps

- For debugging running apps: use **troubleshooting** skill
- For local development: use **devcontainers** skill
- For cloud hot reload: use **hot-reload** skill
- For deploying to production: use **deployment** skill
