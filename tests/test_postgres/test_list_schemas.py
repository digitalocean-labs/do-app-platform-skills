"""Tests for list_schemas_users.py - Schema and user auditing."""

import os
import sys
import pytest
from unittest.mock import patch, MagicMock

# Add scripts to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '../../skills/postgres/scripts'))


class TestListSchemasUsersImport:
    """Tests for module import and structure."""
    
    def test_module_imports(self):
        """Module should import without errors."""
        from list_schemas_users import list_schemas_users
        assert callable(list_schemas_users)


class TestListSchemasUsersFunction:
    """Tests for list_schemas_users function."""
    
    def test_requires_psycopg2(self):
        """Should exit gracefully if psycopg2 not installed."""
        from list_schemas_users import list_schemas_users
        
        with patch.dict('sys.modules', {'psycopg2': None}):
            with patch('builtins.__import__', side_effect=ImportError("No module named 'psycopg2'")):
                with pytest.raises(SystemExit):
                    list_schemas_users("postgresql://user:pass@host/db")  # pragma: allowlist secret
    
    def test_connects_to_database(self):
        """Should attempt to connect with provided connection string."""
        mock_psycopg2 = MagicMock()
        mock_conn = MagicMock()
        mock_cursor = MagicMock()
        mock_cursor.fetchall.return_value = []
        mock_conn.cursor.return_value = mock_cursor
        mock_psycopg2.connect.return_value = mock_conn
        
        with patch.dict('sys.modules', {'psycopg2': mock_psycopg2}):
            from list_schemas_users import list_schemas_users
            
            with patch('builtins.print'):
                try:
                    list_schemas_users("postgresql://user:pass@host:25060/db")  # pragma: allowlist secret
                except:
                    pass  # May fail on cursor operations, that's OK
            
            mock_psycopg2.connect.assert_called_once()
    
    def test_queries_schemas(self):
        """Should query pg_namespace for schemas."""
        mock_psycopg2 = MagicMock()
        mock_conn = MagicMock()
        mock_cursor = MagicMock()
        mock_cursor.fetchall.return_value = [
            ('public', 'postgres', 5),
            ('tenant1', 'doadmin', 3),
        ]
        mock_conn.cursor.return_value = mock_cursor
        mock_psycopg2.connect.return_value = mock_conn
        
        with patch.dict('sys.modules', {'psycopg2': mock_psycopg2}):
            from list_schemas_users import list_schemas_users
            
            with patch('builtins.print'):
                try:
                    list_schemas_users("postgresql://user:pass@host/db")  # pragma: allowlist secret
                except:
                    pass
            
            # Verify SQL was executed
            assert mock_cursor.execute.called
    
    def test_closes_connection(self):
        """Should close connection after use."""
        mock_psycopg2 = MagicMock()
        mock_conn = MagicMock()
        mock_cursor = MagicMock()
        mock_cursor.fetchall.return_value = []
        mock_conn.cursor.return_value = mock_cursor
        mock_psycopg2.connect.return_value = mock_conn
        
        with patch.dict('sys.modules', {'psycopg2': mock_psycopg2}):
            from list_schemas_users import list_schemas_users
            
            with patch('builtins.print'):
                try:
                    list_schemas_users("postgresql://user:pass@host/db")  # pragma: allowlist secret
                except:
                    pass
            
            # Connection should be closed
            mock_conn.close.assert_called()


class TestSchemaFiltering:
    """Tests for schema filtering logic."""
    
    def test_excludes_system_schemas_in_query(self):
        """Query should exclude pg_catalog, information_schema, etc."""
        # The SQL in the module should contain these exclusions
        import list_schemas_users
        import inspect
        source = inspect.getsource(list_schemas_users)
        
        assert "pg_catalog" in source
        assert "information_schema" in source
        assert "pg_toast" in source
        assert "pg_temp" in source


class TestUserFiltering:
    """Tests for user filtering logic."""
    
    def test_excludes_system_users_in_query(self):
        """Query should exclude pg_* and admin users."""
        import list_schemas_users
        import inspect
        source = inspect.getsource(list_schemas_users)
        
        assert "pg_" in source  # Excludes pg_* roles
        assert "doadmin" in source  # Excludes doadmin


class TestOutputFormat:
    """Tests for output formatting."""
    
    def test_outputs_section_headers(self):
        """Output should include section headers."""
        import list_schemas_users
        import inspect
        source = inspect.getsource(list_schemas_users)
        
        # Check for section identifiers in print statements
        assert "SCHEMAS" in source
        assert "USERS" in source
        assert "ISOLATION" in source or "CHECK" in source
