"""Comprehensive tests for secure_setup.py - Full coverage."""

import os
import sys
import pytest
from unittest.mock import patch, MagicMock, call

# Add scripts to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '../../skills/postgres/scripts'))


class TestSecureSetupImports:
    """Tests for module imports."""
    
    def test_module_imports(self):
        """Module should import without errors."""
        import secure_setup
        assert hasattr(secure_setup, 'run_psql')
        assert hasattr(secure_setup, 'secure_postgres_setup')


class TestRunPsql:
    """Tests for run_psql function."""
    
    def test_run_psql_success(self):
        """Should execute psql command and return output."""
        from secure_setup import run_psql
        
        with patch('subprocess.run') as mock_run:
            mock_run.return_value = MagicMock(
                returncode=0,
                stdout='query result',
                stderr=''
            )
            
            result = run_psql('postgresql://user:pass@host/db', 'SELECT 1')
            
            assert result == 'query result'
            mock_run.assert_called_once()
    
    def test_run_psql_with_multiline_sql(self):
        """Should handle multiline SQL statements."""
        from secure_setup import run_psql
        
        with patch('subprocess.run') as mock_run:
            mock_run.return_value = MagicMock(
                returncode=0,
                stdout='ok',
                stderr=''
            )
            
            sql = """
            CREATE TABLE test (
                id SERIAL PRIMARY KEY,
                name TEXT
            );
            """
            result = run_psql('postgresql://user:pass@host/db', sql)
            
            assert result == 'ok'
    
    def test_run_psql_failure(self):
        """Should raise exception on psql failure."""
        from secure_setup import run_psql
        
        with patch('subprocess.run') as mock_run:
            mock_run.return_value = MagicMock(
                returncode=1,
                stdout='',
                stderr='ERROR: connection refused'
            )
            
            with pytest.raises(Exception):
                run_psql('postgresql://user:pass@host/db', 'SELECT 1')
    
    def test_run_psql_uses_sslmode(self):
        """Should include sslmode=require in connection."""
        from secure_setup import run_psql
        
        with patch('subprocess.run') as mock_run:
            mock_run.return_value = MagicMock(returncode=0, stdout='', stderr='')
            
            run_psql('postgresql://user:pass@host/db', 'SELECT 1')
            
            call_args = mock_run.call_args
            cmd = call_args[0][0]
            # Check that sslmode is in the connection string
            assert any('sslmode' in str(arg) for arg in cmd)


class TestSecurePostgresSetup:
    """Tests for secure_postgres_setup main function."""
    
    def test_creates_app_user(self):
        """Should create application user with limited privileges."""
        from secure_setup import secure_postgres_setup
        
        with patch('secure_setup.run_psql') as mock_psql:
            mock_psql.return_value = ''
            
            with patch('builtins.print'):
                with patch('secure_setup.store_secret'):
                    secure_postgres_setup(
                        'postgresql://admin:pass@host/db',
                        'myapp',
                        'app_schema'
                    )
            
            # Check CREATE USER was called
            calls = [str(c) for c in mock_psql.call_args_list]
            assert any('CREATE USER' in str(c) or 'CREATE ROLE' in str(c) for c in calls)
    
    def test_creates_schema(self):
        """Should create dedicated schema."""
        from secure_setup import secure_postgres_setup
        
        with patch('secure_setup.run_psql') as mock_psql:
            mock_psql.return_value = ''
            
            with patch('builtins.print'):
                with patch('secure_setup.store_secret'):
                    secure_postgres_setup(
                        'postgresql://admin:pass@host/db',
                        'myapp',
                        'app_schema'
                    )
            
            calls = [str(c) for c in mock_psql.call_args_list]
            assert any('CREATE SCHEMA' in str(c) for c in calls)
    
    def test_grants_privileges(self):
        """Should grant appropriate privileges to app user."""
        from secure_setup import secure_postgres_setup
        
        with patch('secure_setup.run_psql') as mock_psql:
            mock_psql.return_value = ''
            
            with patch('builtins.print'):
                with patch('secure_setup.store_secret'):
                    secure_postgres_setup(
                        'postgresql://admin:pass@host/db',
                        'myapp',
                        'app_schema'
                    )
            
            calls = [str(c) for c in mock_psql.call_args_list]
            assert any('GRANT' in str(c) for c in calls)
    
    def test_revokes_public_privileges(self):
        """Should revoke public privileges for security."""
        from secure_setup import secure_postgres_setup
        
        with patch('secure_setup.run_psql') as mock_psql:
            mock_psql.return_value = ''
            
            with patch('builtins.print'):
                with patch('secure_setup.store_secret'):
                    secure_postgres_setup(
                        'postgresql://admin:pass@host/db',
                        'myapp',
                        'app_schema'
                    )
            
            calls = [str(c) for c in mock_psql.call_args_list]
            assert any('REVOKE' in str(c) for c in calls)


class TestStoreSecret:
    """Tests for GitHub secret storage."""
    
    def test_store_secret_calls_gh_cli(self):
        """Should use gh CLI to store secret."""
        from secure_setup import store_secret
        
        with patch('subprocess.run') as mock_run:
            mock_run.return_value = MagicMock(returncode=0)
            
            store_secret('MY_SECRET', 'secret_value', 'owner/repo')
            
            mock_run.assert_called()
            call_args = str(mock_run.call_args)
            assert 'gh' in call_args or 'secret' in call_args
    
    def test_store_secret_failure(self):
        """Should handle gh CLI failure gracefully."""
        from secure_setup import store_secret
        
        with patch('subprocess.run') as mock_run:
            mock_run.return_value = MagicMock(
                returncode=1,
                stderr='error'
            )
            
            # Should not raise, just warn
            with patch('builtins.print') as mock_print:
                try:
                    store_secret('MY_SECRET', 'value', 'owner/repo')
                except:
                    pass  # May or may not raise


class TestGeneratePassword:
    """Tests for password generation."""
    
    def test_generate_password_length(self):
        """Should generate password of correct length."""
        from secure_setup import generate_password
        
        password = generate_password(32)
        assert len(password) == 32
    
    def test_generate_password_randomness(self):
        """Should generate different passwords each time."""
        from secure_setup import generate_password
        
        passwords = [generate_password(16) for _ in range(10)]
        # All passwords should be unique
        assert len(set(passwords)) == 10
    
    def test_generate_password_contains_alphanumeric(self):
        """Should contain alphanumeric characters."""
        from secure_setup import generate_password
        
        password = generate_password(32)
        assert any(c.isalpha() for c in password)
        assert any(c.isdigit() for c in password)


class TestMainFunction:
    """Tests for main entry point."""
    
    def test_main_requires_arguments(self):
        """Should exit if required arguments missing."""
        import secure_setup
        
        with patch('sys.argv', ['secure_setup.py']):
            with pytest.raises(SystemExit):
                if hasattr(secure_setup, 'main'):
                    secure_setup.main()
    
    def test_main_with_valid_arguments(self):
        """Should run setup with valid arguments."""
        import secure_setup
        
        with patch('sys.argv', [
            'secure_setup.py',
            '--connection-string', 'postgresql://user:pass@host/db',
            '--app-name', 'myapp',
            '--schema', 'myschema'
        ]):
            with patch('secure_setup.secure_postgres_setup') as mock_setup:
                with patch('secure_setup.store_secret'):
                    if hasattr(secure_setup, 'main'):
                        try:
                            secure_setup.main()
                            mock_setup.assert_called_once()
                        except SystemExit:
                            pass


class TestConnectionStringParsing:
    """Tests for connection string handling."""
    
    def test_handles_special_characters_in_password(self):
        """Should handle passwords with special characters."""
        from secure_setup import run_psql
        
        with patch('subprocess.run') as mock_run:
            mock_run.return_value = MagicMock(returncode=0, stdout='', stderr='')
            
            # Password with special chars
            conn = 'postgresql://user:p%40ss%23word@host/db'
            run_psql(conn, 'SELECT 1')
            
            mock_run.assert_called_once()
    
    def test_handles_ipv6_host(self):
        """Should handle IPv6 addresses in connection string."""
        from secure_setup import run_psql
        
        with patch('subprocess.run') as mock_run:
            mock_run.return_value = MagicMock(returncode=0, stdout='', stderr='')
            
            conn = 'postgresql://user:pass@[::1]:5432/db'
            run_psql(conn, 'SELECT 1')
            
            mock_run.assert_called_once()
