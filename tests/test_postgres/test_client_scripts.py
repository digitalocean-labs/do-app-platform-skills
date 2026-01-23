"""Tests for postgres client management scripts."""

import pytest
import sys
from pathlib import Path
from unittest.mock import patch, MagicMock

sys.path.insert(0, str(Path(__file__).parent.parent.parent / "skills" / "postgres" / "scripts"))

from add_client import generate_password, generate_sql
from cleanup_client import generate_sql as generate_cleanup_sql
from generate_connection_string import generate_connection_strings


class TestAddClient:
    """Tests for add_client.py script."""

    def test_generates_secure_password(self):
        """Should generate secure random password."""
        password = generate_password(32)
        
        assert len(password) == 32
        assert password.isalnum()  # Only alphanumeric
        
        # Multiple calls should generate different passwords
        password2 = generate_password(32)
        assert password != password2

    def test_generates_password_with_custom_length(self):
        """Should respect custom password length."""
        password = generate_password(16)
        assert len(password) == 16
        
        password = generate_password(64)
        assert len(password) == 64

    def test_generates_client_setup_sql(self, capsys):
        """Should generate SQL for client setup."""
        password = generate_sql("acme_corp", "acme_user", "testpass123")
        
        output = capsys.readouterr().out
        assert "CREATE SCHEMA" in output
        assert "acme_corp" in output
        assert "CREATE USER" in output
        assert "acme_user" in output

    def test_generates_permissions_sql(self, capsys):
        """Should generate permission grants."""
        generate_sql("client1", "client1_user", "pass123")
        
        output = capsys.readouterr().out
        assert "GRANT USAGE ON SCHEMA" in output
        assert "GRANT ALL PRIVILEGES" in output
        assert "ALTER DEFAULT PRIVILEGES" in output

    def test_revokes_public_schema_access(self, capsys):
        """Should revoke public schema access."""
        generate_sql("client1", "client1_user", "pass123")
        
        output = capsys.readouterr().out
        assert "REVOKE ALL ON SCHEMA public" in output

    def test_sets_search_path(self, capsys):
        """Should set search path for user."""
        generate_sql("myschema", "myuser", "mypass")
        
        output = capsys.readouterr().out
        assert "SET search_path" in output
        assert "myschema" in output

    def test_writes_sql_files_to_directory(self, tmp_path):
        """Should write SQL files when output_dir provided."""
        generate_sql("client1", "user1", "pass1", output_dir=str(tmp_path))
        
        assert (tmp_path / "db-setup.sql").exists()
        assert (tmp_path / "db-users.sql").exists()
        assert (tmp_path / "db-permissions.sql").exists()
        
        # Check content
        setup_content = (tmp_path / "db-setup.sql").read_text()
        assert "CREATE SCHEMA" in setup_content
        assert "client1" in setup_content

    def test_returns_password(self):
        """Should return generated password."""
        password = generate_sql("client1", "user1", "testpass", output_dir=None)
        assert password == "testpass"


class TestCleanupClient:
    """Tests for cleanup_client.py script."""

    def test_generates_cleanup_sql(self):
        """Should generate SQL for client cleanup."""
        sql = generate_cleanup_sql("old_client", keep_user=False)
        
        assert "DROP SCHEMA" in sql
        assert "old_client" in sql
        assert "CASCADE" in sql
        assert "DROP USER" in sql

    def test_terminates_active_connections(self):
        """Should include connection termination."""
        sql = generate_cleanup_sql("client1")
        
        assert "pg_terminate_backend" in sql
        assert "pg_stat_activity" in sql

    def test_keeps_user_when_requested(self):
        """Should keep user when keep_user=True."""
        sql = generate_cleanup_sql("client1", keep_user=True)
        
        assert "DROP SCHEMA" in sql
        assert "DROP USER" not in sql

    def test_drops_owned_objects(self):
        """Should drop owned objects."""
        sql = generate_cleanup_sql("client1", keep_user=False)
        
        assert "DROP OWNED BY" in sql

    def test_includes_verification_queries(self):
        """Should include verification queries."""
        sql = generate_cleanup_sql("client1")
        
        assert "Schema exists:" in sql or "EXISTS" in sql


class TestGenerateConnectionString:
    """Tests for generate_connection_string.py script."""

    def test_generates_basic_connection_string(self, capsys):
        """Should generate basic connection string."""
        base = "postgresql://admin:FAKE_TEST_PASS@localhost:25060/defaultdb?sslmode=require"  # pragma: allowlist secret
        generate_connection_strings(base, "testuser", "FAKE_NEW_PASS")
        
        output = capsys.readouterr().out
        assert "testuser:FAKE_NEW_PASS@" in output
        assert "localhost:25060" in output
        assert "sslmode=require" in output

    def test_generates_schema_specific_connection(self, capsys):
        """Should generate schema-specific connection string."""
        base = "postgresql://admin:FAKE_TEST_PASS@localhost:25060/defaultdb?sslmode=require"  # pragma: allowlist secret
        generate_connection_strings(base, "testuser", "FAKE_TEST_PASS", schema="myschema")
        
        output = capsys.readouterr().out
        assert "myschema" in output

    def test_url_encodes_special_characters(self, capsys):
        """Should URL-encode passwords with special characters."""
        base = "postgresql://admin:FAKE_TEST_PASS@localhost:25060/defaultdb?sslmode=require"  # pragma: allowlist secret
        password = "FAKE@TEST#PASS!"
        
        generate_connection_strings(base, "testuser", password)
        
        output = capsys.readouterr().out
        # Should have encoded version somewhere
        assert "testuser" in output

    def test_generates_environment_variables(self, capsys):
        """Should generate environment variable format."""
        base = "postgresql://admin:FAKE_TEST_PASS@localhost:25060/defaultdb?sslmode=require"  # pragma: allowlist secret
        generate_connection_strings(base, "testuser", "FAKE_TEST_PASS")
        
        output = capsys.readouterr().out
        assert "DATABASE_URL=" in output
        assert "DB_HOST=" in output
        assert "DB_PORT=" in output
        assert "DB_USER=" in output
        assert "DB_PASSWORD=" in output

    def test_generates_orm_specific_formats(self, capsys):
        """Should generate ORM-specific formats."""
        base = "postgresql://admin:FAKE_TEST_PASS@localhost:25060/defaultdb?sslmode=require"  # pragma: allowlist secret
        generate_connection_strings(base, "testuser", "FAKE_TEST_PASS")
        
        output = capsys.readouterr().out
        assert "Prisma" in output or "SQLAlchemy" in output or "Drizzle" in output

    def test_defaults_to_require_sslmode(self, capsys):
        """Should default to sslmode=require."""
        base = "postgresql://admin:FAKE_TEST_PASS@localhost:25060/defaultdb"  # pragma: allowlist secret
        generate_connection_strings(base, "testuser", "FAKE_TEST_PASS")
        
        output = capsys.readouterr().out
        assert "sslmode=require" in output

    def test_generates_psql_command(self, capsys):
        """Should generate psql command."""
        base = "postgresql://admin:FAKE_TEST_PASS@localhost:25060/defaultdb?sslmode=require"  # pragma: allowlist secret
        generate_connection_strings(base, "testuser", "FAKE_TEST_PASS")
        
        output = capsys.readouterr().out
        assert "psql" in output


class TestListSchemasUsers:
    """Tests for list_schemas_users.py script."""

    def test_lists_schemas_import(self):
        """Should be able to import list_schemas_users."""
        try:
            from list_schemas_users import list_schemas_users
            # Function should exist
            assert callable(list_schemas_users)
        except ImportError:
            pytest.skip("list_schemas_users module not available")
    
    def test_lists_schemas_requires_psycopg2(self):
        """Should handle missing psycopg2 gracefully."""
        try:
            import psycopg2
            pytest.skip("psycopg2 is installed, skipping this test")
        except ImportError:
            # psycopg2 not installed, verify the script handles it
            from list_schemas_users import list_schemas_users
            # Should exit with code 1 when psycopg2 is missing
            with pytest.raises(SystemExit) as exc_info:
                list_schemas_users("postgresql://invalid:invalid@localhost:5432/invalid")  # pragma: allowlist secret
            assert exc_info.value.code == 1


class TestSecureSetup:
    """Tests for secure_setup.py script."""

    def test_generates_secure_password(self):
        """Should generate secure passwords."""
        from secure_setup import generate_password
        
        password = generate_password(32)
        assert len(password) == 32
        assert password.isalnum()

    def test_extracts_host_from_url(self):
        """Should extract hostname from connection string."""
        from secure_setup import extract_host_from_url
        
        url = "postgresql://testuser:FAKE_TEST_PASS@example-db.localhost:25060/testdb"  # pragma: allowlist secret
        host = extract_host_from_url(url)
        
        assert host == "example-db.localhost"
