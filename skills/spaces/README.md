# Spaces Skill

Configure DigitalOcean Spaces (S3-compatible object storage) for App Platform applications.

## What This Skill Does

- Configures **Spaces endpoints** and credentials for App Platform
- Sets up **CORS** for browser-based uploads
- Provides **presigned URL** patterns for secure access
- Enables **CDN** for static asset delivery
- Configures **local development** with MinIO

## Quick Start

```yaml
# Add to .do/app.yaml
envs:
  - key: SPACES_BUCKET
    value: myapp-uploads
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

## Key Decisions This Skill Makes

| Decision | Default | Rationale |
|----------|---------|-----------|
| SDK compatibility | AWS S3 SDK | Industry standard |
| Credential storage | GitHub Secrets | Secure, AI never sees keys |
| Local testing | MinIO | S3-compatible, easy setup |
| CDN | Enabled for public assets | Better performance |

## Files

- `SKILL.md` — Complete skill documentation with patterns
- `reference/sdk-configuration.md` — Node.js, Python, Go SDK setup
- `reference/troubleshooting.md` — Common errors and fixes

## Integration

| Direction | Skill | Integration |
|-----------|-------|-------------|
| → | designer | Include Spaces env vars in app spec |
| → | deployment | Store credentials in GitHub Secrets |
| → | devcontainers | MinIO provides local Spaces parity |

## Related Skills

- **designer** — Include storage in app architecture
- **deployment** — Deploy apps with Spaces integration
- **devcontainers** — Local S3-compatible storage
