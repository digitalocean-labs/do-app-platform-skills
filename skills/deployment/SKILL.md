---
name: deployment
version: 1.0.0
min_doctl_version: "1.82.0"
description: Deploy applications to DigitalOcean App Platform via GitHub Actions with proper environment management and secrets handling. Use when setting up CI/CD pipelines, configuring staging/production environments, managing deployment secrets, or creating GitHub Actions workflows.
related_skills: [designer, troubleshooting]
deprecated: false
---

# Deployment Skill

Deploy to App Platform using GitHub Actions and the `app_action` workflow.

## Philosophy: PUSH Mode Deployment

This skill focuses on **PUSH mode** — where you define infrastructure as code and GitHub Actions drives deployment.

```
PULL MODE (Console-driven) — NOT covered by this skill
• Go to DigitalOcean Console → Create App → Point to GitHub
• App Platform auto-generates app spec
• Good for: Quick starts, manual one-offs

PUSH MODE (CLI/Actions-driven) — THIS SKILL
• Define app spec in repo (.do/app.yaml)
• Use GitHub Actions + app_action to deploy
• Good for: CI/CD, automation, GitOps, multi-environment
```

> **Tip**: For complex projects, consider the **planner** skill for staged approaches. See [root SKILL.md](../../SKILL.md) for all skills.

---

## Quick Decision

```
Using GitHub Actions? (RECOMMENDED)
├── YES → Use digitalocean/app_action/deploy@v2
│         • Handles spec updates AND code deployments
│         • Manages app creation if doesn't exist
│         • Supports PR previews
│
└── NO (Manual/Scripting)
    ├── Spec changed? → doctl apps update --spec
    └── Code only? → doctl apps create-deployment
```

| Command | Purpose | When to Use |
|---------|---------|-------------|
| `doctl apps create --spec` | Create new app | First deployment only |
| `doctl apps update --spec` | Update app spec | Config changes |
| `doctl apps create-deployment` | Trigger rebuild | Code changes only |
| **app_action v2** | **Both spec + rebuild** | **Recommended: Handles everything** |

---

## Quick Start: Environment Setup

```bash
# 1. Create DigitalOcean projects
doctl projects create --name "myapp-staging" --environment "Staging"
doctl projects create --name "myapp-production" --environment "Production"

# 2. Create GitHub environments
gh api --method PUT repos/:owner/:repo/environments/staging
gh api --method PUT repos/:owner/:repo/environments/production

# 3. Set secrets per environment (user fills in values)
gh secret set DIGITALOCEAN_ACCESS_TOKEN --env staging
gh secret set DIGITALOCEAN_ACCESS_TOKEN --env production
gh variable set DO_PROJECT_ID --env staging --body "PROJECT_ID"
gh variable set DO_PROJECT_ID --env production --body "PROJECT_ID"
```

**Full setup guide**: See [initial-setup.md](reference/initial-setup.md)

---

## Quick Start: Basic Workflow

```yaml
# .github/workflows/deploy.yml
name: Deploy
on:
  push:
    branches: [main]
jobs:
  deploy:
    runs-on: ubuntu-latest
    environment: staging
    steps:
      - uses: actions/checkout@v4
      - uses: digitalocean/app_action/deploy@v2
        env:
          DATABASE_URL: ${{ secrets.DATABASE_URL }}
        with:
          token: ${{ secrets.DIGITALOCEAN_ACCESS_TOKEN }}
          project_id: ${{ vars.DO_PROJECT_ID }}
```

**All workflow templates**: See [workflow-templates.md](reference/workflow-templates.md)

---

## Workflow Selection

| Scenario | Workflow | Reference |
|----------|----------|-----------|
| Simple single-environment | Minimum viable | [workflow-templates.md](reference/workflow-templates.md#minimum-viable-deployment) |
| Staging + production | Environment-based | [workflow-templates.md](reference/workflow-templates.md#basic-environment-deployment) |
| Production needs approval | Protected environment | [workflow-templates.md](reference/workflow-templates.md#production-deployment-with-approval) |
| Test PRs before merge | PR previews | [workflow-templates.md](reference/workflow-templates.md#pr-preview-environments) |
| Multiple envs, one workflow | Unified workflow | [workflow-templates.md](reference/workflow-templates.md#multi-environment-with-single-workflow) |
| Need to revert | Rollback | [workflow-templates.md](reference/workflow-templates.md#rollback-workflow) |

---

## Quick Start: Debug Container

For complex apps with multiple integrations, deploy a debug container first:

```yaml
# Add to .do/app.yaml temporarily
workers:
  - name: debug
    image:
      registry_type: GHCR
      registry: ghcr.io
      repository: bikramkgupta/do-app-debug-container-python
      tag: latest
    instance_size_slug: apps-s-1vcpu-2gb
    envs:
      - key: DATABASE_URL
        scope: RUN_TIME
        value: ${db.DATABASE_URL}
```

```bash
# Connect and verify
doctl apps console $APP_ID debug
./diagnose.sh
```

**Full guide**: See [debug-container-deployment.md](reference/debug-container-deployment.md)

---

## Quick Command Reference

| Task | Command |
|------|---------|
| Validate spec | `doctl apps spec validate .do/app.yaml` |
| Create app | `doctl apps create --spec .do/app.yaml --project-id $PROJECT_ID` |
| Update app | `doctl apps update $APP_ID --spec .do/app.yaml` |
| Redeploy | `doctl apps create-deployment $APP_ID` |
| View logs | `doctl apps logs $APP_ID --type run` |
| Set secret | `gh secret set NAME --env staging` |
| List secrets | `gh secret list --env staging` |

**Full reference**: See [command-reference.md](reference/command-reference.md)

---

## Reference Files

| File | Content |
|------|---------|
| [initial-setup.md](reference/initial-setup.md) | Projects, environments, secrets, app spec setup |
| [workflow-templates.md](reference/workflow-templates.md) | All GitHub Actions workflow YAML templates |
| [debug-container-deployment.md](reference/debug-container-deployment.md) | Debug container for infrastructure verification |
| [command-reference.md](reference/command-reference.md) | Complete doctl and gh CLI commands |

---

## Quick Troubleshooting

| Issue | Symptom | Fix |
|-------|---------|-----|
| App spec not found | `Error: spec file not found` | Ensure `.do/app.yaml` exists |
| Invalid token | `401 Unauthorized` | Check `DIGITALOCEAN_ACCESS_TOKEN` secret |
| Project not found | `project_id is invalid` | Verify `DO_PROJECT_ID` variable |
| Build fails | `BuildJobFailed` | Check build logs: `doctl apps logs $APP_ID --type build` |
| Env vars literal | Values show `${...}` | Check bindable variable names match |

---

## Opinionated Defaults

| Decision | Default | Rationale |
|----------|---------|-----------|
| CI Platform | GitHub Actions | Best DO integration via app_action |
| Deploy Action | `app_action/deploy@v2` | Handles spec + deploy in one step |
| Secrets | GitHub Secrets per environment | Secure, AI never sees values |
| deploy_on_push | `false` in app spec | Let GitHub Actions control deploys |
| App spec location | `.do/app.yaml` | Conventional, matches DO button |

---

## Integration with Other Skills

- **← designer**: Creates `.do/app.yaml` that deployment consumes
- **← postgres**: Handles database setup, stores `DATABASE_URL` in GitHub Secrets
- **→ troubleshooting**: Debug deployment failures
- **← devcontainers**: Ensure local dev matches production

---

## Production Checklist

- [ ] DO Projects created with environment tags
- [ ] GitHub environments created (staging, production)
- [ ] `DIGITALOCEAN_ACCESS_TOKEN` secret set per environment
- [ ] `DO_PROJECT_ID` variable set per environment
- [ ] `.do/app.yaml` with `deploy_on_push: false`
- [ ] `.github/workflows/deploy.yml` created
- [ ] Production protection rules enabled
- [ ] Staging deployment tested
- [ ] Production deployment tested

---

## Documentation Links

- [app_action GitHub Repository](https://github.com/digitalocean/app_action)
- [App Platform Docs](https://docs.digitalocean.com/products/app-platform/)
- [App Spec Reference](https://docs.digitalocean.com/products/app-platform/reference/app-spec/)
- [GitHub Environments Docs](https://docs.github.com/en/actions/deployment/targeting-different-environments/using-environments-for-deployment)
