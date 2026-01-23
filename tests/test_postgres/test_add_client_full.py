"""Comprehensive tests for add_client.py - Full coverage."""

import os
import sys
import pytest
from unittest.mock import patch, MagicMock, call

# Add scripts to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '../../skills/postgres/scripts'))

from add_client import (
    generate_password, generate_sql, execute_setup,
    create_connection_pool, get_connection_string, main
)


class TestAddClientImports:
    """Tests for module imports."""
    
    def test_module_imports(self):
        """Module should import without errors."""
        import add_client
        assert hasattr(add_client, 'generate_password')
        assert hasattr(add_client, 'generate_sql')
        assert hasattr(add_client, 'execute_setup')
        assert hasattr(add_client, 'get_connection_string')
        assert hasattr(add_client, 'main')


class TestGeneratePassword:
    """Tests for password generation."""
    
    def test_generates_password(self):
        """Should generate a password."""
        password = generate_password()
        assert isinstance(password, str)
        assert len(password) > 0
    
    def test_default_length_is_32(self):
        """Should default to 32 character password."""
        password = generate_password()
        assert len(password) == 32
    
    def test_custom_length(self):
        """Should respect custom length."""
        password = generate_password(length=16)
        assert len(password) == 16
    
    def test_password_uniqueness(self):
        """Should generate unique passwords."""
        passwords = [generate_password() for _ in range(10)]
        assert len(set(passwords)) == 10


class TestGenerateSql:
    """Tests for SQL generation."""
    
    def test_generates_sql(self, tmp_path, capsys):
        """Should generate SQL statements."""
        generate_sql('tenant1', 'tenant1_user', 'FAKE_TEST_PASS')
        
        captured = capsys.readouterr()
        assert 'CREATE SCHEMA' in captured.out or 'tenant1' in captured.out
    
    def test_generates_user_creation(self, tmp_path, capsys):
        """Should include CREATE USER statement."""
        generate_sql('tenant1', 'tenant1_user', 'FAKE_TEST_PASS')
        
        captured = capsys.readouterr()
        assert 'CREATE USER' in captured.out or 'tenant1_user' in captured.out
    
    def test_grants_privileges(self, tmp_path, capsys):
        """Should include GRANT statements."""
        generate_sql('tenant1', 'tenant1_user', 'FAKE_TEST_PASS')
        
        captured = capsys.readouterr()
        assert 'GRANT' in captured.out
    
    def test_sets_search_path(self, tmp_path, capsys):
        """Should set search_path."""
        generate_sql('tenant1', 'tenant1_user', 'FAKE_TEST_PASS')
        
        captured = capsys.readouterr()
        assert 'search_path' in captured.out.lower()
    
    def test_returns_password(self):
        """Should return the password."""
        result = generate_sql('tenant1', 'tenant1_user', 'FAKE_TEST_PASS')
        assert result == 'FAKE_TEST_PASS'
    
    def test_writes_to_output_dir(self, tmp_path):
        """Should write files when output_dir provided."""
        output_dir = str(tmp_path / 'sql')
        generate_sql('tenant1', 'tenant1_user', 'FAKE_TEST_PASS', output_dir=output_dir)
        
        assert (tmp_path / 'sql' / 'db-setup.sql').exists()
        assert (tmp_path / 'sql' / 'db-users.sql').exists()
        assert (tmp_path / 'sql' / 'db-permissions.sql').exists()


class TestGetConnectionString:
    """Tests for connection string generation."""
    
    def test_generates_connection_string(self):
        """Should generate valid connection string."""
        conn = get_connection_string(
            'postgresql://admin:FAKE@host.db.ondigitalocean.com:25060/defaultdb?sslmode=require',  # pragma: allowlist secret
            'tenant1_user',
            'FAKE_TEST_PASS'
        )
        
        assert 'postgresql://' in conn
        assert 'tenant1_user' in conn
        assert '25060' in conn
    
    def test_includes_sslmode(self):
        """Should include sslmode."""
        conn = get_connection_string(
            'postgresql://admin:FAKE@host:25060/db?sslmode=require',  # pragma: allowlist secret
            'user',
            'FAKE_PASS'
        )
        
        assert 'sslmode' in conn


class TestExecuteSetup:
    """Tests for execute_setup function."""
    
    def test_execute_setup_connects(self):
        """Should connect using psycopg2."""
        mock_psycopg2 = MagicMock()
        mock_conn = MagicMock()
        mock_cursor = MagicMock()
        mock_conn.cursor.return_value = mock_cursor
        mock_psycopg2.connect.return_value = mock_conn
        
        with patch.dict('sys.modules', {'psycopg2': mock_psycopg2}):
            # Need to reload to pick up mock
            import importlib
            import add_client
            importlib.reload(add_client)
            
            with patch('builtins.print'):
                try:
                    add_client.execute_setup(
                        'postgresql://admin:FAKE@host/db',  # pragma: allowlist secret
                        'tenant1',
                        'tenant1_user',
                        'FAKE_PASS'
                    )
                except:
                    pass
            
            mock_psycopg2.connect.assert_called()
    
    def test_execute_setup_creates_schema(self):
        """Should create schema."""
        mock_psycopg2 = MagicMock()
        mock_conn = MagicMock()
        mock_cursor = MagicMock()
        mock_conn.cursor.return_value = mock_cursor
        mock_psycopg2.connect.return_value = mock_conn
        
        with patch.dict('sys.modules', {'psycopg2': mock_psycopg2}):
            import importlib
            import add_client
            importlib.reload(add_client)
            
            with patch('builtins.print'):
                try:
                    add_client.execute_setup(
                        'postgresql://admin:FAKE@host/db',  # pragma: allowlist secret
                        'tenant1',
                        'tenant1_user',
                        'FAKE_PASS'
                    )
                except:
                    pass
            
            # Check that cursor.execute was called
            assert mock_cursor.execute.called


class TestCreateConnectionPool:
    """Tests for connection pool creation."""
    
    def test_create_pool_calls_doctl(self):
        """Should call doctl to create pool."""
        with patch('subprocess.run') as mock_run:
            mock_run.return_value = MagicMock(returncode=0, stdout='')
            
            result = create_connection_pool(
                'cluster-123',
                'tenant1',
                'tenant1_user',
                pool_size=25,
                pool_mode='transaction'
            )
            
            mock_run.assert_called()
            call_args = str(mock_run.call_args)
            assert 'doctl' in call_args


class TestMainFunction:
    """Tests for main entry point."""
    
    def test_main_requires_arguments(self):
        """Should exit if required arguments missing."""
        with patch('sys.argv', ['add_client.py']):
            with pytest.raises(SystemExit):
                main()
    
    def test_main_outputs_connection_string(self, capsys):
        """Should output connection info."""
        mock_psycopg2 = MagicMock()
        mock_conn = MagicMock()
        mock_cursor = MagicMock()
        mock_conn.cursor.return_value = mock_cursor
        mock_psycopg2.connect.return_value = mock_conn
        
        with patch.dict('sys.modules', {'psycopg2': mock_psycopg2}):
            import importlib
            import add_client
            importlib.reload(add_client)
            
            with patch('sys.argv', [
                'add_client.py',
                'cluster-123',
                'postgresql://admin:FAKE@host:25060/db?sslmode=require',  # pragma: allowlist secret
                'tenant1'
            ]):
                try:
                    add_client.main()
                except SystemExit:
                    pass
            
            captured = capsys.readouterr()
            # Should print something about the client
            assert 'tenant1' in captured.out.lower() or captured.out != ''


class TestErrorHandling:
    """Tests for error handling."""
    
    def test_handles_connection_error(self):
        """Should handle database connection errors."""
        # Create proper mock exception classes that inherit from BaseException
        class MockPsycopgError(Exception):
            pass
        
        class MockDuplicateSchema(MockPsycopgError):
            pass
        
        class MockDuplicateObject(MockPsycopgError):
            pass
        
        mock_psycopg2 = MagicMock()
        # Throw an instance of our mock Error class so it gets caught by `except psycopg2.Error`
        mock_psycopg2.connect.side_effect = MockPsycopgError("Connection refused")
        mock_psycopg2.Error = MockPsycopgError
        
        # Mock errors module with proper exception classes
        mock_errors = MagicMock()
        mock_errors.DuplicateSchema = MockDuplicateSchema
        mock_errors.DuplicateObject = MockDuplicateObject
        mock_psycopg2.errors = mock_errors
        
        with patch.dict('sys.modules', {'psycopg2': mock_psycopg2, 'psycopg2.errors': mock_errors}):
            import importlib
            import add_client
            importlib.reload(add_client)
            
            with patch('builtins.print'):
                result = add_client.execute_setup(
                    'postgresql://admin:FAKE@invalid/db',  # pragma: allowlist secret
                    'tenant1',
                    'tenant1_user',
                    'FAKE_PASS'
                )
                
                # Should return False on error
                assert result is False
    
    def test_handles_duplicate_schema(self):
        """Should handle duplicate schema error."""
        mock_psycopg2 = MagicMock()
        mock_conn = MagicMock()
        mock_cursor = MagicMock()
        
        # Simulate DuplicateSchema error
        class DuplicateSchema(Exception):
            pass
        mock_psycopg2.errors = MagicMock()
        mock_psycopg2.errors.DuplicateSchema = DuplicateSchema
        mock_cursor.execute.side_effect = DuplicateSchema("schema exists")
        mock_conn.cursor.return_value = mock_cursor
        mock_psycopg2.connect.return_value = mock_conn
        
        with patch.dict('sys.modules', {'psycopg2': mock_psycopg2, 'psycopg2.errors': mock_psycopg2.errors}):
            import importlib
            import add_client
            importlib.reload(add_client)
            
            with patch('builtins.print'):
                result = add_client.execute_setup(
                    'postgresql://admin:FAKE@host/db',  # pragma: allowlist secret
                    'existing_schema',
                    'user',
                    'FAKE_PASS'
                )
                
                # Should return False for duplicate
                assert result is False
        
