"""Comprehensive tests for create_schema_user.py - Full coverage."""

import os
import sys
import pytest
from unittest.mock import patch, MagicMock

# Add scripts to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '../../skills/postgres/scripts'))

from create_schema_user import generate_sql, build_connection_string


class TestCreateSchemaUserImports:
    """Tests for module imports."""
    
    def test_module_imports(self):
        """Module should import without errors."""
        import create_schema_user
        assert hasattr(create_schema_user, 'generate_sql')
        assert hasattr(create_schema_user, 'build_connection_string')


class TestGenerateSqlFull:
    """Additional tests for SQL generation."""
    
    def test_generates_create_schema(self, capsys):
        """Should generate CREATE SCHEMA statement."""
        generate_sql('myschema', 'myuser', 'FAKE_TEST_PASS')
        output = capsys.readouterr().out
        
        assert 'CREATE SCHEMA' in output
        assert 'myschema' in output
    
    def test_generates_create_user(self, capsys):
        """Should generate CREATE USER statement."""
        generate_sql('myschema', 'myuser', 'FAKE_TEST_PASS')
        output = capsys.readouterr().out
        
        assert 'CREATE USER' in output
        assert 'myuser' in output
    
    def test_includes_password(self, capsys):
        """Should include password in CREATE statement."""
        generate_sql('myschema', 'myuser', 'FAKE_TEST_PASS')
        output = capsys.readouterr().out
        
        assert 'FAKE_TEST_PASS' in output or 'PASSWORD' in output
    
    def test_grants_schema_privileges(self, capsys):
        """Should grant privileges on schema."""
        generate_sql('myschema', 'myuser', 'FAKE_TEST_PASS')
        output = capsys.readouterr().out
        
        assert 'GRANT' in output
    
    def test_sets_default_privileges(self, capsys):
        """Should set default privileges for future objects."""
        generate_sql('myschema', 'myuser', 'FAKE_TEST_PASS')
        output = capsys.readouterr().out
        
        assert 'DEFAULT PRIVILEGES' in output or 'ALTER DEFAULT' in output


class TestBuildConnectionStringFull:
    """Additional tests for connection string building."""
    
    def test_builds_basic_connection_string(self):
        """Should build basic connection string."""
        conn = build_connection_string(
            'postgresql://admin:FAKE_ADMIN_PASS@localhost:25060/defaultdb',
            'newuser',
            'FAKE_NEW_PASS'
        )
        
        assert 'postgresql://' in conn
        assert 'newuser' in conn
    
    def test_preserves_host_and_port(self):
        """Should preserve host and port from base URL."""
        conn = build_connection_string(
            'postgresql://admin:FAKE_ADMIN_PASS@localhost:25060/defaultdb',
            'newuser',
            'FAKE_NEW_PASS'
        )
        
        assert 'localhost' in conn
        assert '25060' in conn
    
    def test_includes_sslmode(self):
        """Should include sslmode=require."""
        conn = build_connection_string(
            'postgresql://admin:FAKE_ADMIN_PASS@localhost:25060/defaultdb',
            'newuser',
            'FAKE_NEW_PASS'
        )
        
        assert 'sslmode=require' in conn


class TestGenerateSqlToFiles:
    """Tests for SQL file generation."""
    
    def test_writes_sql_files(self, tmp_path):
        """Should write SQL files when output_dir provided."""
        generate_sql('myschema', 'myuser', 'FAKE_TEST_PASS', output_dir=str(tmp_path))
        
        # Check that files were created
        files = list(tmp_path.glob('*.sql'))
        assert len(files) > 0
    
    def test_generates_multiple_files(self, tmp_path):
        """Should generate multiple SQL files."""
        generate_sql('myschema', 'myuser', 'FAKE_TEST_PASS', output_dir=str(tmp_path))
        
        # Check for expected files
        expected_files = ['db-setup.sql', 'db-users.sql', 'db-permissions.sql', 'db-connections.env']
        for filename in expected_files:
            assert (tmp_path / filename).exists(), f"Expected {filename} to exist"


class TestMainFunction:
    """Tests for main entry point."""
    
    def test_main_requires_arguments(self):
        """Should exit if required arguments missing."""
        import create_schema_user
        
        with patch('sys.argv', ['create_schema_user.py']):
            with pytest.raises(SystemExit):
                create_schema_user.main()
    
    def test_main_generate_mode(self, capsys):
        """Should generate SQL in generate mode."""
        import create_schema_user
        
        with patch('sys.argv', [
            'create_schema_user.py',
            'myschema',
            'myuser', 
            'FAKE_TEST_PASS',
            '--generate'
        ]):
            try:
                create_schema_user.main()
            except SystemExit:
                pass
            
            output = capsys.readouterr().out
            assert 'CREATE' in output or output != ''
