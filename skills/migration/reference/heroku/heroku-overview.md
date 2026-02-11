# Heroku Migration Chapter

Deep reference for migrating Heroku applications to DigitalOcean App Platform.

## Table of Contents

1. [When to Use This Chapter](#when-to-use)
2. [User Intent Detection](#user-intent-detection)
3. [Mode Decision Tree](#mode-decision-tree)
4. [Sub-File Guide](#sub-file-guide)
5. [Key Principles](#key-principles)

---

## When to Use

Read this chapter when ANY of these are true:

- User mentions Heroku, Procfile, app.json, heroku.yml, dynos, or Heroku add-ons
- Platform detection finds `Procfile`, `app.json`, or `heroku.yml`
- User asks about mapping Heroku concepts to App Platform
- User wants to migrate from Heroku (any scope: questions, guidance, or full auto-migration)

---

## User Intent Detection

Determine which mode the user needs:

| Signal | Mode | Action |
|--------|------|--------|
| "How does X map to App Platform?" | Q&A | Answer using mapping references |
| "What's the equivalent of Heroku pipelines?" | Q&A | Answer using mapping references |
| "Help me migrate this app" + provides repo | Guided | Analyze, present plan, user executes |
| "Walk me through moving to App Platform" | Guided | Step-by-step with user in control |
| "Migrate this to App Platform" + provides repo | Auto-Migrate | Full automated migration |
| "Convert my Heroku app and test it" | Auto-Migrate | Branch, refactor, generate spec, validate |
| Mixed signals | Ask user | "Would you like me to guide you or handle the migration?" |

---

## Mode Decision Tree

```
USER MENTIONS HEROKU
        │
        ▼
┌─────────────────────────┐
│ What does the user want?│
└─────────────────────────┘
        │
   ┌────┼──────────────┐
   │    │              │
   ▼    ▼              ▼
Q&A   GUIDED      AUTO-MIGRATE
 │      │              │
 │      │              ├── Clone repo
 │      │              ├── Create branch
 │      ├── Analyze    ├── Analyze
 │      ├── Present    ├── Refactor code
 │      │   plan       ├── Generate app spec
 │      ├── User       ├── Validate
 │      │   executes   ├── Commit + push
 │      └── Verify     └── Hand off to deployment
 │
 ├── Read heroku-mapping.md
 ├── Read heroku-addons.md (if add-on question)
 └── Answer with mapping context
```

---

## Sub-File Guide

Read ONLY the files relevant to the current task:

| File | Read When | Content |
|------|-----------|---------|
| **[heroku-concepts.md](heroku-concepts.md)** | Parsing Heroku config files (Procfile, app.json, heroku.yml) | Config file schemas, CLI commands, buildpack detection, pipeline structure |
| **[heroku-mapping.md](heroku-mapping.md)** | Mapping Heroku features to App Platform equivalents | Component types, build config, env vars, instance sizes, networking, regions |
| **[heroku-addons.md](heroku-addons.md)** | Migrating Heroku add-ons to DO services or external alternatives | Add-on detection from app.json, DO managed service equivalents, external alternatives |
| **[heroku-workflows.md](heroku-workflows.md)** | Executing any of the 3 migration modes | Step-by-step procedures for Q&A, Guided, and Auto-Migrate modes |

### Typical reading order by mode

- **Q&A**: heroku-mapping.md (+ heroku-addons.md if add-on specific)
- **Guided**: heroku-concepts.md → heroku-mapping.md → heroku-workflows.md
- **Auto-Migrate**: heroku-concepts.md → heroku-mapping.md → heroku-addons.md → heroku-workflows.md

---

## Key Principles

1. **Heroku is well-understood** — don't over-explain Heroku basics. Focus on what's DIFFERENT on App Platform.

2. **Opinionated translation** — don't ask "buildpack or Dockerfile?" Detect what the user has on Heroku and map it:
   - Procfile + buildpacks → App Platform buildpacks (CNB) or Dockerfile (if complex)
   - heroku.yml with Docker → Dockerfile-based app spec
   - app.json addons → Managed DB bindings

3. **Honest about gaps** — flag what doesn't map cleanly:
   - Heroku Scheduler UI → cron jobs (no UI, define in app spec)
   - Review Apps → preview environments (different trigger mechanism)
   - Pipeline promotion → GitHub Actions deployment workflow
   - Sticky sessions → not available

4. **Redis → Valkey** — always. Heroku Redis maps to DO Managed Valkey. Redis is EOL on DO.

5. **Config Vars → GitHub Secrets** — this is the biggest workflow change. Heroku's `heroku config:set` model becomes GitHub Secrets + app spec references.

6. **DATABASE_URL format** — Heroku uses `postgres://`, some libraries need `postgresql://`. App Platform bindable variables use the standard format. Flag if the user's code has a `postgres://` → `postgresql://` fix that may no longer be needed.
