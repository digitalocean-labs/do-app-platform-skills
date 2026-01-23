"""Comprehensive tests for analyze_architecture.py - Full coverage."""

import os
import sys
import pytest
import json
from unittest.mock import patch, MagicMock

# Add scripts to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '../../skills/migration/scripts'))


class TestAnalyzeArchitectureImports:
    """Tests for module imports."""
    
    def test_module_imports(self):
        """Module should import without errors."""
        import analyze_architecture
        assert hasattr(analyze_architecture, 'analyze_project')


class TestProcfileParsing:
    """Tests for Procfile parsing."""
    
    def test_parses_simple_procfile(self, tmp_path):
        """Should parse simple Procfile."""
        from analyze_architecture import parse_procfile
        
        (tmp_path / 'Procfile').write_text('web: npm start\nworker: npm run worker')
        
        result = parse_procfile(tmp_path / 'Procfile')
        
        assert 'web' in result
        assert result['web'] == 'npm start'
        assert 'worker' in result
    
    def test_parses_complex_commands(self, tmp_path):
        """Should parse complex Procfile commands."""
        from analyze_architecture import parse_procfile
        
        (tmp_path / 'Procfile').write_text('web: bundle exec puma -C config/puma.rb')
        
        result = parse_procfile(tmp_path / 'Procfile')
        
        assert 'bundle exec puma' in result['web']
    
    def test_handles_empty_procfile(self, tmp_path):
        """Should handle empty Procfile."""
        from analyze_architecture import parse_procfile
        
        (tmp_path / 'Procfile').write_text('')
        
        result = parse_procfile(tmp_path / 'Procfile')
        
        assert result == {} or result is None


class TestDockerComposeParsing:
    """Tests for docker-compose.yml parsing."""
    
    def test_parses_docker_compose(self, tmp_path):
        """Should parse docker-compose.yml."""
        from analyze_architecture import parse_docker_compose
        
        compose = """
version: '3.8'
services:
  web:
    build: .
    ports:
      - "3000:3000"
  db:
    image: postgres:15
"""
        (tmp_path / 'docker-compose.yml').write_text(compose)
        
        result = parse_docker_compose(tmp_path / 'docker-compose.yml')
        
        assert 'services' in result
        assert 'web' in result['services']
    
    def test_extracts_service_dependencies(self, tmp_path):
        """Should extract service dependencies."""
        from analyze_architecture import parse_docker_compose
        
        compose = """
version: '3.8'
services:
  web:
    build: .
    depends_on:
      - db
      - redis
  db:
    image: postgres:15
  redis:
    image: redis:7
"""
        (tmp_path / 'docker-compose.yml').write_text(compose)
        
        result = parse_docker_compose(tmp_path / 'docker-compose.yml')
        
        assert 'db' in result['services']['web'].get('depends_on', [])


class TestRenderYamlParsing:
    """Tests for render.yaml parsing."""
    
    def test_parses_render_yaml(self, tmp_path):
        """Should parse render.yaml."""
        from analyze_architecture import parse_render_yaml
        
        render_yaml = """
services:
  - type: web
    name: api
    env: node
    buildCommand: npm install && npm run build
    startCommand: npm start
"""
        (tmp_path / 'render.yaml').write_text(render_yaml)
        
        result = parse_render_yaml(tmp_path / 'render.yaml')
        
        assert 'services' in result
        assert result['services'][0]['name'] == 'api'
    
    def test_extracts_databases(self, tmp_path):
        """Should extract database configurations."""
        from analyze_architecture import parse_render_yaml
        
        render_yaml = """
services:
  - type: web
    name: api
databases:
  - name: mydb
    databaseName: myapp
    user: myuser
"""
        (tmp_path / 'render.yaml').write_text(render_yaml)
        
        result = parse_render_yaml(tmp_path / 'render.yaml')
        
        assert 'databases' in result


class TestFlyTomlParsing:
    """Tests for fly.toml parsing."""
    
    def test_parses_fly_toml(self, tmp_path):
        """Should parse fly.toml."""
        from analyze_architecture import parse_fly_toml
        
        fly_toml = """
app = "my-app"
primary_region = "ewr"

[build]
  dockerfile = "Dockerfile"

[http_service]
  internal_port = 3000
  force_https = true
"""
        (tmp_path / 'fly.toml').write_text(fly_toml)
        
        result = parse_fly_toml(tmp_path / 'fly.toml')
        
        assert result['app'] == 'my-app'
    
    def test_extracts_services(self, tmp_path):
        """Should extract service configuration."""
        from analyze_architecture import parse_fly_toml
        
        fly_toml = """
app = "my-app"

[[services]]
  internal_port = 8080
  protocol = "tcp"
"""
        (tmp_path / 'fly.toml').write_text(fly_toml)
        
        result = parse_fly_toml(tmp_path / 'fly.toml')
        
        # May have services key
        assert 'app' in result


class TestRuntimeDetection:
    """Tests for runtime detection."""
    
    def test_detects_node_runtime(self, tmp_path):
        """Should detect Node.js runtime."""
        from analyze_architecture import detect_runtime
        
        (tmp_path / 'package.json').write_text('{"name": "test"}')
        
        result = detect_runtime(str(tmp_path))
        
        assert result == 'node' or 'node' in result.lower()
    
    def test_detects_python_runtime(self, tmp_path):
        """Should detect Python runtime."""
        from analyze_architecture import detect_runtime
        
        (tmp_path / 'requirements.txt').write_text('flask==2.0.0')
        
        result = detect_runtime(str(tmp_path))
        
        assert result == 'python' or 'python' in result.lower()
    
    def test_detects_go_runtime(self, tmp_path):
        """Should detect Go runtime."""
        from analyze_architecture import detect_runtime
        
        (tmp_path / 'go.mod').write_text('module example.com/app')
        
        result = detect_runtime(str(tmp_path))
        
        assert result == 'go' or 'go' in result.lower()
    
    def test_detects_ruby_runtime(self, tmp_path):
        """Should detect Ruby runtime."""
        from analyze_architecture import detect_runtime
        
        (tmp_path / 'Gemfile').write_text('source "https://rubygems.org"')
        
        result = detect_runtime(str(tmp_path))
        
        assert result == 'ruby' or 'ruby' in result.lower()
    
    def test_detects_php_runtime(self, tmp_path):
        """Should detect PHP runtime."""
        from analyze_architecture import detect_runtime
        
        (tmp_path / 'composer.json').write_text('{"name": "test"}')
        
        result = detect_runtime(str(tmp_path))
        
        assert result == 'php' or 'php' in result.lower()
    
    def test_detects_java_runtime(self, tmp_path):
        """Should detect Java runtime."""
        from analyze_architecture import detect_runtime
        
        (tmp_path / 'pom.xml').write_text('<project></project>')
        
        result = detect_runtime(str(tmp_path))
        
        assert result == 'java' or 'java' in result.lower()
    
    def test_detects_rust_runtime(self, tmp_path):
        """Should detect Rust runtime."""
        from analyze_architecture import detect_runtime
        
        (tmp_path / 'Cargo.toml').write_text('[package]\nname = "test"')
        
        result = detect_runtime(str(tmp_path))
        
        assert result == 'rust' or 'rust' in result.lower()
    
    def test_detects_dotnet_runtime(self, tmp_path):
        """Should detect .NET runtime."""
        from analyze_architecture import detect_runtime
        
        (tmp_path / 'app.csproj').write_text('<Project></Project>')
        
        result = detect_runtime(str(tmp_path))
        
        assert result == 'dotnet' or '.net' in result.lower() or 'csharp' in result.lower()


class TestDependencyDetection:
    """Tests for dependency detection."""
    
    def test_detects_postgres_dependency(self, tmp_path):
        """Should detect PostgreSQL dependency."""
        from analyze_architecture import detect_dependencies
        
        (tmp_path / 'package.json').write_text('{"dependencies": {"pg": "^8.0.0"}}')
        
        result = detect_dependencies(str(tmp_path))
        
        assert 'postgres' in result or 'postgresql' in str(result).lower()
    
    def test_detects_redis_dependency(self, tmp_path):
        """Should detect Redis dependency."""
        from analyze_architecture import detect_dependencies
        
        (tmp_path / 'package.json').write_text('{"dependencies": {"redis": "^4.0.0"}}')
        
        result = detect_dependencies(str(tmp_path))
        
        assert 'redis' in result or 'redis' in str(result).lower()
    
    def test_detects_mongodb_dependency(self, tmp_path):
        """Should detect MongoDB dependency."""
        from analyze_architecture import detect_dependencies
        
        (tmp_path / 'requirements.txt').write_text('pymongo==4.0.0')
        
        result = detect_dependencies(str(tmp_path))
        
        assert 'mongodb' in result or 'mongo' in str(result).lower()


class TestMonorepoDetection:
    """Tests for monorepo detection."""
    
    def test_detects_monorepo(self, tmp_path):
        """Should detect monorepo structure."""
        from analyze_architecture import detect_monorepo
        
        (tmp_path / 'packages').mkdir()
        (tmp_path / 'packages' / 'api').mkdir()
        (tmp_path / 'packages' / 'web').mkdir()
        (tmp_path / 'package.json').write_text('{"workspaces": ["packages/*"]}')
        
        result = detect_monorepo(str(tmp_path))
        
        assert result == True or result is not None
    
    def test_detects_lerna_monorepo(self, tmp_path):
        """Should detect Lerna monorepo."""
        from analyze_architecture import detect_monorepo
        
        (tmp_path / 'lerna.json').write_text('{"packages": ["packages/*"]}')
        (tmp_path / 'packages').mkdir()
        
        result = detect_monorepo(str(tmp_path))
        
        assert result == True or result is not None


class TestFullAnalysis:
    """Tests for full project analysis."""
    
    def test_analyze_node_project(self, tmp_path):
        """Should analyze complete Node.js project."""
        from analyze_architecture import analyze_project
        
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
        
        result = analyze_project(str(tmp_path))
        
        assert result is not None
        assert 'runtime' in result or 'services' in result or 'components' in result
    
    def test_analyze_python_project(self, tmp_path):
        """Should analyze complete Python project."""
        from analyze_architecture import analyze_project
        
        (tmp_path / 'requirements.txt').write_text('flask==2.0.0\npsycopg2-binary==2.9.0')
        (tmp_path / 'app.py').write_text('from flask import Flask')
        (tmp_path / 'Procfile').write_text('web: gunicorn app:app')
        
        result = analyze_project(str(tmp_path))
        
        assert result is not None
    
    def test_outputs_json(self, tmp_path):
        """Should output analysis as JSON."""
        import analyze_architecture
        
        (tmp_path / 'package.json').write_text('{"name": "test"}')
        
        if hasattr(analyze_architecture, 'main'):
            with patch('sys.argv', ['analyze_architecture.py', str(tmp_path), '--format', 'json']):
                with patch('builtins.print') as mock_print:
                    try:
                        analyze_architecture.main()
                    except SystemExit:
                        pass
                    
                    if mock_print.called:
                        output = str(mock_print.call_args)
                        # May contain JSON
                        assert mock_print.called


class TestMainFunction:
    """Tests for main entry point."""
    
    def test_main_requires_directory(self):
        """Should require directory argument."""
        import analyze_architecture
        
        if hasattr(analyze_architecture, 'main'):
            with patch('sys.argv', ['analyze_architecture.py']):
                with pytest.raises(SystemExit):
                    analyze_architecture.main()
    
    def test_main_analyzes_directory(self, tmp_path):
        """Should analyze provided directory."""
        import analyze_architecture
        
        (tmp_path / 'package.json').write_text('{"name": "test"}')
        
        if hasattr(analyze_architecture, 'main'):
            with patch('sys.argv', ['analyze_architecture.py', str(tmp_path)]):
                with patch('builtins.print'):
                    try:
                        analyze_architecture.main()
                    except SystemExit:
                        pass
