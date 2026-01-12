#!/usr/bin/env bash
# Rotate Spaces credentials for an application
#
# Creates a new key with timestamp suffix, prints credentials,
# and provides instructions for completing the rotation.
#
# Required env vars:
#   APP_NAME              - Application name (for naming)
#   DO_SPACES_KEY_NAME    - Base name for the Spaces key
#
# This script does NOT automatically delete old keys - that's a manual
# step after verifying the new key works in production.

set -euo pipefail
cd "$(dirname "$0")/.."

source scripts/_lib.sh

# Check dependencies
need doctl
need jq

# Validate required env vars
req_env APP_NAME
req_env DO_SPACES_KEY_NAME

echo "=============================================="
echo "Rotate Spaces Key for: ${APP_NAME}"
echo "=============================================="
echo ""

# Generate new key name with timestamp
TS="$(date +%Y%m%d-%H%M%S)"
NEW_KEY_NAME="${DO_SPACES_KEY_NAME}-${TS}"

info "Creating new key: ${NEW_KEY_NAME}"

# Create the new key
OUT="$(doctl spaces keys create "${NEW_KEY_NAME}" --output json)"

NEW_ACCESS_KEY="$(jq -r '.[0].access_key' <<<"$OUT")"
NEW_SECRET_KEY="$(jq -r '.[0].secret_key' <<<"$OUT")"

[[ -n "$NEW_ACCESS_KEY" && "$NEW_ACCESS_KEY" != "null" ]] || die "Failed to parse new access_key"
[[ -n "$NEW_SECRET_KEY" && "$NEW_SECRET_KEY" != "null" ]] || die "Failed to parse new secret_key"

echo ""
echo "=============================================="
echo "NEW CREDENTIALS"
echo "=============================================="
echo ""
echo "Key Name:   ${NEW_KEY_NAME}"
echo "Access Key: ${NEW_ACCESS_KEY}"
echo "Secret Key: ${NEW_SECRET_KEY}"
echo ""
warn "IMPORTANT: Secret is only shown once. Copy it now!"
echo ""

echo "=============================================="
echo "NEXT STEPS (Manual)"
echo "=============================================="
echo ""
echo "1. Update your secret manager / GitHub Secrets with new credentials:"
echo "   - SPACES_ACCESS_KEY = ${NEW_ACCESS_KEY}"
echo "   - SPACES_SECRET_KEY = (the secret shown above)"
echo ""
echo "2. Redeploy your application to pick up new secrets"
echo ""
echo "3. Verify the application works with the new key"
echo ""
echo "4. After confirming success, delete old key(s):"
echo ""
echo "   # List all keys:"
echo "   doctl spaces keys list --format ID,Name,CreatedAt"
echo ""
echo "   # Delete old key by ID:"
echo "   doctl spaces keys delete <old-key-id>"
echo ""

# Show existing keys for reference
echo "=============================================="
echo "EXISTING KEYS (for reference)"
echo "=============================================="
doctl spaces keys list --format ID,Name,CreatedAt
