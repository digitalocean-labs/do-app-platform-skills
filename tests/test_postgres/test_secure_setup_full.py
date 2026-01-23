"""Comprehensive tests for secure_setup.py - Full coverage."""

import os
import sys
import pytest
from unittest.mock import patch, MagicMock, call

# Add scripts to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '../../skills/postgres/scripts'))

from secure_setup import (
    generate_password,
    check_prerequisites,
    extract_host_from_url,
    execute_sql,
    execute_sql_script,
    set_github_secret,
)


class TestSecureSetupImports:
    """Tests for module imports."""
    
    def test_module_imports(self):
        """Module should import without errors."""
        import secure_setup
        assert hasattr(secure_setup, 'generate_password')
        assert hasattr(secure_setup, 'execute_sql')
        assert hasattr(secure_setup, 'set_github_secret')


class TestExecuteSql:
    """Tests for execute_sql function."""
    
    def test_execute_sql_success(self):
        """Should execute SQL command via psql."""
        with patch('subprocess.run') as mock_run:
            mock_run.return_value = MagicMock(
                returncode=0,
                stdout='query result',
                stderr=''
            )
            
            result = execute_sql('postgresql://user:FAKE_PASS@localhost/db', 'SELECT 1')
            
            assert result == True
            mock_run.assert_called_once()
    
    def test_execute_sql_failure(self):
        """Should return False on psql failure."""
        with patch('subprocess.run') as mock_run:
            mock_run.return_value = MagicMock(
                returncode=1,
                stdout='',
                stderr='ERROR: connection refused'
            )
            
            result = execute_sql('postgresql://user:FAKE_PASS@localhost/db', 'SELECT 1')
            
            assert result == False


class TestExecuteSqlScript:
    """Tests for execute_sql_script function."""
    
    def test_execute_sql_script_success(self):
        """Should execute SQL script file via psql."""
        with patch('subprocess.run') as mock_run:
            mock_run.return_value = MagicMock(returncode=0, stdout='', stderr='')
            
            result = execute_sql_script('postgresql://user:FAKE_PASS@localhost/db', '/path/to/script.sql')
            
            assert result == True
            mock_run.assert_called_once()
    
    def test_execute_sql_script_failure(self):
        """Should return False on script failure."""
        with patch('subprocess.run') as mock_run:
            mock_run.return_value = MagicMock(returncode=1, stdout='', stderr='error')
            
            result = execute_sql_script('postgresql://user:FAKE_PASS@localhost/db', '/path/to/script.sql')
            
            assert result == False


class TestSetGithubSecret:
    """Tests for GitHub secret storage."""
    
    def test_set_github_secret_success(self):
        """Should use gh CLI to store secret."""
        with patch('subprocess.run') as mock_run:
            mock_run.return_value = MagicMock(returncode=0)
            
            result = set_github_secret('owner/repo', 'MY_SECRET', 'secret_value')
            
            assert result == True
            mock_run.assert_called()
    
    def test_set_github_secret_failure(self):
        """Should return False on gh CLI failure."""
        with patch('subprocess.run') as mock_run:
            mock_run.return_value = MagicMock(returncode=1, stderr='error')
            
            result = set_github_secret('owner/repo', 'MY_SECRET', 'value')
            
            assert result == False
    
    def test_set_github_secret_with_env(self):
        """Should support environment-specific secrets."""
        with patch('subprocess.run') as mock_run:
            mock_run.return_value = MagicMock(returncode=0)
            
            result = set_github_secret('owner/repo', 'MY_SECRET', 'value', env='production')
            
            assert result == True


class TestGeneratePasswordFull:
    """Additional tests for password generation."""
    
    def test_generate_password_length(self):
        """Should generate password of correct length."""
        password = generate_password(32)
        assert len(password) == 32
    
    def test_generate_password_custom_length(self):
        """Should support custom lengths."""
        password = generate_password(64)
        assert len(password) == 64
    
    def test_generate_password_randomness(self):
        """Should generate different passwords each time."""
        passwords = [generate_password(16) for _ in range(10)]
        # All passwords should be unique
        assert len(set(passwords)) == 10
    
    def test_generate_password_alphanumeric(self):
        """Should contain alphanumeric characters only."""
        password = generate_password(32)
        assert password.isalnum()


class TestExtractHostFromUrl:
    """Tests for URL parsing."""
    
    def test_extracts_host(self):
        """Should extract hostname from connection string."""
        host = extract_host_from_url('postgresql://user:FAKE_PASS@example-db.localhost:25060/db')
        assert host == 'example-db.localhost'
    
    def test_handles_port(self):
        """Should handle URLs with port."""
        host = extract_host_from_url('postgresql://user:FAKE_PASS@localhost:5432/db')
        assert host == 'localhost'


class TestCheckPrerequisites:
    """Tests for prerequisite checking."""
    
    def test_check_prerequisites_success(self):
        """Should return True when gh and psql are available."""
        with patch('subprocess.run') as mock_run:
            mock_run.return_value = MagicMock(returncode=0)
            
            result = check_prerequisites('owner/repo')
            
            assert result == True
    
    def test_check_prerequisites_missing_gh(self):
        """Should return False when gh is not available."""
        with patch('subprocess.run') as mock_run:
            mock_run.side_effect = FileNotFoundError()
            
            result = check_prerequisites('owner/repo')
            
            assert result == False


class TestMainFunction:
    """Tests for main entry point."""
    
    def test_main_requires_arguments(self):
        """Should exit if required arguments missing."""
        import secure_setup
        
        with patch('sys.argv', ['secure_setup.py']):
            with pytest.raises(SystemExit):
                secure_setup.main()
    
    def test_main_with_dry_run(self):
        """Should support --dry-run mode."""
        import secure_setup
        
        with patch('sys.argv', [
            'secure_setup.py',
            '--admin-url', 'postgresql://admin:FAKE_PASS@localhost/db',
            '--app-name', 'myapp',
            '--repo', 'owner/repo',
            '--dry-run'
        ]):
            with patch('builtins.print'):
                with patch.object(secure_setup, 'check_prerequisites', return_value=True):
                    try:
                        secure_setup.main()
                    except SystemExit:
                        pass  # Expected for dry-run
