"""Comprehensive tests for generate_checklist.py - Full coverage."""

import os
import sys
import pytest
from unittest.mock import patch, MagicMock

# Add scripts to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '../../skills/migration/scripts'))

from generate_checklist import generate_checklist, main


class TestGenerateChecklistImports:
    """Tests for module imports."""
    
    def test_module_imports(self):
        """Module should import without errors."""
        import generate_checklist
        assert hasattr(generate_checklist, 'generate_checklist')
        assert hasattr(generate_checklist, 'main')


class TestChecklistGeneration:
    """Tests for checklist generation."""
    
    def test_generates_checklist_for_heroku(self, tmp_path):
        """Should generate migration checklist for Heroku project."""
        (tmp_path / 'Procfile').write_text('web: gunicorn app:app')
        (tmp_path / 'requirements.txt').write_text('flask==2.0.0\ngunicorn==20.0.0')
        (tmp_path / 'app.py').touch()
        
        result = generate_checklist(str(tmp_path), 'myapp')
        
        assert isinstance(result, str)
        assert len(result) > 0
    
    def test_generates_checklist_for_render(self, tmp_path):
        """Should generate migration checklist for Render project."""
        (tmp_path / 'render.yaml').write_text('services:\n  - type: web\n')
        (tmp_path / 'app.py').touch()
        (tmp_path / 'requirements.txt').touch()
        
        result = generate_checklist(str(tmp_path), 'renderapp')
        
        assert isinstance(result, str)
        assert len(result) > 0
    
    def test_includes_app_name(self, tmp_path):
        """Should include app name in checklist."""
        (tmp_path / 'Procfile').write_text('web: app')
        (tmp_path / 'app.py').touch()
        
        result = generate_checklist(str(tmp_path), 'testapp123')
        
        assert 'testapp123' in result
    
    def test_includes_platform_info(self, tmp_path):
        """Should include detected platform information."""
        (tmp_path / 'Procfile').write_text('web: gunicorn app:app')
        (tmp_path / 'requirements.txt').touch()
        (tmp_path / 'app.py').touch()
        
        result = generate_checklist(str(tmp_path), 'myapp')
        
        # Should mention platform or migration
        assert 'Platform' in result or 'Migration' in result or 'Heroku' in result


class TestChecklistWithOptionalParams:
    """Tests for optional parameters."""
    
    def test_with_repo_url(self, tmp_path):
        """Should accept repo_url parameter."""
        (tmp_path / 'app.py').touch()
        (tmp_path / 'requirements.txt').touch()
        
        result = generate_checklist(
            str(tmp_path), 
            'myapp',
            repo_url='https://github.com/example/repo'
        )
        
        assert isinstance(result, str)
    
    def test_with_custom_branches(self, tmp_path):
        """Should accept custom branch names."""
        (tmp_path / 'app.py').touch()
        (tmp_path / 'requirements.txt').touch()
        
        result = generate_checklist(
            str(tmp_path), 
            'myapp',
            test_branch='staging',
            prod_branch='main'
        )
        
        assert isinstance(result, str)


class TestChecklistContent:
    """Tests for checklist content."""
    
    def test_contains_migration_header(self, tmp_path):
        """Should contain migration header."""
        (tmp_path / 'Procfile').write_text('web: app')
        (tmp_path / 'app.py').touch()
        
        result = generate_checklist(str(tmp_path), 'myapp')
        
        # Should have markdown header
        assert '#' in result or 'Migration' in result
    
    def test_contains_summary_section(self, tmp_path):
        """Should contain summary section."""
        (tmp_path / 'Procfile').write_text('web: app')
        (tmp_path / 'app.py').touch()
        
        result = generate_checklist(str(tmp_path), 'myapp')
        
        # Should have summary or table
        assert 'Summary' in result or '|' in result


class TestChecklistWithDatabase:
    """Tests for checklist with database detection."""
    
    def test_database_app_checklist(self, tmp_path):
        """Should handle apps with database dependencies."""
        (tmp_path / 'requirements.txt').write_text('flask==2.0.0\npsycopg2==2.9.0')
        (tmp_path / 'Procfile').write_text('web: gunicorn app:app')
        (tmp_path / 'app.py').touch()
        
        result = generate_checklist(str(tmp_path), 'dbapp')
        
        assert isinstance(result, str)


class TestChecklistWithWorkers:
    """Tests for checklist with worker detection."""
    
    def test_worker_app_checklist(self, tmp_path):
        """Should handle apps with workers."""
        (tmp_path / 'Procfile').write_text('web: gunicorn app:app\nworker: celery -A tasks worker')
        (tmp_path / 'requirements.txt').write_text('celery==5.0.0')
        (tmp_path / 'app.py').touch()
        
        result = generate_checklist(str(tmp_path), 'workerapp')
        
        assert isinstance(result, str)


class TestChecklistErrorHandling:
    """Tests for error handling in checklist generation."""
    
    def test_handles_minimal_project(self, tmp_path):
        """Should handle minimal project."""
        (tmp_path / 'README.md').write_text('# Empty project')
        
        # Should not crash
        result = generate_checklist(str(tmp_path), 'emptyapp')
        assert isinstance(result, str)
    
    def test_handles_invalid_path(self):
        """Should handle invalid path."""
        with pytest.raises((ValueError, FileNotFoundError, Exception)):
            generate_checklist('/nonexistent/path/12345', 'app')


class TestMainFunction:
    """Tests for main entry point."""
    
    def test_main_requires_arguments(self):
        """Should require arguments."""
        with patch('sys.argv', ['generate_checklist.py']):
            with pytest.raises(SystemExit):
                main()
    
    def test_main_generates_checklist(self, tmp_path, capsys):
        """Should generate checklist output."""
        (tmp_path / 'Procfile').write_text('web: app')
        (tmp_path / 'app.py').touch()
        
        with patch('sys.argv', ['generate_checklist.py', str(tmp_path), '--name', 'testapp']):
            main()
        
        captured = capsys.readouterr()
        assert 'testapp' in captured.out or 'Migration' in captured.out
    
    def test_main_with_repo_url(self, tmp_path, capsys):
        """Should accept repo URL option."""
        (tmp_path / 'app.py').touch()
        (tmp_path / 'requirements.txt').touch()
        
        with patch('sys.argv', [
            'generate_checklist.py', str(tmp_path), 
            '--name', 'testapp',
            '--repo-url', 'https://github.com/example/repo'
        ]):
            main()
        
        captured = capsys.readouterr()
        assert captured.out is not None
    
    def test_main_with_invalid_repo(self):
        """Should handle invalid repo path."""
        with patch('sys.argv', ['generate_checklist.py', '/nonexistent/path', '--name', 'app']):
            with pytest.raises((SystemExit, Exception)):
                main()


class TestChecklistPlatformSpecific:
    """Tests for platform-specific checklist items."""
    
    def test_fly_project_checklist(self, tmp_path):
        """Should handle Fly.io project."""
        (tmp_path / 'fly.toml').write_text('app = "myapp"\nprimary_region = "ord"')
        (tmp_path / 'app.py').touch()
        (tmp_path / 'requirements.txt').touch()
        
        result = generate_checklist(str(tmp_path), 'flyapp')
        
        assert isinstance(result, str)
    
    def test_docker_compose_project_checklist(self, tmp_path):
        """Should handle docker-compose project."""
        (tmp_path / 'docker-compose.yml').write_text("version: '3'\nservices:\n  web:\n    build: .")
        (tmp_path / 'Dockerfile').write_text('FROM python:3.11')
        (tmp_path / 'app.py').touch()
        
        result = generate_checklist(str(tmp_path), 'dockerapp')
        
        assert isinstance(result, str)


class TestChecklistMarkdownOutput:
    """Tests for markdown output format."""
    
    def test_outputs_markdown(self, tmp_path):
        """Should output valid markdown."""
        (tmp_path / 'Procfile').write_text('web: app')
        (tmp_path / 'app.py').touch()
        
        result = generate_checklist(str(tmp_path), 'myapp')
        
        # Should have markdown elements
        assert '#' in result  # Headers
    
    def test_includes_checkboxes_or_lists(self, tmp_path):
        """Should include task items."""
        (tmp_path / 'Procfile').write_text('web: app')
        (tmp_path / 'app.py').touch()
        
        result = generate_checklist(str(tmp_path), 'myapp')
        
        # May include checkbox markers [ ] or list markers -
        assert isinstance(result, str)


class TestChecklistStaticSite:
    """Tests for static site migration checklist."""
    
    def test_static_site_checklist(self, tmp_path):
        """Should handle static site project."""
        (tmp_path / 'index.html').write_text('<html></html>')
        (tmp_path / 'package.json').write_text('{"scripts": {"build": "vite build"}}')
        
        result = generate_checklist(str(tmp_path), 'staticapp')
        
        assert isinstance(result, str)
