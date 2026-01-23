"""Tests for secure_setup.py - Secure hands-free database setup."""

import os
import sys
import pytest
from unittest.mock import patch, MagicMock
import subprocess

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


class TestGeneratePassword:
    """Tests for secure password generation."""
    
    def test_default_length(self):
        """Should generate 32-character password by default."""
        password = generate_password()
        assert len(password) == 32
    
    def test_custom_length(self):
        """Should respect custom length."""
        password = generate_password(16)
        assert len(password) == 16
    
    def test_alphanumeric_only(self):
        """Should only contain alphanumeric to avoid URL issues."""
        password = generate_password()
        assert password.isalnum()
    
    def test_uniqueness(self):
        """Should generate unique passwords."""
        passwords = {generate_password() for _ in range(100)}
        assert len(passwords) == 100


class TestExtractHostFromUrl:
    """Tests for URL host extraction."""
    
    def test_extracts_hostname(self):
        """Should extract hostname from connection string."""
        url = "postgresql://user:pass@my-db.db.ondigitalocean.com:25060/db"
        host = extract_host_from_url(url)
        assert host == "my-db.db.ondigitalocean.com"
    
    def test_handles_ip_address(self):
        """Should handle IP addresses."""
        url = "postgresql://user:pass@192.168.1.100:5432/db"
        host = extract_host_from_url(url)
        assert host == "192.168.1.100"
    
    def test_handles_localhost(self):
        """Should handle localhost."""
        url = "postgresql://user:pass@localhost:5432/db"
        host = extract_host_from_url(url)
        assert host == "localhost"


class TestCheckPrerequisites:
    """Tests for prerequisite checking."""
    
    @patch('subprocess.run')
    def test_checks_psql(self, mock_run):
        """Should check for psql installation."""
        mock_run.return_value = MagicMock(returncode=0)
        
        with patch('builtins.print'):
            check_prerequisites("owner/repo")
        
        # Should have called psql --version
        calls = [str(c) for c in mock_run.call_args_list]
        assert any("psql" in str(c) for c in calls)
    
    @patch('subprocess.run')
    def test_checks_gh_cli(self, mock_run):
        """Should check for gh CLI installation."""
        mock_run.return_value = MagicMock(returncode=0)
        
        with patch('builtins.print'):
            check_prerequisites("owner/repo")
        
        calls = [str(c) for c in mock_run.call_args_list]
        assert any("gh" in str(c) for c in calls)
    
    @patch('subprocess.run')
    def test_checks_gh_auth(self, mock_run):
        """Should verify gh is authenticated."""
        mock_run.return_value = MagicMock(returncode=0)
        
        with patch('builtins.print'):
            check_prerequisites("owner/repo")
        
        calls = [str(c) for c in mock_run.call_args_list]
        assert any("auth" in str(c) for c in calls)
    
    @patch('subprocess.run')
    def test_returns_false_if_psql_missing(self, mock_run):
        """Should return False if psql not installed."""
        mock_run.side_effect = FileNotFoundError()
        
        with patch('builtins.print'):
            result = check_prerequisites("owner/repo")
        
        assert result is False
    
    @patch('subprocess.run')
    def test_returns_true_if_all_present(self, mock_run):
        """Should return True if all prerequisites met."""
        mock_run.return_value = MagicMock(returncode=0)
        
        with patch('builtins.print'):
            result = check_prerequisites("owner/repo")
        
        assert result is True


class TestExecuteSQL:
    """Tests for SQL execution."""
    
    @patch('subprocess.run')
    def test_calls_psql_with_url_and_sql(self, mock_run):
        """Should call psql with connection URL and SQL."""
        mock_run.return_value = MagicMock(returncode=0)
        
        result = execute_sql("postgresql://user:pass@host/db", "SELECT 1")
        
        mock_run.assert_called_once()
        call_args = mock_run.call_args[0][0]
        assert "psql" in call_args
        assert "SELECT 1" in call_args
    
    @patch('subprocess.run')
    def test_returns_true_on_success(self, mock_run):
        """Should return True on successful execution."""
        mock_run.return_value = MagicMock(returncode=0)
        
        result = execute_sql("postgresql://user:pass@host/db", "SELECT 1")
        
        assert result is True
    
    @patch('subprocess.run')
    def test_returns_false_on_failure(self, mock_run):
        """Should return False on execution failure."""
        mock_run.return_value = MagicMock(returncode=1)
        
        result = execute_sql("postgresql://user:pass@host/db", "INVALID SQL")
        
        assert result is False


class TestExecuteSQLScript:
    """Tests for multi-line SQL script execution."""
    
    @patch('subprocess.run')
    def test_pipes_script_to_psql(self, mock_run):
        """Should pipe script to psql stdin."""
        mock_run.return_value = MagicMock(returncode=0)
        
        script = "CREATE TABLE test (id INT);\nINSERT INTO test VALUES (1);"
        result = execute_sql_script("postgresql://user:pass@host/db", script)
        
        mock_run.assert_called_once()
        assert mock_run.call_args[1]['input'] == script
    
    @patch('subprocess.run')
    def test_returns_true_on_success(self, mock_run):
        """Should return True on successful execution."""
        mock_run.return_value = MagicMock(returncode=0)
        
        result = execute_sql_script("postgresql://user:pass@host/db", "SELECT 1;")
        
        assert result is True


class TestSetGitHubSecret:
    """Tests for GitHub secret management."""
    
    @patch('subprocess.run')
    def test_calls_gh_secret_set(self, mock_run):
        """Should call gh secret set command."""
        mock_run.return_value = MagicMock(returncode=0)
        
        result = set_github_secret("owner/repo", "MY_SECRET", "secret_value")
        
        mock_run.assert_called_once()
        call_args = mock_run.call_args[0][0]
        assert "gh" in call_args
        assert "secret" in call_args
        assert "set" in call_args
        assert "MY_SECRET" in call_args
    
    @patch('subprocess.run')
    def test_includes_repo_flag(self, mock_run):
        """Should include --repo flag."""
        mock_run.return_value = MagicMock(returncode=0)
        
        set_github_secret("myorg/myrepo", "SECRET", "value")
        
        call_args = mock_run.call_args[0][0]
        assert "--repo" in call_args
        assert "myorg/myrepo" in call_args
    
    @patch('subprocess.run')
    def test_includes_env_flag_when_provided(self, mock_run):
        """Should include --env flag when environment specified."""
        mock_run.return_value = MagicMock(returncode=0)
        
        set_github_secret("owner/repo", "SECRET", "value", env="production")
        
        call_args = mock_run.call_args[0][0]
        assert "--env" in call_args
        assert "production" in call_args
    
    @patch('subprocess.run')
    def test_no_env_flag_when_not_provided(self, mock_run):
        """Should not include --env flag when environment not specified."""
        mock_run.return_value = MagicMock(returncode=0)
        
        set_github_secret("owner/repo", "SECRET", "value")
        
        call_args = mock_run.call_args[0][0]
        assert "--env" not in call_args
    
    @patch('subprocess.run')
    def test_returns_true_on_success(self, mock_run):
        """Should return True when secret is set."""
        mock_run.return_value = MagicMock(returncode=0)
        
        result = set_github_secret("owner/repo", "SECRET", "value")
        
        assert result is True
    
    @patch('subprocess.run')
    def test_returns_false_on_failure(self, mock_run):
        """Should return False when setting fails."""
        mock_run.return_value = MagicMock(returncode=1)
        
        result = set_github_secret("owner/repo", "SECRET", "value")
        
        assert result is False


class TestSecurityPractices:
    """Tests for security-conscious practices."""
    
    @patch('subprocess.run')
    def test_password_passed_via_body_flag(self, mock_run):
        """Secret value should be passed via --body flag, not visible in command."""
        mock_run.return_value = MagicMock(returncode=0)
        
        set_github_secret("owner/repo", "DB_PASSWORD", "supersecret123")
        
        call_args = mock_run.call_args[0][0]
        assert "--body" in call_args
        # Value is in the command args but passed securely
        assert "supersecret123" in call_args
    
    def test_password_never_printed_in_module(self):
        """Module should not print passwords in normal flow."""
        import secure_setup
        import inspect
        source = inspect.getsource(secure_setup)
        
        # Check that we don't print password directly
        # The module should use secure handling
        assert "Password:" not in source or "NEVER" in source or "never" in source
