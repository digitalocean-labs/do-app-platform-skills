"""Comprehensive tests for detect_platform.py - Full coverage."""

import os
import sys
import pytest
import json
from unittest.mock import patch, MagicMock

# Add scripts to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '../../skills/migration/scripts'))

from detect_platform import PlatformDetector, main


class TestDetectPlatformImports:
    """Tests for module imports."""
    
    def test_module_imports(self):
        """Module should import without errors."""
        import detect_platform
        assert hasattr(detect_platform, 'PlatformDetector')
        assert hasattr(detect_platform, 'main')


class TestPlatformDetectorInit:
    """Tests for PlatformDetector initialization."""
    
    def test_init_with_valid_path(self, tmp_path):
        """Should initialize with valid path."""
        (tmp_path / 'app.py').touch()
        detector = PlatformDetector(str(tmp_path))
        assert detector.repo_path == tmp_path
    
    def test_init_with_invalid_path(self):
        """Should raise error for invalid path."""
        with pytest.raises(ValueError, match="does not exist"):
            PlatformDetector('/nonexistent/path/12345')


class TestHerokuDetection:
    """Tests for Heroku platform detection."""
    
    def test_detects_heroku_by_procfile(self, tmp_path):
        """Should detect Heroku by Procfile."""
        (tmp_path / 'Procfile').write_text('web: npm start')
        
        detector = PlatformDetector(str(tmp_path))
        result = detector.detect()
        
        assert result['primary_platform'] == 'heroku'
    
    def test_detects_heroku_by_app_json(self, tmp_path):
        """Should detect Heroku by app.json."""
        (tmp_path / 'app.json').write_text('{"formation": {"web": {"quantity": 1}}}')
        
        detector = PlatformDetector(str(tmp_path))
        result = detector.detect()
        
        assert result['primary_platform'] == 'heroku'


class TestRenderDetection:
    """Tests for Render platform detection."""
    
    def test_detects_render_by_yaml(self, tmp_path):
        """Should detect Render by render.yaml."""
        (tmp_path / 'render.yaml').write_text('services:\n  - type: web')
        
        detector = PlatformDetector(str(tmp_path))
        result = detector.detect()
        
        assert result['primary_platform'] == 'render'
    
    def test_detects_render_by_yml(self, tmp_path):
        """Should detect Render by render.yml."""
        (tmp_path / 'render.yml').write_text('services:\n  - type: web')
        
        detector = PlatformDetector(str(tmp_path))
        result = detector.detect()
        
        assert result['primary_platform'] == 'render'


class TestFlyDetection:
    """Tests for Fly.io platform detection."""
    
    def test_detects_fly_by_toml(self, tmp_path):
        """Should detect Fly.io by fly.toml."""
        (tmp_path / 'fly.toml').write_text('app = "my-app"\nprimary_region = "ord"')
        
        detector = PlatformDetector(str(tmp_path))
        result = detector.detect()
        
        assert result['primary_platform'] == 'fly'


class TestRailwayDetection:
    """Tests for Railway platform detection."""
    
    def test_detects_railway_by_json(self, tmp_path):
        """Should detect Railway by railway.json."""
        (tmp_path / 'railway.json').write_text('{"build": {}}')
        
        detector = PlatformDetector(str(tmp_path))
        result = detector.detect()
        
        assert result['primary_platform'] == 'railway'
    
    def test_detects_railway_by_toml(self, tmp_path):
        """Should detect Railway by railway.toml."""
        (tmp_path / 'railway.toml').write_text('[build]')
        
        detector = PlatformDetector(str(tmp_path))
        result = detector.detect()
        
        assert result['primary_platform'] == 'railway'


class TestDockerDetection:
    """Tests for Docker/container platform detection."""
    
    def test_detects_docker_compose(self, tmp_path):
        """Should detect Docker Compose."""
        (tmp_path / 'docker-compose.yml').write_text('services:\n  web:\n    build: .')
        
        detector = PlatformDetector(str(tmp_path))
        result = detector.detect()
        
        assert result['primary_platform'] == 'docker_compose'
    
    def test_detects_dockerfile(self, tmp_path):
        """Should detect generic Dockerfile."""
        (tmp_path / 'Dockerfile').write_text('FROM node:18')
        
        detector = PlatformDetector(str(tmp_path))
        result = detector.detect()
        
        assert result['primary_platform'] == 'generic_docker'


class TestAWSDetection:
    """Tests for AWS platform detection."""
    
    def test_detects_aws_apprunner(self, tmp_path):
        """Should detect AWS App Runner."""
        (tmp_path / 'apprunner.yaml').write_text('version: 1.0\nruntime: python3')
        
        detector = PlatformDetector(str(tmp_path))
        result = detector.detect()
        
        assert result['primary_platform'] == 'aws_apprunner'
    
    def test_detects_aws_beanstalk(self, tmp_path):
        """Should detect AWS Elastic Beanstalk."""
        (tmp_path / 'Dockerrun.aws.json').write_text('{"AWSEBDockerrunVersion": "1"}')
        
        detector = PlatformDetector(str(tmp_path))
        result = detector.detect()
        
        assert result['primary_platform'] == 'aws_beanstalk'


class TestPlatformPriority:
    """Tests for platform detection priority."""
    
    def test_prefers_specific_over_generic(self, tmp_path):
        """Should prefer specific platform files over generic ones."""
        # Create both Dockerfile and render.yaml
        (tmp_path / 'Dockerfile').write_text('FROM node:18')
        (tmp_path / 'render.yaml').write_text('services:\n  - type: web')
        
        detector = PlatformDetector(str(tmp_path))
        result = detector.detect()
        
        # Should prefer Render (priority 2) over generic Docker (priority 10)
        assert result['primary_platform'] == 'render'
    
    def test_handles_multiple_platforms(self, tmp_path):
        """Should handle multiple platform indicators."""
        (tmp_path / 'Procfile').write_text('web: npm start')
        (tmp_path / 'fly.toml').write_text('app = "test"')
        
        detector = PlatformDetector(str(tmp_path))
        result = detector.detect()
        
        # Should detect one based on priority
        assert result['primary_platform'] in ['heroku', 'fly']


class TestUnknownPlatform:
    """Tests for unknown platform handling."""
    
    def test_returns_unknown_for_empty_dir(self, tmp_path):
        """Should return unknown for empty directory."""
        (tmp_path / 'README.md').write_text('# Test')
        
        detector = PlatformDetector(str(tmp_path))
        result = detector.detect()
        
        assert result['primary_platform'] in [None, 'unknown']
    
    def test_returns_unknown_for_no_platform_files(self, tmp_path):
        """Should return unknown when no platform files found."""
        (tmp_path / 'index.js').write_text('console.log("hello")')
        (tmp_path / 'package.json').write_text('{"name": "test"}')
        
        detector = PlatformDetector(str(tmp_path))
        result = detector.detect()
        
        # No platform config files, may return unknown
        assert result['primary_platform'] in [None, 'unknown']


class TestDetectMethod:
    """Tests for detect() method output."""
    
    def test_detect_returns_dict(self, tmp_path):
        """Should return dictionary."""
        (tmp_path / 'app.py').touch()
        
        detector = PlatformDetector(str(tmp_path))
        result = detector.detect()
        
        assert isinstance(result, dict)
    
    def test_detect_contains_primary_platform(self, tmp_path):
        """Should contain primary_platform key."""
        (tmp_path / 'Procfile').write_text('web: app')
        
        detector = PlatformDetector(str(tmp_path))
        result = detector.detect()
        
        assert 'primary_platform' in result
    
    def test_detect_contains_description(self, tmp_path):
        """Should contain primary_description key."""
        (tmp_path / 'Procfile').write_text('web: app')
        
        detector = PlatformDetector(str(tmp_path))
        result = detector.detect()
        
        assert 'primary_description' in result


class TestMainFunction:
    """Tests for main entry point."""
    
    def test_main_requires_directory(self):
        """Should require directory argument."""
        with patch('sys.argv', ['detect_platform.py']):
            with pytest.raises(SystemExit):
                main()
    
    def test_main_outputs_platform(self, tmp_path, capsys):
        """Should output detected platform."""
        (tmp_path / 'render.yaml').write_text('services: []')
        
        with patch('sys.argv', ['detect_platform.py', str(tmp_path)]):
            main()
        
        captured = capsys.readouterr()
        assert 'render' in captured.out.lower() or 'Platform' in captured.out
    
    def test_main_json_output(self, tmp_path, capsys):
        """Should output JSON when requested."""
        (tmp_path / 'Procfile').write_text('web: npm start')
        
        with patch('sys.argv', ['detect_platform.py', str(tmp_path), '--json']):
            main()
        
        captured = capsys.readouterr()
        data = json.loads(captured.out)
        assert 'primary_platform' in data


class TestPlatformIndicators:
    """Tests for platform indicators constant."""
    
    def test_has_platform_indicators(self):
        """Should have PLATFORM_INDICATORS defined."""
        assert hasattr(PlatformDetector, 'PLATFORM_INDICATORS')
        assert isinstance(PlatformDetector.PLATFORM_INDICATORS, dict)
    
    def test_heroku_in_indicators(self):
        """Should have Heroku in platform indicators."""
        assert 'heroku' in PlatformDetector.PLATFORM_INDICATORS
    
    def test_render_in_indicators(self):
        """Should have Render in platform indicators."""
        assert 'render' in PlatformDetector.PLATFORM_INDICATORS
    
    def test_fly_in_indicators(self):
        """Should have Fly in platform indicators."""
        assert 'fly' in PlatformDetector.PLATFORM_INDICATORS
