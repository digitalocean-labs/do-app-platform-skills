# S3-Compatible Storage Patterns

Local vs production S3 configuration patterns for DigitalOcean Spaces compatibility.

## The Problem

DigitalOcean Spaces and local S3 storage (RustFS/MinIO) require different configurations:

| Aspect | Local (RustFS) | Production (DO Spaces) |
|--------|----------------|------------------------|
| Endpoint | `http://minio:9000` | `https://{region}.digitaloceanspaces.com` |
| Path Style | `true` (required) | `false` |
| Bucket Creation | Auto-create on connect | Manual via dashboard/CLI |
| Credentials | `rustfsadmin/rustfsadmin` | Your Spaces access keys |

---

## Environment Variable Pattern

### Local Development (`env-devcontainer`)

```bash
SPACES_ENDPOINT=http://minio:9000
SPACES_KEY_ID=rustfsadmin
SPACES_SECRET_KEY=rustfsadmin
SPACES_BUCKET_NAME=my-app-local
SPACES_FORCE_PATH_STYLE=true
SPACES_REGION=us-east-1
```

### Production (App Platform env vars)

```bash
SPACES_KEY_ID=DO00...
SPACES_SECRET_KEY=...
SPACES_BUCKET_NAME=my-app-prod
SPACES_REGION=nyc3
# SPACES_ENDPOINT not set - uses default DO Spaces URL
```

---

## Code Pattern: Auto-Detect Local Endpoint

### TypeScript/JavaScript

```typescript
function isLocalS3Endpoint(): boolean {
  const endpoint = process.env.SPACES_ENDPOINT || '';
  return (
    endpoint.startsWith('http://') ||
    endpoint.includes('localhost') ||
    endpoint.includes('minio') ||
    endpoint.includes('127.0.0.1')
  );
}

// S3 Client configuration
const s3Client = new S3Client({
  endpoint: process.env.SPACES_ENDPOINT ||
    `https://${process.env.SPACES_REGION}.digitaloceanspaces.com`,
  region: process.env.SPACES_REGION || 'us-east-1',
  forcePathStyle: isLocalS3Endpoint(),
  credentials: {
    accessKeyId: process.env.SPACES_KEY_ID!,
    secretAccessKey: process.env.SPACES_SECRET_KEY!,
  },
});
```

### Python

```python
import os
from boto3 import client
from botocore.config import Config

def is_local_s3_endpoint():
    endpoint = os.environ.get('SPACES_ENDPOINT', '')
    return any(x in endpoint for x in ['http://', 'localhost', 'minio', '127.0.0.1'])

s3 = client(
    's3',
    endpoint_url=os.environ.get('SPACES_ENDPOINT') or
        f"https://{os.environ['SPACES_REGION']}.digitaloceanspaces.com",
    aws_access_key_id=os.environ['SPACES_KEY_ID'],
    aws_secret_access_key=os.environ['SPACES_SECRET_KEY'],
    config=Config(s3={'addressing_style': 'path' if is_local_s3_endpoint() else 'virtual'})
)
```

### Go

```go
package main

import (
    "os"
    "strings"

    "github.com/aws/aws-sdk-go-v2/config"
    "github.com/aws/aws-sdk-go-v2/service/s3"
)

func isLocalS3Endpoint() bool {
    endpoint := os.Getenv("SPACES_ENDPOINT")
    return strings.HasPrefix(endpoint, "http://") ||
        strings.Contains(endpoint, "localhost") ||
        strings.Contains(endpoint, "minio") ||
        strings.Contains(endpoint, "127.0.0.1")
}

func getS3Client() *s3.Client {
    endpoint := os.Getenv("SPACES_ENDPOINT")
    if endpoint == "" {
        endpoint = "https://" + os.Getenv("SPACES_REGION") + ".digitaloceanspaces.com"
    }

    cfg, _ := config.LoadDefaultConfig(context.TODO())

    return s3.NewFromConfig(cfg, func(o *s3.Options) {
        o.BaseEndpoint = &endpoint
        o.UsePathStyle = isLocalS3Endpoint()
    })
}
```

---

## Auto-Create Bucket (Local Only)

For local development, auto-create the bucket if it doesn't exist:

### TypeScript

```typescript
import { S3Client, HeadBucketCommand, CreateBucketCommand } from '@aws-sdk/client-s3';

async function ensureBucketExists(client: S3Client, bucket: string) {
  if (!isLocalS3Endpoint()) return; // Only for local

  try {
    await client.send(new HeadBucketCommand({ Bucket: bucket }));
  } catch (error: any) {
    if (error.name === 'NotFound' || error.name === 'NoSuchBucket') {
      await client.send(new CreateBucketCommand({ Bucket: bucket }));
      console.log(`Created bucket: ${bucket}`);
    }
  }
}

// Usage at app startup
await ensureBucketExists(s3Client, process.env.SPACES_BUCKET_NAME!);
```

### Python

```python
import boto3
from botocore.exceptions import ClientError

def ensure_bucket_exists(s3_client, bucket_name):
    if not is_local_s3_endpoint():
        return  # Only for local

    try:
        s3_client.head_bucket(Bucket=bucket_name)
    except ClientError as e:
        if e.response['Error']['Code'] in ['404', 'NoSuchBucket']:
            s3_client.create_bucket(Bucket=bucket_name)
            print(f"Created bucket: {bucket_name}")

# Usage at app startup
ensure_bucket_exists(s3, os.environ['SPACES_BUCKET_NAME'])
```

---

## Complete Environment Template

```bash
# S3-Compatible Storage (DigitalOcean Spaces / RustFS)
# ================================================
# Local: Set SPACES_ENDPOINT to http://minio:9000
# Production: Leave SPACES_ENDPOINT unset

# Required in all environments
SPACES_KEY_ID=rustfsadmin
SPACES_SECRET_KEY=rustfsadmin
SPACES_BUCKET_NAME=my-app-local
SPACES_REGION=us-east-1

# Local only - set for RustFS/MinIO
SPACES_ENDPOINT=http://minio:9000
SPACES_FORCE_PATH_STYLE=true
```

---

## Testing S3 Connectivity

### Using AWS CLI

```bash
# Configure AWS CLI for local RustFS
export AWS_ACCESS_KEY_ID=rustfsadmin
export AWS_SECRET_ACCESS_KEY=rustfsadmin

# List buckets
aws --endpoint-url http://minio:9000 s3 ls

# Create bucket
aws --endpoint-url http://minio:9000 s3 mb s3://my-app-local

# Upload file
aws --endpoint-url http://minio:9000 s3 cp test.txt s3://my-app-local/

# Download file
aws --endpoint-url http://minio:9000 s3 cp s3://my-app-local/test.txt ./downloaded.txt
```

### Using curl

```bash
# Health check
curl -sf http://minio:9000/health

# List buckets (requires signing - use AWS CLI instead)
```

---

## RustFS vs MinIO

This skill uses RustFS (`rustfs/rustfs:latest`) as the S3-compatible storage:

| Feature | RustFS | MinIO |
|---------|--------|-------|
| Image size | Smaller | Larger |
| Memory usage | Lower | Higher |
| S3 compatibility | Good | Excellent |
| Console UI | Port 9001 | Port 9001 |
| Default creds | `rustfsadmin/rustfsadmin` | `minioadmin/minioadmin` |

The profile name `minio` is kept for backward compatibility.

---

## Common Issues

### Path Style vs Virtual Hosted Style

**Problem:** `The bucket you are attempting to access must be addressed using the specified endpoint`

**Solution:** Set `forcePathStyle: true` for local endpoints.

### SSL/TLS for Local

**Problem:** `unable to verify the first certificate`

**Solution:** Local endpoints use `http://` not `https://`. Ensure your code handles this:

```typescript
// Check if local endpoint
const isSecure = !isLocalS3Endpoint();
// Use http:// for local, https:// for production
```

### CORS for Browser Uploads

**Problem:** Browser-based uploads fail with CORS errors.

**Solution:** RustFS/MinIO needs CORS configuration for browser uploads. Use signed URLs from backend instead, or configure CORS:

```bash
# MinIO client example
mc cors set my-bucket '{"CORSRules":[{"AllowedOrigins":["*"],"AllowedMethods":["GET","PUT","POST"],"AllowedHeaders":["*"]}]}'
```
