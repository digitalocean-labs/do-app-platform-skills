#!/bin/bash
#
# Get admin connection string for a DigitalOcean Postgres cluster
#
# Usage:
#   ./get_admin_conn.sh <cluster-id>
#   ./get_admin_conn.sh --list  # List available clusters
#
# Example:
#   ./get_admin_conn.sh 66991d56-450d-42d4-8f7f-7d26b8cc9382

set -e

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

if [ "$1" == "--list" ] || [ "$1" == "-l" ]; then
    echo "Available Postgres clusters:"
    echo ""
    doctl databases list --format ID,Name,Engine,Region,Status --no-header | grep -i pg || echo "No Postgres clusters found"
    exit 0
fi

if [ -z "$1" ]; then
    echo -e "${YELLOW}Usage:${NC} $0 <cluster-id>"
    echo ""
    echo "Options:"
    echo "  --list, -l    List available clusters"
    echo ""
    echo "Example:"
    echo "  $0 66991d56-450d-42d4-8f7f-7d26b8cc9382"
    echo ""
    echo "Find your cluster ID with:"
    echo "  doctl databases list"
    exit 1
fi

CLUSTER_ID="$1"

echo "Fetching connection string for cluster: $CLUSTER_ID"
echo ""

# Verify doctl is authenticated
if ! doctl account get &>/dev/null; then
    echo -e "${RED}❌ Error: doctl not authenticated${NC}"
    echo ""
    echo "Run: doctl auth init"
    exit 1
fi

# Get connection details
CONN_OUTPUT=$(doctl databases connection "$CLUSTER_ID" 2>&1) || {
    echo -e "${RED}❌ Error: Could not retrieve connection string${NC}"
    echo ""
    echo "Make sure the cluster ID is correct."
    echo "List clusters with: doctl databases list"
    exit 1
}

# Extract URI
CONN_STRING=$(echo "$CONN_OUTPUT" | grep -oE 'postgresql://[^ ]+' | head -n1)

if [ -z "$CONN_STRING" ]; then
    echo -e "${RED}❌ Error: Could not parse connection string${NC}"
    echo ""
    echo "Raw output:"
    echo "$CONN_OUTPUT"
    exit 1
fi

echo -e "${GREEN}✅ Admin Connection String:${NC}"
echo ""
echo "$CONN_STRING"
echo ""
echo "Usage examples:"
echo ""
echo "  # Connect with psql:"
echo "  psql \"$CONN_STRING\""
echo ""
echo "  # Use with create_schema_user.py:"
echo "  python scripts/create_schema_user.py myapp myapp_user secure_pass --execute -c \"$CONN_STRING\""
echo ""
echo "  # Export as variable:"
echo "  export ADMIN_URL=\"$CONN_STRING\""
