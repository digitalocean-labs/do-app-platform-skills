#!/bin/bash
#
# Secure Hands-Free Database Setup
# 
# Creates database user and stores credentials directly in GitHub Secrets.
# Password is NEVER printed — flows directly from generation to secrets.
#
# Usage:
#   ./secure_setup.sh --admin-url <url> --app-name <name> --repo <owner/repo> [options]
#
# Required:
#   --admin-url     Admin connection string (doadmin)
#   --app-name      Application name (used for user/schema naming)
#   --repo          GitHub repository (owner/repo format)
#
# Optional:
#   --schema        Schema name (defaults to app-name)
#   --env           GitHub environment (staging, production, etc.)
#   --db-host       Database host (extracted from admin-url if not provided)
#   --db-port       Database port (default: 25060)
#   --db-name       Database name (default: defaultdb)
#   --secret-name   Secret name (default: DATABASE_URL)
#   --dry-run       Show what would be done without executing
#   --skip-confirm  Skip confirmation prompt
#
# Examples:
#   ./secure_setup.sh \
#     --admin-url "postgresql://doadmin:xxx@host:25060/defaultdb?sslmode=require" \
#     --app-name myapp \
#     --repo myorg/myrepo \
#     --env production
#
#   ./secure_setup.sh \
#     --admin-url "$ADMIN_URL" \
#     --app-name tenant1 \
#     --schema tenant1 \
#     --repo myorg/multitenant-app \
#     --secret-name DATABASE_URL_TENANT1
#

set -e

# Colors
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Defaults
DB_PORT="25060"
DB_NAME="defaultdb"
SECRET_NAME="DATABASE_URL"
DRY_RUN=false
SKIP_CONFIRM=false

# Parse arguments
while [[ $# -gt 0 ]]; do
    case $1 in
        --admin-url)
            ADMIN_URL="$2"
            shift 2
            ;;
        --app-name)
            APP_NAME="$2"
            shift 2
            ;;
        --schema)
            SCHEMA_NAME="$2"
            shift 2
            ;;
        --repo)
            REPO="$2"
            shift 2
            ;;
        --env)
            GH_ENV="$2"
            shift 2
            ;;
        --db-host)
            DB_HOST="$2"
            shift 2
            ;;
        --db-port)
            DB_PORT="$2"
            shift 2
            ;;
        --db-name)
            DB_NAME="$2"
            shift 2
            ;;
        --secret-name)
            SECRET_NAME="$2"
            shift 2
            ;;
        --dry-run)
            DRY_RUN=true
            shift
            ;;
        --skip-confirm)
            SKIP_CONFIRM=true
            shift
            ;;
        -h|--help)
            head -50 "$0" | tail -45
            exit 0
            ;;
        *)
            echo -e "${RED}Unknown option: $1${NC}"
            exit 1
            ;;
    esac
done

# Validate required arguments
if [[ -z "$ADMIN_URL" ]]; then
    echo -e "${RED}Error: --admin-url is required${NC}"
    exit 1
fi

if [[ -z "$APP_NAME" ]]; then
    echo -e "${RED}Error: --app-name is required${NC}"
    exit 1
fi

if [[ -z "$REPO" ]]; then
    echo -e "${RED}Error: --repo is required${NC}"
    exit 1
fi

# Derive values
SCHEMA_NAME="${SCHEMA_NAME:-$APP_NAME}"
USERNAME="${APP_NAME}_user"

# Extract DB_HOST from admin URL if not provided
if [[ -z "$DB_HOST" ]]; then
    DB_HOST=$(echo "$ADMIN_URL" | sed -E 's|.*@([^:]+):.*|\1|')
fi

# Check prerequisites
echo -e "${BLUE}Checking prerequisites...${NC}"

if ! command -v psql &> /dev/null; then
    echo -e "${RED}Error: psql is not installed${NC}"
    exit 1
fi

if ! command -v gh &> /dev/null; then
    echo -e "${RED}Error: gh CLI is not installed${NC}"
    echo "Install with: brew install gh (macOS) or see https://cli.github.com"
    exit 1
fi

if ! gh auth status &> /dev/null; then
    echo -e "${RED}Error: gh is not authenticated${NC}"
    echo "Run: gh auth login"
    exit 1
fi

# Test repo access
if ! gh secret list --repo "$REPO" &> /dev/null; then
    echo -e "${RED}Error: Cannot access secrets for $REPO${NC}"
    echo "Ensure you have admin/write access to the repository"
    exit 1
fi

echo -e "${GREEN}✓ Prerequisites OK${NC}"
echo ""

# Build environment flag
ENV_FLAG=""
if [[ -n "$GH_ENV" ]]; then
    ENV_FLAG="--env $GH_ENV"
fi

# Show plan
echo -e "${BLUE}═══════════════════════════════════════════════════════════════${NC}"
echo -e "${BLUE}                    SECURE DATABASE SETUP                       ${NC}"
echo -e "${BLUE}═══════════════════════════════════════════════════════════════${NC}"
echo ""
echo -e "  Application:    ${GREEN}$APP_NAME${NC}"
echo -e "  Schema:         ${GREEN}$SCHEMA_NAME${NC}"
echo -e "  User:           ${GREEN}$USERNAME${NC}"
echo -e "  Database:       ${GREEN}$DB_NAME${NC}"
echo -e "  Host:           ${GREEN}$DB_HOST${NC}"
echo ""
echo -e "  Repository:     ${GREEN}$REPO${NC}"
echo -e "  Environment:    ${GREEN}${GH_ENV:-<none>}${NC}"
echo -e "  Secret name:    ${GREEN}$SECRET_NAME${NC}"
echo ""
echo -e "${YELLOW}  ⚠️  Password will be generated and stored directly in GitHub Secrets${NC}"
echo -e "${YELLOW}     It will NEVER be displayed in this terminal${NC}"
echo ""

if [[ "$DRY_RUN" == true ]]; then
    echo -e "${YELLOW}DRY RUN - No changes will be made${NC}"
    echo ""
    echo "Would execute:"
    echo "  1. CREATE SCHEMA IF NOT EXISTS \"$SCHEMA_NAME\""
    echo "  2. CREATE USER $USERNAME WITH PASSWORD '<generated>'"
    echo "  3. GRANT permissions on schema $SCHEMA_NAME to $USERNAME"
    echo "  4. gh secret set $SECRET_NAME --repo $REPO $ENV_FLAG"
    exit 0
fi

# Confirmation
if [[ "$SKIP_CONFIRM" != true ]]; then
    echo -e "${BLUE}═══════════════════════════════════════════════════════════════${NC}"
    read -p "Proceed with setup? (y/N): " confirm
    if [[ "$confirm" != "y" && "$confirm" != "Y" ]]; then
        echo "Aborted."
        exit 0
    fi
    echo ""
fi

# Generate secure password (NEVER printed)
PASSWORD=$(openssl rand -base64 32)

echo -e "${BLUE}Creating schema and user...${NC}"

# Create schema
psql "$ADMIN_URL" -c "CREATE SCHEMA IF NOT EXISTS \"$SCHEMA_NAME\";" 2>/dev/null || {
    echo -e "${YELLOW}Schema may already exist, continuing...${NC}"
}

# Create user (password never echoed)
psql "$ADMIN_URL" -c "CREATE USER $USERNAME WITH PASSWORD '$PASSWORD';" 2>/dev/null || {
    echo -e "${RED}Error creating user (may already exist)${NC}"
    echo "If user exists, use cleanup_client.py to remove first"
    exit 1
}

echo -e "${GREEN}✓ User created${NC}"

# Grant permissions
echo -e "${BLUE}Granting permissions...${NC}"

psql "$ADMIN_URL" <<EOF
-- Grant schema access
GRANT USAGE ON SCHEMA "$SCHEMA_NAME" TO $USERNAME;

-- Grant full privileges on existing objects
GRANT ALL PRIVILEGES ON ALL TABLES IN SCHEMA "$SCHEMA_NAME" TO $USERNAME;
GRANT ALL PRIVILEGES ON ALL SEQUENCES IN SCHEMA "$SCHEMA_NAME" TO $USERNAME;
GRANT ALL PRIVILEGES ON ALL FUNCTIONS IN SCHEMA "$SCHEMA_NAME" TO $USERNAME;

-- Grant privileges on future objects
ALTER DEFAULT PRIVILEGES IN SCHEMA "$SCHEMA_NAME" GRANT ALL ON TABLES TO $USERNAME;
ALTER DEFAULT PRIVILEGES IN SCHEMA "$SCHEMA_NAME" GRANT ALL ON SEQUENCES TO $USERNAME;
ALTER DEFAULT PRIVILEGES IN SCHEMA "$SCHEMA_NAME" GRANT ALL ON FUNCTIONS TO $USERNAME;

-- Set default search path
ALTER USER $USERNAME SET search_path TO "$SCHEMA_NAME";

-- Revoke public schema access (isolation)
REVOKE ALL ON SCHEMA public FROM $USERNAME;
EOF

echo -e "${GREEN}✓ Permissions granted${NC}"

# Build connection string
DATABASE_URL="postgresql://${USERNAME}:${PASSWORD}@${DB_HOST}:${DB_PORT}/${DB_NAME}?sslmode=require"

# Store in GitHub Secrets (password never printed)
echo -e "${BLUE}Storing credentials in GitHub Secrets...${NC}"

echo "$DATABASE_URL" | gh secret set "$SECRET_NAME" --repo "$REPO" $ENV_FLAG

echo -e "${GREEN}✓ Secret stored${NC}"

# Clear password from memory
PASSWORD=""
DATABASE_URL=""

echo ""
echo -e "${GREEN}═══════════════════════════════════════════════════════════════${NC}"
echo -e "${GREEN}                    SETUP COMPLETE                              ${NC}"
echo -e "${GREEN}═══════════════════════════════════════════════════════════════${NC}"
echo ""
echo -e "  Schema:     $SCHEMA_NAME"
echo -e "  User:       $USERNAME"
echo -e "  Secret:     $SECRET_NAME"
echo -e "  Repository: $REPO"
if [[ -n "$GH_ENV" ]]; then
echo -e "  Environment: $GH_ENV"
fi
echo ""
echo -e "  ${GREEN}✓ Password stored securely — never displayed${NC}"
echo ""
echo -e "${BLUE}Next steps:${NC}"
echo "  1. Reference the secret in your app spec or GitHub Actions:"
echo ""
echo "     # App spec (for GitHub Actions deployment)"
echo "     envs:"
echo "       - key: DATABASE_URL"
echo "         scope: RUN_TIME"
echo "         type: SECRET"
echo "         value: $SECRET_NAME"
echo ""
echo "     # Or in GitHub Actions workflow"
echo "     env:"
echo "       DATABASE_URL: \${{ secrets.$SECRET_NAME }}"
echo ""
