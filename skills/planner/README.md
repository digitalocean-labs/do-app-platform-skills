# Planner Skill

Generate staged project plans - from design through coding, testing, to cloud deployment.

## When to Use

- "Create a plan for this project"
- "Plan this project"
- "Help me plan"
- "How should I approach this?"
- "Staged approach"
- "How should I deploy this app?"
- "Create a deployment plan"

## What It Does

1. **Detects complexity tier** from user description or app.yaml
2. **Generates Plan/ folder** with numbered stage files
3. **Includes checkboxes** for progress tracking
4. **Captures credentials** in tables for session resumability

## Tiers

| Tier | Criteria | Stages |
|------|----------|--------|
| 1 - Simple | Static site, no DB | 5 (3 local + 2 cloud) |
| 2 - Database | Single DB (PostgreSQL/MySQL) | 7 (3 local + 4 cloud) |
| 3 - Complex | Kafka, OpenSearch, workers | 9 (3 local + 6 cloud) |

## Output

```
Plan/
├── 01-local-design.md
├── 02-local-coding.md
├── 03-local-testing.md
├── 04-cloud-*.md
└── ...
```

## See Also

- **designer** - Creates .do/app.yaml (input for this skill)
- **deployment** - Executes the deployment (uses Plan/ for context)
- **troubleshooting** - Debugs failures (references Plan/ stages)
