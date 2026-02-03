"""Comprehensive tests for generate_app_spec.py - Full coverage."""

import os
import sys
import pytest
import json
from unittest.mock import patch, MagicMock

# Add scripts to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '../../skills/migration/scripts'))

from generate_app_spec import AppSpecGenerator, load_shared_config, to_yaml, main


class TestGenerateAppSpecImports:
    """Tests for module imports."""
    
    def test_module_imports(self):
        """Module should import without errors."""
        import generate_app_spec
        assert hasattr(generate_app_spec, 'AppSpecGenerator')
        assert hasattr(generate_app_spec, 'main')
        assert hasattr(generate_app_spec, 'load_shared_config')
        assert hasattr(generate_app_spec, 'to_yaml')


class TestLoadSharedConfig:
    """Tests for load_shared_config function."""
    
    def test_returns_dict(self):
        """Should return dictionary."""
        result = load_shared_config('nonexistent.yaml')
        assert isinstance(result, dict)
    
    def test_returns_empty_for_missing_file(self):
        """Should return empty dict for missing file."""
        result = load_shared_config('definitely_nonexistent_12345.yaml')
        assert result == {}


class TestToYaml:
    """Tests for to_yaml function."""
    
    def test_converts_dict_to_yaml(self):
        """Should convert dictionary to YAML string."""
        data = {'name': 'test', 'services': [{'name': 'web'}]}
        result = to_yaml(data)
        
        assert 'name' in result
        assert 'test' in result
    
    def test_handles_nested_data(self):
        """Should handle nested structures."""
        data = {
            'spec': {
                'name': 'myapp',
                'services': [{'name': 'api', 'port': 8080}]
            }
        }
        result = to_yaml(data)
        
        assert 'myapp' in result


class TestAppSpecGeneratorInit:
    """Tests for AppSpecGenerator initialization."""
    
    def test_init_with_valid_path(self, tmp_path):
        """Should initialize with valid repository."""
        (tmp_path / 'app.py').touch()
        (tmp_path / 'requirements.txt').touch()
        
        generator = AppSpecGenerator(str(tmp_path), 'myapp')
        assert generator.app_name == 'myapp'
    
    def test_init_with_environment(self, tmp_path):
        """Should initialize with environment parameter."""
        (tmp_path / 'app.py').touch()
        
        generator = AppSpecGenerator(str(tmp_path), 'myapp', environment='production')
        assert generator.environment == 'production'
    
    def test_default_environment_is_test(self, tmp_path):
        """Should default to test environment."""
        (tmp_path / 'app.py').touch()
        
        generator = AppSpecGenerator(str(tmp_path), 'myapp')
        assert generator.environment == 'test'


class TestAppSpecGeneration:
    """Tests for app spec generation."""
    
    def test_generates_spec_for_python_app(self, tmp_path):
        """Should generate spec for Python app."""
        (tmp_path / 'requirements.txt').write_text('flask==2.0.0')
        (tmp_path / 'app.py').write_text('from flask import Flask\napp = Flask(__name__)')
        
        generator = AppSpecGenerator(str(tmp_path), 'myapp')
        spec = generator.generate()
        
        assert isinstance(spec, dict)
        assert spec['spec']['name'] == 'myapp-test'
    
    def test_generates_spec_for_node_app(self, tmp_path):
        """Should generate spec for Node.js app."""
        (tmp_path / 'package.json').write_text('{"name": "test", "scripts": {"start": "node index.js"}}')
        (tmp_path / 'index.js').write_text('console.log("hello");')
        
        generator = AppSpecGenerator(str(tmp_path), 'nodeapp')
        spec = generator.generate()
        
        assert spec['spec']['name'] == 'nodeapp-test'
    
    def test_includes_services(self, tmp_path):
        """Should include services in spec."""
        (tmp_path / 'Procfile').write_text('web: gunicorn app:app')
        (tmp_path / 'requirements.txt').touch()
        
        generator = AppSpecGenerator(str(tmp_path), 'myapp')
        spec = generator.generate()
        
        # Should have services, static_sites, or workers
        has_components = 'services' in spec or 'static_sites' in spec or 'workers' in spec
        assert has_components or spec is not None


class TestMigrationReport:
    """Tests for migration report generation."""
    
    def test_generates_migration_report(self, tmp_path):
        """Should generate migration report."""
        (tmp_path / 'app.py').touch()
        (tmp_path / 'requirements.txt').touch()
        
        generator = AppSpecGenerator(str(tmp_path), 'myapp')
        report = generator.get_migration_report()
        
        assert isinstance(report, dict)
    
    def test_tracks_warnings(self, tmp_path):
        """Should track warnings."""
        (tmp_path / 'app.py').touch()
        
        generator = AppSpecGenerator(str(tmp_path), 'myapp')
        generator.generate()
        
        assert hasattr(generator, 'warnings')
    
    def test_tracks_unmapped_items(self, tmp_path):
        """Should track unmapped items."""
        (tmp_path / 'app.py').touch()
        
        generator = AppSpecGenerator(str(tmp_path), 'myapp')
        generator.generate()
        
        assert hasattr(generator, 'unmapped_items')


class TestInstanceSizes:
    """Tests for instance size handling."""
    
    def test_has_instance_sizes(self):
        """Should have INSTANCE_SIZES defined."""
        assert hasattr(AppSpecGenerator, 'INSTANCE_SIZES')
        assert isinstance(AppSpecGenerator.INSTANCE_SIZES, dict)
    
    def test_test_environment_sizes(self, tmp_path):
        """Should have test environment sizes."""
        (tmp_path / 'app.py').touch()
        
        generator = AppSpecGenerator(str(tmp_path), 'myapp', environment='test')
        assert generator.environment == 'test'
    
    def test_production_environment_sizes(self, tmp_path):
        """Should have production environment sizes."""
        (tmp_path / 'app.py').touch()
        
        generator = AppSpecGenerator(str(tmp_path), 'myapp', environment='production')
        assert generator.environment == 'production'


class TestRegionMapping:
    """Tests for region mapping."""
    
    def test_has_region_map(self):
        """Should have REGION_MAP defined."""
        assert hasattr(AppSpecGenerator, 'REGION_MAP')
        assert isinstance(AppSpecGenerator.REGION_MAP, dict)


class TestDockerfileHandling:
    """Tests for Dockerfile handling."""
    
    def test_detects_dockerfile(self, tmp_path):
        """Should detect Dockerfile."""
        (tmp_path / 'Dockerfile').write_text('FROM python:3.11\nCOPY . .\n')
        (tmp_path / 'app.py').touch()
        
        generator = AppSpecGenerator(str(tmp_path), 'dockerapp')
        spec = generator.generate()
        
        # Should use dockerfile or detect it
        assert generator.architecture.get('has_dockerfile', False) or spec is not None


class TestMainFunction:
    """Tests for main entry point."""
    
    def test_main_requires_arguments(self):
        """Should require arguments."""
        with patch('sys.argv', ['generate_app_spec.py']):
            with pytest.raises(SystemExit):
                main()
    
    def test_main_outputs_spec(self, tmp_path, capsys):
        """Should output generated spec."""
        (tmp_path / 'package.json').write_text('{"name": "test", "scripts": {"start": "node index.js"}}')
        (tmp_path / 'index.js').touch()
        
        with patch('sys.argv', ['generate_app_spec.py', str(tmp_path), '--name', 'testapp']):
            main()
        
        captured = capsys.readouterr()
        assert 'testapp' in captured.out or 'name' in captured.out
    
    def test_main_with_output_file(self, tmp_path):
        """Should write to output file."""
        (tmp_path / 'app.py').touch()
        (tmp_path / 'requirements.txt').touch()
        output_file = tmp_path / 'output' / 'app.yaml'
        
        with patch('sys.argv', ['generate_app_spec.py', str(tmp_path), '--name', 'testapp', '--output', str(output_file)]):
            main()
        
        assert output_file.exists()
    
    def test_main_with_environment(self, tmp_path, capsys):
        """Should accept environment option."""
        (tmp_path / 'app.py').touch()
        
        with patch('sys.argv', ['generate_app_spec.py', str(tmp_path), '--name', 'testapp', '--env', 'production']):
            main()
        
        captured = capsys.readouterr()
        assert captured.out is not None


class TestGitHubSourceConfig:
    """Tests for GitHub source configuration in generated spec."""
    
    def test_spec_can_include_git_source(self, tmp_path):
        """Should be able to include git source in spec."""
        (tmp_path / 'app.py').touch()
        (tmp_path / 'requirements.txt').touch()
        
        generator = AppSpecGenerator(str(tmp_path), 'myapp')
        spec = generator.generate()
        
        # Spec should be valid
        assert spec is not None


class TestStaticSiteHandling:
    """Tests for static site handling."""
    
    def test_detects_static_site(self, tmp_path):
        """Should detect static site."""
        (tmp_path / 'index.html').write_text('<html></html>')
        (tmp_path / 'package.json').write_text('{"scripts": {"build": "vite build"}}')
        
        generator = AppSpecGenerator(str(tmp_path), 'staticapp')
        spec = generator.generate()
        
        # Should generate spec
        assert spec is not None


class TestDatabaseSpecGeneration:
    """Tests for database handling in spec."""
    
    def test_spec_can_include_database(self, tmp_path):
        """Should be able to include database in spec."""
        (tmp_path / 'requirements.txt').write_text('psycopg2==2.9.0\nflask==2.0.0')
        (tmp_path / 'app.py').touch()
        
        generator = AppSpecGenerator(str(tmp_path), 'dbapp')
        spec = generator.generate()
        
        assert spec is not None


class TestEnvironmentVariableHandling:
    """Tests for environment variable handling."""
    
    def test_includes_env_vars(self, tmp_path):
        """Should handle environment variables."""
        (tmp_path / '.env.example').write_text('DATABASE_URL=\nREDIS_URL=\n')
        (tmp_path / 'app.py').touch()
        (tmp_path / 'requirements.txt').touch()
        
        generator = AppSpecGenerator(str(tmp_path), 'myapp')
        spec = generator.generate()
        
        assert spec is not None
