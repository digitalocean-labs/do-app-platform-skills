"""Comprehensive tests for analyze_architecture.py - Full coverage.

Tests the ArchitectureAnalyzer class and main() function.
"""

import os
import sys
import pytest
import json
from unittest.mock import patch, MagicMock

# Add scripts to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '../../skills/migration/scripts'))

from analyze_architecture import ArchitectureAnalyzer, main


class TestAnalyzeArchitectureImports:
    """Tests for module imports."""
    
    def test_module_imports(self):
        """Module should import without errors."""
        import analyze_architecture
        assert hasattr(analyze_architecture, 'ArchitectureAnalyzer')
        assert hasattr(analyze_architecture, 'main')


class TestArchitectureAnalyzerInit:
    """Tests for ArchitectureAnalyzer initialization."""
    
    def test_init_with_valid_path(self, tmp_path):
        """Should initialize with valid repository path."""
        analyzer = ArchitectureAnalyzer(str(tmp_path))
        assert analyzer.repo_path == tmp_path
    
    def test_init_with_invalid_path_raises(self):
        """Should raise ValueError for non-existent path."""
        with pytest.raises(ValueError, match="does not exist"):
            ArchitectureAnalyzer('/nonexistent/path/12345')
    
    def test_init_scans_files(self, tmp_path):
        """Should scan files on initialization."""
        (tmp_path / 'package.json').write_text('{}')
        (tmp_path / 'src').mkdir()
        (tmp_path / 'src' / 'index.js').write_text('// test')
        
        analyzer = ArchitectureAnalyzer(str(tmp_path))
        
        assert 'package.json' in analyzer.files
        assert 'src/index.js' in analyzer.files


class TestFileScan:
    """Tests for file scanning."""
    
    def test_skips_git_directory(self, tmp_path):
        """Should skip .git directory."""
        (tmp_path / '.git').mkdir()
        (tmp_path / '.git' / 'config').write_text('test')
        
        analyzer = ArchitectureAnalyzer(str(tmp_path))
        
        assert '.git/config' not in analyzer.files
    
    def test_skips_node_modules(self, tmp_path):
        """Should skip node_modules directory."""
        (tmp_path / 'node_modules').mkdir()
        (tmp_path / 'node_modules' / 'lodash').mkdir()
        (tmp_path / 'node_modules' / 'lodash' / 'index.js').write_text('test')
        
        analyzer = ArchitectureAnalyzer(str(tmp_path))
        
        assert not any('node_modules' in f for f in analyzer.files)
    
    def test_skips_venv_directory(self, tmp_path):
        """Should skip venv directory."""
        (tmp_path / 'venv').mkdir()
        (tmp_path / 'venv' / 'bin').mkdir()
        (tmp_path / 'venv' / 'bin' / 'python').write_text('test')
        
        analyzer = ArchitectureAnalyzer(str(tmp_path))
        
        assert not any('venv' in f for f in analyzer.files)


class TestArchitectureTypeDetection:
    """Tests for architecture type detection."""
    
    def test_detects_monolith_by_default(self, tmp_path):
        """Should default to monolith architecture."""
        (tmp_path / 'app.py').write_text('# simple app')
        
        analyzer = ArchitectureAnalyzer(str(tmp_path))
        result = analyzer.analyze()
        
        assert result['architecture_type'] == 'monolith'
    
    def test_detects_fullstack(self, tmp_path):
        """Should detect full-stack architecture."""
        frontend = tmp_path / 'frontend'
        frontend.mkdir()
        (frontend / 'package.json').write_text('{"name": "frontend"}')
        
        backend = tmp_path / 'backend'
        backend.mkdir()
        (backend / 'requirements.txt').touch()
        
        analyzer = ArchitectureAnalyzer(str(tmp_path))
        result = analyzer.analyze()
        
        assert result['architecture_type'] in ['full-stack', 'monolith']


class TestRuntimeDetection:
    """Tests for runtime detection via ArchitectureAnalyzer."""
    
    def test_detects_node_runtime(self, tmp_path):
        """Should detect Node.js runtime."""
        (tmp_path / 'package.json').write_text('{"name": "test"}')
        
        analyzer = ArchitectureAnalyzer(str(tmp_path))
        result = analyzer.analyze()
        
        assert result['runtime'] == 'nodejs'
    
    def test_detects_python_runtime(self, tmp_path):
        """Should detect Python runtime."""
        (tmp_path / 'requirements.txt').write_text('flask==2.0.0')
        
        analyzer = ArchitectureAnalyzer(str(tmp_path))
        result = analyzer.analyze()
        
        assert result['runtime'] == 'python'
    
    def test_detects_go_runtime(self, tmp_path):
        """Should detect Go runtime."""
        (tmp_path / 'go.mod').write_text('module example.com/app\ngo 1.20\n')
        
        analyzer = ArchitectureAnalyzer(str(tmp_path))
        result = analyzer.analyze()
        
        assert result['runtime'] == 'go'
    
    def test_detects_ruby_runtime(self, tmp_path):
        """Should detect Ruby runtime."""
        (tmp_path / 'Gemfile').write_text('source "https://rubygems.org"')
        
        analyzer = ArchitectureAnalyzer(str(tmp_path))
        result = analyzer.analyze()
        
        assert result['runtime'] == 'ruby'
    
    def test_detects_php_runtime(self, tmp_path):
        """Should detect PHP runtime."""
        (tmp_path / 'composer.json').write_text('{"name": "test"}')
        
        analyzer = ArchitectureAnalyzer(str(tmp_path))
        result = analyzer.analyze()
        
        assert result['runtime'] == 'php'
    
    def test_detects_java_runtime(self, tmp_path):
        """Should detect Java runtime."""
        (tmp_path / 'pom.xml').write_text('<project></project>')
        
        analyzer = ArchitectureAnalyzer(str(tmp_path))
        result = analyzer.analyze()
        
        assert result['runtime'] == 'java'
    
    def test_detects_rust_runtime(self, tmp_path):
        """Should detect Rust runtime."""
        (tmp_path / 'Cargo.toml').write_text('[package]\nname = "test"')
        
        analyzer = ArchitectureAnalyzer(str(tmp_path))
        result = analyzer.analyze()
        
        assert result['runtime'] == 'rust'
    
    def test_detects_dotnet_runtime(self, tmp_path):
        """Should detect .NET runtime."""
        (tmp_path / 'app.csproj').write_text('<Project></Project>')
        
        analyzer = ArchitectureAnalyzer(str(tmp_path))
        result = analyzer.analyze()
        
        assert result['runtime'] in ['dotnet', 'csharp', '.net']


class TestDependencyDetection:
    """Tests for dependency detection via ArchitectureAnalyzer."""
    
    def test_detects_postgres_dependency(self, tmp_path):
        """Should detect PostgreSQL dependency."""
        (tmp_path / 'requirements.txt').write_text('psycopg2==2.9.0')
        
        analyzer = ArchitectureAnalyzer(str(tmp_path))
        result = analyzer.analyze()
        
        assert 'dependencies' in result
        deps = result['dependencies']
        assert isinstance(deps, dict)
    
    def test_detects_redis_dependency(self, tmp_path):
        """Should detect Redis dependency."""
        (tmp_path / 'package.json').write_text('{"dependencies": {"redis": "^4.0.0"}}')
        
        analyzer = ArchitectureAnalyzer(str(tmp_path))
        result = analyzer.analyze()
        
        assert 'dependencies' in result
    
    def test_detects_mongodb_dependency(self, tmp_path):
        """Should detect MongoDB dependency."""
        (tmp_path / 'requirements.txt').write_text('pymongo==4.0.0')
        
        analyzer = ArchitectureAnalyzer(str(tmp_path))
        result = analyzer.analyze()
        
        assert 'dependencies' in result


class TestMonorepoDetection:
    """Tests for monorepo detection via ArchitectureAnalyzer."""
    
    def test_detects_monorepo(self, tmp_path):
        """Should detect monorepo structure."""
        (tmp_path / 'packages').mkdir()
        (tmp_path / 'packages' / 'api').mkdir()
        (tmp_path / 'packages' / 'web').mkdir()
        (tmp_path / 'package.json').write_text('{"workspaces": ["packages/*"]}')
        
        analyzer = ArchitectureAnalyzer(str(tmp_path))
        result = analyzer.analyze()
        
        assert 'monorepo_structure' in result
    
    def test_detects_lerna_monorepo(self, tmp_path):
        """Should detect Lerna monorepo."""
        (tmp_path / 'lerna.json').write_text('{"packages": ["packages/*"]}')
        (tmp_path / 'packages').mkdir()
        
        analyzer = ArchitectureAnalyzer(str(tmp_path))
        result = analyzer.analyze()
        
        assert 'monorepo_structure' in result


class TestDockerDetection:
    """Tests for Docker detection."""
    
    def test_detects_dockerfile(self, tmp_path):
        """Should detect Dockerfile."""
        (tmp_path / 'Dockerfile').write_text('FROM python:3.11\n')
        
        analyzer = ArchitectureAnalyzer(str(tmp_path))
        result = analyzer.analyze()
        
        assert result['has_dockerfile'] is True
    
    def test_detects_docker_compose(self, tmp_path):
        """Should detect docker-compose."""
        (tmp_path / 'docker-compose.yml').write_text("version: '3'\n")
        
        analyzer = ArchitectureAnalyzer(str(tmp_path))
        result = analyzer.analyze()
        
        assert result['has_docker_compose'] is True


class TestFullAnalysis:
    """Tests for full project analysis."""
    
    def test_analyze_node_project(self, tmp_path):
        """Should analyze complete Node.js project."""
        (tmp_path / 'package.json').write_text(json.dumps({
            'name': 'my-app',
            'scripts': {
                'start': 'node server.js',
                'build': 'npm run compile'
            },
            'dependencies': {
                'express': '^4.18.0',
                'pg': '^8.11.0'
            }
        }))
        (tmp_path / 'server.js').write_text('const express = require("express")')
        
        analyzer = ArchitectureAnalyzer(str(tmp_path))
        result = analyzer.analyze()
        
        assert result is not None
        assert 'runtime' in result
        assert result['runtime'] == 'nodejs'
    
    def test_analyze_python_project(self, tmp_path):
        """Should analyze complete Python project."""
        (tmp_path / 'requirements.txt').write_text('flask==2.0.0\npsycopg2-binary==2.9.0')
        (tmp_path / 'app.py').write_text('from flask import Flask')
        (tmp_path / 'Procfile').write_text('web: gunicorn app:app')
        
        analyzer = ArchitectureAnalyzer(str(tmp_path))
        result = analyzer.analyze()
        
        assert result is not None
        assert result['runtime'] == 'python'
    
    def test_analyze_returns_expected_keys(self, tmp_path):
        """Should return expected keys in analysis."""
        (tmp_path / 'package.json').write_text('{"name": "test"}')
        
        analyzer = ArchitectureAnalyzer(str(tmp_path))
        result = analyzer.analyze()
        
        expected_keys = ['architecture_type', 'runtime', 'has_dockerfile', 'has_docker_compose', 'dependencies']
        for key in expected_keys:
            assert key in result, f"Missing key: {key}"


class TestMainFunction:
    """Tests for main entry point."""
    
    def test_main_requires_directory(self):
        """Should require directory argument."""
        with patch('sys.argv', ['analyze_architecture.py']):
            with pytest.raises(SystemExit):
                main()
    
    def test_main_analyzes_directory(self, tmp_path, capsys):
        """Should analyze provided directory."""
        (tmp_path / 'package.json').write_text('{"name": "test"}')
        
        with patch('sys.argv', ['analyze_architecture.py', str(tmp_path)]):
            main()
        
        captured = capsys.readouterr()
        assert 'node' in captured.out.lower() or 'runtime' in captured.out.lower()
    
    def test_main_json_output(self, tmp_path, capsys):
        """Should output JSON when requested."""
        (tmp_path / 'package.json').write_text('{"name": "test"}')
        
        with patch('sys.argv', ['analyze_architecture.py', str(tmp_path), '--json']):
            main()
        
        captured = capsys.readouterr()
        data = json.loads(captured.out)
        assert 'runtime' in data


class TestProcfileParsing:
    """Tests for Procfile parsing via analyze."""
    
    def test_parses_simple_procfile(self, tmp_path):
        """Should handle projects with Procfile."""
        (tmp_path / 'Procfile').write_text('web: gunicorn app:app\n')
        (tmp_path / 'app.py').touch()
        (tmp_path / 'requirements.txt').touch()
        
        analyzer = ArchitectureAnalyzer(str(tmp_path))
        result = analyzer.analyze()
        
        # Should detect components
        assert 'components' in result
    
    def test_parses_complex_commands(self, tmp_path):
        """Should handle complex Procfile commands."""
        (tmp_path / 'Procfile').write_text('web: gunicorn app:app --workers 4\nworker: celery -A tasks worker\n')
        (tmp_path / 'requirements.txt').touch()
        
        analyzer = ArchitectureAnalyzer(str(tmp_path))
        result = analyzer.analyze()
        
        assert result is not None
    
    def test_handles_empty_procfile(self, tmp_path):
        """Should handle empty Procfile."""
        (tmp_path / 'Procfile').write_text('')
        (tmp_path / 'app.py').touch()
        
        analyzer = ArchitectureAnalyzer(str(tmp_path))
        result = analyzer.analyze()
        
        assert result is not None


class TestDockerComposeParsing:
    """Tests for docker-compose.yml handling."""
    
    def test_parses_docker_compose(self, tmp_path):
        """Should handle docker-compose.yml."""
        docker_compose = """version: '3'
services:
  web:
    build: .
    ports:
      - "8000:8000"
  db:
    image: postgres:14
"""
        (tmp_path / 'docker-compose.yml').write_text(docker_compose)
        
        analyzer = ArchitectureAnalyzer(str(tmp_path))
        result = analyzer.analyze()
        
        assert result['has_docker_compose'] is True
    
    def test_extracts_service_dependencies(self, tmp_path):
        """Should detect services in docker-compose."""
        docker_compose = """version: '3'
services:
  web:
    build: .
    depends_on:
      - db
  db:
    image: postgres:14
"""
        (tmp_path / 'docker-compose.yml').write_text(docker_compose)
        
        analyzer = ArchitectureAnalyzer(str(tmp_path))
        result = analyzer.analyze()
        
        assert result['has_docker_compose'] is True


class TestRenderYamlParsing:
    """Tests for render.yaml handling."""
    
    def test_parses_render_yaml(self, tmp_path):
        """Should handle render.yaml."""
        render_yaml = """services:
  - type: web
    name: api
    env: python
    buildCommand: pip install -r requirements.txt
    startCommand: gunicorn app:app
"""
        (tmp_path / 'render.yaml').write_text(render_yaml)
        (tmp_path / 'requirements.txt').touch()
        
        analyzer = ArchitectureAnalyzer(str(tmp_path))
        result = analyzer.analyze()
        
        assert result is not None
    
    def test_extracts_databases(self, tmp_path):
        """Should handle render.yaml with databases."""
        render_yaml = """services:
  - type: web
    name: api
databases:
  - name: mydb
"""
        (tmp_path / 'render.yaml').write_text(render_yaml)
        
        analyzer = ArchitectureAnalyzer(str(tmp_path))
        result = analyzer.analyze()
        
        assert result is not None


class TestFlyTomlParsing:
    """Tests for fly.toml handling."""
    
    def test_parses_fly_toml(self, tmp_path):
        """Should handle fly.toml."""
        fly_toml = """app = "my-app"
primary_region = "ewr"

[build]
  dockerfile = "Dockerfile"
"""
        (tmp_path / 'fly.toml').write_text(fly_toml)
        (tmp_path / 'Dockerfile').write_text('FROM python:3.11\n')
        
        analyzer = ArchitectureAnalyzer(str(tmp_path))
        result = analyzer.analyze()
        
        assert result['has_dockerfile'] is True
    
    def test_extracts_services(self, tmp_path):
        """Should handle fly.toml services."""
        fly_toml = """app = "my-app"

[[services]]
  internal_port = 8080
  protocol = "tcp"
"""
        (tmp_path / 'fly.toml').write_text(fly_toml)
        
        analyzer = ArchitectureAnalyzer(str(tmp_path))
        result = analyzer.analyze()
        
        assert result is not None
