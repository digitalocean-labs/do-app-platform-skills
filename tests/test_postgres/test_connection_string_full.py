"""Comprehensive tests for generate_connection_string.py - Full coverage."""

import os
import sys
import pytest
from unittest.mock import patch, MagicMock
from io import StringIO

# Add scripts to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '../../skills/postgres/scripts'))


class TestConnectionStringImports:
    """Tests for module imports."""
    
    def test_module_imports(self):
        """Module should import without errors."""
        import generate_connection_string
        assert hasattr(generate_connection_string, 'generate_connection_strings')
        assert hasattr(generate_connection_string, 'main')


class TestGenerateConnectionStrings:
    """Tests for connection string generation."""
    
    def test_basic_connection_string(self):
        """Should generate basic connection string output."""
        from generate_connection_string import generate_connection_strings
        
        with patch('builtins.print') as mock_print:
            generate_connection_strings(
                base_url='postgresql://doadmin:adminpass@db-host.ondigitalocean.com:25060/defaultdb?sslmode=require',  # ggshield-ignore-line
                username='testuser',
                password='testpassword123'
            )
        
        # Verify print was called
        assert mock_print.called
        printed_output = ' '.join(str(call) for call in mock_print.call_args_list)
        assert 'testuser' in printed_output
    
    def test_includes_sslmode(self):
        """Should include sslmode in connection string."""
        from generate_connection_string import generate_connection_strings
        
        with patch('builtins.print') as mock_print:
            generate_connection_strings(
                base_url='postgresql://doadmin:pass@host:25060/db?sslmode=require',  # ggshield-ignore-line
                username='user',
                password='pass'
            )
        
        printed_output = ' '.join(str(call) for call in mock_print.call_args_list)
        assert 'sslmode=require' in printed_output
    
    def test_url_encodes_password(self):
        """Should URL-encode special characters in password."""
        from generate_connection_string import generate_connection_strings
        
        with patch('builtins.print') as mock_print:
            generate_connection_strings(
                base_url='postgresql://doadmin:pass@host:25060/db?sslmode=require',  # ggshield-ignore-line
                username='user',
                password='p@ss:word/with?special&chars='
            )
        
        printed_output = ' '.join(str(call) for call in mock_print.call_args_list)
        # URL-encoded special characters should appear
        assert '%40' in printed_output or '%3A' in printed_output or '%2F' in printed_output
    
    def test_custom_schema(self):
        """Should support custom schema in search_path."""
        from generate_connection_string import generate_connection_strings
        
        with patch('builtins.print') as mock_print:
            generate_connection_strings(
                base_url='postgresql://doadmin:pass@host:25060/db?sslmode=require',  # ggshield-ignore-line
                username='user',
                password='pass',
                schema='myschema'
            )
        
        printed_output = ' '.join(str(call) for call in mock_print.call_args_list)
        assert 'myschema' in printed_output


class TestConnectionStringFormats:
    """Tests for different connection string format outputs."""
    
    def test_outputs_env_vars(self):
        """Should output environment variable format."""
        from generate_connection_string import generate_connection_strings
        
        with patch('builtins.print') as mock_print:
            generate_connection_strings(
                base_url='postgresql://doadmin:pass@host.db.ondigitalocean.com:25060/db?sslmode=require',  # ggshield-ignore-line
                username='user',
                password='pass'
            )
        
        printed_output = ' '.join(str(call) for call in mock_print.call_args_list)
        assert 'DATABASE_URL' in printed_output
        assert 'DB_HOST' in printed_output
        assert 'DB_PORT' in printed_output
    
    def test_outputs_psql_command(self):
        """Should output psql command."""
        from generate_connection_string import generate_connection_strings
        
        with patch('builtins.print') as mock_print:
            generate_connection_strings(
                base_url='postgresql://doadmin:pass@host:25060/db?sslmode=require',  # ggshield-ignore-line
                username='user',
                password='pass'
            )
        
        printed_output = ' '.join(str(call) for call in mock_print.call_args_list)
        assert 'psql' in printed_output
    
    def test_outputs_prisma_format(self):
        """Should output Prisma format."""
        from generate_connection_string import generate_connection_strings
        
        with patch('builtins.print') as mock_print:
            generate_connection_strings(
                base_url='postgresql://doadmin:pass@host:25060/db?sslmode=require',  # ggshield-ignore-line
                username='user',
                password='pass'
            )
        
        printed_output = ' '.join(str(call) for call in mock_print.call_args_list)
        assert 'Prisma' in printed_output
    
    def test_outputs_sqlalchemy_format(self):
        """Should output SQLAlchemy format."""
        from generate_connection_string import generate_connection_strings
        
        with patch('builtins.print') as mock_print:
            generate_connection_strings(
                base_url='postgresql://doadmin:pass@host:25060/db?sslmode=require',  # ggshield-ignore-line
                username='user',
                password='pass'
            )
        
        printed_output = ' '.join(str(call) for call in mock_print.call_args_list)
        assert 'SQLAlchemy' in printed_output


class TestEdgeCases:
    """Tests for edge cases."""
    
    def test_handles_default_port(self):
        """Should handle URLs without explicit port."""
        from generate_connection_string import generate_connection_strings
        
        with patch('builtins.print') as mock_print:
            # URL without port should default to 25060
            generate_connection_strings(
                base_url='postgresql://doadmin:pass@host/db?sslmode=require',  # ggshield-ignore-line
                username='user',
                password='pass'
            )
        
        printed_output = ' '.join(str(call) for call in mock_print.call_args_list)
        assert '25060' in printed_output
    
    def test_handles_default_database(self):
        """Should handle URLs without database name."""
        from generate_connection_string import generate_connection_strings
        
        with patch('builtins.print') as mock_print:
            generate_connection_strings(
                base_url='postgresql://doadmin:pass@host:25060/?sslmode=require',  # ggshield-ignore-line
                username='user',
                password='pass'
            )
        
        printed_output = ' '.join(str(call) for call in mock_print.call_args_list)
        assert 'defaultdb' in printed_output
    
    def test_handles_missing_sslmode(self):
        """Should default sslmode to require if not specified."""
        from generate_connection_string import generate_connection_strings
        
        with patch('builtins.print') as mock_print:
            generate_connection_strings(
                base_url='postgresql://doadmin:pass@host:25060/db',  # ggshield-ignore-line
                username='user',
                password='pass'
            )
        
        printed_output = ' '.join(str(call) for call in mock_print.call_args_list)
        assert 'sslmode=require' in printed_output


class TestMainFunction:
    """Tests for main entry point."""
    
    def test_main_requires_arguments(self):
        """Should exit if required arguments missing."""
        import generate_connection_string
        
        with patch('sys.argv', ['generate_connection_string.py']):
            with pytest.raises(SystemExit):
                generate_connection_string.main()
    
    def test_main_with_valid_arguments(self):
        """Should run with valid arguments."""
        import generate_connection_string
        
        with patch('sys.argv', [
            'generate_connection_string.py',
            'postgresql://doadmin:pass@host:25060/db?sslmode=require',  # ggshield-ignore-line
            'testuser',
            'testpassword123'
        ]):
            with patch('builtins.print') as mock_print:
                generate_connection_string.main()
                
                printed_output = ' '.join(str(call) for call in mock_print.call_args_list)
                assert 'testuser' in printed_output
    
    def test_main_with_schema_argument(self):
        """Should accept schema argument."""
        import generate_connection_string
        
        with patch('sys.argv', [
            'generate_connection_string.py',
            'postgresql://doadmin:pass@host:25060/db?sslmode=require',  # ggshield-ignore-line
            'testuser',
            'testpassword123',
            '--schema', 'myschema'
        ]):
            with patch('builtins.print') as mock_print:
                generate_connection_string.main()
                
                printed_output = ' '.join(str(call) for call in mock_print.call_args_list)
                assert 'myschema' in printed_output


class TestDOConnectionString:
    """Tests specific to DigitalOcean database connection strings."""
    
    def test_do_managed_database_format(self):
        """Should handle DO managed database format."""
        from generate_connection_string import generate_connection_strings
        
        with patch('builtins.print') as mock_print:
            generate_connection_strings(
                base_url='postgresql://doadmin:adminpass@db-postgresql-nyc1-12345-do-user-123456-0.b.db.ondigitalocean.com:25060/defaultdb?sslmode=require',  # ggshield-ignore-line
                username='myapp_user',
                password='FAKE_TEST_PASSWORD_12345'
            )
        
        printed_output = ' '.join(str(call) for call in mock_print.call_args_list)
        assert 'postgresql://' in printed_output
        assert 'myapp_user' in printed_output
    
    def test_preserves_do_host(self):
        """Should preserve the DO hostname."""
        from generate_connection_string import generate_connection_strings
        
        with patch('builtins.print') as mock_print:
            generate_connection_strings(
                base_url='postgresql://doadmin:pass@my-db-host.db.ondigitalocean.com:25060/db?sslmode=require',  # ggshield-ignore-line
                username='user',
                password='pass'
            )
        
        printed_output = ' '.join(str(call) for call in mock_print.call_args_list)
        assert 'my-db-host.db.ondigitalocean.com' in printed_output
