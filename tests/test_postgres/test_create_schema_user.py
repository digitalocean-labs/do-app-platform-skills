"""Tests for postgres scripts."""

import pytest
import sys
from pathlib import Path
from unittest.mock import patch

sys.path.insert(0, str(Path(__file__).parent.parent.parent / "skills" / "postgres" / "scripts"))

from create_schema_user import generate_sql, build_connection_string


class TestGenerateSQL:
    """Tests for SQL generation."""

    def test_generates_schema_creation(self, capsys):
        """Should generate CREATE SCHEMA."""
        generate_sql("myschema", "myuser", "mypass")
        output = capsys.readouterr().out
        assert "CREATE SCHEMA" in output
        assert "myschema" in output

    def test_generates_user_creation(self, capsys):
        """Should generate CREATE USER."""
        generate_sql("myschema", "myuser", "mypass")
        output = capsys.readouterr().out
        assert "CREATE USER" in output

    def test_generates_permissions(self, capsys):
        """Should generate GRANT statements."""
        generate_sql("myschema", "myuser", "mypass")
        output = capsys.readouterr().out
        assert "GRANT" in output

    def test_revokes_public_access(self, capsys):
        """Should revoke public schema access."""
        generate_sql("myschema", "myuser", "mypass")
        output = capsys.readouterr().out
        assert "REVOKE" in output

    def test_writes_files_to_output_dir(self, tmp_path):
        """Should write SQL files when output_dir specified."""
        generate_sql("schema", "user", "pass", output_dir=str(tmp_path))
        assert (tmp_path / "db-setup.sql").exists()
        assert (tmp_path / "db-users.sql").exists()
        assert (tmp_path / "db-permissions.sql").exists()


class TestBuildConnectionString:
    """Tests for connection string building."""

    def test_builds_valid_connection(self):
        """Should build valid PostgreSQL URL."""
        base = "postgresql://admin:old@host:25060/db?sslmode=require"
        result = build_connection_string(base, "newuser", "newpass")
        assert "newuser:newpass@" in result
        assert "host:25060" in result
        assert "sslmode=require" in result

    def test_defaults_ssl_require(self):
        """Should default to sslmode=require."""
        base = "postgresql://admin:old@host:25060/db"
        result = build_connection_string(base, "user", "pass")
        assert "sslmode=require" in result
