#!/usr/bin/env python3
"""
List all schemas and users with their permissions.

Useful for auditing multi-tenant setups and verifying isolation.

Usage:
    python list_schemas_users.py <connection_string>

Example:
    python list_schemas_users.py "postgresql://doadmin:pass@host:25060/defaultdb?sslmode=require"
"""

import sys

def list_schemas_users(connection_string: str):
    """List all schemas, users, and their permissions."""
    try:
        import psycopg2
    except ImportError:
        print("❌ psycopg2 not installed. Install with: uv pip install psycopg2-binary")
        sys.exit(1)
    
    conn = None
    try:
        conn = psycopg2.connect(connection_string)
        cur = conn.cursor()
        
        # Get schemas with table counts
        print("=" * 70)
        print("SCHEMAS")
        print("=" * 70)
        
        cur.execute("""
            SELECT 
                n.nspname AS schema_name,
                r.rolname AS owner,
                (SELECT COUNT(*) 
                 FROM information_schema.tables 
                 WHERE table_schema = n.nspname 
                 AND table_type = 'BASE TABLE') as table_count
            FROM pg_namespace n
            JOIN pg_roles r ON n.nspowner = r.oid
            WHERE n.nspname NOT IN ('pg_catalog', 'information_schema', 'pg_toast')
              AND n.nspname NOT LIKE 'pg_temp_%'
              AND n.nspname NOT LIKE 'pg_toast_temp_%'
            ORDER BY n.nspname
        """)
        
        schemas = cur.fetchall()
        print(f"{'Schema':<30} {'Owner':<20} {'Tables':<10}")
        print("-" * 70)
        for schema_name, owner, table_count in schemas:
            print(f"{schema_name:<30} {owner:<20} {table_count:<10}")
        
        # Get users (non-system)
        print()
        print("=" * 70)
        print("USERS (non-system)")
        print("=" * 70)
        
        cur.execute("""
            SELECT 
                rolname,
                rolcanlogin,
                rolconnlimit,
                COALESCE(
                    (SELECT string_agg(nspname, ', ')
                     FROM pg_namespace
                     WHERE has_schema_privilege(rolname, nspname, 'USAGE')
                       AND nspname NOT IN ('pg_catalog', 'information_schema', 'pg_toast')
                       AND nspname NOT LIKE 'pg_temp_%'
                    ), 'none'
                ) as accessible_schemas
            FROM pg_roles
            WHERE rolname NOT LIKE 'pg_%'
              AND rolname NOT IN ('doadmin', 'postgres')
            ORDER BY rolname
        """)
        
        users = cur.fetchall()
        print(f"{'User':<25} {'Can Login':<12} {'Conn Limit':<12} {'Accessible Schemas'}")
        print("-" * 70)
        for username, can_login, conn_limit, accessible_schemas in users:
            limit_str = str(conn_limit) if conn_limit >= 0 else "unlimited"
            print(f"{username:<25} {str(can_login):<12} {limit_str:<12} {accessible_schemas}")
        
        # Check for potential isolation issues
        print()
        print("=" * 70)
        print("ISOLATION CHECK")
        print("=" * 70)
        
        cur.execute("""
            SELECT 
                grantee,
                privilege_type
            FROM information_schema.schema_privileges
            WHERE schema_name = 'public'
              AND grantee NOT IN ('postgres', 'doadmin', 'PUBLIC')
              AND grantee NOT LIKE 'pg_%'
        """)
        
        public_access = cur.fetchall()
        if public_access:
            print("⚠️  WARNING: Following users have access to 'public' schema:")
            for grantee, priv_type in public_access:
                print(f"   - {grantee}: {priv_type}")
            print()
            print("   To fix, run for each user:")
            print("   REVOKE ALL ON SCHEMA public FROM <username>;")
        else:
            print("✅ No non-admin users have access to 'public' schema")
        
        cur.close()
        
    except psycopg2.Error as e:
        print(f"❌ Database error: {e}")
        sys.exit(1)
    finally:
        if conn:
            conn.close()


def main():
    if len(sys.argv) != 2:
        print("Usage: python list_schemas_users.py <connection_string>")
        print()
        print("Example:")
        print('  python list_schemas_users.py "postgresql://doadmin:pass@host:25060/defaultdb?sslmode=require"')
        sys.exit(1)
    
    connection_string = sys.argv[1]
    list_schemas_users(connection_string)


if __name__ == "__main__":
    main()
