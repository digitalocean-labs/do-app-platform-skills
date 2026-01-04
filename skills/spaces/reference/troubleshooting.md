# Spaces Troubleshooting

Detailed troubleshooting for common DigitalOcean Spaces issues.

---

## BucketAlreadyExists (409)

**Cause**: Bucket name is already taken (globally unique namespace).

**Symptoms**:
```
ERROR: BucketAlreadyExists: The requested bucket name is not available.
```

**Fix**:

1. If it's your bucket, treat as success:
```bash
s3cmd mb s3://myapp-uploads 2>&1 | grep -q "already exists" && echo "Bucket ready" || s3cmd mb s3://myapp-uploads
```

2. If bucket belongs to someone else, choose a different name:
```bash
# Add project prefix or suffix
s3cmd mb s3://mycompany-myapp-uploads
```

---

## Access Denied (403)

**Cause**: Wrong credentials, bucket permissions, or region mismatch.

**Symptoms**:
```
AccessDenied: Access Denied
```

**Diagnostic steps**:

1. Verify keys match DO Console:
```bash
# Check current keys (first 4 chars)
echo $SPACES_ACCESS_KEY | head -c 4
# Compare with DO Console → API → Spaces Keys
```

2. Verify bucket region matches endpoint:
```bash
# If bucket is in nyc3, endpoint must be:
SPACES_ENDPOINT=https://nyc3.digitaloceanspaces.com
```

3. Check bucket ownership:
```bash
s3cmd ls s3://myapp-uploads
# If empty or error, you may not own this bucket
```

4. Regenerate keys if necessary:
   - Go to DO Console → API → Spaces Keys
   - Generate new key pair
   - Update GitHub Secrets

---

## CORS Error in Browser

**Cause**: CORS not configured or missing your app origin.

**Symptoms**:
```
Access to XMLHttpRequest at 'https://bucket.nyc3.digitaloceanspaces.com/...'
from origin 'https://myapp.com' has been blocked by CORS policy
```

**Fix**:

1. Go to DO Console → Spaces → your bucket → Settings → CORS

2. Add your origins:
```json
{
  "CORSRules": [
    {
      "AllowedOrigins": [
        "https://myapp.com",
        "https://*.ondigitalocean.app"
      ],
      "AllowedMethods": ["GET", "PUT", "POST", "DELETE"],
      "AllowedHeaders": ["*"],
      "ExposeHeaders": ["ETag"],
      "MaxAgeSeconds": 3600
    }
  ]
}
```

3. Include `https://*.ondigitalocean.app` for App Platform preview URLs

4. Wait 1-2 minutes for CORS changes to propagate

---

## SignatureDoesNotMatch

**Cause**: Endpoint URL format issue or clock skew.

**Symptoms**:
```
SignatureDoesNotMatch: The request signature we calculated does not match the signature you provided.
```

**Fix**:

1. Ensure endpoint includes `https://`:
```javascript
// Correct
endpoint: 'https://nyc3.digitaloceanspaces.com'

// Wrong - missing protocol
endpoint: 'nyc3.digitaloceanspaces.com'
```

2. Ensure no trailing slash:
```javascript
// Correct
endpoint: 'https://nyc3.digitaloceanspaces.com'

// Wrong - trailing slash
endpoint: 'https://nyc3.digitaloceanspaces.com/'
```

3. Check system clock (signature includes timestamp):
```bash
# Compare with NTP server
date && curl -s http://worldtimeapi.org/api/ip | jq .datetime
```

---

## SlowDown (503)

**Cause**: Rate limiting - too many requests.

**Symptoms**:
```
SlowDown: Please reduce your request rate.
```

**Fix**:

1. Implement exponential backoff:
```javascript
async function uploadWithRetry(params, maxRetries = 3) {
  for (let i = 0; i < maxRetries; i++) {
    try {
      return await s3.send(new PutObjectCommand(params));
    } catch (err) {
      if (err.Code === 'SlowDown' && i < maxRetries - 1) {
        await new Promise(r => setTimeout(r, Math.pow(2, i) * 1000));
        continue;
      }
      throw err;
    }
  }
}
```

2. Use batch operations where possible
3. Consider CDN for high-traffic reads

---

## Upload Succeeds but File Not Found

**Cause**: Eventual consistency or wrong bucket/key.

**Diagnostic**:
```bash
# List bucket contents
s3cmd ls s3://myapp-uploads/uploads/

# Check if file exists with exact key
s3cmd info s3://myapp-uploads/uploads/file.txt
```

**Fix**:
1. Wait a few seconds after upload before reading
2. Verify bucket name and key path are correct
3. Check if uploading to wrong bucket (environment mismatch)
