#!/usr/bin/env python3
"""
Generate formatted connection strings for database users.

Takes a base admin connection string and generates user-specific connection
strings in multiple formats (URI, components, environment variables).

Usage:
    python generate_connection_string.py <base_connection> <username> <password> [--schema <schema>]

Example:
    python generate_connection_string.py \
      "postgresql://doadmin:pass@host:25060/defaultdb?sslmode=require" \
      myapp_user \
      "secure_password" \
      --schema myapp
"""

import argparse
import sys
from urllib.parse import urlparse, parse_qs, quote_plus


def generate_connection_strings(base_url: str, username: str, password: str, schema: str = None):
    """Generate connection strings in multiple formats."""
    parsed = urlparse(base_url)
    
    host = parsed.hostname
    port = parsed.port or 25060
    database = parsed.path.lstrip('/') or 'defaultdb'
    
    query_params = parse_qs(parsed.query)
    sslmode = query_params.get('sslmode', ['require'])[0]
    
    # URL-encode password if it contains special characters
    encoded_password = quote_plus(password)
    
    # Build connection strings
    basic_url = f"postgresql://{username}:{encoded_password}@{host}:{port}/{database}?sslmode={sslmode}"
    
    if schema:
        schema_url = f"{basic_url}&options=-csearch_path%3D{schema}"
    else:
        schema_url = basic_url
    
    print("=" * 70)
    print("CONNECTION STRINGS")
    print("=" * 70)
    print()
    
    print("📋 Basic Connection String:")
    print(f"   {basic_url}")
    print()
    
    if schema:
        print(f"📋 Connection String with Schema ({schema}):")
        print(f"   {schema_url}")
        print()
    
    print("📋 psql Command:")
    print(f'   psql "{basic_url}"')
    print()
    
    print("=" * 70)
    print("ENVIRONMENT VARIABLES")
    print("=" * 70)
    print()
    print("# Add to .env file or GitHub Secrets:")
    print(f"DATABASE_URL={basic_url}")
    print()
    print("# Individual components:")
    print(f"DB_HOST={host}")
    print(f"DB_PORT={port}")
    print(f"DB_NAME={database}")
    print(f"DB_USER={username}")
    print(f"DB_PASSWORD={password}")
    if schema:
        print(f"DB_SCHEMA={schema}")
    print(f"DB_SSLMODE={sslmode}")
    print()
    
    print("=" * 70)
    print("ORM-SPECIFIC FORMATS")
    print("=" * 70)
    print()
    
    print("# Prisma (.env):")
    if schema:
        print(f'DATABASE_URL="{basic_url}&schema={schema}"')
    else:
        print(f'DATABASE_URL="{basic_url}"')
    print()
    
    print("# SQLAlchemy (Python):")
    print(f'DATABASE_URL = "{basic_url}"')
    if schema:
        print(f"# Add to engine: connect_args={{'options': '-csearch_path={schema}'}}")
    print()
    
    print("# Drizzle / TypeORM (TypeScript):")
    print(f"const connectionString = \"{basic_url}\";")
    if schema:
        print(f'const schema = "{schema}";')
    print()


def main():
    parser = argparse.ArgumentParser(
        description="Generate database connection strings",
        formatter_class=argparse.RawDescriptionHelpFormatter
    )
    
    parser.add_argument("base_connection", help="Base admin connection string")
    parser.add_argument("username", help="Username for connection")
    parser.add_argument("password", help="Password for connection")
    parser.add_argument("--schema", "-s", help="Default schema (optional)")
    
    args = parser.parse_args()
    
    generate_connection_strings(
        args.base_connection,
        args.username,
        args.password,
        args.schema
    )


if __name__ == "__main__":
    main()
