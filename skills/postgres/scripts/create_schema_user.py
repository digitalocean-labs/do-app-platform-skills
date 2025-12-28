#!/usr/bin/env python3
"""
Create a new schema with dedicated user and proper permissions.

Supports two modes:
  1. GENERATE (default): Output SQL to stdout/file for manual review and execution
  2. EXECUTE: Run SQL directly against database (dev/test only)

Usage:
    # Generate SQL to stdout (default - safe)
    python create_schema_user.py <schema_name> <username> <password> --generate

    # Generate SQL to files
    python create_schema_user.py <schema_name> <username> <password> --generate --output-dir ./sql

    # Execute directly (dev/test only - requires connection string)
    python create_schema_user.py <schema_name> <username> <password> --execute --connection-string "postgresql://..."

Examples:
    python create_schema_user.py myapp app_user "$(openssl rand -base64 32)" --generate
    python create_schema_user.py myapp app_user secure_pass --execute --connection-string "$ADMIN_URL"
"""

import argparse
import sys
import os
from urllib.parse import urlparse, parse_qs
from datetime import datetime

# SQL Templates
SETUP_SQL_TEMPLATE = """-- ============================================
-- Database Setup for: {schema_name}
-- Generated: {timestamp}
-- Mode: {mode}
-- ============================================

\\c defaultdb

-- Create application schema
CREATE SCHEMA IF NOT EXISTS "{schema_name}";
"""

USERS_SQL_TEMPLATE = """-- ============================================
-- User Setup for: {schema_name}
-- Generated: {timestamp}
-- ============================================
-- SECURITY: Review password before executing
-- Generate secure password with: openssl rand -base64 32

CREATE USER {username} WITH PASSWORD '{password}';
"""

PERMISSIONS_SQL_TEMPLATE = """-- ============================================
-- Permissions for: {schema_name} -> {username}
-- Generated: {timestamp}
-- ============================================

-- Grant schema usage
GRANT USAGE ON SCHEMA "{schema_name}" TO {username};

-- Grant table permissions (CRUD)
GRANT SELECT, INSERT, UPDATE, DELETE ON ALL TABLES IN SCHEMA "{schema_name}" TO {username};

-- Grant sequence permissions (for serial/auto-increment)
GRANT USAGE, SELECT ON ALL SEQUENCES IN SCHEMA "{schema_name}" TO {username};

-- Grant function permissions
GRANT EXECUTE ON ALL FUNCTIONS IN SCHEMA "{schema_name}" TO {username};

-- CRITICAL: Set default privileges for future objects
ALTER DEFAULT PRIVILEGES IN SCHEMA "{schema_name}" 
  GRANT SELECT, INSERT, UPDATE, DELETE ON TABLES TO {username};
ALTER DEFAULT PRIVILEGES IN SCHEMA "{schema_name}" 
  GRANT USAGE, SELECT ON SEQUENCES TO {username};
ALTER DEFAULT PRIVILEGES IN SCHEMA "{schema_name}" 
  GRANT EXECUTE ON FUNCTIONS TO {username};

-- Set default search_path for user
ALTER USER {username} SET search_path TO "{schema_name}";

-- SECURITY: Revoke public schema access (isolation)
REVOKE ALL ON SCHEMA public FROM {username};
"""

CONNECTIONS_ENV_TEMPLATE = """# ============================================
# Connection Strings for: {schema_name}
# Generated: {timestamp}
# ============================================
# Replace HOST and PORT with values from: doctl databases connection <cluster-id>

# Primary connection string
DATABASE_URL=postgresql://{username}:{password}@HOST:25060/defaultdb?sslmode=require

# Individual components (for ORMs)
DB_HOST=HOST
DB_PORT=25060
DB_NAME=defaultdb
DB_USER={username}
DB_PASSWORD={password}
DB_SCHEMA={schema_name}
DB_SSLMODE=require

# With schema in search_path
DATABASE_URL_WITH_SCHEMA=postgresql://{username}:{password}@HOST:25060/defaultdb?sslmode=require&options=-csearch_path%3D{schema_name}
"""


def generate_sql(schema_name: str, username: str, password: str, output_dir: str = None):
    """Generate SQL files for schema/user setup."""
    timestamp = datetime.now().isoformat()
    
    context = {
        "schema_name": schema_name,
        "username": username,
        "password": password,
        "timestamp": timestamp,
        "mode": "generate"
    }
    
    setup_sql = SETUP_SQL_TEMPLATE.format(**context)
    users_sql = USERS_SQL_TEMPLATE.format(**context)
    permissions_sql = PERMISSIONS_SQL_TEMPLATE.format(**context)
    connections_env = CONNECTIONS_ENV_TEMPLATE.format(**context)
    
    if output_dir:
        os.makedirs(output_dir, exist_ok=True)
        
        with open(os.path.join(output_dir, "db-setup.sql"), "w") as f:
            f.write(setup_sql)
        with open(os.path.join(output_dir, "db-users.sql"), "w") as f:
            f.write(users_sql)
        with open(os.path.join(output_dir, "db-permissions.sql"), "w") as f:
            f.write(permissions_sql)
        with open(os.path.join(output_dir, "db-connections.env"), "w") as f:
            f.write(connections_env)
        
        print(f"✅ Generated SQL files in: {output_dir}/")
        print(f"   - db-setup.sql")
        print(f"   - db-users.sql")
        print(f"   - db-permissions.sql")
        print(f"   - db-connections.env")
        print()
        print("Next steps:")
        print("  1. Review the generated SQL files")
        print("  2. Replace password placeholder if needed")
        print("  3. Execute with: psql \"$ADMIN_URL\" -f db-setup.sql")
        print("                   psql \"$ADMIN_URL\" -f db-users.sql")
        print("                   psql \"$ADMIN_URL\" -f db-permissions.sql")
    else:
        # Output to stdout
        print("-- ===========================================")
        print("-- GENERATED SQL - Review before executing")
        print("-- ===========================================")
        print()
        print("-- FILE: db-setup.sql")
        print(setup_sql)
        print()
        print("-- FILE: db-users.sql")
        print(users_sql)
        print()
        print("-- FILE: db-permissions.sql")
        print(permissions_sql)
        print()
        print("-- FILE: db-connections.env")
        print(connections_env)


def execute_sql(connection_string: str, schema_name: str, username: str, password: str):
    """Execute SQL directly against database (dev/test only)."""
    try:
        import psycopg2
    except ImportError:
        print("❌ psycopg2 not installed. Install with: uv pip install psycopg2-binary")
        sys.exit(1)
    
    print("⚠️  EXECUTING SQL DIRECTLY - Use only for dev/test environments")
    print()
    
    conn = None
    try:
        conn = psycopg2.connect(connection_string)
        conn.autocommit = True
        cur = conn.cursor()
        
        print(f"Creating schema: {schema_name}")
        cur.execute(f'CREATE SCHEMA IF NOT EXISTS "{schema_name}"')
        
        print(f"Creating user: {username}")
        cur.execute(f"CREATE USER {username} WITH PASSWORD %s", (password,))
        
        print(f"Granting permissions to {username} on schema {schema_name}")
        
        cur.execute(f'GRANT USAGE ON SCHEMA "{schema_name}" TO {username}')
        cur.execute(f'GRANT ALL PRIVILEGES ON ALL TABLES IN SCHEMA "{schema_name}" TO {username}')
        cur.execute(f'GRANT ALL PRIVILEGES ON ALL SEQUENCES IN SCHEMA "{schema_name}" TO {username}')
        cur.execute(f'GRANT ALL PRIVILEGES ON ALL FUNCTIONS IN SCHEMA "{schema_name}" TO {username}')
        
        cur.execute(f'ALTER DEFAULT PRIVILEGES IN SCHEMA "{schema_name}" GRANT ALL ON TABLES TO {username}')
        cur.execute(f'ALTER DEFAULT PRIVILEGES IN SCHEMA "{schema_name}" GRANT ALL ON SEQUENCES TO {username}')
        cur.execute(f'ALTER DEFAULT PRIVILEGES IN SCHEMA "{schema_name}" GRANT ALL ON FUNCTIONS TO {username}')
        
        cur.execute(f'ALTER USER {username} SET search_path TO "{schema_name}"')
        cur.execute(f'REVOKE ALL ON SCHEMA public FROM {username}')
        
        cur.close()
        
        print()
        print(f"✅ Created schema '{schema_name}' with user '{username}'")
        print(f"✅ User isolated to schema (public revoked)")
        
        # Generate connection string for new user
        new_conn = build_connection_string(connection_string, username, password)
        print()
        print(f"📋 Connection string for {username}:")
        print(f"   {new_conn}")
        
    except psycopg2.errors.DuplicateSchema:
        print(f"⚠️  Schema '{schema_name}' already exists")
    except psycopg2.errors.DuplicateObject:
        print(f"⚠️  User '{username}' already exists")
    except psycopg2.Error as e:
        print(f"❌ Database error: {e}")
        sys.exit(1)
    finally:
        if conn:
            conn.close()


def build_connection_string(base_connection_string: str, username: str, password: str) -> str:
    """Build connection string for the new user."""
    parsed = urlparse(base_connection_string)
    query_params = parse_qs(parsed.query)
    sslmode = query_params.get('sslmode', ['require'])[0]
    
    return (
        f"postgresql://{username}:{password}@"
        f"{parsed.hostname}:{parsed.port}"
        f"{parsed.path}?sslmode={sslmode}"
    )


def main():
    parser = argparse.ArgumentParser(
        description="Create PostgreSQL schema with dedicated user",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  # Generate SQL files for review (recommended)
  python create_schema_user.py myapp myapp_user secure_pass --generate --output-dir ./sql

  # Execute directly (dev/test only)
  python create_schema_user.py myapp myapp_user secure_pass --execute --connection-string "$ADMIN_URL"
        """
    )
    
    parser.add_argument("schema_name", help="Name of schema to create")
    parser.add_argument("username", help="Name of user to create")
    parser.add_argument("password", help="Password for user (or use: $(openssl rand -base64 32))")
    
    mode_group = parser.add_mutually_exclusive_group(required=True)
    mode_group.add_argument("--generate", action="store_true", help="Generate SQL files (safe, default)")
    mode_group.add_argument("--execute", action="store_true", help="Execute SQL directly (dev/test only)")
    
    parser.add_argument("--output-dir", "-o", help="Directory for generated SQL files (generate mode)")
    parser.add_argument("--connection-string", "-c", help="Admin connection string (execute mode)")
    
    args = parser.parse_args()
    
    if args.execute and not args.connection_string:
        parser.error("--execute requires --connection-string")
    
    if args.generate:
        generate_sql(args.schema_name, args.username, args.password, args.output_dir)
    else:
        execute_sql(args.connection_string, args.schema_name, args.username, args.password)


if __name__ == "__main__":
    main()
