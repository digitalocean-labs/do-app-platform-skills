#!/usr/bin/env python3
"""
Add a new client/tenant to a multi-tenant Postgres setup.

Creates schema, user, sets permissions, and optionally creates connection pool.

Usage:
    python add_client.py <cluster-id> <admin-connection> <client-name> [options]

Options:
    --password       Password for user (generated if not provided)
    --create-pool    Create connection pool for the client
    --pool-size      Pool size (default: 25)
    --pool-mode      Pool mode: transaction, session, statement (default: transaction)
    --generate       Generate SQL only, don't execute
    --output-dir     Directory for generated SQL (with --generate)

Example:
    python add_client.py abc123 "$ADMIN_URL" acme_corp --create-pool
    python add_client.py abc123 "$ADMIN_URL" acme_corp --generate --output-dir ./sql/acme
"""

import argparse
import subprocess
import sys
import os
import secrets
import string
from urllib.parse import urlparse, parse_qs


def generate_password(length: int = 32) -> str:
    """Generate a secure random password."""
    alphabet = string.ascii_letters + string.digits
    return ''.join(secrets.choice(alphabet) for _ in range(length))


def generate_sql(client_name: str, username: str, password: str, output_dir: str = None):
    """Generate SQL files for client setup."""
    schema_name = client_name
    
    setup_sql = f"""-- Client Setup: {client_name}
\\c defaultdb
CREATE SCHEMA IF NOT EXISTS "{schema_name}";
"""
    
    users_sql = f"""-- User Setup: {client_name}
CREATE USER {username} WITH PASSWORD '{password}';
"""
    
    permissions_sql = f"""-- Permissions: {client_name}
GRANT USAGE ON SCHEMA "{schema_name}" TO {username};
GRANT ALL PRIVILEGES ON ALL TABLES IN SCHEMA "{schema_name}" TO {username};
GRANT ALL PRIVILEGES ON ALL SEQUENCES IN SCHEMA "{schema_name}" TO {username};
GRANT ALL PRIVILEGES ON ALL FUNCTIONS IN SCHEMA "{schema_name}" TO {username};
ALTER DEFAULT PRIVILEGES IN SCHEMA "{schema_name}" GRANT ALL ON TABLES TO {username};
ALTER DEFAULT PRIVILEGES IN SCHEMA "{schema_name}" GRANT ALL ON SEQUENCES TO {username};
ALTER DEFAULT PRIVILEGES IN SCHEMA "{schema_name}" GRANT ALL ON FUNCTIONS TO {username};
ALTER USER {username} SET search_path TO "{schema_name}";
REVOKE ALL ON SCHEMA public FROM {username};
"""
    
    if output_dir:
        os.makedirs(output_dir, exist_ok=True)
        with open(os.path.join(output_dir, "db-setup.sql"), "w") as f:
            f.write(setup_sql)
        with open(os.path.join(output_dir, "db-users.sql"), "w") as f:
            f.write(users_sql)
        with open(os.path.join(output_dir, "db-permissions.sql"), "w") as f:
            f.write(permissions_sql)
        
        print(f"✅ Generated SQL files in: {output_dir}/")
        print(f"   Password: {password}")
    else:
        print(setup_sql)
        print(users_sql)
        print(permissions_sql)
        print(f"\n# Generated password: {password}")
    
    return password


def execute_setup(connection_string: str, client_name: str, username: str, password: str):
    """Execute client setup directly."""
    try:
        import psycopg2
    except ImportError:
        print("❌ psycopg2 not installed. Install with: uv pip install psycopg2-binary")
        sys.exit(1)
    
    schema_name = client_name
    
    conn = None
    try:
        conn = psycopg2.connect(connection_string)
        conn.autocommit = True
        cur = conn.cursor()
        
        print(f"Setting up client: {client_name}")
        
        cur.execute(f'CREATE SCHEMA IF NOT EXISTS "{schema_name}"')
        print(f"  ✅ Created schema: {schema_name}")
        
        cur.execute(f"CREATE USER {username} WITH PASSWORD %s", (password,))
        print(f"  ✅ Created user: {username}")
        
        cur.execute(f'GRANT USAGE ON SCHEMA "{schema_name}" TO {username}')
        cur.execute(f'GRANT ALL PRIVILEGES ON ALL TABLES IN SCHEMA "{schema_name}" TO {username}')
        cur.execute(f'GRANT ALL PRIVILEGES ON ALL SEQUENCES IN SCHEMA "{schema_name}" TO {username}')
        cur.execute(f'GRANT ALL PRIVILEGES ON ALL FUNCTIONS IN SCHEMA "{schema_name}" TO {username}')
        cur.execute(f'ALTER DEFAULT PRIVILEGES IN SCHEMA "{schema_name}" GRANT ALL ON TABLES TO {username}')
        cur.execute(f'ALTER DEFAULT PRIVILEGES IN SCHEMA "{schema_name}" GRANT ALL ON SEQUENCES TO {username}')
        cur.execute(f'ALTER DEFAULT PRIVILEGES IN SCHEMA "{schema_name}" GRANT ALL ON FUNCTIONS TO {username}')
        cur.execute(f'ALTER USER {username} SET search_path TO "{schema_name}"')
        cur.execute(f'REVOKE ALL ON SCHEMA public FROM {username}')
        print(f"  ✅ Configured permissions")
        
        cur.close()
        return True
        
    except psycopg2.errors.DuplicateSchema:
        print(f"  ⚠️  Schema '{schema_name}' already exists")
        return False
    except psycopg2.errors.DuplicateObject:
        print(f"  ⚠️  User '{username}' already exists")
        return False
    except psycopg2.Error as e:
        print(f"❌ Database error: {e}")
        return False
    finally:
        if conn:
            conn.close()


def create_connection_pool(cluster_id: str, client_name: str, username: str, 
                           pool_size: int = 25, pool_mode: str = "transaction"):
    """Create connection pool via doctl."""
    pool_name = f"{client_name}_pool"
    
    cmd = [
        "doctl", "databases", "pool", "create", cluster_id, pool_name,
        "--db", "defaultdb",
        "--mode", pool_mode,
        "--size", str(pool_size),
        "--user", username
    ]
    
    try:
        result = subprocess.run(cmd, capture_output=True, text=True, check=True)
        print(f"  ✅ Created connection pool: {pool_name}")
        print(f"     Mode: {pool_mode}, Size: {pool_size}")
        return True
    except subprocess.CalledProcessError as e:
        print(f"  ⚠️  Failed to create pool: {e.stderr}")
        return False


def get_connection_string(base_url: str, username: str, password: str) -> str:
    """Build connection string for the new user."""
    parsed = urlparse(base_url)
    query_params = parse_qs(parsed.query)
    sslmode = query_params.get('sslmode', ['require'])[0]
    
    return (
        f"postgresql://{username}:{password}@"
        f"{parsed.hostname}:{parsed.port}"
        f"{parsed.path}?sslmode={sslmode}"
    )


def main():
    parser = argparse.ArgumentParser(
        description="Add new client/tenant to multi-tenant Postgres setup"
    )
    
    parser.add_argument("cluster_id", help="DO database cluster ID")
    parser.add_argument("admin_connection", help="Admin connection string")
    parser.add_argument("client_name", help="Client/tenant name (used for schema and user prefix)")
    
    parser.add_argument("--password", help="Password for user (generated if not provided)")
    parser.add_argument("--create-pool", action="store_true", help="Create connection pool")
    parser.add_argument("--pool-size", type=int, default=25, help="Pool size (default: 25)")
    parser.add_argument("--pool-mode", choices=["transaction", "session", "statement"], 
                        default="transaction", help="Pool mode")
    parser.add_argument("--generate", action="store_true", help="Generate SQL only, don't execute")
    parser.add_argument("--output-dir", help="Output directory for SQL files")
    
    args = parser.parse_args()
    
    # Derive names
    client_name = args.client_name.lower().replace("-", "_").replace(" ", "_")
    username = f"{client_name}_user"
    password = args.password or generate_password()
    
    print(f"Adding client: {client_name}")
    print(f"  Schema: {client_name}")
    print(f"  User: {username}")
    print()
    
    if args.generate:
        generate_sql(client_name, username, password, args.output_dir)
    else:
        success = execute_setup(args.admin_connection, client_name, username, password)
        
        if success and args.create_pool:
            create_connection_pool(
                args.cluster_id, client_name, username,
                args.pool_size, args.pool_mode
            )
        
        if success:
            conn_string = get_connection_string(args.admin_connection, username, password)
            print()
            print("=" * 60)
            print("CLIENT CREDENTIALS")
            print("=" * 60)
            print(f"User: {username}")
            print(f"Password: {password}")
            print(f"Schema: {client_name}")
            print()
            print("Connection string:")
            print(f"  {conn_string}")


if __name__ == "__main__":
    main()
