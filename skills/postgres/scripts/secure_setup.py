#!/usr/bin/env python3
"""
Secure Hands-Free Database Setup

Creates database user and stores credentials directly in GitHub Secrets.
Password is NEVER printed — flows directly from generation to secrets.

Usage:
    python secure_setup.py --admin-url <url> --app-name <n> --repo <owner/repo> [options]

Required:
    --admin-url     Admin connection string (doadmin)
    --app-name      Application name (used for user/schema naming)
    --repo          GitHub repository (owner/repo format)

Optional:
    --schema        Schema name (defaults to app-name)
    --env           GitHub environment (staging, production, etc.)
    --db-name       Database name (default: defaultdb)
    --secret-name   Secret name (default: DATABASE_URL)
    --dry-run       Show what would be done without executing
    --skip-confirm  Skip confirmation prompt

Examples:
    python secure_setup.py \\
        --admin-url "$ADMIN_URL" \\
        --app-name myapp \\
        --repo myorg/myrepo \\
        --env production

    python secure_setup.py \\
        --admin-url "$ADMIN_URL" \\
        --app-name tenant1 \\
        --schema tenant1 \\
        --repo myorg/multitenant-app \\
        --secret-name DATABASE_URL_TENANT1
"""

import argparse
import secrets
import string
import subprocess
import sys
from urllib.parse import urlparse, parse_qs


def generate_password(length: int = 32) -> str:
    """Generate a secure random password."""
    # Use alphanumeric to avoid URL encoding issues
    alphabet = string.ascii_letters + string.digits
    return ''.join(secrets.choice(alphabet) for _ in range(length))


def check_prerequisites(repo: str) -> bool:
    """Check that required tools are available."""
    print("\033[94mChecking prerequisites...\033[0m")
    
    # Check psql
    try:
        subprocess.run(["psql", "--version"], capture_output=True, check=True)
    except (subprocess.CalledProcessError, FileNotFoundError):
        print("\033[91mError: psql is not installed\033[0m")
        return False
    
    # Check gh
    try:
        subprocess.run(["gh", "--version"], capture_output=True, check=True)
    except (subprocess.CalledProcessError, FileNotFoundError):
        print("\033[91mError: gh CLI is not installed\033[0m")
        print("Install with: brew install gh (macOS) or see https://cli.github.com")
        return False
    
    # Check gh auth
    result = subprocess.run(["gh", "auth", "status"], capture_output=True)
    if result.returncode != 0:
        print("\033[91mError: gh is not authenticated\033[0m")
        print("Run: gh auth login")
        return False
    
    # Check repo access
    result = subprocess.run(
        ["gh", "secret", "list", "--repo", repo],
        capture_output=True
    )
    if result.returncode != 0:
        print(f"\033[91mError: Cannot access secrets for {repo}\033[0m")
        print("Ensure you have admin/write access to the repository")
        return False
    
    print("\033[92m✓ Prerequisites OK\033[0m\n")
    return True


def extract_host_from_url(url: str) -> str:
    """Extract hostname from connection string."""
    parsed = urlparse(url)
    return parsed.hostname


def execute_sql(admin_url: str, sql: str) -> bool:
    """Execute SQL via psql."""
    result = subprocess.run(
        ["psql", admin_url, "-c", sql],
        capture_output=True,
        text=True
    )
    return result.returncode == 0


def execute_sql_script(admin_url: str, script: str) -> bool:
    """Execute multi-line SQL script via psql."""
    result = subprocess.run(
        ["psql", admin_url],
        input=script,
        capture_output=True,
        text=True
    )
    return result.returncode == 0


def set_github_secret(repo: str, secret_name: str, value: str, env: str = None) -> bool:
    """Store secret in GitHub."""
    cmd = ["gh", "secret", "set", secret_name, "--repo", repo, "--body", value]
    if env:
        cmd.extend(["--env", env])
    
    result = subprocess.run(cmd, capture_output=True)
    return result.returncode == 0


def main():
    try:
        import psycopg2
        from psycopg2 import sql
    except ImportError:
        print("\033[91mError: psycopg2 is not installed\033[0m")
        print("Install with: uv pip install psycopg2-binary")
        sys.exit(1)

    parser = argparse.ArgumentParser(
        description="Secure hands-free database setup with GitHub Secrets",
        formatter_class=argparse.RawDescriptionHelpFormatter
    )
    
    parser.add_argument("--admin-url", required=True, help="Admin connection string")
    parser.add_argument("--app-name", required=True, help="Application name")
    parser.add_argument("--repo", required=True, help="GitHub repository (owner/repo)")
    parser.add_argument("--schema", help="Schema name (defaults to app-name)")
    parser.add_argument("--env", help="GitHub environment")
    parser.add_argument("--db-name", default="defaultdb", help="Database name")
    parser.add_argument("--secret-name", default="DATABASE_URL", help="Secret name")
    parser.add_argument("--dry-run", action="store_true", help="Show plan without executing")
    parser.add_argument("--skip-confirm", action="store_true", help="Skip confirmation")
    
    args = parser.parse_args()
    
    # Derive values
    schema_name = args.schema or args.app_name
    username = f"{args.app_name}_user"
    db_host = extract_host_from_url(args.admin_url)
    db_port = 25060
    
    # Check prerequisites
    if not check_prerequisites(args.repo):
        sys.exit(1)
    
    # Show plan
    print("\033[94m" + "═" * 65 + "\033[0m")
    print("\033[94m                    SECURE DATABASE SETUP                       \033[0m")
    print("\033[94m" + "═" * 65 + "\033[0m")
    print()
    print(f"  Application:    \033[92m{args.app_name}\033[0m")
    print(f"  Schema:         \033[92m{schema_name}\033[0m")
    print(f"  User:           \033[92m{username}\033[0m")
    print(f"  Database:       \033[92m{args.db_name}\033[0m")
    print(f"  Host:           \033[92m{db_host}\033[0m")
    print()
    print(f"  Repository:     \033[92m{args.repo}\033[0m")
    print(f"  Environment:    \033[92m{args.env or '<none>'}\033[0m")
    print(f"  Secret name:    \033[92m{args.secret_name}\033[0m")
    print()
    print("  \033[93m⚠️  Password will be generated and stored directly in GitHub Secrets\033[0m")
    print("  \033[93m   It will NEVER be displayed in this terminal\033[0m")
    print()
    
    if args.dry_run:
        print("\033[93mDRY RUN - No changes will be made\033[0m")
        print()
        print("Would execute:")
        print(f'  1. CREATE SCHEMA IF NOT EXISTS "{schema_name}"')
        print(f"  2. CREATE USER {username} WITH PASSWORD '<generated>'")
        print(f"  3. GRANT permissions on schema {schema_name} to {username}")
        print(f"  4. gh secret set {args.secret_name} --repo {args.repo}")
        sys.exit(0)
    
    # Confirmation
    if not args.skip_confirm:
        print("\033[94m" + "═" * 65 + "\033[0m")
        confirm = input("Proceed with setup? (y/N): ")
        if confirm.lower() != 'y':
            print("Aborted.")
            sys.exit(0)
        print()
    
    # Generate secure password (NEVER printed)
    password = generate_password()
    
    print("\033[94mCreating schema and user...\033[0m")

    conn = None
    try:
        conn = psycopg2.connect(args.admin_url)
        conn.autocommit = True
        cur = conn.cursor()

        cur.execute(
            sql.SQL("CREATE SCHEMA IF NOT EXISTS {}")
            .format(sql.Identifier(schema_name))
        )

        cur.execute(
            sql.SQL("CREATE USER {} WITH PASSWORD %s")
            .format(sql.Identifier(username)),
            (password,)
        )

        print("\033[92m✓ User created\033[0m")
        print("\033[94mGranting permissions...\033[0m")

        cur.execute(
            sql.SQL("GRANT USAGE ON SCHEMA {} TO {}")
            .format(sql.Identifier(schema_name), sql.Identifier(username))
        )
        cur.execute(
            sql.SQL("GRANT ALL PRIVILEGES ON ALL TABLES IN SCHEMA {} TO {}")
            .format(sql.Identifier(schema_name), sql.Identifier(username))
        )
        cur.execute(
            sql.SQL("GRANT ALL PRIVILEGES ON ALL SEQUENCES IN SCHEMA {} TO {}")
            .format(sql.Identifier(schema_name), sql.Identifier(username))
        )
        cur.execute(
            sql.SQL("GRANT ALL PRIVILEGES ON ALL FUNCTIONS IN SCHEMA {} TO {}")
            .format(sql.Identifier(schema_name), sql.Identifier(username))
        )
        cur.execute(
            sql.SQL("ALTER DEFAULT PRIVILEGES IN SCHEMA {} GRANT ALL ON TABLES TO {}")
            .format(sql.Identifier(schema_name), sql.Identifier(username))
        )
        cur.execute(
            sql.SQL("ALTER DEFAULT PRIVILEGES IN SCHEMA {} GRANT ALL ON SEQUENCES TO {}")
            .format(sql.Identifier(schema_name), sql.Identifier(username))
        )
        cur.execute(
            sql.SQL("ALTER DEFAULT PRIVILEGES IN SCHEMA {} GRANT ALL ON FUNCTIONS TO {}")
            .format(sql.Identifier(schema_name), sql.Identifier(username))
        )
        cur.execute(
            sql.SQL("ALTER USER {} SET search_path TO {}")
            .format(sql.Identifier(username), sql.Identifier(schema_name))
        )
        cur.execute(
            sql.SQL("REVOKE ALL ON SCHEMA public FROM {}")
            .format(sql.Identifier(username))
        )

        cur.close()
        print("\033[92m✓ Permissions granted\033[0m")
    except psycopg2.errors.DuplicateObject:
        print("\033[91mError creating user (may already exist)\033[0m")
        print("If user exists, use cleanup_client.py to remove first")
        sys.exit(1)
    except psycopg2.Error as e:
        print(f"\033[91mDatabase error: {e}\033[0m")
        sys.exit(1)
    finally:
        if conn:
            conn.close()
    
    # Build connection string
    database_url = f"postgresql://{username}:{password}@{db_host}:{db_port}/{args.db_name}?sslmode=require"
    
    # Store in GitHub Secrets
    print("\033[94mStoring credentials in GitHub Secrets...\033[0m")
    
    if not set_github_secret(args.repo, args.secret_name, database_url, args.env):
        print("\033[91mError storing secret\033[0m")
        sys.exit(1)
    
    print("\033[92m✓ Secret stored\033[0m")
    
    # Clear sensitive data
    password = None
    database_url = None
    
    print()
    print("\033[92m" + "═" * 65 + "\033[0m")
    print("\033[92m                    SETUP COMPLETE                              \033[0m")
    print("\033[92m" + "═" * 65 + "\033[0m")
    print()
    print(f"  Schema:     {schema_name}")
    print(f"  User:       {username}")
    print(f"  Secret:     {args.secret_name}")
    print(f"  Repository: {args.repo}")
    if args.env:
        print(f"  Environment: {args.env}")
    print()
    print("  \033[92m✓ Password stored securely — never displayed\033[0m")
    print()
    print("\033[94mNext steps:\033[0m")
    print("  Reference the secret in your app spec or GitHub Actions:")
    print()
    print("     # App spec (for GitHub Actions deployment)")
    print("     envs:")
    print("       - key: DATABASE_URL")
    print("         scope: RUN_TIME")
    print("         type: SECRET")
    print(f"         value: {args.secret_name}")
    print()


if __name__ == "__main__":
    main()
