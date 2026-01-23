"""Comprehensive tests for cleanup_client.py - Full coverage."""

import os
import sys
import pytest
from unittest.mock import patch, MagicMock, call
import subprocess

# Add scripts to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '../../skills/postgres/scripts'))


class TestCleanupClientImports:
    """Tests for module imports."""
    
    def test_module_imports(self):
        """Module should import without errors."""
        import cleanup_client
        assert hasattr(cleanup_client, 'generate_sql')
        assert hasattr(cleanup_client, 'execute_cleanup')
        assert hasattr(cleanup_client, 'remove_connection_pool')
        assert hasattr(cleanup_client, 'main')


class TestGenerateSql:
    """Tests for SQL generation."""
    
    def test_generates_drop_schema(self):
        """Should generate DROP SCHEMA statement."""
        from cleanup_client import generate_sql
        
        sql = generate_sql('test_client')
        
        assert 'DROP SCHEMA' in sql
        assert 'test_client' in sql
    
    def test_generates_drop_user(self):
        """Should generate DROP USER statement."""
        from cleanup_client import generate_sql
        
        sql = generate_sql('test_client')
        
        assert 'DROP USER' in sql
        assert 'test_client_user' in sql  # Username is client_name + "_user"
    
    def test_uses_cascade(self):
        """Should use CASCADE to drop dependent objects."""
        from cleanup_client import generate_sql
        
        sql = generate_sql('test_client')
        
        assert 'CASCADE' in sql
    
    def test_terminates_connections(self):
        """Should terminate active connections first."""
        from cleanup_client import generate_sql
        
        sql = generate_sql('test_client')
        
        assert 'pg_terminate_backend' in sql
    
    def test_keep_user_option(self):
        """Should not drop user when keep_user is True."""
        from cleanup_client import generate_sql
        
        sql = generate_sql('test_client', keep_user=True)
        
        assert 'DROP SCHEMA' in sql
        assert 'DROP USER' not in sql
    
    def test_includes_verification_query(self):
        """Should include verification queries."""
        from cleanup_client import generate_sql
        
        sql = generate_sql('test_client')
        
        assert 'pg_namespace' in sql or 'exists' in sql.lower()


class TestExecuteCleanup:
    """Tests for database cleanup execution."""
    
    def test_cleanup_connects_to_database(self):
        """Should connect using psycopg2."""
        mock_psycopg2 = MagicMock()
        mock_conn = MagicMock()
        mock_cursor = MagicMock()
        mock_cursor.rowcount = 0
        mock_conn.cursor.return_value = mock_cursor
        mock_psycopg2.connect.return_value = mock_conn
        
        with patch.dict('sys.modules', {'psycopg2': mock_psycopg2, 'psycopg2.errors': MagicMock()}):
            from cleanup_client import execute_cleanup
            
            with patch('builtins.print'):
                execute_cleanup(
                    'postgresql://admin:testpassword@host/db',  # pragma: allowlist secret
                    'test_client'
                )
            
            mock_psycopg2.connect.assert_called_once_with('postgresql://admin:testpassword@host/db')  # pragma: allowlist secret
    
    def test_cleanup_executes_sql(self):
        """Should execute cleanup SQL statements."""
        mock_psycopg2 = MagicMock()
        mock_conn = MagicMock()
        mock_cursor = MagicMock()
        mock_cursor.rowcount = 0
        mock_conn.cursor.return_value = mock_cursor
        mock_psycopg2.connect.return_value = mock_conn
        
        with patch.dict('sys.modules', {'psycopg2': mock_psycopg2, 'psycopg2.errors': MagicMock()}):
            from cleanup_client import execute_cleanup
            
            with patch('builtins.print'):
                execute_cleanup(
                    'postgresql://admin:testpassword@host/db',  # pragma: allowlist secret
                    'test_client'
                )
            
            assert mock_cursor.execute.called
    
    def test_cleanup_sets_autocommit(self):
        """Should set autocommit mode."""
        mock_psycopg2 = MagicMock()
        mock_conn = MagicMock()
        mock_cursor = MagicMock()
        mock_cursor.rowcount = 0
        mock_conn.cursor.return_value = mock_cursor
        mock_psycopg2.connect.return_value = mock_conn
        
        with patch.dict('sys.modules', {'psycopg2': mock_psycopg2, 'psycopg2.errors': MagicMock()}):
            from cleanup_client import execute_cleanup
            
            with patch('builtins.print'):
                execute_cleanup(
                    'postgresql://admin:testpassword@host/db',  # pragma: allowlist secret
                    'test_client'
                )
            
            assert mock_conn.autocommit == True
    
    def test_cleanup_closes_connection(self):
        """Should close the connection."""
        mock_psycopg2 = MagicMock()
        mock_conn = MagicMock()
        mock_cursor = MagicMock()
        mock_cursor.rowcount = 0
        mock_conn.cursor.return_value = mock_cursor
        mock_psycopg2.connect.return_value = mock_conn
        
        with patch.dict('sys.modules', {'psycopg2': mock_psycopg2, 'psycopg2.errors': MagicMock()}):
            from cleanup_client import execute_cleanup
            
            with patch('builtins.print'):
                execute_cleanup(
                    'postgresql://admin:testpassword@host/db',  # pragma: allowlist secret
                    'test_client'
                )
            
            mock_conn.close.assert_called()
    
    def test_cleanup_returns_true_on_success(self):
        """Should return True on successful cleanup."""
        mock_psycopg2 = MagicMock()
        mock_conn = MagicMock()
        mock_cursor = MagicMock()
        mock_cursor.rowcount = 0
        mock_conn.cursor.return_value = mock_cursor
        mock_psycopg2.connect.return_value = mock_conn
        
        with patch.dict('sys.modules', {'psycopg2': mock_psycopg2, 'psycopg2.errors': MagicMock()}):
            from cleanup_client import execute_cleanup
            
            with patch('builtins.print'):
                result = execute_cleanup(
                    'postgresql://admin:testpassword@host/db',  # pragma: allowlist secret
                    'test_client'
                )
            
            assert result == True
    
    def test_cleanup_with_keep_user(self):
        """Should respect keep_user option."""
        mock_psycopg2 = MagicMock()
        mock_conn = MagicMock()
        mock_cursor = MagicMock()
        mock_cursor.rowcount = 0
        mock_conn.cursor.return_value = mock_cursor
        mock_psycopg2.connect.return_value = mock_conn
        
        with patch.dict('sys.modules', {'psycopg2': mock_psycopg2, 'psycopg2.errors': MagicMock()}):
            from cleanup_client import execute_cleanup
            
            with patch('builtins.print'):
                result = execute_cleanup(
                    'postgresql://admin:testpassword@host/db',  # pragma: allowlist secret
                    'test_client',
                    keep_user=True
                )
            
            assert result == True


class TestRemoveConnectionPool:
    """Tests for connection pool removal."""
    
    def test_remove_pool_calls_doctl(self):
        """Should call doctl to remove pool."""
        from cleanup_client import remove_connection_pool
        
        with patch('subprocess.run') as mock_run:
            mock_run.return_value = MagicMock(returncode=0)
            
            with patch('builtins.print'):
                remove_connection_pool('cluster-123', 'test_client')
            
            mock_run.assert_called()
            call_args = mock_run.call_args[0][0]
            assert 'doctl' in call_args
            assert 'databases' in call_args
            assert 'pool' in call_args
            assert 'delete' in call_args
    
    def test_remove_pool_uses_correct_pool_name(self):
        """Should construct pool name from client name."""
        from cleanup_client import remove_connection_pool
        
        with patch('subprocess.run') as mock_run:
            mock_run.return_value = MagicMock(returncode=0)
            
            with patch('builtins.print'):
                remove_connection_pool('cluster-123', 'test_client')
            
            call_args = mock_run.call_args[0][0]
            assert 'test_client_pool' in call_args
    
    def test_remove_pool_handles_not_found(self):
        """Should handle pool not found gracefully."""
        from cleanup_client import remove_connection_pool
        
        with patch('subprocess.run') as mock_run:
            error = subprocess.CalledProcessError(1, 'doctl')
            error.stderr = 'pool not found'
            mock_run.side_effect = error
            
            with patch('builtins.print'):
                result = remove_connection_pool('cluster-123', 'nonexistent')
            
            assert result == False
    
    def test_remove_pool_returns_true_on_success(self):
        """Should return True on successful removal."""
        from cleanup_client import remove_connection_pool
        
        with patch('subprocess.run') as mock_run:
            mock_run.return_value = MagicMock(returncode=0)
            
            with patch('builtins.print'):
                result = remove_connection_pool('cluster-123', 'test_client')
            
            assert result == True


class TestMainFunction:
    """Tests for main entry point."""
    
    def test_main_requires_arguments(self):
        """Should exit if required arguments missing."""
        import cleanup_client
        
        with patch('sys.argv', ['cleanup_client.py']):
            with pytest.raises(SystemExit):
                cleanup_client.main()
    
    def test_main_with_generate_flag(self):
        """Should only generate SQL with --generate flag."""
        import cleanup_client
        
        with patch('sys.argv', [
            'cleanup_client.py',
            'postgresql://admin:testpassword@host/db',  # pragma: allowlist secret
            'test_client',
            '--generate'
        ]):
            with patch('builtins.print') as mock_print:
                with patch.object(cleanup_client, 'execute_cleanup') as mock_execute:
                    cleanup_client.main()
                    
                    # Should NOT have called execute_cleanup
                    mock_execute.assert_not_called()
                    # Should have printed SQL
                    assert mock_print.called
    
    def test_main_prompts_for_confirmation(self):
        """Should prompt user before destructive action."""
        import cleanup_client
        
        with patch('sys.argv', [
            'cleanup_client.py',
            'postgresql://admin:testpassword@host/db',  # pragma: allowlist secret
            'test_client'
        ]):
            with patch('builtins.input', return_value='n') as mock_input:
                with patch('builtins.print'):
                    try:
                        cleanup_client.main()
                    except SystemExit:
                        pass
                
                # Should have prompted
                mock_input.assert_called()
    
    def test_main_aborts_on_no_confirmation(self):
        """Should abort if user doesn't confirm."""
        import cleanup_client
        
        with patch('sys.argv', [
            'cleanup_client.py',
            'postgresql://admin:testpassword@host/db',  # pragma: allowlist secret
            'test_client'
        ]):
            with patch('builtins.input', return_value='n'):
                with patch('builtins.print'):
                    with patch.object(cleanup_client, 'execute_cleanup') as mock_cleanup:
                        try:
                            cleanup_client.main()
                        except SystemExit:
                            pass
                        
                        # Should NOT have called cleanup
                        mock_cleanup.assert_not_called()
    
    def test_main_proceeds_on_yes_confirmation(self):
        """Should proceed if user confirms."""
        mock_psycopg2 = MagicMock()
        mock_conn = MagicMock()
        mock_cursor = MagicMock()
        mock_cursor.rowcount = 0
        mock_conn.cursor.return_value = mock_cursor
        mock_psycopg2.connect.return_value = mock_conn
        
        with patch.dict('sys.modules', {'psycopg2': mock_psycopg2, 'psycopg2.errors': MagicMock()}):
            import cleanup_client
            
            with patch('sys.argv', [
                'cleanup_client.py',
                'postgresql://admin:testpassword@host/db',  # pragma: allowlist secret
                'test_client'
            ]):
                # Must type exact client name to confirm, not 'yes'
                with patch('builtins.input', return_value='test_client'):
                    with patch('builtins.print'):
                        cleanup_client.main()
    
    def test_main_with_confirm_flag_skips_prompt(self):
        """Should skip confirmation with --confirm flag."""
        mock_psycopg2 = MagicMock()
        mock_conn = MagicMock()
        mock_cursor = MagicMock()
        mock_cursor.rowcount = 0
        mock_conn.cursor.return_value = mock_cursor
        mock_psycopg2.connect.return_value = mock_conn
        
        with patch.dict('sys.modules', {'psycopg2': mock_psycopg2, 'psycopg2.errors': MagicMock()}):
            import cleanup_client
            
            with patch('sys.argv', [
                'cleanup_client.py',
                'postgresql://admin:testpassword@host/db',  # pragma: allowlist secret
                'test_client',
                '--confirm'
            ]):
                with patch('builtins.input') as mock_input:
                    with patch('builtins.print'):
                        cleanup_client.main()
                    
                    # Should NOT have prompted
                    mock_input.assert_not_called()
    
    def test_main_with_keep_user_flag(self):
        """Should pass keep_user option."""
        mock_psycopg2 = MagicMock()
        mock_conn = MagicMock()
        mock_cursor = MagicMock()
        mock_cursor.rowcount = 0
        mock_conn.cursor.return_value = mock_cursor
        mock_psycopg2.connect.return_value = mock_conn
        
        with patch.dict('sys.modules', {'psycopg2': mock_psycopg2, 'psycopg2.errors': MagicMock()}):
            import cleanup_client
            
            with patch('sys.argv', [
                'cleanup_client.py',
                'postgresql://admin:testpassword@host/db',  # pragma: allowlist secret
                'test_client',
                '--confirm',
                '--keep-user'
            ]):
                with patch('builtins.print'):
                    cleanup_client.main()
    
    def test_main_with_cluster_id_removes_pool(self):
        """Should remove connection pool when cluster-id provided."""
        mock_psycopg2 = MagicMock()
        mock_conn = MagicMock()
        mock_cursor = MagicMock()
        mock_cursor.rowcount = 0
        mock_conn.cursor.return_value = mock_cursor
        mock_psycopg2.connect.return_value = mock_conn
        
        with patch.dict('sys.modules', {'psycopg2': mock_psycopg2, 'psycopg2.errors': MagicMock()}):
            import cleanup_client
            
            with patch('sys.argv', [
                'cleanup_client.py',
                'postgresql://admin:testpassword@host/db',  # pragma: allowlist secret
                'test_client',
                '--confirm',
                '--cluster-id', 'cluster-123'
            ]):
                with patch.object(cleanup_client, 'remove_connection_pool') as mock_remove:
                    with patch('builtins.print'):
                        cleanup_client.main()
                    
                    mock_remove.assert_called_once_with('cluster-123', 'test_client')
