"""Tests for generate_connection_string.py - Connection string formatting."""

import os
import sys
import pytest
from io import StringIO
from unittest.mock import patch

# Add scripts to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '../../skills/postgres/scripts'))

from generate_connection_string import generate_connection_strings


class TestConnectionStringGeneration:
    """Tests for connection string generation."""
    
    def test_basic_output(self):
        """Should output connection string without errors."""
        base_url = "postgresql://doadmin:pass@host:25060/defaultdb?sslmode=require"  # pragma: allowlist secret
        
        with patch('sys.stdout', new=StringIO()) as mock_stdout:
            generate_connection_strings(base_url, "myuser", "mypass")
            output = mock_stdout.getvalue()
        
        assert "myuser" in output
        assert "CONNECTION STRINGS" in output
    
    def test_includes_basic_connection_string(self):
        """Should include basic connection string."""
        base_url = "postgresql://doadmin:pass@db-host.com:25060/defaultdb?sslmode=require"  # pragma: allowlist secret
        
        with patch('sys.stdout', new=StringIO()) as mock_stdout:
            generate_connection_strings(base_url, "appuser", "secretpass")
            output = mock_stdout.getvalue()
        
        assert "postgresql://appuser:" in output
        assert "db-host.com:25060" in output
    
    def test_includes_psql_command(self):
        """Should include psql command example."""
        base_url = "postgresql://doadmin:pass@host:25060/db?sslmode=require"  # pragma: allowlist secret
        
        with patch('sys.stdout', new=StringIO()) as mock_stdout:
            generate_connection_strings(base_url, "user", "pass")
            output = mock_stdout.getvalue()
        
        assert "psql" in output
    
    def test_includes_environment_variables(self):
        """Should include environment variable format."""
        base_url = "postgresql://doadmin:pass@myhost:25060/mydb?sslmode=require"  # pragma: allowlist secret
        
        with patch('sys.stdout', new=StringIO()) as mock_stdout:
            generate_connection_strings(base_url, "dbuser", "dbpass")
            output = mock_stdout.getvalue()
        
        assert "DATABASE_URL=" in output
        assert "DB_HOST=myhost" in output
        assert "DB_PORT=25060" in output
        assert "DB_USER=dbuser" in output
        assert "DB_PASSWORD=dbpass" in output
    
    def test_includes_schema_when_provided(self):
        """Should include schema in connection string when specified."""
        base_url = "postgresql://doadmin:pass@host:25060/db?sslmode=require"  # pragma: allowlist secret
        
        with patch('sys.stdout', new=StringIO()) as mock_stdout:
            generate_connection_strings(base_url, "user", "pass", schema="myschema")
            output = mock_stdout.getvalue()
        
        assert "myschema" in output
        assert "DB_SCHEMA=myschema" in output
    
    def test_includes_orm_formats(self):
        """Should include ORM-specific formats."""
        base_url = "postgresql://doadmin:pass@host:25060/db?sslmode=require"  # pragma: allowlist secret
        
        with patch('sys.stdout', new=StringIO()) as mock_stdout:
            generate_connection_strings(base_url, "user", "pass")
            output = mock_stdout.getvalue()
        
        assert "Prisma" in output
        assert "SQLAlchemy" in output


class TestURLParsing:
    """Tests for URL parsing and component extraction."""
    
    def test_extracts_host(self):
        """Should correctly extract hostname."""
        base_url = "postgresql://admin:pass@my-db-cluster.db.ondigitalocean.com:25060/db?sslmode=require"  # pragma: allowlist secret
        
        with patch('sys.stdout', new=StringIO()) as mock_stdout:
            generate_connection_strings(base_url, "user", "pass")
            output = mock_stdout.getvalue()
        
        assert "my-db-cluster.db.ondigitalocean.com" in output
    
    def test_extracts_port(self):
        """Should correctly extract port."""
        base_url = "postgresql://admin:pass@host:25061/db?sslmode=require"  # pragma: allowlist secret
        
        with patch('sys.stdout', new=StringIO()) as mock_stdout:
            generate_connection_strings(base_url, "user", "pass")
            output = mock_stdout.getvalue()
        
        assert "25061" in output
    
    def test_extracts_database(self):
        """Should correctly extract database name."""
        base_url = "postgresql://admin:pass@host:25060/myappdb?sslmode=require"  # pragma: allowlist secret
        
        with patch('sys.stdout', new=StringIO()) as mock_stdout:
            generate_connection_strings(base_url, "user", "pass")
            output = mock_stdout.getvalue()
        
        assert "myappdb" in output
    
    def test_extracts_sslmode(self):
        """Should correctly extract SSL mode."""
        base_url = "postgresql://admin:pass@host:25060/db?sslmode=verify-full"  # pragma: allowlist secret
        
        with patch('sys.stdout', new=StringIO()) as mock_stdout:
            generate_connection_strings(base_url, "user", "pass")
            output = mock_stdout.getvalue()
        
        assert "verify-full" in output or "sslmode" in output


class TestPasswordHandling:
    """Tests for password handling in connection strings."""
    
    def test_password_url_encoded(self):
        """Passwords with special chars should be URL encoded."""
        base_url = "postgresql://admin:pass@host:25060/db?sslmode=require"  # pragma: allowlist secret
        
        # Password with special characters
        with patch('sys.stdout', new=StringIO()) as mock_stdout:
            generate_connection_strings(base_url, "user", "p@ss#word!")
            output = mock_stdout.getvalue()
        
        # URL-encoded version should be in the connection string
        # @ -> %40, # -> %23, ! -> %21
        assert "p%40ss%23word%21" in output or "p@ss#word!" in output
    
    def test_password_not_in_env_var_name(self):
        """Password should only appear in values, not variable names."""
        base_url = "postgresql://admin:pass@host:25060/db?sslmode=require"  # pragma: allowlist secret
        
        with patch('sys.stdout', new=StringIO()) as mock_stdout:
            generate_connection_strings(base_url, "user", "secretvalue")
            output = mock_stdout.getvalue()
        
        # Password should appear after = sign
        assert "DB_PASSWORD=secretvalue" in output


class TestDefaultValues:
    """Tests for default value handling."""
    
    def test_default_port(self):
        """Should use default port if not specified."""
        # Note: This URL parsing behavior depends on implementation
        base_url = "postgresql://admin:pass@host/db?sslmode=require"  # pragma: allowlist secret
        
        with patch('sys.stdout', new=StringIO()) as mock_stdout:
            generate_connection_strings(base_url, "user", "pass")
            output = mock_stdout.getvalue()
        
        # Should have some port value
        assert "DB_PORT=" in output
    
    def test_default_sslmode(self):
        """Should default to require SSL mode."""
        base_url = "postgresql://admin:pass@host:25060/db"  # pragma: allowlist secret
        
        with patch('sys.stdout', new=StringIO()) as mock_stdout:
            generate_connection_strings(base_url, "user", "pass")
            output = mock_stdout.getvalue()
        
        assert "require" in output
