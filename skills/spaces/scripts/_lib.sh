#!/usr/bin/env bash
# Common functions for Spaces management scripts
# Source this file: source scripts/_lib.sh

set -euo pipefail

# -----------------------------------------------------------------------------
# Utility functions
# -----------------------------------------------------------------------------

die() {
  echo "ERROR: $*" >&2
  exit 1
}

warn() {
  echo "WARNING: $*" >&2
}

info() {
  echo "INFO: $*"
}

need() {
  command -v "$1" >/dev/null 2>&1 || die "Missing dependency: $1"
}

req_env() {
  local v="$1"
  [[ -n "${!v:-}" ]] || die "Missing required env var: $v"
}

# -----------------------------------------------------------------------------
# AWS CLI helpers
# -----------------------------------------------------------------------------

# Build common aws CLI args for Spaces endpoint
# Usage: aws $(aws_args) s3 ls
aws_args() {
  local args=()
  args+=(--endpoint-url "${DO_SPACES_ENDPOINT}")
  # If AWS_PROFILE is set, use it. Otherwise rely on env vars.
  if [[ -n "${AWS_PROFILE:-}" ]]; then
    args+=(--profile "${AWS_PROFILE}")
  fi
  printf '%s\n' "${args[@]}"
}

# Run aws command with Spaces endpoint
# Usage: aws_spaces s3 ls
aws_spaces() {
  aws --endpoint-url "${DO_SPACES_ENDPOINT}" "$@"
}

# -----------------------------------------------------------------------------
# Bucket operations (idempotent)
# -----------------------------------------------------------------------------

# Check if bucket exists
bucket_exists() {
  local bucket="$1"
  aws_spaces s3api head-bucket --bucket "$bucket" >/dev/null 2>&1
}

# Create bucket if it doesn't exist (idempotent)
ensure_bucket() {
  local bucket="$1"

  if bucket_exists "$bucket"; then
    info "Bucket exists: $bucket"
    return 0
  fi

  info "Creating bucket: $bucket"
  aws_spaces s3api create-bucket --bucket "$bucket" >/dev/null
  info "Created bucket: $bucket"
}

# -----------------------------------------------------------------------------
# Logging configuration
# -----------------------------------------------------------------------------

# Enable bucket logging (idempotent)
put_logging() {
  local src_bucket="$1"
  local log_bucket="$2"
  local log_prefix="$3"

  local tmp_json
  tmp_json="$(mktemp)"

  # Check if template exists, otherwise create inline
  local script_dir
  script_dir="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
  local template_path="${script_dir}/../templates/bucket-logging.json"

  if [[ -f "$template_path" ]]; then
    sed \
      -e "s/__LOG_BUCKET__/${log_bucket}/g" \
      -e "s#__LOG_PREFIX__#${log_prefix}#g" \
      "$template_path" > "${tmp_json}"
  else
    cat > "${tmp_json}" << EOF
{
  "LoggingEnabled": {
    "TargetBucket": "${log_bucket}",
    "TargetPrefix": "${log_prefix}"
  }
}
EOF
  fi

  info "Enabling access logging:"
  info "  source: ${src_bucket}"
  info "  target: ${log_bucket}"
  info "  prefix: ${log_prefix}"

  aws_spaces s3api put-bucket-logging \
    --bucket "${src_bucket}" \
    --bucket-logging-status "file://${tmp_json}" >/dev/null

  rm -f "${tmp_json}"
  info "Logging enabled successfully"
}

# Get current logging configuration
get_logging() {
  local src_bucket="$1"
  aws_spaces s3api get-bucket-logging --bucket "${src_bucket}"
}

# -----------------------------------------------------------------------------
# Key management via doctl
# -----------------------------------------------------------------------------

# Create a new Spaces key and export credentials to current shell
# Returns JSON output; caller should capture and store the secret
mint_spaces_key() {
  local key_name="$1"

  info "Creating Spaces key via doctl: ${key_name}"
  local out
  out="$(doctl spaces keys create "${key_name}" --output json)"

  local access_key secret_key
  access_key="$(jq -r '.[0].access_key' <<<"$out")"
  secret_key="$(jq -r '.[0].secret_key' <<<"$out")"

  [[ -n "$access_key" && "$access_key" != "null" ]] || die "Failed to parse access_key from doctl output"
  [[ -n "$secret_key" && "$secret_key" != "null" ]] || die "Failed to parse secret_key from doctl output"

  echo "$out"
}

# Create key and export to environment (for immediate use)
mint_spaces_key_to_env() {
  local key_name="$1"

  local out
  out="$(mint_spaces_key "$key_name")"

  local access_key secret_key
  access_key="$(jq -r '.[0].access_key' <<<"$out")"
  secret_key="$(jq -r '.[0].secret_key' <<<"$out")"

  # Export for AWS CLI (env-based auth)
  export AWS_ACCESS_KEY_ID="$access_key"
  export AWS_SECRET_ACCESS_KEY="$secret_key"
  export AWS_DEFAULT_REGION="${AWS_DEFAULT_REGION:-us-east-1}"

  info "Exported AWS_ACCESS_KEY_ID/AWS_SECRET_ACCESS_KEY into current shell"
  warn "IMPORTANT: Secret is only shown once. Store it in your secret manager!"
  echo ""
  echo "Access Key: $access_key"
  echo "Secret Key: $secret_key"
  echo ""
}

# List all Spaces keys
list_spaces_keys() {
  doctl spaces keys list --format ID,Name,CreatedAt
}

# Delete a Spaces key by ID
delete_spaces_key() {
  local key_id="$1"
  doctl spaces keys delete "$key_id" --force
}
