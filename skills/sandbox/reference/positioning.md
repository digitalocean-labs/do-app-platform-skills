# Sandbox vs Lambda: Positioning Guide

When to use DO App Platform Sandboxes vs serverless functions.

---

## Quick Decision

```
Need to run code in isolation?
         │
         ▼
    Duration > 15 minutes?
    ├── YES → Sandbox (Lambda has hard 15-min limit)
    └── NO  → Continue
              │
              ▼
         Need state persistence between calls?
         ├── YES → Sandbox (Lambda is stateless)
         └── NO  → Continue
                   │
                   ▼
              Need to install packages at runtime?
              ├── YES → Sandbox (Lambda requires image rebuild)
              └── NO  → Continue
                        │
                        ▼
                   Sub-second cold start critical?
                   ├── YES → Lambda (100-500ms vs 30s)
                   └── NO  → Continue
                             │
                             ▼
                        High concurrency (1000+)?
                        ├── YES → Lambda (auto-scales)
                        └── NO  → Sandbox
```

---

## Comparison Table

| Dimension | AWS Lambda | DO App Sandbox |
|-----------|------------|----------------|
| Cold start | 100-1000ms (optimized) | ~30s raw, ~50ms with pool |
| Max duration | 15 minutes (hard limit) | Unlimited |
| Billing | Per 1ms | Per hour (~$0.01-0.03) |
| State persistence | None | During sandbox lifetime |
| Shell access | No | Yes (full bash) |
| Package install | At build time only | At runtime |
| Custom images | Yes (ECR) | Yes (any registry) |
| Network egress | VPC config required | Direct internet |
| Concurrency | 1000+ per region | Limited by pool size |

---

## Sandbox Wins

### Long-Running Workloads

Lambda's 15-minute limit is a hard ceiling. Agents that need to work for hours have no Lambda option.

```python
# Sandbox: Run for hours
sandbox = Sandbox.create(image="python")
sandbox.exec("python3 long_running_job.py")  # Can run indefinitely
```

### Stateful Execution

Lambda is stateless. If your agent needs to iterate—install a package, run code, check results, modify, repeat—Lambda forces serialize/deserialize between invocations.

```python
# Sandbox: State persists within one sandbox session
sandbox = Sandbox.create(image="python")
sandbox.exec("pip install pandas")  # Installed
sandbox.exec("python3 -c 'import pandas'")  # Still there
sandbox.exec("echo 'data' > /tmp/file.txt")  # File persists
sandbox.exec("cat /tmp/file.txt")  # Can read it later
sandbox.delete()  # Always delete when done
```

**Note:** State persists within a single sandbox's lifetime. Sandboxes are single-use—once deleted, state is gone. Hot pools provide fast acquisition of *new* sandboxes, not state reuse.

### Interactive/Iterative Workflows

Agents that operate like a human developer—run code, read errors, fix code, run again—fit sandboxes better than Lambda's request/response model.

```python
# Agent workflow in sandbox
result = sandbox.exec("python3 code.py")
if result.exit_code != 0:
    # Analyze error, modify code, try again
    sandbox.filesystem.write_file("/app/code.py", fixed_code)
    result = sandbox.exec("python3 code.py")
```

### Runtime Package Installation

An agent that needs to `pip install obscure-package` can do it in a sandbox. Lambda requires rebuilding the image.

```python
# Sandbox: Install on demand
sandbox.exec("pip install some-obscure-package==1.2.3")
sandbox.exec("python3 -c 'import some_obscure_package'")
```

### Custom Toolchains

Bring any Docker image with specialized tools. Lambda's runtime constraints are limiting for exotic stacks.

---

## Lambda Wins

### Sub-Second Cold Start

With provisioned concurrency and snap-start, Lambda can hit 100-500ms. Sandbox's 30s raw cold start is an eternity for request/response APIs.

**Mitigation:** Use SandboxManager hot pool (~50ms acquire).

### Scale

Lambda scales to thousands of concurrent executions automatically. Sandbox pool manager is manually configured and limited.

**Mitigation:** Only relevant if you need 100+ concurrent executions.

### Cost at Scale

For short tasks (< 30 seconds), Lambda's per-ms billing destroys hourly container billing.

```
Lambda: 1000 executions × 5 seconds × $0.0000166/GB-s = $0.083
Sandbox: 1 hour running = $0.02 (even if idle most of the time)
```

**Mitigation:** Sandbox wins for long-running or continuous workloads.

### No Infrastructure Management

Lambda is truly serverless. Sandbox SDK requires users to understand pools, scaling, and cost tradeoffs.

---

## Cost Estimation

### Sandbox Costs

```
Instance: apps-s-1vcpu-1gb @ ~$0.02/hour

Cold sandbox (one-off):
  - 1 sandbox × 1 hour = $0.02

Hot pool (always-on):
  - 3 sandboxes × 8 hours/day × 30 days = $14.40/month

Hot pool (business hours only):
  - 3 sandboxes × 8 hours × 22 workdays = $10.56/month
```

### Break-Even Analysis

```
When does sandbox beat Lambda?

Lambda: 1000 executions/day × 10s each × $0.0000166/GB-s = $0.17/day
Sandbox: 3 sandboxes × 8 hours × $0.02 = $0.48/day

Lambda wins for: Short, frequent, stateless tasks
Sandbox wins for: Long, stateful, iterative workflows
```

---

## Decision Matrix

| Your Workload | Recommendation |
|---------------|----------------|
| API endpoint (< 30s response) | Lambda |
| AI code interpreter | Sandbox (hot pool) |
| Multi-step agent workflow | Sandbox |
| ETL job (> 15 min) | Sandbox |
| High-traffic webhook | Lambda |
| Development/testing environment | Sandbox |
| Batch processing (many short tasks) | Lambda |
| Interactive debugging | Sandbox |
