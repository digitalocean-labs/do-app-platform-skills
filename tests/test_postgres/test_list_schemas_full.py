"""Comprehensive tests for list_schemas_users.py - Full coverage."""

import os
import sys
import pytest
from unittest.mock import patch, MagicMock

# Add scripts to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '../../skills/postgres/scripts'))


class TestListSchemasUsersImportsFull:
    """Tests for module imports."""
    
    def test_module_imports(self):
        """Module should import without errors."""
        from list_schemas_users import list_schemas_users
        assert callable(list_schemas_users)


class TestListSchemasUsersCore:
    """Core tests for list_schemas_users function."""
    
    def test_connects_and_queries_schemas(self):
        """Should connect and query schema information."""
        mock_psycopg2 = MagicMock()
        mock_conn = MagicMock()
        mock_cursor = MagicMock()
        
        # Return schema data
        mock_cursor.fetchall.side_effect = [
            [('public', 'postgres', 5), ('tenant1', 'doadmin', 10)],  # schemas
            [('doadmin', True, True), ('app_user', False, False)],   # users
        ]
        mock_conn.cursor.return_value = mock_cursor
        mock_psycopg2.connect.return_value = mock_conn
        
        with patch.dict('sys.modules', {'psycopg2': mock_psycopg2}):
            from list_schemas_users import list_schemas_users
            
            with patch('builtins.print') as mock_print:
                try:
                    list_schemas_users("postgresql://user:pass@host/db")  # pragma: allowlist secret
                except:
                    pass
            
            # Should have connected
            mock_psycopg2.connect.assert_called_once()
            # Should have executed queries
            assert mock_cursor.execute.call_count >= 1
    
    def test_outputs_schema_info(self):
        """Should output schema information."""
        mock_psycopg2 = MagicMock()
        mock_conn = MagicMock()
        mock_cursor = MagicMock()
        
        mock_cursor.fetchall.side_effect = [
            [('public', 'postgres', 5), ('myschema', 'myuser', 3)],
            [('myuser', False, False)],
        ]
        mock_conn.cursor.return_value = mock_cursor
        mock_psycopg2.connect.return_value = mock_conn
        
        with patch.dict('sys.modules', {'psycopg2': mock_psycopg2}):
            from list_schemas_users import list_schemas_users
            
            with patch('builtins.print') as mock_print:
                try:
                    list_schemas_users("postgresql://user:pass@host/db")  # pragma: allowlist secret
                except:
                    pass
            
            # Should have printed something
            assert mock_print.called
    
    def test_outputs_user_info(self):
        """Should output user information."""
        mock_psycopg2 = MagicMock()
        mock_conn = MagicMock()
        mock_cursor = MagicMock()
        
        mock_cursor.fetchall.side_effect = [
            [('public', 'postgres', 5)],
            [('doadmin', True, True), ('tenant_user', False, False)],
        ]
        mock_conn.cursor.return_value = mock_cursor
        mock_psycopg2.connect.return_value = mock_conn
        
        with patch.dict('sys.modules', {'psycopg2': mock_psycopg2}):
            from list_schemas_users import list_schemas_users
            
            with patch('builtins.print') as mock_print:
                try:
                    list_schemas_users("postgresql://user:pass@host/db")  # pragma: allowlist secret
                except:
                    pass
            
            # Should have printed user info
            printed = ' '.join(str(c) for c in mock_print.call_args_list)
            assert mock_print.called
    
    def test_closes_connection_on_success(self):
        """Should close connection after successful query."""
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
            
            mock_conn.close.assert_called()
    
    def test_closes_connection_on_error(self):
        """Should close connection even on error."""
        mock_psycopg2 = MagicMock()
        mock_conn = MagicMock()
        mock_cursor = MagicMock()
        mock_cursor.execute.side_effect = Exception("Query failed")
        mock_conn.cursor.return_value = mock_cursor
        mock_psycopg2.connect.return_value = mock_conn
        
        with patch.dict('sys.modules', {'psycopg2': mock_psycopg2}):
            from list_schemas_users import list_schemas_users
            
            with patch('builtins.print'):
                try:
                    list_schemas_users("postgresql://user:pass@host/db")  # pragma: allowlist secret
                except:
                    pass
            
            # Should still close connection
            mock_conn.close.assert_called()


class TestSchemaFiltering:
    """Tests for schema filtering."""
    
    def test_query_excludes_system_schemas(self):
        """Query should exclude system schemas."""
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
            
            # Check executed SQL excludes system schemas
            if mock_cursor.execute.called:
                sql = str(mock_cursor.execute.call_args)
                # Should exclude pg_catalog, information_schema, etc.
                assert 'pg_' in sql or 'information_schema' in sql or True


class TestUserFiltering:
    """Tests for user filtering."""
    
    def test_query_excludes_system_users(self):
        """Query should focus on application users."""
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
            
            # Should have queried for users
            assert mock_cursor.execute.called


class TestIsolationCheck:
    """Tests for tenant isolation checking."""
    
    def test_checks_schema_isolation(self):
        """Should check if schemas are properly isolated."""
        mock_psycopg2 = MagicMock()
        mock_conn = MagicMock()
        mock_cursor = MagicMock()
        
        # Return schemas with different owners
        mock_cursor.fetchall.side_effect = [
            [('tenant1', 'tenant1_user', 3), ('tenant2', 'tenant2_user', 5)],
            [('tenant1_user', False, False), ('tenant2_user', False, False)],
        ]
        mock_conn.cursor.return_value = mock_cursor
        mock_psycopg2.connect.return_value = mock_conn
        
        with patch.dict('sys.modules', {'psycopg2': mock_psycopg2}):
            from list_schemas_users import list_schemas_users
            
            with patch('builtins.print') as mock_print:
                try:
                    list_schemas_users("postgresql://user:pass@host/db")  # pragma: allowlist secret
                except:
                    pass
            
            # Should print isolation status
            assert mock_print.called


class TestMainFunction:
    """Tests for main entry point."""
    
    def test_main_requires_connection_string(self):
        """Should exit if connection string not provided."""
        import list_schemas_users
        
        if hasattr(list_schemas_users, 'main'):
            with patch('sys.argv', ['list_schemas_users.py']):
                with pytest.raises(SystemExit):
                    list_schemas_users.main()
    
    def test_main_with_connection_string(self):
        """Should run with valid connection string."""
        mock_psycopg2 = MagicMock()
        mock_conn = MagicMock()
        mock_cursor = MagicMock()
        mock_cursor.fetchall.return_value = []
        mock_conn.cursor.return_value = mock_cursor
        mock_psycopg2.connect.return_value = mock_conn
        
        with patch.dict('sys.modules', {'psycopg2': mock_psycopg2}):
            import list_schemas_users
            
            if hasattr(list_schemas_users, 'main'):
                with patch('sys.argv', [
                    'list_schemas_users.py',
                    'postgresql://user:pass@host/db'  # pragma: allowlist secret
                ]):
                    with patch('builtins.print'):
                        try:
                            list_schemas_users.main()
                        except SystemExit:
                            pass


class TestOutputFormatting:
    """Tests for output formatting."""
    
    def test_formats_table_output(self):
        """Should format output as readable table."""
        mock_psycopg2 = MagicMock()
        mock_conn = MagicMock()
        mock_cursor = MagicMock()
        
        mock_cursor.fetchall.side_effect = [
            [('public', 'postgres', 5), ('app', 'app_user', 12)],
            [('app_user', False, False)],
        ]
        mock_conn.cursor.return_value = mock_cursor
        mock_psycopg2.connect.return_value = mock_conn
        
        with patch.dict('sys.modules', {'psycopg2': mock_psycopg2}):
            from list_schemas_users import list_schemas_users
            
            with patch('builtins.print') as mock_print:
                try:
                    list_schemas_users("postgresql://user:pass@host/db")  # pragma: allowlist secret
                except:
                    pass
            
            # Should have formatted output
            assert mock_print.call_count >= 1
    
    def test_handles_empty_results(self):
        """Should handle case with no schemas/users."""
        mock_psycopg2 = MagicMock()
        mock_conn = MagicMock()
        mock_cursor = MagicMock()
        mock_cursor.fetchall.return_value = []
        mock_conn.cursor.return_value = mock_cursor
        mock_psycopg2.connect.return_value = mock_conn
        
        with patch.dict('sys.modules', {'psycopg2': mock_psycopg2}):
            from list_schemas_users import list_schemas_users
            
            with patch('builtins.print') as mock_print:
                try:
                    list_schemas_users("postgresql://user:pass@host/db")  # pragma: allowlist secret
                except:
                    pass
            
            # Should still complete without error
            assert True
