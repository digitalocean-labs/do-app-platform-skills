# Spaces Key Management

Complete guide for managing DigitalOcean Spaces access keys using doctl.

## Overview

Spaces keys are used to authenticate S3-compatible API requests. Unlike bucket operations (which use aws CLI), key management is done through the DigitalOcean API via doctl.

**Key characteristics:**
- Keys are **account-wide** (not region-specific)
- Region is determined by the endpoint URL, not the key
- Secret is shown **only once** at creation time
- Best practice: **one key per application**

---

## Prerequisites

```bash
# Install doctl
# macOS
brew install doctl

# Linux (snap)
sudo snap install doctl

# Authenticate (one-time)
doctl auth init
```

---

## Basic Operations

### List Keys

```bash
# Default format
doctl spaces keys list

# Specific columns
doctl spaces keys list --format ID,Name,CreatedAt

# JSON output (for scripting)
doctl spaces keys list --output json
```

### Create Key

```bash
# Basic creation
doctl spaces keys create "myapp-spaces-key"

# With JSON output (recommended for scripting)
doctl spaces keys create "myapp-spaces-key" --output json
```

**Output:**
```json
[{
  "access_key": "DO00...",
  "secret_key": "...",
  "name": "myapp-spaces-key"
}]
```

> **CRITICAL**: The secret key is shown only once. Save it immediately!

### Delete Key

```bash
# List keys to find ID
doctl spaces keys list --format ID,Name

# Delete by ID (not name)
doctl spaces keys delete <key-id>

# Force delete (no confirmation)
doctl spaces keys delete <key-id> --force
```

---

## Per-App Key Pattern

### Why One Key Per App?

1. **Blast radius** - Compromised key affects only one app
2. **Rotation** - Rotate without affecting other apps
3. **Auditing** - Track which app made which requests
4. **Revocation** - Disable one app without disrupting others

### Naming Convention

```
<app-name>-spaces-key
<app-name>-spaces-key-<timestamp>  # For rotation
```

Examples:
- `webapp-spaces-key`
- `api-prod-spaces-key`
- `myapp-spaces-key-20240115`

### Bootstrap Script

```bash
#!/usr/bin/env bash
set -euo pipefail

APP_NAME="${1:?Usage: $0 <app-name>}"
KEY_NAME="${APP_NAME}-spaces-key"

# Create key
echo "Creating Spaces key: ${KEY_NAME}"
KEY_JSON=$(doctl spaces keys create "${KEY_NAME}" --output json)

# Extract credentials
ACCESS_KEY=$(echo "$KEY_JSON" | jq -r '.[0].access_key')
SECRET_KEY=$(echo "$KEY_JSON" | jq -r '.[0].secret_key')

echo ""
echo "Access Key: ${ACCESS_KEY}"
echo "Secret Key: ${SECRET_KEY}"
echo ""
echo "Add these to your secret manager or GitHub Secrets:"
echo "  SPACES_ACCESS_KEY=${ACCESS_KEY}"
echo "  SPACES_SECRET_KEY=<secret from above>"
```

---

## Key Rotation

### Why Rotate?

- Regular security hygiene (recommended: every 90 days)
- After team member departure
- After suspected compromise
- Before/after major deployments

### Rotation Process

```
1. Create new key (with timestamp suffix)
2. Update application secrets
3. Deploy application with new key
4. Verify application works
5. Delete old key
```

### Rotation Script

```bash
#!/usr/bin/env bash
set -euo pipefail

APP_NAME="${1:?Usage: $0 <app-name>}"
BASE_KEY_NAME="${APP_NAME}-spaces-key"
TIMESTAMP=$(date +%Y%m%d-%H%M%S)
NEW_KEY_NAME="${BASE_KEY_NAME}-${TIMESTAMP}"

echo "=== Rotating Spaces Key for: ${APP_NAME} ==="

# Step 1: Create new key
echo "Creating new key: ${NEW_KEY_NAME}"
KEY_JSON=$(doctl spaces keys create "${NEW_KEY_NAME}" --output json)

ACCESS_KEY=$(echo "$KEY_JSON" | jq -r '.[0].access_key')
SECRET_KEY=$(echo "$KEY_JSON" | jq -r '.[0].secret_key')

echo ""
echo "NEW CREDENTIALS:"
echo "  Access Key: ${ACCESS_KEY}"
echo "  Secret Key: ${SECRET_KEY}"
echo ""

# Step 2: Show existing keys for cleanup
echo "=== Existing Keys ==="
doctl spaces keys list --format ID,Name,CreatedAt

echo ""
echo "=== NEXT STEPS ==="
echo "1. Update GitHub Secrets with new credentials"
echo "2. Trigger deployment to pick up new secrets"
echo "3. Verify application works with new key"
echo "4. Delete old key: doctl spaces keys delete <old-key-id>"
```

### Zero-Downtime Rotation

For applications that can't afford any downtime:

1. **Support multiple keys** in your application (environment variable list)
2. **Add new key** to the list
3. **Deploy** with both keys
4. **Remove old key** from configuration
5. **Deploy** again
6. **Delete old key** from DigitalOcean

---

## Storing Secrets

### GitHub Secrets (Recommended)

```bash
# Using GitHub CLI
gh secret set SPACES_ACCESS_KEY --body "$ACCESS_KEY"
gh secret set SPACES_SECRET_KEY --body "$SECRET_KEY"
```

Reference in App Spec:
```yaml
envs:
  - key: SPACES_ACCESS_KEY
    scope: RUN_TIME
    type: SECRET
    value: ${SPACES_ACCESS_KEY}
```

### Environment Variables

For local development or CI:

```bash
export AWS_ACCESS_KEY_ID="DO00..."
export AWS_SECRET_ACCESS_KEY="..."
```

### AWS Credentials File

For persistent local configuration:

```bash
# ~/.aws/credentials
[spaces-myapp]
aws_access_key_id = DO00...
aws_secret_access_key = ...
```

Usage:
```bash
aws --profile spaces-myapp --endpoint-url https://nyc3.digitaloceanspaces.com s3 ls
```

---

## Security Best Practices

### DO

- Use one key per application
- Rotate keys regularly (every 90 days)
- Store secrets in a secret manager
- Use environment variables, not hardcoded values
- Delete unused keys immediately
- Monitor key usage via access logs

### DON'T

- Share keys between applications
- Commit keys to source control
- Log secrets in application output
- Use account-wide keys for all apps
- Keep old keys after rotation

---

## Troubleshooting

### "Key not found" when deleting

Keys are deleted by ID, not name:
```bash
# Get the ID first
doctl spaces keys list --format ID,Name

# Then delete by ID
doctl spaces keys delete abc123
```

### "Permission denied" creating keys

Your DO API token needs Spaces key management permission:
1. Go to API → Tokens
2. Regenerate token with full access, or
3. Create new token with Spaces scope

### Lost secret key

Secrets are shown only once. If lost:
1. Create a new key
2. Update application
3. Delete the old key

```bash
# Create replacement
doctl spaces keys create "myapp-spaces-key-replacement" --output json

# After updating app, delete old
doctl spaces keys list --format ID,Name
doctl spaces keys delete <old-key-id>
```

---

## Scripting Reference

### Extract Credentials from JSON

```bash
KEY_JSON=$(doctl spaces keys create "myapp-key" --output json)
ACCESS_KEY=$(echo "$KEY_JSON" | jq -r '.[0].access_key')
SECRET_KEY=$(echo "$KEY_JSON" | jq -r '.[0].secret_key')
```

### Export for AWS CLI

```bash
export AWS_ACCESS_KEY_ID="$ACCESS_KEY"
export AWS_SECRET_ACCESS_KEY="$SECRET_KEY"
export AWS_DEFAULT_REGION="us-east-1"  # Required placeholder
```

### Find Key ID by Name

```bash
KEY_ID=$(doctl spaces keys list --output json | jq -r '.[] | select(.name == "myapp-key") | .id')
```

### Delete All Keys Matching Pattern

```bash
# Careful! This deletes all matching keys
doctl spaces keys list --output json \
  | jq -r '.[] | select(.name | startswith("myapp-")) | .id' \
  | xargs -I {} doctl spaces keys delete {} --force
```
