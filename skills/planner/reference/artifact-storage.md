# Artifact Storage Philosophy

Plan files contain **status only** - all captured values (IDs, passwords, URLs) go to `.env.secrets`.

---

## Why This Pattern?

```
Plan/05-cloud-config.md          .env.secrets (gitignored)
├── Status: COMPLETED            ├── PG_ID=92e5a881-...
├── Tasks:                       ├── KAFKA_ID=9568252b-...
│   - [x] Create database        ├── PG_PASSWORD=AVNS_...
│   - [x] Create user            ├── DATABASE_PRIVATE_URL=...
└── Next: Stage 6                └── OPENSEARCH_PRIVATE_URL=...
```

**Benefits**:
1. Plan files are **commitable** - no secrets, reusable across projects
2. Single source of truth for artifacts - `.env.secrets`
3. AI can resume by reading `.env.secrets` for context
4. Status updates are simple: `TODO → IN_PROGRESS → COMPLETED`

---

## AI Assistant Instructions

When working with staged plans:

- When creating resources, **always** write captured values to `.env.secrets`
- Never write passwords, IDs, or hostnames directly into Plan files
- Plan file updates should be **status changes only** (checkboxes, status header)
- To resume a stage, read `.env.secrets` first for context

---

## Credential Safety

- Plan files contain placeholders, not actual values
- All secrets stored in `.env.secrets` (gitignored)
- References GitHub Secrets for production deployment
- Debug containers read from `.env.secrets` for testing

---

## Session Resumability

- Stage files persist in git (status tracking only)
- `Status: TODO/IN PROGRESS/COMPLETE` headers
- All captured values stored in `.env.secrets` (gitignored)
- AI assistants read `.env.secrets` to resume from any stage

---

## Team Handoff

- Numbered files sort correctly in any viewer
- Checkboxes show progress at a glance
- Prerequisites link stages together
