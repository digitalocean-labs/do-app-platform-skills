# Spaces Access Logging

Complete guide for enabling and analyzing DigitalOcean Spaces access logs.

## Overview

Access logging records all requests made to your Spaces bucket. Logs are delivered to a target bucket asynchronously.

**Use cases:**
- Security auditing
- Usage analytics
- Debugging access issues
- Compliance requirements

**Characteristics:**
- Logs delivered asynchronously (may take minutes)
- One log file per time period
- Standard S3 access log format
- Stored in a separate bucket (recommended)

---

## Prerequisites

```bash
# Required tools
aws --version   # AWS CLI v2
jq --version    # JSON processor (optional, for parsing)

# Credentials must be set
export AWS_ACCESS_KEY_ID="your-access-key"
export AWS_SECRET_ACCESS_KEY="your-secret-key"

# Endpoint
export EP="--endpoint-url https://nyc3.digitaloceanspaces.com"
```

---

## Quick Setup

### 1. Create Log Bucket

```bash
# Create dedicated log bucket
aws $EP s3api create-bucket --bucket myapp-logs

# Verify
aws $EP s3 ls
```

### 2. Enable Logging

```bash
aws $EP s3api put-bucket-logging \
  --bucket myapp-uploads \
  --bucket-logging-status '{
    "LoggingEnabled": {
      "TargetBucket": "myapp-logs",
      "TargetPrefix": "access-logs/myapp/"
    }
  }'
```

### 3. Verify Configuration

```bash
aws $EP s3api get-bucket-logging --bucket myapp-uploads
```

Expected output:
```json
{
  "LoggingEnabled": {
    "TargetBucket": "myapp-logs",
    "TargetPrefix": "access-logs/myapp/"
  }
}
```

---

## Logging Configuration

### Using Config File

```bash
cat > /tmp/logging.json << 'EOF'
{
  "LoggingEnabled": {
    "TargetBucket": "myapp-logs",
    "TargetPrefix": "access-logs/myapp/"
  }
}
EOF

aws $EP s3api put-bucket-logging \
  --bucket myapp-uploads \
  --bucket-logging-status file:///tmp/logging.json
```

### Multiple Buckets to Same Log Bucket

Use different prefixes to separate logs:

```bash
# API bucket logs
aws $EP s3api put-bucket-logging \
  --bucket api-uploads \
  --bucket-logging-status '{
    "LoggingEnabled": {
      "TargetBucket": "central-logs",
      "TargetPrefix": "spaces/api-uploads/"
    }
  }'

# Web bucket logs
aws $EP s3api put-bucket-logging \
  --bucket web-assets \
  --bucket-logging-status '{
    "LoggingEnabled": {
      "TargetBucket": "central-logs",
      "TargetPrefix": "spaces/web-assets/"
    }
  }'
```

### Disable Logging

```bash
aws $EP s3api put-bucket-logging \
  --bucket myapp-uploads \
  --bucket-logging-status '{}'
```

---

## Viewing Logs

### List Log Files

```bash
# List all logs
aws $EP s3 ls s3://myapp-logs/access-logs/myapp/ --recursive

# Recent logs
aws $EP s3 ls s3://myapp-logs/access-logs/myapp/ --recursive | tail -20

# Count log files
aws $EP s3 ls s3://myapp-logs/access-logs/myapp/ --recursive | wc -l
```

### Download Logs

```bash
# Download all logs
mkdir -p ./spaces-logs
aws $EP s3 sync s3://myapp-logs/access-logs/myapp/ ./spaces-logs/

# Download specific date range (by prefix)
aws $EP s3 sync s3://myapp-logs/access-logs/myapp/2024-01-15 ./spaces-logs/
```

### View Log Content

```bash
# Download and view a single log
aws $EP s3 cp s3://myapp-logs/access-logs/myapp/2024-01-15-12-34-56-ABC123 - | head

# Or download first, then view
aws $EP s3 cp s3://myapp-logs/access-logs/myapp/2024-01-15-12-34-56-ABC123 /tmp/log.txt
cat /tmp/log.txt
```

---

## Log Format

Spaces access logs follow the standard S3 access log format:

```
bucket_owner bucket time remote_ip requester request_id operation key request_uri http_status error_code bytes_sent object_size total_time turn_around_time referer user_agent version_id host_id ...
```

### Key Fields

| Field | Description |
|-------|-------------|
| `bucket` | Bucket name |
| `time` | Request timestamp `[DD/Mon/YYYY:HH:MM:SS +0000]` |
| `remote_ip` | Client IP address |
| `operation` | S3 operation (GET, PUT, DELETE, etc.) |
| `key` | Object key |
| `http_status` | HTTP response code |
| `bytes_sent` | Response size |
| `user_agent` | Client user agent |

### Example Log Entry

```
myapp-uploads myapp-uploads [15/Jan/2024:14:30:22 +0000] 192.168.1.100 - ABC123 REST.GET.OBJECT images/photo.jpg "GET /images/photo.jpg HTTP/1.1" 200 - 1234567 1234567 50 - "https://myapp.com/" "Mozilla/5.0" - def456 ...
```

---

## Log Analysis

### Search for Specific Operations

```bash
# Find all DELETE operations
grep "REST.DELETE" ./spaces-logs/*

# Find 403 errors
grep " 403 " ./spaces-logs/*

# Find requests from specific IP
grep "192.168.1.100" ./spaces-logs/*
```

### Count Operations by Type

```bash
cat ./spaces-logs/* | awk '{print $8}' | sort | uniq -c | sort -rn
```

### Find Large Downloads

```bash
# Find downloads over 10MB (10485760 bytes)
cat ./spaces-logs/* | awk '$12 > 10485760 {print $0}' | head -20
```

### Top Accessed Objects

```bash
cat ./spaces-logs/* | awk '{print $9}' | sort | uniq -c | sort -rn | head -20
```

### Requests by Hour

```bash
cat ./spaces-logs/* | awk -F'[:\\[]' '{print $2":"$3}' | sort | uniq -c
```

### Error Rate

```bash
# Count by status code
cat ./spaces-logs/* | awk '{print $10}' | sort | uniq -c | sort -rn
```

---

## Automated Log Processing

### Daily Log Sync Script

```bash
#!/usr/bin/env bash
set -euo pipefail

LOG_BUCKET="myapp-logs"
LOG_PREFIX="access-logs/myapp/"
LOCAL_DIR="./spaces-logs"
EP="--endpoint-url https://nyc3.digitaloceanspaces.com"

# Sync logs
mkdir -p "$LOCAL_DIR"
aws $EP s3 sync "s3://${LOG_BUCKET}/${LOG_PREFIX}" "$LOCAL_DIR/"

# Generate daily summary
TODAY=$(date +%Y-%m-%d)
echo "=== Spaces Access Log Summary: $TODAY ===" > "${LOCAL_DIR}/summary-${TODAY}.txt"
echo "" >> "${LOCAL_DIR}/summary-${TODAY}.txt"

echo "Operations by type:" >> "${LOCAL_DIR}/summary-${TODAY}.txt"
cat "$LOCAL_DIR"/* 2>/dev/null | awk '{print $8}' | sort | uniq -c | sort -rn >> "${LOCAL_DIR}/summary-${TODAY}.txt"

echo "" >> "${LOCAL_DIR}/summary-${TODAY}.txt"
echo "Status codes:" >> "${LOCAL_DIR}/summary-${TODAY}.txt"
cat "$LOCAL_DIR"/* 2>/dev/null | awk '{print $10}' | sort | uniq -c | sort -rn >> "${LOCAL_DIR}/summary-${TODAY}.txt"

echo "Summary written to: ${LOCAL_DIR}/summary-${TODAY}.txt"
```

### Log Retention

Clean up old logs to manage storage costs:

```bash
# Delete logs older than 30 days
CUTOFF=$(date -d "30 days ago" +%Y-%m-%d)
aws $EP s3 ls s3://myapp-logs/access-logs/myapp/ \
  | awk -v cutoff="$CUTOFF" '$1 < cutoff {print $4}' \
  | xargs -I {} aws $EP s3 rm "s3://myapp-logs/access-logs/myapp/{}"
```

---

## Cost Considerations

### Storage Costs

- Logs are stored as objects in your log bucket
- Standard Spaces storage pricing applies (~$5/250GB/month)
- Each request generates ~1KB of log data
- High-traffic buckets can generate significant log volume

### Recommendations

1. **Use a dedicated log bucket** - Easier to manage retention
2. **Set up lifecycle rules** - Auto-delete old logs
3. **Compress for archival** - Download, compress, re-upload
4. **Monitor log bucket size** - Alert on unexpected growth

---

## Troubleshooting

### Logs Not Appearing

- **Wait longer** - Logs are delivered asynchronously (up to several minutes)
- **Generate traffic** - Make some PUT/GET requests to the bucket
- **Check configuration** - `get-bucket-logging` should show enabled
- **Verify log bucket** - Ensure it exists and is in the same region

### Empty Log Files

- Some requests may not generate log entries
- Check if the log bucket has the correct permissions

### Permission Denied on Log Bucket

Ensure your credentials have access to both the source bucket AND the log bucket.

### Log Format Issues

- Logs are space-delimited, not comma-delimited
- Use `awk` with space as delimiter
- Quoted fields (like request URI) contain spaces
