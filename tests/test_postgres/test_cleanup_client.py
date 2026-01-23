"""Tests for cleanup_client.py - Multi-tenant client removal."""

import os
import sys
import pytest
from unittest.mock import patch, MagicMock

# Add scripts to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '../../skills/postgres/scripts'))

from cleanup_client import generate_sql


class TestGenerateCleanupSQL:
    """Tests for cleanup SQL generation."""
    
    def test_generates_terminate_connections(self):
        """Should generate SQL to terminate active connections."""
        sql = generate_sql("test_client")
        assert "pg_terminate_backend" in sql
        assert "test_client_user" in sql
    
    def test_generates_drop_owned(self):
        """Should generate DROP OWNED statement."""
        sql = generate_sql("test_client")
        assert "DROP OWNED BY" in sql
    
    def test_generates_drop_user(self):
        """Should generate DROP USER statement."""
        sql = generate_sql("test_client")
        assert "DROP USER" in sql
    
    def test_generates_drop_schema(self):
        """Should generate DROP SCHEMA CASCADE."""
        sql = generate_sql("my_tenant")
        assert "DROP SCHEMA" in sql
        assert "CASCADE" in sql
        assert "my_tenant" in sql
    
    def test_includes_verification_queries(self):
        """Should include queries to verify cleanup."""
        sql = generate_sql("test_client")
        assert "Schema exists" in sql or "pg_namespace" in sql
        assert "User exists" in sql or "pg_roles" in sql
    
    def test_keep_user_option(self):
        """With keep_user=True, should not drop user."""
        sql = generate_sql("test_client", keep_user=True)
        assert "DROP USER" not in sql
        # But should still drop schema
        assert "DROP SCHEMA" in sql
    
    def test_includes_warning_comment(self):
        """SQL should include warning about data deletion."""
        sql = generate_sql("important_data")
        assert "WARNING" in sql or "DELETE" in sql
    
    def test_client_name_in_comments(self):
        """SQL should identify the client in comments."""
        sql = generate_sql("acme_corp")
        assert "acme_corp" in sql


class TestCleanupSQLSafety:
    """Tests for cleanup SQL safety measures."""
    
    def test_uses_if_exists(self):
        """Should use IF EXISTS to avoid errors on missing objects."""
        sql = generate_sql("nonexistent")
        assert "IF EXISTS" in sql
    
    def test_terminates_connections_first(self):
        """Should terminate connections before dropping objects."""
        sql = generate_sql("test")
        terminate_pos = sql.find("pg_terminate_backend")
        drop_pos = sql.find("DROP")
        assert terminate_pos < drop_pos, "Connections should be terminated before DROP"
    
    def test_drops_owned_before_user(self):
        """Should drop owned objects before dropping user."""
        sql = generate_sql("test")
        drop_owned_pos = sql.find("DROP OWNED")
        drop_user_pos = sql.find("DROP USER")
        assert drop_owned_pos < drop_user_pos, "OWNED should be dropped before USER"


class TestClientNameDerivation:
    """Tests for deriving username from client name."""
    
    def test_username_suffix(self):
        """Username should be client_name + '_user'."""
        sql = generate_sql("myapp")
        assert "myapp_user" in sql
    
    def test_schema_matches_client(self):
        """Schema name should match client name."""
        sql = generate_sql("tenant_abc")
        # Check schema reference (in quotes for case preservation)
        assert '"tenant_abc"' in sql or "tenant_abc" in sql
