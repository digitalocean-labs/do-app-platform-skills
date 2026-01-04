#!/usr/bin/env python3
"""
Remove a client/tenant from a multi-tenant Postgres setup.

Drops schema (with all objects) and removes user. Requires explicit confirmation.

Usage:
    python cleanup_client.py <admin-connection> <client-name> [options]

Options:
    --confirm        Skip confirmation prompt (DANGEROUS)
    --keep-user      Keep user, only drop schema
    --generate       Generate SQL only, don't execute
    --cluster-id     Cluster ID (for removing connection pools)

Example:
    python cleanup_client.py "$ADMIN_URL" old_client
    python cleanup_client.py "$ADMIN_URL" old_client --confirm --cluster-id abc123
"""

import argparse
import subprocess
import sys


def generate_sql(client_name: str, keep_user: bool = False):
    """Generate SQL for client cleanup."""
    schema_name = client_name
    username = f"{client_name}_user"
    
    sql = f"""-- ============================================
-- CLEANUP: {client_name}
-- WARNING: This will DELETE ALL DATA in the schema!
-- ============================================

-- Step 1: Terminate active connections for user
SELECT pg_terminate_backend(pid)
FROM pg_stat_activity
WHERE usename = '{username}';

"""
    
    if not keep_user:
        sql += f"""-- Step 2: Drop owned objects and user
DROP OWNED BY {username} CASCADE;
DROP USER IF EXISTS {username};

"""
    
    sql += f"""-- Step 3: Drop schema and all objects
DROP SCHEMA IF EXISTS "{schema_name}" CASCADE;

-- Verify cleanup
SELECT 'Schema exists:' AS check, 
       EXISTS(SELECT 1 FROM pg_namespace WHERE nspname = '{schema_name}') AS result;
"""
    
    if not keep_user:
        sql += f"""
SELECT 'User exists:' AS check, 
       EXISTS(SELECT 1 FROM pg_roles WHERE rolname = '{username}') AS result;
"""
    
    return sql


def execute_cleanup(connection_string: str, client_name: str, keep_user: bool = False):
    """Execute client cleanup."""
    try:
        import psycopg2
    except ImportError:
        print("❌ psycopg2 not installed. Install with: uv pip install psycopg2-binary")
        sys.exit(1)
    
    schema_name = client_name
    username = f"{client_name}_user"
    
    conn = None
    try:
        conn = psycopg2.connect(connection_string)
        conn.autocommit = True
        cur = conn.cursor()
        
        # Terminate active connections
        cur.execute("""
            SELECT pg_terminate_backend(pid)
            FROM pg_stat_activity
            WHERE usename = %s
        """, (username,))
        terminated = cur.rowcount
        if terminated > 0:
            print(f"  Terminated {terminated} active connection(s)")
        
        if not keep_user:
            # Drop owned objects first
            try:
                cur.execute(f"DROP OWNED BY {username} CASCADE")
                print(f"  ✅ Dropped objects owned by {username}")
            except psycopg2.errors.UndefinedObject:
                pass  # User doesn't exist
            
            # Drop user
            try:
                cur.execute(f"DROP USER IF EXISTS {username}")
                print(f"  ✅ Dropped user: {username}")
            except psycopg2.Error as e:
                print(f"  ⚠️  Could not drop user: {e}")
        
        # Drop schema
        cur.execute(f'DROP SCHEMA IF EXISTS "{schema_name}" CASCADE')
        print(f"  ✅ Dropped schema: {schema_name}")
        
        cur.close()
        return True
        
    except psycopg2.Error as e:
        print(f"❌ Database error: {e}")
        return False
    finally:
        if conn:
            conn.close()


def remove_connection_pool(cluster_id: str, client_name: str):
    """Remove connection pool via doctl."""
    pool_name = f"{client_name}_pool"
    
    cmd = ["doctl", "databases", "pool", "delete", cluster_id, pool_name, "--force"]
    
    try:
        subprocess.run(cmd, capture_output=True, text=True, check=True)
        print(f"  ✅ Removed connection pool: {pool_name}")
        return True
    except subprocess.CalledProcessError as e:
        if "not found" in e.stderr.lower():
            print(f"  ℹ️  No connection pool found: {pool_name}")
        else:
            print(f"  ⚠️  Failed to remove pool: {e.stderr}")
        return False


def main():
    parser = argparse.ArgumentParser(
        description="Remove client/tenant from multi-tenant Postgres setup"
    )
    
    parser.add_argument("admin_connection", help="Admin connection string")
    parser.add_argument("client_name", help="Client/tenant name to remove")
    
    parser.add_argument("--confirm", action="store_true", 
                        help="Skip confirmation (DANGEROUS)")
    parser.add_argument("--keep-user", action="store_true",
                        help="Keep user, only drop schema")
    parser.add_argument("--generate", action="store_true",
                        help="Generate SQL only, don't execute")
    parser.add_argument("--cluster-id", help="Cluster ID for pool removal")
    
    args = parser.parse_args()
    
    client_name = args.client_name.lower().replace("-", "_").replace(" ", "_")
    username = f"{client_name}_user"
    
    print(f"Client to remove: {client_name}")
    print(f"  Schema: {client_name}")
    if not args.keep_user:
        print(f"  User: {username}")
    print()
    
    if args.generate:
        sql = generate_sql(client_name, args.keep_user)
        print(sql)
        return
    
    # Confirmation
    if not args.confirm:
        print("⚠️  WARNING: This will permanently DELETE all data in the schema!")
        print()
        response = input(f"Type '{client_name}' to confirm deletion: ")
        if response != client_name:
            print("Aborted.")
            sys.exit(1)
        print()
    
    print("Executing cleanup...")
    
    # Remove pool first (if cluster-id provided)
    if args.cluster_id:
        remove_connection_pool(args.cluster_id, client_name)
    
    # Execute database cleanup
    success = execute_cleanup(args.admin_connection, client_name, args.keep_user)
    
    if success:
        print()
        print(f"✅ Client '{client_name}' removed successfully")
    else:
        print()
        print(f"⚠️  Cleanup completed with warnings")


if __name__ == "__main__":
    main()
