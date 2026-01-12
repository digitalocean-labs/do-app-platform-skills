---
name: spaces
description: Configure DigitalOcean Spaces (S3-compatible object storage) for App Platform applications. Use when setting up file uploads, static asset hosting, CDN-backed storage, access logging, or per-app credential management.
---

# Spaces Skill

Configure DigitalOcean Spaces (S3-compatible object storage) for App Platform applications.

## Philosophy

**This skill covers DO-specific configuration only.** Claude already knows S3 SDK usage, presigned URL patterns, and object storage concepts.

**This skill teaches:** Spaces endpoint URLs, CORS configuration, app spec patterns, CDN enablement, per-app key management, and access logging.

> **Tip**: For complex multi-step projects, consider using the **planner** skill. For an overview of all skills, see the [root SKILL.md](../../SKILL.md).

---

## Tool Separation (Critical)

| Tool | Use For | NOT For |
|------|---------|---------|
| `doctl` | Key management (create, rotate, delete) | Bucket or object operations |
| `aws` CLI | All bucket/object ops (create, delete, upload, list, logging) | Key management |

**Why?** doctl's Spaces support is limited to key management. Bucket operations require S3-compatible tools.

---

## Credential Handling

### Security Model

1. **One Spaces key per app** — isolate blast radius
2. **Store secrets externally** — GitHub Secrets, Vault, or env vars
3. **Rotate regularly** — mint new key, update app, revoke old key
4. **Never log secrets** — keys shown once at creation

### How Credentials Flow

```
doctl (DO API token) → Creates Spaces key
                            ↓
                      AWS_ACCESS_KEY_ID + AWS_SECRET_ACCESS_KEY
                            ↓
aws CLI (S3 API) → Bucket/object operations
```

Keys are account-wide. Region is determined by endpoint URL, not by the key.

---

## Quick Start: Bootstrap Spaces for an App

### Prerequisites

```bash
# Required tools
doctl auth init          # One-time DO API auth
aws --version            # AWS CLI v2
jq --version             # JSON processor
```

### Step 1: Set Environment

```bash
export DO_SPACES_REGION="nyc3"
export DO_SPACES_ENDPOINT="https://nyc3.digitaloceanspaces.com"
export APP_NAME="myapp"
export SRC_BUCKET="${APP_NAME}-uploads"
export LOG_BUCKET="${APP_NAME}-logs"
export LOG_PREFIX="access-logs/${APP_NAME}/"
export DO_SPACES_KEY_NAME="${APP_NAME}-spaces-key"
```

### Step 2: Create Spaces Key (doctl)

```bash
# Create key and capture credentials
KEY_JSON=$(doctl spaces keys create "${DO_SPACES_KEY_NAME}" --output json)

# Extract credentials
export AWS_ACCESS_KEY_ID=$(echo "$KEY_JSON" | jq -r '.[0].access_key')
export AWS_SECRET_ACCESS_KEY=$(echo "$KEY_JSON" | jq -r '.[0].secret_key')

# IMPORTANT: Secret shown only once - save it now!
echo "Access Key: $AWS_ACCESS_KEY_ID"
echo "Secret Key: $AWS_SECRET_ACCESS_KEY"
```

### Step 3: Create Buckets (aws CLI)

```bash
# Create log bucket first (required for logging target)
aws --endpoint-url "$DO_SPACES_ENDPOINT" s3api create-bucket --bucket "$LOG_BUCKET"

# Create source bucket
aws --endpoint-url "$DO_SPACES_ENDPOINT" s3api create-bucket --bucket "$SRC_BUCKET"

# Verify
aws --endpoint-url "$DO_SPACES_ENDPOINT" s3 ls
```

### Step 4: Enable Access Logging

```bash
# Create logging config
cat > /tmp/logging.json << EOF
{
  "LoggingEnabled": {
    "TargetBucket": "${LOG_BUCKET}",
    "TargetPrefix": "${LOG_PREFIX}"
  }
}
EOF

# Apply to source bucket
aws --endpoint-url "$DO_SPACES_ENDPOINT" s3api put-bucket-logging \
  --bucket "$SRC_BUCKET" \
  --bucket-logging-status file:///tmp/logging.json

# Verify
aws --endpoint-url "$DO_SPACES_ENDPOINT" s3api get-bucket-logging --bucket "$SRC_BUCKET"
```

### Step 5: Store Credentials

Add to GitHub Secrets (Repo → Settings → Secrets → Actions):
- `SPACES_ACCESS_KEY` → value of `$AWS_ACCESS_KEY_ID`
- `SPACES_SECRET_KEY` → value of `$AWS_SECRET_ACCESS_KEY`

### Step 6: App Spec Configuration

```yaml
services:
  - name: api
    envs:
      - key: SPACES_BUCKET
        value: myapp-uploads
      - key: SPACES_REGION
        value: nyc3
      - key: SPACES_ENDPOINT
        value: https://nyc3.digitaloceanspaces.com
      - key: SPACES_ACCESS_KEY
        scope: RUN_TIME
        type: SECRET
        value: ${SPACES_ACCESS_KEY}
      - key: SPACES_SECRET_KEY
        scope: RUN_TIME
        type: SECRET
        value: ${SPACES_SECRET_KEY}
```

---

## Scripts (AI-Friendly Automation)

For idempotent, scriptable operations, use the provided scripts:

| Script | Purpose |
|--------|---------|
| `scripts/bootstrap_app_spaces.sh` | Full setup: key + buckets + logging |
| `scripts/enable_bucket_logging.sh` | Enable/verify logging (idempotent) |
| `scripts/view_access_logs.sh` | List/download access logs |
| `scripts/rotate_spaces_key.sh` | Rotate credentials safely |

### Usage Example

```bash
# Set required env vars (see Quick Start)
export DO_SPACES_REGION="nyc3"
export DO_SPACES_ENDPOINT="https://nyc3.digitaloceanspaces.com"
export APP_NAME="myapp"
export SRC_BUCKET="${APP_NAME}-uploads"
export LOG_BUCKET="${APP_NAME}-logs"
export LOG_PREFIX="access-logs/${APP_NAME}/"
export DO_SPACES_KEY_NAME="${APP_NAME}-spaces-key"

# Bootstrap everything
./scripts/bootstrap_app_spaces.sh

# Later: view logs
./scripts/view_access_logs.sh --tail 50

# Rotate key when needed
./scripts/rotate_spaces_key.sh
```

---

## doctl Commands (Keys Only)

```bash
# List all Spaces keys
doctl spaces keys list

# Create a new key
doctl spaces keys create "myapp-spaces-key" --output json

# Delete a key (by ID, not name)
doctl spaces keys list --format ID,Name
doctl spaces keys delete <key-id>
```

> **Note**: doctl manages **keys only**, not buckets or objects. Use aws CLI for all S3 operations.

---

## aws CLI Commands (Buckets & Objects)

Always include `--endpoint-url`:

```bash
# Set endpoint for convenience
export EP="--endpoint-url https://nyc3.digitaloceanspaces.com"

# List buckets
aws $EP s3 ls

# Create bucket
aws $EP s3api create-bucket --bucket myapp-uploads

# Delete bucket (must be empty)
aws $EP s3 rb s3://myapp-uploads

# Upload file
aws $EP s3 cp ./local-file.txt s3://myapp-uploads/path/file.txt

# Download file
aws $EP s3 cp s3://myapp-uploads/path/file.txt ./local-file.txt

# List objects
aws $EP s3 ls s3://myapp-uploads/ --recursive

# Delete object
aws $EP s3 rm s3://myapp-uploads/path/file.txt

# Sync directory
aws $EP s3 sync ./local-dir/ s3://myapp-uploads/prefix/
```

---

## Environment Variables Reference

| Variable | Purpose | Example |
|----------|---------|---------|
| `SPACES_BUCKET` | Bucket name | `myapp-uploads` |
| `SPACES_REGION` | Region code | `nyc3`, `sfo3`, `ams3`, `sgp1`, `syd1` |
| `SPACES_ENDPOINT` | API endpoint | `https://nyc3.digitaloceanspaces.com` |
| `SPACES_ACCESS_KEY` | Access key ID | (from doctl) |
| `SPACES_SECRET_KEY` | Secret access key | (from doctl, shown once) |
| `SPACES_CDN_ENDPOINT` | CDN URL (if enabled) | `https://myapp-uploads.nyc3.cdn.digitaloceanspaces.com` |

---

## Regions & Endpoints

| Region | Endpoint |
|--------|----------|
| NYC3 | `https://nyc3.digitaloceanspaces.com` |
| SFO3 | `https://sfo3.digitaloceanspaces.com` |
| AMS3 | `https://ams3.digitaloceanspaces.com` |
| SGP1 | `https://sgp1.digitaloceanspaces.com` |
| FRA1 | `https://fra1.digitaloceanspaces.com` |
| SYD1 | `https://syd1.digitaloceanspaces.com` |

---

## CORS Configuration

Configure via aws CLI (not doctl):

### Private Uploads (Presigned URLs)

```bash
cat > /tmp/cors.json << 'EOF'
{
  "CORSRules": [{
    "AllowedOrigins": ["https://myapp.com", "https://*.ondigitalocean.app"],
    "AllowedMethods": ["GET", "PUT", "POST"],
    "AllowedHeaders": ["*"],
    "ExposeHeaders": ["ETag"],
    "MaxAgeSeconds": 3600
  }]
}
EOF

aws --endpoint-url https://nyc3.digitaloceanspaces.com \
  s3api put-bucket-cors --bucket myapp-uploads --cors-configuration file:///tmp/cors.json
```

### Public Assets (CDN)

```bash
cat > /tmp/cors.json << 'EOF'
{
  "CORSRules": [{
    "AllowedOrigins": ["*"],
    "AllowedMethods": ["GET", "HEAD"],
    "AllowedHeaders": ["*"],
    "MaxAgeSeconds": 86400
  }]
}
EOF

aws --endpoint-url https://nyc3.digitaloceanspaces.com \
  s3api put-bucket-cors --bucket myapp-uploads --cors-configuration file:///tmp/cors.json
```

---

## Common Patterns

### Pattern 1: Server-Side Uploads

```
User → App API → Spaces (private bucket) → Presigned URL for download
```

App handles upload, stores in Spaces, returns presigned download URL.

### Pattern 2: Direct Upload (Presigned URLs)

```
Browser → App API (get presigned URL) → Browser uploads directly to Spaces
```

More efficient for large files — bypasses your server.

> **Warning**: Presigned URLs bypass CDN caching. Use presigned URLs for private access; use CDN URLs for public static assets.

### Pattern 3: Static Assets with CDN

```
Build process → Spaces (public bucket + CDN) → Browser loads from CDN edge
```

Best for images, CSS, JS bundles.

---

## URL Patterns

| Type | URL Format |
|------|------------|
| Standard | `https://<bucket>.<region>.digitaloceanspaces.com/<key>` |
| CDN | `https://<bucket>.<region>.cdn.digitaloceanspaces.com/<key>` |
| Custom Domain | `https://assets.myapp.com/<key>` (requires DNS setup) |

**Examples:**
```
Standard: https://myapp-uploads.nyc3.digitaloceanspaces.com/images/photo.jpg
CDN:      https://myapp-uploads.nyc3.cdn.digitaloceanspaces.com/images/photo.jpg
```

---

## SDK Configuration

For SDK setup in Node.js, Python, and Go, see [sdk-configuration.md](reference/sdk-configuration.md).

Quick example (Python):
```python
import boto3
import os

s3 = boto3.client(
    's3',
    endpoint_url=os.environ['SPACES_ENDPOINT'],
    region_name='us-east-1',  # Required placeholder
    aws_access_key_id=os.environ['SPACES_ACCESS_KEY'],
    aws_secret_access_key=os.environ['SPACES_SECRET_KEY'],
)
```

---

## Key Rotation Workflow

```bash
# 1. Create new key
NEW_KEY=$(doctl spaces keys create "myapp-spaces-key-$(date +%Y%m%d)" --output json)
echo "$NEW_KEY" | jq -r '.[0].access_key, .[0].secret_key'

# 2. Update GitHub Secrets with new credentials

# 3. Redeploy app to pick up new secrets

# 4. Verify app works with new key

# 5. Delete old key
doctl spaces keys list --format ID,Name
doctl spaces keys delete <old-key-id>
```

See [key-management.md](reference/key-management.md) for detailed rotation guide.

---

## Access Logging

Spaces can log all access requests to a separate bucket.

```bash
# Enable logging
aws --endpoint-url https://nyc3.digitaloceanspaces.com s3api put-bucket-logging \
  --bucket myapp-uploads \
  --bucket-logging-status '{
    "LoggingEnabled": {
      "TargetBucket": "myapp-logs",
      "TargetPrefix": "access-logs/myapp/"
    }
  }'

# View logs (may take minutes to appear)
aws --endpoint-url https://nyc3.digitaloceanspaces.com s3 ls s3://myapp-logs/access-logs/myapp/
```

See [access-logging.md](reference/access-logging.md) for full guide.

---

## Local Development

Use MinIO for local S3-compatible storage:

```yaml
# docker-compose.yml
services:
  minio:
    image: minio/minio
    command: server /data --console-address ":9001"
    ports:
      - "9000:9000"
      - "9001:9001"
    environment:
      MINIO_ROOT_USER: minioadmin
      MINIO_ROOT_PASSWORD: minioadmin
```

Local environment variables:
```bash
SPACES_ENDPOINT=http://localhost:9000
SPACES_REGION=us-east-1
SPACES_ACCESS_KEY=minioadmin
SPACES_SECRET_KEY=minioadmin
SPACES_BUCKET=local-bucket
```

---

## Quick Troubleshooting

| Error | Cause | Fix |
|-------|-------|-----|
| BucketAlreadyExists (409) | Name taken globally | Use unique prefix: `mycompany-myapp-uploads` |
| Access Denied (403) | Wrong credentials/region | Verify keys, check endpoint matches bucket region |
| CORS error | Origin not allowed | Add domain via `put-bucket-cors` |
| SignatureDoesNotMatch | Endpoint format wrong | Use `https://nyc3.digitaloceanspaces.com` (no trailing slash) |
| SlowDown (503) | Rate limiting | Implement exponential backoff |

**Full troubleshooting guide**: See [troubleshooting.md](reference/troubleshooting.md)

---

## Reference Files

- **[sdk-configuration.md](reference/sdk-configuration.md)** — Node.js, Python, Go SDK setup
- **[troubleshooting.md](reference/troubleshooting.md)** — Detailed error resolution
- **[aws-cli-operations.md](reference/aws-cli-operations.md)** — Complete aws CLI reference
- **[key-management.md](reference/key-management.md)** — Per-app keys and rotation
- **[access-logging.md](reference/access-logging.md)** — Bucket logging setup

---

## Integration with Other Skills

- **→ designer**: Includes Spaces environment variables when architecting apps
- **→ deployment**: Spaces credentials stored in GitHub Secrets
- **→ devcontainers**: MinIO provides local Spaces parity

---

## Documentation Links

- [Spaces Overview](https://docs.digitalocean.com/products/spaces/)
- [Using AWS SDKs with Spaces](https://docs.digitalocean.com/products/spaces/how-to/use-aws-sdks/)
- [CORS Configuration](https://docs.digitalocean.com/products/spaces/how-to/configure-cors/)
- [CDN](https://docs.digitalocean.com/products/spaces/how-to/enable-cdn/)
- [Spaces Access Logs (Blog)](https://www.digitalocean.com/blog/spaces-api-access-logs)
