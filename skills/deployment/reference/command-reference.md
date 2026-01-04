# Command Reference

Complete doctl and GitHub CLI command reference for App Platform deployments.

---

## doctl App Management

```bash
# Create app
doctl apps create --spec .do/app.yaml --project-id $PROJECT_ID --wait

# Update app spec
doctl apps update $APP_ID --spec .do/app.yaml --wait

# Trigger deployment (code only, no spec change)
doctl apps create-deployment $APP_ID --wait

# Force rebuild (ignores cache)
doctl apps create-deployment $APP_ID --force-rebuild --wait

# Get app info
doctl apps get $APP_ID
doctl apps get $APP_ID -o json | jq '.[]'

# Get app spec
doctl apps spec get $APP_ID > app-spec.yaml

# Validate spec locally
doctl apps spec validate .do/app.yaml

# Delete app
doctl apps delete $APP_ID --force
```

---

## doctl Deployment History

```bash
# List deployments
doctl apps list-deployments $APP_ID

# Get deployment details
doctl apps get-deployment $APP_ID $DEPLOYMENT_ID

# Get logs
doctl apps logs $APP_ID --type run
doctl apps logs $APP_ID $COMPONENT --type build
doctl apps logs $APP_ID --type run --follow
```

---

## doctl Project Management

```bash
# List projects
doctl projects list --format ID,Name,Environment

# Create project with environment
doctl projects create --name "myapp-staging" \
  --purpose "Staging" \
  --environment "Staging"

# Get project ID for an app
APP_ID="your-app-id"
doctl apps get "$APP_ID" -o json | jq -r '.[0].project_id'

# Get environment for an app's project
PROJECT_ID=$(doctl apps get "$APP_ID" -o json | jq -r '.[0].project_id')
doctl projects get "$PROJECT_ID" -o json | jq -r '.[0].environment'
```

---

## GitHub Environment Management

```bash
# Create environment
gh api --method PUT repos/:owner/:repo/environments/staging

# Create environment with protection
gh api --method PUT repos/:owner/:repo/environments/production \
  -F prevent_self_review=true \
  -F reviewers[0][type]=User \
  -F reviewers[0][id]=USER_ID

# List environments
gh api repos/:owner/:repo/environments --jq '.environments[].name'

# Delete environment
gh api --method DELETE repos/:owner/:repo/environments/staging
```

---

## GitHub Secrets and Variables

```bash
# Set secret for environment (prompted for value)
gh secret set SECRET_NAME --env staging

# Set secret with value (use cautiously)
gh secret set SECRET_NAME --env staging --body "value"

# Set variable for environment
gh variable set VAR_NAME --env staging --body "value"

# List secrets (names only, not values)
gh secret list --env staging

# List variables
gh variable list --env staging

# Delete secret
gh secret delete SECRET_NAME --env staging
```

---

## Rollback Commands

```bash
# List recent deployments
doctl apps list-deployments $APP_ID --format ID,Phase,CreatedAt

# Get current spec
doctl apps spec get $APP_ID > current-spec.yaml

# Restore from git and redeploy
git checkout HEAD~1 -- .do/app.yaml
doctl apps update $APP_ID --spec .do/app.yaml --wait
```

---

## Quick Reference Table

| Task | Command |
|------|---------|
| Validate spec | `doctl apps spec validate .do/app.yaml` |
| Deploy new app | `doctl apps create --spec .do/app.yaml --project-id $PROJECT_ID` |
| Update app | `doctl apps update $APP_ID --spec .do/app.yaml` |
| Redeploy code | `doctl apps create-deployment $APP_ID` |
| View logs | `doctl apps logs $APP_ID --type run` |
| Set secret | `gh secret set NAME --env staging` |
| List secrets | `gh secret list --env staging` |
