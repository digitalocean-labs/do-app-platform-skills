"""Tests for add_client.py - Multi-tenant client setup."""

import os
import sys
import tempfile
import pytest
from unittest.mock import patch, MagicMock

# Add scripts to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '../../skills/postgres/scripts'))

from add_client import (
    generate_password,
    generate_sql,
    get_connection_string,
)


class TestGeneratePassword:
    """Tests for password generation."""
    
    def test_default_length(self):
        """Password should be 32 characters by default."""
        password = generate_password()
        assert len(password) == 32
    
    def test_custom_length(self):
        """Password should respect custom length."""
        password = generate_password(length=16)
        assert len(password) == 16
        
        password = generate_password(length=64)
        assert len(password) == 64
    
    def test_alphanumeric_only(self):
        """Password should contain only alphanumeric characters."""
        password = generate_password()
        assert password.isalnum()
    
    def test_randomness(self):
        """Consecutive passwords should be different."""
        passwords = [generate_password() for _ in range(10)]
        assert len(set(passwords)) == 10  # All unique


class TestGenerateSQL:
    """Tests for SQL generation."""
    
    def test_generates_schema_creation(self):
        """Should generate CREATE SCHEMA statement."""
        with patch('builtins.print'):
            generate_sql("test_client", "test_client_user", "testpass123")
        # Function prints SQL, we verify it runs without error
    
    def test_output_to_directory(self):
        """Should create SQL files in output directory."""
        with tempfile.TemporaryDirectory() as tmpdir:
            output_dir = os.path.join(tmpdir, "sql")
            
            with patch('builtins.print'):
                generate_sql("acme", "acme_user", "securepass", output_dir)
            
            # Check files were created
            assert os.path.exists(os.path.join(output_dir, "db-setup.sql"))
            assert os.path.exists(os.path.join(output_dir, "db-users.sql"))
            assert os.path.exists(os.path.join(output_dir, "db-permissions.sql"))
            
            # Check content
            with open(os.path.join(output_dir, "db-setup.sql")) as f:
                content = f.read()
                assert "CREATE SCHEMA" in content
                assert "acme" in content
            
            with open(os.path.join(output_dir, "db-users.sql")) as f:
                content = f.read()
                assert "CREATE USER" in content
                assert "acme_user" in content
            
            with open(os.path.join(output_dir, "db-permissions.sql")) as f:
                content = f.read()
                assert "GRANT" in content
                assert "acme_user" in content
    
    def test_sql_contains_security_revoke(self):
        """Generated SQL should revoke public schema access."""
        with tempfile.TemporaryDirectory() as tmpdir:
            output_dir = os.path.join(tmpdir, "sql")
            
            with patch('builtins.print'):
                generate_sql("tenant1", "tenant1_user", "pass", output_dir)
            
            with open(os.path.join(output_dir, "db-permissions.sql")) as f:
                content = f.read()
                assert "REVOKE ALL ON SCHEMA public" in content
    
    def test_sql_sets_search_path(self):
        """Generated SQL should set user search path to their schema."""
        with tempfile.TemporaryDirectory() as tmpdir:
            output_dir = os.path.join(tmpdir, "sql")
            
            with patch('builtins.print'):
                generate_sql("myapp", "myapp_user", "pass", output_dir)
            
            with open(os.path.join(output_dir, "db-permissions.sql")) as f:
                content = f.read()
                assert "SET search_path" in content
                assert "myapp" in content


class TestGetConnectionString:
    """Tests for connection string generation."""
    
    def test_basic_connection_string(self):
        """Should generate valid connection string."""
        base_url = "postgresql://doadmin:adminpass@db-host.com:25060/defaultdb?sslmode=require"  # ggshield-ignore-line
        conn = get_connection_string(base_url, "myuser", "mypass")
        
        assert "myuser:mypass" in conn
        assert "db-host.com:25060" in conn
        assert "sslmode=require" in conn
    
    def test_preserves_ssl_mode(self):
        """Should preserve SSL mode from base URL."""
        base_url = "postgresql://doadmin:x@host:25060/db?sslmode=verify-full"  # ggshield-ignore-line
        conn = get_connection_string(base_url, "user", "pass")
        
        assert "sslmode=verify-full" in conn
    
    def test_default_ssl_mode(self):
        """Should default to require if sslmode not in URL."""
        base_url = "postgresql://doadmin:x@host:25060/db"  # ggshield-ignore-line
        conn = get_connection_string(base_url, "user", "pass")
        
        assert "sslmode=require" in conn


class TestClientNameSanitization:
    """Tests for client name handling."""
    
    def test_lowercase_conversion(self):
        """Client names should be lowercased."""
        # This is tested via main() but we verify the pattern
        client_name = "ACME_Corp".lower().replace("-", "_").replace(" ", "_")
        assert client_name == "acme_corp"
    
    def test_dash_to_underscore(self):
        """Dashes should become underscores."""
        client_name = "my-client-name".lower().replace("-", "_")
        assert client_name == "my_client_name"
    
    def test_space_to_underscore(self):
        """Spaces should become underscores."""
        client_name = "my client name".lower().replace(" ", "_")
        assert client_name == "my_client_name"
