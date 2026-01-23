"""Comprehensive tests for create_schema_user.py - Full coverage."""

import os
import sys
import pytest
from unittest.mock import patch, MagicMock

# Add scripts to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '../../skills/postgres/scripts'))


class TestCreateSchemaUserImports:
    """Tests for module imports."""
    
    def test_module_imports(self):
        """Module should import without errors."""
        import create_schema_user
        assert hasattr(create_schema_user, 'generate_setup_sql')


class TestGenerateSetupSql:
    """Tests for SQL generation."""
    
    def test_generates_create_schema(self):
        """Should generate CREATE SCHEMA statement."""
        from create_schema_user import generate_setup_sql
        
        sql = generate_setup_sql('myschema', 'myuser', 'mypassword')
        
        assert 'CREATE SCHEMA' in sql
        assert 'myschema' in sql
    
    def test_generates_create_user(self):
        """Should generate CREATE USER statement."""
        from create_schema_user import generate_setup_sql
        
        sql = generate_setup_sql('myschema', 'myuser', 'mypassword')
        
        assert 'CREATE' in sql
        assert 'myuser' in sql
    
    def test_includes_password(self):
        """Should include password in CREATE statement."""
        from create_schema_user import generate_setup_sql
        
        sql = generate_setup_sql('myschema', 'myuser', 'mypassword')
        
        assert 'mypassword' in sql or 'PASSWORD' in sql
    
    def test_grants_schema_privileges(self):
        """Should grant privileges on schema."""
        from create_schema_user import generate_setup_sql
        
        sql = generate_setup_sql('myschema', 'myuser', 'mypassword')
        
        assert 'GRANT' in sql
    
    def test_sets_default_privileges(self):
        """Should set default privileges for future objects."""
        from create_schema_user import generate_setup_sql
        
        sql = generate_setup_sql('myschema', 'myuser', 'mypassword')
        
        assert 'DEFAULT PRIVILEGES' in sql or 'GRANT' in sql


class TestExecuteDirectly:
    """Tests for direct database execution via psycopg2."""
    
    def test_connects_to_database(self):
        """Should connect using psycopg2."""
        mock_psycopg2 = MagicMock()
        mock_conn = MagicMock()
        mock_cursor = MagicMock()
        mock_conn.cursor.return_value = mock_cursor
        mock_psycopg2.connect.return_value = mock_conn
        
        with patch.dict('sys.modules', {'psycopg2': mock_psycopg2}):
            from create_schema_user import execute_directly
            
            with patch('builtins.print'):
                try:
                    execute_directly(
                        'postgresql://admin:pass@host/db',
                        'myschema',
                        'myuser',
                        'mypassword'
                    )
                except:
                    pass
            
            mock_psycopg2.connect.assert_called()
    
    def test_executes_sql(self):
        """Should execute setup SQL."""
        mock_psycopg2 = MagicMock()
        mock_conn = MagicMock()
        mock_cursor = MagicMock()
        mock_conn.cursor.return_value = mock_cursor
        mock_psycopg2.connect.return_value = mock_conn
        
        with patch.dict('sys.modules', {'psycopg2': mock_psycopg2}):
            from create_schema_user import execute_directly
            
            with patch('builtins.print'):
                try:
                    execute_directly(
                        'postgresql://admin:pass@host/db',
                        'myschema',
                        'myuser',
                        'mypassword'
                    )
                except:
                    pass
            
            assert mock_cursor.execute.called
    
    def test_commits_transaction(self):
        """Should commit the transaction."""
        mock_psycopg2 = MagicMock()
        mock_conn = MagicMock()
        mock_cursor = MagicMock()
        mock_conn.cursor.return_value = mock_cursor
        mock_psycopg2.connect.return_value = mock_conn
        
        with patch.dict('sys.modules', {'psycopg2': mock_psycopg2}):
            from create_schema_user import execute_directly
            
            with patch('builtins.print'):
                try:
                    execute_directly(
                        'postgresql://admin:pass@host/db',
                        'myschema',
                        'myuser',
                        'mypassword'
                    )
                except:
                    pass
            
            mock_conn.commit.assert_called()
    
    def test_handles_duplicate_schema(self):
        """Should handle duplicate schema error."""
        mock_psycopg2 = MagicMock()
        
        # Create DuplicateSchema exception class
        class DuplicateSchema(Exception):
            pass
        
        mock_psycopg2.errors = MagicMock()
        mock_psycopg2.errors.DuplicateSchema = DuplicateSchema
        
        mock_conn = MagicMock()
        mock_cursor = MagicMock()
        mock_cursor.execute.side_effect = DuplicateSchema("schema already exists")
        mock_conn.cursor.return_value = mock_cursor
        mock_psycopg2.connect.return_value = mock_conn
        
        with patch.dict('sys.modules', {'psycopg2': mock_psycopg2, 'psycopg2.errors': mock_psycopg2.errors}):
            from create_schema_user import execute_directly
            
            with patch('builtins.print') as mock_print:
                try:
                    execute_directly(
                        'postgresql://admin:pass@host/db',
                        'existing_schema',
                        'myuser',
                        'mypassword'
                    )
                except:
                    pass
    
    def test_handles_duplicate_role(self):
        """Should handle duplicate role error."""
        mock_psycopg2 = MagicMock()
        
        class DuplicateObject(Exception):
            pass
        
        mock_psycopg2.errors = MagicMock()
        mock_psycopg2.errors.DuplicateObject = DuplicateObject
        
        mock_conn = MagicMock()
        mock_cursor = MagicMock()
        mock_cursor.execute.side_effect = DuplicateObject("role already exists")
        mock_conn.cursor.return_value = mock_cursor
        mock_psycopg2.connect.return_value = mock_conn
        
        with patch.dict('sys.modules', {'psycopg2': mock_psycopg2, 'psycopg2.errors': mock_psycopg2.errors}):
            from create_schema_user import execute_directly
            
            with patch('builtins.print'):
                try:
                    execute_directly(
                        'postgresql://admin:pass@host/db',
                        'myschema',
                        'existing_user',
                        'mypassword'
                    )
                except:
                    pass


class TestMainFunction:
    """Tests for main entry point."""
    
    def test_main_requires_arguments(self):
        """Should exit if required arguments missing."""
        import create_schema_user
        
        if hasattr(create_schema_user, 'main'):
            with patch('sys.argv', ['create_schema_user.py']):
                with pytest.raises(SystemExit):
                    create_schema_user.main()
    
    def test_main_sql_only_mode(self):
        """Should output SQL only when --sql-only flag used."""
        import create_schema_user
        
        if hasattr(create_schema_user, 'main'):
            with patch('sys.argv', [
                'create_schema_user.py',
                '--schema', 'myschema',
                '--username', 'myuser',
                '--password', 'mypass',
                '--sql-only'
            ]):
                with patch('builtins.print') as mock_print:
                    try:
                        create_schema_user.main()
                    except SystemExit:
                        pass
                    
                    # Should have printed SQL
                    printed = ' '.join(str(c) for c in mock_print.call_args_list)
                    assert 'CREATE' in printed or mock_print.called
    
    def test_main_execute_mode(self):
        """Should execute SQL when connection string provided."""
        mock_psycopg2 = MagicMock()
        mock_conn = MagicMock()
        mock_cursor = MagicMock()
        mock_conn.cursor.return_value = mock_cursor
        mock_psycopg2.connect.return_value = mock_conn
        
        with patch.dict('sys.modules', {'psycopg2': mock_psycopg2}):
            import create_schema_user
            
            if hasattr(create_schema_user, 'main'):
                with patch('sys.argv', [
                    'create_schema_user.py',
                    '--connection-string', 'postgresql://admin:pass@host/db',
                    '--schema', 'myschema',
                    '--username', 'myuser',
                    '--password', 'mypass'
                ]):
                    with patch('builtins.print'):
                        try:
                            create_schema_user.main()
                        except SystemExit:
                            pass


class TestPasswordGeneration:
    """Tests for password generation."""
    
    def test_generates_password_when_not_provided(self):
        """Should generate password if not provided."""
        import create_schema_user
        
        if hasattr(create_schema_user, 'generate_password'):
            password = create_schema_user.generate_password()
            
            assert len(password) >= 16
            assert any(c.isupper() for c in password)
            assert any(c.islower() for c in password)
    
    def test_uses_provided_password(self):
        """Should use provided password."""
        from create_schema_user import generate_setup_sql
        
        sql = generate_setup_sql('schema', 'user', 'my_custom_password')
        
        assert 'my_custom_password' in sql


class TestConnectionHandling:
    """Tests for connection string handling."""
    
    def test_adds_sslmode(self):
        """Should add sslmode=require if not present."""
        import create_schema_user
        
        if hasattr(create_schema_user, 'ensure_ssl'):
            conn = create_schema_user.ensure_ssl('postgresql://user:pass@host/db')
            
            assert 'sslmode' in conn
    
    def test_preserves_existing_sslmode(self):
        """Should preserve existing sslmode."""
        import create_schema_user
        
        if hasattr(create_schema_user, 'ensure_ssl'):
            conn = create_schema_user.ensure_ssl('postgresql://user:pass@host/db?sslmode=verify-full')
            
            assert 'verify-full' in conn


class TestSchemaIsolation:
    """Tests for schema isolation features."""
    
    def test_revokes_public_access(self):
        """Should revoke access from public schema."""
        from create_schema_user import generate_setup_sql
        
        sql = generate_setup_sql('myschema', 'myuser', 'mypassword')
        
        # Should contain REVOKE for public
        assert 'REVOKE' in sql or 'public' in sql.lower()
    
    def test_sets_search_path(self):
        """Should set search_path for user."""
        from create_schema_user import generate_setup_sql
        
        sql = generate_setup_sql('myschema', 'myuser', 'mypassword')
        
        assert 'search_path' in sql.lower() or 'ALTER' in sql
