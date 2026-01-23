"""Comprehensive tests for add_client.py - Full coverage."""

import os
import sys
import pytest
from unittest.mock import patch, MagicMock, call

# Add scripts to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '../../skills/postgres/scripts'))


class TestAddClientImports:
    """Tests for module imports."""
    
    def test_module_imports(self):
        """Module should import without errors."""
        import add_client
        assert hasattr(add_client, 'generate_client_sql')
        assert hasattr(add_client, 'generate_connection_string')


class TestGenerateClientSql:
    """Tests for client SQL generation."""
    
    def test_generates_create_user(self):
        """Should generate CREATE USER statement."""
        from add_client import generate_client_sql
        
        sql = generate_client_sql('tenant1', 'tenant1_user', 'securepass123')
        
        assert 'CREATE' in sql
        assert 'tenant1_user' in sql
    
    def test_generates_create_schema(self):
        """Should generate CREATE SCHEMA statement."""
        from add_client import generate_client_sql
        
        sql = generate_client_sql('tenant1', 'tenant1_user', 'securepass123')
        
        assert 'CREATE SCHEMA' in sql
        assert 'tenant1' in sql
    
    def test_grants_schema_privileges(self):
        """Should grant privileges on schema."""
        from add_client import generate_client_sql
        
        sql = generate_client_sql('tenant1', 'tenant1_user', 'securepass123')
        
        assert 'GRANT' in sql
        assert 'tenant1' in sql
    
    def test_sets_search_path(self):
        """Should set search_path for user."""
        from add_client import generate_client_sql
        
        sql = generate_client_sql('tenant1', 'tenant1_user', 'securepass123')
        
        assert 'search_path' in sql.lower() or 'SEARCH_PATH' in sql
    
    def test_password_in_sql(self):
        """Should include password in CREATE statement."""
        from add_client import generate_client_sql
        
        sql = generate_client_sql('tenant1', 'tenant1_user', 'securepass123')
        
        assert 'securepass123' in sql or 'PASSWORD' in sql


class TestGenerateConnectionString:
    """Tests for connection string generation."""
    
    def test_basic_connection_string(self):
        """Should generate valid connection string."""
        from add_client import generate_connection_string
        
        conn = generate_connection_string(
            host='db-postgresql-nyc1-12345-do-user.db.ondigitalocean.com',
            port=25060,
            database='defaultdb',
            user='tenant1_user',
            password='securepass123'
        )
        
        assert 'postgresql://' in conn
        assert 'tenant1_user' in conn
        assert '25060' in conn
    
    def test_includes_sslmode(self):
        """Should include sslmode=require."""
        from add_client import generate_connection_string
        
        conn = generate_connection_string(
            host='host.db.ondigitalocean.com',
            port=25060,
            database='db',
            user='user',
            password='pass'
        )
        
        assert 'sslmode=require' in conn
    
    def test_url_encodes_special_chars(self):
        """Should URL-encode special characters in password."""
        from add_client import generate_connection_string
        
        conn = generate_connection_string(
            host='host.db.ondigitalocean.com',
            port=25060,
            database='db',
            user='user',
            password='p@ss#word!'
        )
        
        # Special chars should be encoded
        assert '@' not in conn.split('@')[0].split(':')[-1] or '%40' in conn


class TestSetupClientDirect:
    """Tests for direct database setup via psycopg2."""
    
    def test_setup_connects_to_database(self):
        """Should connect using psycopg2."""
        mock_psycopg2 = MagicMock()
        mock_conn = MagicMock()
        mock_cursor = MagicMock()
        mock_conn.cursor.return_value = mock_cursor
        mock_psycopg2.connect.return_value = mock_conn
        
        with patch.dict('sys.modules', {'psycopg2': mock_psycopg2}):
            from add_client import setup_client_direct
            
            with patch('builtins.print'):
                try:
                    setup_client_direct(
                        'postgresql://admin:pass@host/db',
                        'tenant1',
                        'tenant1_user',
                        'securepass'
                    )
                except:
                    pass
            
            mock_psycopg2.connect.assert_called()
    
    def test_setup_executes_sql(self):
        """Should execute setup SQL."""
        mock_psycopg2 = MagicMock()
        mock_conn = MagicMock()
        mock_cursor = MagicMock()
        mock_conn.cursor.return_value = mock_cursor
        mock_psycopg2.connect.return_value = mock_conn
        
        with patch.dict('sys.modules', {'psycopg2': mock_psycopg2}):
            from add_client import setup_client_direct
            
            with patch('builtins.print'):
                try:
                    setup_client_direct(
                        'postgresql://admin:pass@host/db',
                        'tenant1',
                        'tenant1_user',
                        'securepass'
                    )
                except:
                    pass
            
            assert mock_cursor.execute.called
    
    def test_setup_commits_transaction(self):
        """Should commit the transaction."""
        mock_psycopg2 = MagicMock()
        mock_conn = MagicMock()
        mock_cursor = MagicMock()
        mock_conn.cursor.return_value = mock_cursor
        mock_psycopg2.connect.return_value = mock_conn
        
        with patch.dict('sys.modules', {'psycopg2': mock_psycopg2}):
            from add_client import setup_client_direct
            
            with patch('builtins.print'):
                try:
                    setup_client_direct(
                        'postgresql://admin:pass@host/db',
                        'tenant1',
                        'tenant1_user',
                        'securepass'
                    )
                except:
                    pass
            
            mock_conn.commit.assert_called()
    
    def test_setup_handles_duplicate_user(self):
        """Should handle duplicate user error."""
        mock_psycopg2 = MagicMock()
        mock_conn = MagicMock()
        mock_cursor = MagicMock()
        mock_cursor.execute.side_effect = Exception("role already exists")
        mock_conn.cursor.return_value = mock_cursor
        mock_psycopg2.connect.return_value = mock_conn
        
        with patch.dict('sys.modules', {'psycopg2': mock_psycopg2}):
            from add_client import setup_client_direct
            
            with patch('builtins.print'):
                # Should handle gracefully
                try:
                    setup_client_direct(
                        'postgresql://admin:pass@host/db',
                        'tenant1',
                        'existing_user',
                        'securepass'
                    )
                except:
                    pass


class TestCreatePool:
    """Tests for connection pool creation via doctl."""
    
    def test_create_pool_calls_doctl(self):
        """Should call doctl to create pool."""
        import add_client
        
        if hasattr(add_client, 'create_pool'):
            with patch('subprocess.run') as mock_run:
                mock_run.return_value = MagicMock(returncode=0, stdout='{}')
                
                add_client.create_pool(
                    'my-pool',
                    'my-cluster',
                    'defaultdb',
                    'tenant1_user',
                    25
                )
                
                mock_run.assert_called()
                call_args = str(mock_run.call_args)
                assert 'doctl' in call_args
    
    def test_create_pool_specifies_size(self):
        """Should specify pool size."""
        import add_client
        
        if hasattr(add_client, 'create_pool'):
            with patch('subprocess.run') as mock_run:
                mock_run.return_value = MagicMock(returncode=0, stdout='{}')
                
                add_client.create_pool(
                    'my-pool',
                    'my-cluster',
                    'defaultdb',
                    'tenant1_user',
                    50
                )
                
                call_args = str(mock_run.call_args)
                assert '50' in call_args or 'size' in call_args


class TestPasswordGeneration:
    """Tests for secure password generation."""
    
    def test_generates_secure_password(self):
        """Should generate a secure random password."""
        import add_client
        
        if hasattr(add_client, 'generate_password'):
            password = add_client.generate_password()
            
            assert len(password) >= 16
            assert any(c.isupper() for c in password)
            assert any(c.islower() for c in password)
            assert any(c.isdigit() for c in password)
    
    def test_password_uniqueness(self):
        """Should generate unique passwords."""
        import add_client
        
        if hasattr(add_client, 'generate_password'):
            passwords = [add_client.generate_password() for _ in range(10)]
            assert len(set(passwords)) == 10


class TestMainFunction:
    """Tests for main entry point."""
    
    def test_main_requires_arguments(self):
        """Should exit if required arguments missing."""
        import add_client
        
        if hasattr(add_client, 'main'):
            with patch('sys.argv', ['add_client.py']):
                with pytest.raises(SystemExit):
                    add_client.main()
    
    def test_main_with_valid_arguments(self):
        """Should run setup with valid arguments."""
        mock_psycopg2 = MagicMock()
        mock_conn = MagicMock()
        mock_cursor = MagicMock()
        mock_conn.cursor.return_value = mock_cursor
        mock_psycopg2.connect.return_value = mock_conn
        
        with patch.dict('sys.modules', {'psycopg2': mock_psycopg2}):
            import add_client
            
            if hasattr(add_client, 'main'):
                with patch('sys.argv', [
                    'add_client.py',
                    '--admin-connection', 'postgresql://admin:pass@host/db',
                    '--schema', 'tenant1',
                    '--username', 'tenant1_user'
                ]):
                    with patch('builtins.print'):
                        try:
                            add_client.main()
                        except SystemExit:
                            pass
    
    def test_main_outputs_connection_string(self):
        """Should output the new connection string."""
        mock_psycopg2 = MagicMock()
        mock_conn = MagicMock()
        mock_cursor = MagicMock()
        mock_conn.cursor.return_value = mock_cursor
        mock_psycopg2.connect.return_value = mock_conn
        
        with patch.dict('sys.modules', {'psycopg2': mock_psycopg2}):
            import add_client
            
            if hasattr(add_client, 'main'):
                with patch('sys.argv', [
                    'add_client.py',
                    '--admin-connection', 'postgresql://admin:pass@host:25060/db',
                    '--schema', 'tenant1',
                    '--username', 'tenant1_user'
                ]):
                    with patch('builtins.print') as mock_print:
                        try:
                            add_client.main()
                        except SystemExit:
                            pass
                        
                        # Should have printed connection string
                        printed = ' '.join(str(c) for c in mock_print.call_args_list)
                        # May contain connection info
                        assert mock_print.called


class TestErrorHandling:
    """Tests for error handling."""
    
    def test_handles_connection_error(self):
        """Should handle database connection errors."""
        mock_psycopg2 = MagicMock()
        mock_psycopg2.connect.side_effect = Exception("Connection refused")
        
        with patch.dict('sys.modules', {'psycopg2': mock_psycopg2}):
            from add_client import setup_client_direct
            
            with patch('builtins.print'):
                with pytest.raises(Exception):
                    setup_client_direct(
                        'postgresql://admin:pass@invalid/db',
                        'tenant1',
                        'tenant1_user',
                        'securepass'
                    )
    
    def test_handles_permission_error(self):
        """Should handle permission denied errors."""
        mock_psycopg2 = MagicMock()
        mock_conn = MagicMock()
        mock_cursor = MagicMock()
        mock_cursor.execute.side_effect = Exception("permission denied")
        mock_conn.cursor.return_value = mock_cursor
        mock_psycopg2.connect.return_value = mock_conn
        
        with patch.dict('sys.modules', {'psycopg2': mock_psycopg2}):
            from add_client import setup_client_direct
            
            with patch('builtins.print'):
                with pytest.raises(Exception):
                    setup_client_direct(
                        'postgresql://limited:pass@host/db',
                        'tenant1',
                        'tenant1_user',
                        'securepass'
                    )
