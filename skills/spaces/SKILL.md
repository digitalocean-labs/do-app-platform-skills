---
name: spaces
version: 1.0.0
min_doctl_version: "1.82.0"
description: Configure DigitalOcean Spaces (S3-compatible object storage) for App Platform apps. Use when setting up file uploads, static assets, CDN, access logging, or per-app credential management.
related_skills: [designer]
deprecated: false
---

# Spaces Skill

S3-compatible object storage for App Platform applications.

## Tool Separation (Critical)

```
┌─────────────────────────────────────────────────────────────────┐
│  doctl: KEYS ONLY          │  aws CLI: EVERYTHING ELSE          │
│  • doctl spaces keys create│  • Bucket create/delete            │
│  • doctl spaces keys list  │  • Object upload/download          │
│  • doctl spaces keys delete│  • CORS, logging, lifecycle        │
└─────────────────────────────────────────────────────────────────┘
```

> **Why?** doctl's Spaces support is limited to key management. Bucket operations require S3-compatible tools.

---

## Quick Decision

```
┌─────────────────────────────────────────────────────────────────┐
│              What do you need to do with Spaces?                 │
└─────────────────────────────────────────────────────────────────┘
                              │
        ┌─────────────────────┼─────────────────────┐
        │                     │                     │
   Create key            Create bucket         Upload/download
   or rotate             set CORS/logging      objects
        │                     │                     │
        ▼                     ▼                     ▼
┌───────────────┐    ┌───────────────┐    ┌───────────────┐
│    doctl      │    │   aws CLI     │    │   aws CLI     │
│ spaces keys   │    │   s3api       │    │   s3 cp/sync  │
└───────────────┘    └───────────────┘    └───────────────┘
```

---

## Prerequisites

```bash
doctl auth init          # One-time DO API auth
aws --version            # AWS CLI v2
jq --version             # JSON processor
```

---

## Quick Start

### 1. Set Environment

```bash
# Choose region matching your App Platform app (see shared/regions.yaml)
export DO_SPACES_REGION="syd1"
export DO_SPACES_ENDPOINT="https://${DO_SPACES_REGION}.digitaloceanspaces.com"
export APP_NAME="myapp"
export BUCKET="${APP_NAME}-uploads"
export DO_SPACES_KEY_NAME="${APP_NAME}-spaces-key"
```

### 2. Create Key (doctl)

```bash
KEY_JSON=$(doctl spaces keys create "${DO_SPACES_KEY_NAME}" --output json)
export AWS_ACCESS_KEY_ID=$(echo "$KEY_JSON" | jq -r '.[0].access_key')
export AWS_SECRET_ACCESS_KEY=$(echo "$KEY_JSON" | jq -r '.[0].secret_key')

# IMPORTANT: Secret shown only once - save it now!
```

### 3. Create Bucket (aws CLI)

```bash
aws --endpoint-url "$DO_SPACES_ENDPOINT" s3api create-bucket --bucket "$BUCKET"
```

### 4. App Spec

```yaml
services:
  - name: api
    envs:
      - key: SPACES_BUCKET
        value: myapp-uploads
      - key: SPACES_REGION
        value: ${SPACES_REGION}           # Your bucket's region
      - key: SPACES_ENDPOINT
        value: ${SPACES_ENDPOINT}         # e.g., https://syd1.digitaloceanspaces.com
      - key: SPACES_ACCESS_KEY
        scope: RUN_TIME
        type: SECRET
        value: ${SPACES_ACCESS_KEY}
      - key: SPACES_SECRET_KEY
        scope: RUN_TIME
        type: SECRET
        value: ${SPACES_SECRET_KEY}
```

> Store `SPACES_ACCESS_KEY` and `SPACES_SECRET_KEY` in GitHub Secrets.

---

## Regions

Spaces uses different slugs than App Platform. See [shared/regions.yaml](../../shared/regions.yaml).

| App Platform | Spaces | Endpoint |
|--------------|--------|----------|
| `nyc` | `nyc3` | `https://nyc3.digitaloceanspaces.com` |
| `sfo` | `sfo3` | `https://sfo3.digitaloceanspaces.com` |
| `ams` | `ams3` | `https://ams3.digitaloceanspaces.com` |
| `lon` | `lon1` | `https://lon1.digitaloceanspaces.com` |
| `fra` | `fra1` | `https://fra1.digitaloceanspaces.com` |
| `tor` | `tor1` | `https://tor1.digitaloceanspaces.com` |
| `sgp` | `sgp1` | `https://sgp1.digitaloceanspaces.com` |
| `blr` | `blr1` | `https://blr1.digitaloceanspaces.com` |
| `syd` | `syd1` | `https://syd1.digitaloceanspaces.com` |
| `atl` | `atl1` | `https://atl1.digitaloceanspaces.com` |

---

## Common Operations

### doctl (Keys Only)

```bash
doctl spaces keys list
doctl spaces keys create "myapp-key" --output json
doctl spaces keys delete <key-id>
```

### aws CLI (Buckets & Objects)

```bash
EP="--endpoint-url https://syd1.digitaloceanspaces.com"

# Buckets
aws $EP s3 ls
aws $EP s3api create-bucket --bucket myapp-uploads
aws $EP s3 rb s3://myapp-uploads

# Objects
aws $EP s3 cp ./file.txt s3://myapp-uploads/path/file.txt
aws $EP s3 cp s3://myapp-uploads/path/file.txt ./file.txt
aws $EP s3 ls s3://myapp-uploads/ --recursive
aws $EP s3 sync ./local-dir/ s3://myapp-uploads/prefix/
```

---

## Scripts (AI-Friendly)

| Script | Purpose |
|--------|---------|
| `scripts/bootstrap_app_spaces.sh` | Full setup: key + buckets + logging |
| `scripts/enable_bucket_logging.sh` | Enable/verify logging (idempotent) |
| `scripts/view_access_logs.sh` | List/download access logs |
| `scripts/rotate_spaces_key.sh` | Rotate credentials safely |

```bash
# Set env vars then run
./scripts/bootstrap_app_spaces.sh
```

---

## Reference Files

| File | Content |
|------|---------|
| [aws-cli-operations.md](reference/aws-cli-operations.md) | Complete aws CLI reference |
| [key-management.md](reference/key-management.md) | Per-app keys, rotation workflow |
| [access-logging.md](reference/access-logging.md) | Bucket logging setup |
| [sdk-configuration.md](reference/sdk-configuration.md) | Node.js, Python, Go SDK setup |
| [troubleshooting.md](reference/troubleshooting.md) | Common errors and fixes |

---

## URL Patterns

| Type | Format |
|------|--------|
| Standard | `https://<bucket>.<region>.digitaloceanspaces.com/<key>` |
| CDN | `https://<bucket>.<region>.cdn.digitaloceanspaces.com/<key>` |

---

## Quick Troubleshooting

| Error | Fix |
|-------|-----|
| BucketAlreadyExists (409) | Use unique prefix: `mycompany-myapp-uploads` |
| Access Denied (403) | Verify keys, check endpoint matches bucket region |
| CORS error | Configure via `aws s3api put-bucket-cors` |
| SignatureDoesNotMatch | Use `https://` prefix, no trailing slash |

See [troubleshooting.md](reference/troubleshooting.md) for details.

---

## Integration

- **→ designer**: Includes Spaces env vars when architecting apps
- **→ deployment**: Credentials stored in GitHub Secrets
- **→ devcontainers**: MinIO provides local Spaces parity
