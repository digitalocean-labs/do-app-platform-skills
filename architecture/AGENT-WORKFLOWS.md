# Agent Workflows for App Platform

Structured workflows for AI agents working with DigitalOcean App Platform. Designed for efficient context management within 160K token limits.

---

## Core Pattern: Orchestrator + Subagent + Verifier

Complex App Platform tasks should use a three-tier pattern:

```
┌─────────────────────────────────────────────────────────────────┐
│  ORCHESTRATOR (main agent)                                       │
│  - Receives user request                                         │
│  - Decomposes into phases                                        │
│  - Dispatches subagents                                          │
│  - Aggregates results                                            │
│  - NEVER writes code directly                                    │
└─────────────────────────────────────────────────────────────────┘
          │                          │                    │
          ▼                          ▼                    ▼
┌──────────────────┐    ┌──────────────────┐    ┌──────────────────┐
│  SUBAGENT        │    │  SUBAGENT        │    │  SUBAGENT        │
│  (architect)     │    │  (code-writer)   │    │  (deployer)      │
│  - Focused task  │    │  - Focused task  │    │  - Focused task  │
│  - Reads skills  │    │  - Reads skills  │    │  - Reads skills  │
└──────────────────┘    └────────┬─────────┘    └────────┬─────────┘
                                 │                       │
                                 ▼                       ▼
                        ┌──────────────────┐    ┌──────────────────┐
                        │  VERIFIER        │    │  VERIFIER        │
                        │  - Runs tests    │    │  - Smoke tests   │
                        │  - Feedback loop │    │  - Health checks │
                        └──────────────────┘    └──────────────────┘
```

### Why This Pattern?

| Problem | Solution |
|---------|----------|
| 160K token limit | Subagents load only relevant context |
| Complex tasks fail | Break into verifiable phases |
| No feedback loops | Builder-verifier pairing catches issues |
| Hard to restart | State tracked between phases |

### Key Rules

1. **Orchestrator orchestrates** — never writes code, never runs commands
2. **Subagents are specialized** — each handles one type of work
3. **Verifiers validate** — every build/deploy has paired verification
4. **State is explicit** — progress visible between phases

---

## Workflow 1: Greenfield (New Applications)

Use when building a new application from scratch.

### Phases

| Phase | Subagent | Output |
|-------|----------|--------|
| 0. Context | skill-explorer | Relevant skills, constraints, defaults |
| 1. Architecture | architect | `.do/app.yaml`, architecture doc, verification plan |
| 2. Dev Environment | devcontainer | `.devcontainer/`, `docker-compose.yml` |
| 3. Implementation | code-writer + **verifier** | Application code, tests (iterate until pass) |
| 4. Database | database-config | SQL scripts, connection config |
| 5. Deployment | deployer + **verifier** | GitHub Actions, deployed app (iterate until healthy) |
| 6. Production | verifier | Health check report, smoke tests |

### Phase 3 & 5: Builder-Verifier Pairing

These phases use a **feedback loop**:

```
code-writer writes code
        │
        ▼
verifier runs tests ──► FAIL ──► code-writer fixes
        │
        ▼ PASS
return to orchestrator
```

The orchestrator only sees the final result — not the iterations.

### Greenfield Quick Start

```
User: "Build a FastAPI REST API with PostgreSQL on App Platform"

Orchestrator should:
1. Dispatch skill-explorer → identifies: designer, postgres, deployment skills
2. Dispatch architect → produces app.yaml + verification plan
3. Dispatch devcontainer → produces local dev environment
4. Dispatch code-writer + verifier → iterates until tests pass
5. Dispatch database-config → produces SQL + connection setup
6. Dispatch deployer + verifier → iterates until deployment healthy
7. Report success with deployed URL
```

---

## Workflow 2: Enhancement (Existing Applications)

Use when modifying an existing codebase.

### Key Difference from Greenfield

| Aspect | Greenfield | Enhancement |
|--------|------------|-------------|
| Starting point | Empty repo | Existing code |
| First step | Design | Analyze existing |
| Test requirement | New tests | New + **regression** tests |
| Risk | None | Breaking changes |

### Phases

| Phase | Subagent | Output |
|-------|----------|--------|
| 0. Context | skill-explorer | Workflow type, relevant skills |
| 1. Analysis | architect | Codebase map, existing patterns, test coverage |
| 2. Change Plan | architect | Change plan, impact assessment, verification plan |
| 3. Environment | devcontainer | Dev environment (if needed) |
| 4. Implementation | code-writer + **verifier** | Modified code, new + regression tests |
| 5. Deployment | deployer + **verifier** | Updated deployment, rollback plan |
| 6. Production | verifier | Health check, regression verification |

### Critical: Regression Testing

Enhancement verifier MUST run:
- New tests (for changed functionality)
- **All existing tests** (regression)
- Integration tests (new code + existing code)

```
Enhancement verification = New tests + ALL existing tests
```

### Enhancement Quick Start

```
User: "Add user authentication to my existing FastAPI app"

Orchestrator should:
1. Dispatch skill-explorer → identifies enhancement workflow
2. Dispatch architect → analyzes existing code, maps auth integration points
3. Dispatch architect → plans changes, identifies affected files
4. Dispatch code-writer + verifier → implements auth, runs new + regression tests
5. Dispatch deployer + verifier → deploys, verifies existing features still work
6. Report success with what changed
```

---

## Workflow 3: Troubleshooting

Use when debugging issues in deployed applications.

### Approach: Proactive Validation

**Old way (reactive):** Deploy → wait 5-7min → see error → fix → repeat
**New way (proactive):** Validate in 30-sec cycles using debug container

### Troubleshooting Flow

```
┌─────────────────────────────────────────────────────────────────┐
│  TROUBLESHOOTING FLOW                                            │
├─────────────────────────────────────────────────────────────────┤
│                                                                  │
│  1. CONNECT: doctl apps console → debug container                │
│  2. VALIDATE: Run validate-infra suite                           │
│  3. IDENTIFY: Error layering (SSL → Permissions → Config)        │
│  4. FIX: Apply fix                                               │
│  5. VERIFY: Re-run validation (30-sec cycle)                     │
│  6. DEPLOY: Only after validation passes                         │
│                                                                  │
└─────────────────────────────────────────────────────────────────┘
```

### Error Layering

Debug in this order — later issues mask earlier ones:

1. **SSL/TLS** — Certificate errors block everything
2. **Permissions** — User privileges block operations
3. **Configuration** — Wrong values cause unexpected behavior

### Debug Container

Use the pre-built debug container for troubleshooting:

```bash
# Deploy debug component
# In app spec, add:
services:
  - name: debug
    image:
      registry_type: GHCR
      repository: bikramkgupta/debug-python
      tag: latest
    http_port: 8080

# Connect via console
doctl apps console <app-id> debug

# Run validation suite
validate-infra
```

### Common Patterns

| Issue | Validation | Fix |
|-------|------------|-----|
| DB connection fails | `psql $DATABASE_URL -c "SELECT 1"` | Check SSL config, firewall |
| Health check fails | `curl localhost:$PORT/health` | Check port binding, endpoint |
| Permission denied | `SELECT current_user, has_database_privilege(...)` | Grant as doadmin |
| VPC not working | `dig +short private-xxx.db.ondigitalocean.com` | Should return 10.x.x.x |

---

## Verification Protocol

Every significant change requires verification.

### Builder-Verifier Contract

```
BUILDER produces:
  - Code changes
  - New tests for changes

VERIFIER runs:
  - Unit tests
  - Integration tests
  - Smoke tests (post-deploy)

VERIFIER returns:
  - PASS: All tests green → continue
  - FAIL: Specific failures → builder fixes
```

### Verification Checklist

**Code Phase:**
- [ ] Unit tests pass
- [ ] Integration tests pass
- [ ] No type errors
- [ ] No linting errors

**Deploy Phase:**
- [ ] Build succeeds
- [ ] Health check returns 200
- [ ] Database connects
- [ ] Critical paths work

**Production Phase:**
- [ ] All health endpoints green
- [ ] Logs show no errors
- [ ] Performance acceptable

---

## Subagent Reference

| Subagent | Purpose | Reads | Produces |
|----------|---------|-------|----------|
| skill-explorer | Build context | All skills | Relevant skills, constraints |
| architect | Design | designer, postgres skills | App spec, architecture doc |
| devcontainer | Local env | devcontainers skill | .devcontainer/, compose |
| code-writer | Implement | Relevant tech docs | Application code |
| verifier | Validate | Test patterns | Pass/fail report |
| database-config | DB setup | postgres/managed-db skills | SQL, connection config |
| deployer | Deploy | deployment skill | GitHub Actions, deployed app |
| troubleshooter | Debug | troubleshooting skill | Fix recommendations |

---

## Quick Reference

### When to Use Each Workflow

| User Request | Workflow |
|--------------|----------|
| "Build a new API" | Greenfield |
| "Add feature to existing app" | Enhancement |
| "Fix this error" | Troubleshooting |
| "Migrate from Heroku" | Enhancement (migration subtype) |
| "Why is my app slow?" | Troubleshooting |

### Token Efficiency

| Approach | Orchestrator Tokens |
|----------|---------------------|
| Read all skills upfront | ~50K (wasteful) |
| Lazy loading via skill-explorer | ~5K (efficient) |

---

## See Also

- [shared/error-patterns.md](../shared/error-patterns.md) — Quick error lookup
- [shared/ssl-database-connections.md](../shared/ssl-database-connections.md) — SSL by language
- [skills/troubleshooting/SKILL.md](../skills/troubleshooting/SKILL.md) — Full troubleshooting guide
