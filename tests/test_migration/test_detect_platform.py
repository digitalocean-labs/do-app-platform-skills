"""Tests for platform detection."""

import pytest
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent.parent / "skills" / "migration" / "scripts"))

from detect_platform import PlatformDetector


class TestPlatformDetector:
    """Tests for PlatformDetector class."""

    def test_detects_heroku_from_procfile(self, heroku_repo):
        """Should detect Heroku from Procfile."""
        detector = PlatformDetector(str(heroku_repo))
        result = detector.detect()
        assert result["primary_platform"] == "heroku"

    def test_detects_docker_compose(self, docker_compose_repo):
        """Should detect Docker Compose."""
        detector = PlatformDetector(str(docker_compose_repo))
        result = detector.detect()
        assert result["primary_platform"] == "docker_compose"

    def test_detects_generic_docker(self, temp_repo):
        """Should detect generic Docker from Dockerfile only."""
        (temp_repo / "Dockerfile").write_text("FROM python:3.12")
        detector = PlatformDetector(str(temp_repo))
        result = detector.detect()
        assert result["primary_platform"] == "generic_docker"

    def test_returns_unknown_for_empty_repo(self, temp_repo):
        """Should return unknown for empty repository."""
        detector = PlatformDetector(str(temp_repo))
        result = detector.detect()
        assert result["primary_platform"] == "unknown"

    def test_raises_for_nonexistent_path(self):
        """Should raise for nonexistent path."""
        with pytest.raises(ValueError):
            PlatformDetector("/nonexistent/path")

    def test_detects_render(self, temp_repo):
        """Should detect Render from render.yaml."""
        (temp_repo / "render.yaml").write_text("services:\n  - type: web")
        detector = PlatformDetector(str(temp_repo))
        result = detector.detect()
        assert result["primary_platform"] == "render"

    def test_detects_flyio(self, temp_repo):
        """Should detect Fly.io from fly.toml."""
        (temp_repo / "fly.toml").write_text('app = "myapp"')
        detector = PlatformDetector(str(temp_repo))
        result = detector.detect()
        assert result["primary_platform"] == "fly"

    def test_heroku_takes_priority(self, temp_repo):
        """Heroku should take priority over generic Docker."""
        (temp_repo / "Procfile").write_text("web: python app.py")
        (temp_repo / "Dockerfile").write_text("FROM python:3.12")
        detector = PlatformDetector(str(temp_repo))
        result = detector.detect()
        assert result["primary_platform"] == "heroku"
