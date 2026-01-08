# Sandbox Use Cases

Practical patterns for common sandbox applications.

---

## AI Code Interpreter

The primary use case: execute user-submitted code safely in isolation.

```python
import asyncio
from do_app_sandbox import SandboxManager, PoolConfig

class AICodeInterpreter:
    """Sandbox-backed code execution for AI agents."""

    def __init__(self):
        self.manager = SandboxManager(
            pools={"python": PoolConfig(target_ready=2)},
        )
        self._started = False

    async def start(self):
        await self.manager.start()
        self._started = True

    async def run(self, code: str, packages: list[str] = None) -> dict:
        if not self._started:
            await self.start()

        sandbox = await self.manager.acquire(image="python")
        try:
            # Install requested packages
            if packages:
                install_cmd = f"pip install {' '.join(packages)}"
                sandbox.exec(install_cmd)

            # Write and execute code
            sandbox.filesystem.write_file("/tmp/code.py", code)
            result = sandbox.exec("python3 /tmp/code.py", timeout=30)

            return {
                "success": result.exit_code == 0,
                "stdout": result.stdout,
                "stderr": result.stderr,
                "exit_code": result.exit_code
            }
        finally:
            sandbox.delete()  # Sandboxes are single-use!

    async def shutdown(self):
        await self.manager.shutdown()

# Integration with LLM
async def main():
    interpreter = AICodeInterpreter()
    await interpreter.start()

    # Agent decides to run code
    response = await interpreter.run(
        code="import pandas as pd; print(pd.DataFrame({'a': [1,2,3]}))",
        packages=["pandas"]
    )
    print(response["stdout"])

    await interpreter.shutdown()

asyncio.run(main())
```

---

## Multi-Step Agent Workflow

For workflows requiring state persistence across multiple steps, use a **single sandbox** for the entire session:

```python
from do_app_sandbox import Sandbox

class IterativeAgent:
    """Agent that can modify and re-run code based on results.

    Uses a single sandbox for the session to preserve state.
    State persists WITHIN the sandbox, not across sandboxes.
    """

    def __init__(self):
        self.sandbox = None

    def start_session(self):
        """Create a sandbox for the entire session."""
        self.sandbox = Sandbox.create(image="python")

    def run_code(self, code: str) -> dict:
        """Execute code, preserving state from previous runs."""
        self.sandbox.filesystem.write_file("/tmp/code.py", code)
        result = self.sandbox.exec("python3 /tmp/code.py")
        return {
            "output": result.stdout,
            "error": result.stderr,
            "success": result.exit_code == 0
        }

    def install_package(self, package: str) -> bool:
        """Install a package (persists for session)."""
        result = self.sandbox.exec(f"pip install {package}")
        return result.exit_code == 0

    def read_file(self, path: str) -> str:
        """Read a file created by previous code execution."""
        return self.sandbox.filesystem.read_file(path)

    def end_session(self):
        """Delete sandbox when done."""
        if self.sandbox:
            self.sandbox.delete()
            self.sandbox = None

# Usage: Agent maintains state across multiple interactions
agent = IterativeAgent()
agent.start_session()

# First interaction: write data
agent.run_code("""
import json
data = {'step': 1, 'value': 42}
with open('/tmp/state.json', 'w') as f:
    json.dump(data, f)
print('Data saved')
""")

# Second interaction: read and modify (state persists within sandbox!)
agent.run_code("""
import json
with open('/tmp/state.json') as f:
    data = json.load(f)
data['step'] = 2
data['value'] *= 2
print(f"Updated value: {data['value']}")
""")

agent.end_session()  # Deletes the sandbox
```

---

## Integration Testing

Use sandboxes for isolated integration tests in CI/CD:

```python
from do_app_sandbox import Sandbox
import pytest

@pytest.fixture
def sandbox():
    """Provide a fresh sandbox for each test."""
    sb = Sandbox.create(image="python")
    yield sb
    sb.delete()

def test_api_client(sandbox):
    """Test API client in isolated environment."""
    # Upload test code
    sandbox.filesystem.write_file("/app/client.py", """
import requests
def fetch_data(url):
    return requests.get(url).json()
""")

    sandbox.filesystem.write_file("/app/test_client.py", """
from client import fetch_data
result = fetch_data('https://api.github.com')
assert 'current_user_url' in result
print('PASS')
""")

    # Install dependencies and run
    sandbox.exec("pip install requests")
    result = sandbox.exec("python3 test_client.py", cwd="/app")

    assert "PASS" in result.stdout
    assert result.exit_code == 0

def test_data_processing(sandbox):
    """Test data processing pipeline."""
    sandbox.exec("pip install pandas numpy")

    sandbox.filesystem.write_file("/app/process.py", """
import pandas as pd
import numpy as np

# Create test data
df = pd.DataFrame(np.random.rand(100, 3), columns=['a', 'b', 'c'])

# Process
result = df.describe()
assert len(result) == 8  # describe() returns 8 rows
print('PASS')
""")

    result = sandbox.exec("python3 process.py", cwd="/app")
    assert "PASS" in result.stdout
```

---

## Batch Processing

Process multiple items using the hot pool for speed:

```python
import asyncio
import json
from do_app_sandbox import SandboxManager, PoolConfig

async def process_item(manager, item):
    """Process a single item in a sandbox."""
    sandbox = await manager.acquire(image="python")
    try:
        sandbox.filesystem.write_file("/tmp/input.json", json.dumps(item))
        sandbox.filesystem.write_file("/tmp/process.py", """
import json
with open('/tmp/input.json') as f:
    data = json.load(f)
result = {'id': data['id'], 'processed': data['value'] * 2}
print(json.dumps(result))
""")
        result = sandbox.exec("python3 /tmp/process.py")
        return json.loads(result.stdout)
    finally:
        sandbox.delete()  # Always delete - sandboxes are single-use!

async def main():
    # Process batch
    items = [{"id": i, "value": i * 10} for i in range(10)]

    manager = SandboxManager(
        pools={"python": PoolConfig(target_ready=3)},
    )
    await manager.start()

    # Process items concurrently
    tasks = [process_item(manager, item) for item in items]
    results = await asyncio.gather(*tasks)

    print(results)
    await manager.shutdown()

asyncio.run(main())
```

---

## Data Analysis Sandbox

Provide analysts with isolated environments:

```python
from do_app_sandbox import Sandbox

def create_analysis_environment():
    """Create a sandbox pre-configured for data analysis."""
    sandbox = Sandbox.create(image="python", instance_size="apps-s-1vcpu-2gb")

    # Install analysis packages
    sandbox.exec("pip install pandas numpy matplotlib seaborn scikit-learn")

    return sandbox

def run_analysis(sandbox, code: str, data_file: str = None):
    """Run analysis code, optionally with input data."""
    if data_file:
        sandbox.filesystem.upload_file(data_file, "/tmp/data.csv")

    sandbox.filesystem.write_file("/tmp/analysis.py", code)
    result = sandbox.exec("python3 /tmp/analysis.py")

    # Check for generated files
    files = sandbox.filesystem.list_dir("/tmp")
    outputs = [f for f in files if f['name'].endswith(('.png', '.csv', '.json'))]

    return {
        "stdout": result.stdout,
        "stderr": result.stderr,
        "output_files": outputs
    }

# Usage
sandbox = create_analysis_environment()

result = run_analysis(sandbox, """
import pandas as pd
import matplotlib.pyplot as plt

# Generate sample data
df = pd.DataFrame({
    'x': range(100),
    'y': [i**2 + i for i in range(100)]
})

# Create plot
plt.figure(figsize=(10, 6))
plt.plot(df['x'], df['y'])
plt.savefig('/tmp/plot.png')
print('Analysis complete')
""")

# Download generated plot
sandbox.filesystem.download_file("/tmp/plot.png", "./local_plot.png")

# Clean up when done with analysis session
sandbox.delete()
```

---

## Key Pattern Summary

| Pattern | Sandbox Type | Lifecycle |
|---------|-------------|-----------|
| Code Interpreter | Hot Pool | acquire → exec → delete (per request) |
| Multi-step workflow | Cold Sandbox | create once → multiple execs → delete |
| Integration tests | Cold Sandbox | create → test → delete (per test) |
| Batch processing | Hot Pool | acquire → process → delete (per item) |
| Data analysis | Cold Sandbox | create → long session → delete |

**Remember:** Sandboxes are single-use. Always call `delete()` when done.
