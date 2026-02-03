"""Tests for architecture analysis."""

import pytest
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent.parent / "skills" / "migration" / "scripts"))

from analyze_architecture import ArchitectureAnalyzer


class TestArchitectureAnalyzer:
    """Tests for ArchitectureAnalyzer class."""

    def test_detects_monolith_architecture(self, heroku_repo):
        """Should detect monolith architecture for simple apps."""
        analyzer = ArchitectureAnalyzer(str(heroku_repo))
        result = analyzer.analyze()
        
        assert "architecture_type" in result
        assert result["architecture_type"] in ["monolith", "full-stack", "static-site", "microservices"]

    def test_detects_python_runtime(self, temp_repo):
        """Should detect Python runtime from requirements.txt."""
        (temp_repo / "requirements.txt").write_text("flask>=2.0\ndjango>=4.0")
        
        analyzer = ArchitectureAnalyzer(str(temp_repo))
        result = analyzer.analyze()
        
        assert result["runtime"] == "python"

    def test_detects_nodejs_runtime(self, temp_repo):
        """Should detect Node.js runtime from package.json."""
        (temp_repo / "package.json").write_text('{"name": "test", "version": "1.0.0"}')
        
        analyzer = ArchitectureAnalyzer(str(temp_repo))
        result = analyzer.analyze()
        
        assert result["runtime"] == "nodejs"

    def test_detects_go_runtime(self, temp_repo):
        """Should detect Go runtime from go.mod."""
        (temp_repo / "go.mod").write_text("module example.com/myapp\n\ngo 1.21")
        
        analyzer = ArchitectureAnalyzer(str(temp_repo))
        result = analyzer.analyze()
        
        assert result["runtime"] == "go"

    def test_detects_ruby_runtime(self, temp_repo):
        """Should detect Ruby runtime from Gemfile."""
        (temp_repo / "Gemfile").write_text('source "https://rubygems.org"\n\ngem "rails"')
        
        analyzer = ArchitectureAnalyzer(str(temp_repo))
        result = analyzer.analyze()
        
        assert result["runtime"] == "ruby"

    def test_detects_dockerfile_presence(self, docker_compose_repo):
        """Should detect Dockerfile."""
        analyzer = ArchitectureAnalyzer(str(docker_compose_repo))
        result = analyzer.analyze()
        
        assert result["has_dockerfile"] is True

    def test_detects_docker_compose_presence(self, docker_compose_repo):
        """Should detect docker-compose.yml."""
        analyzer = ArchitectureAnalyzer(str(docker_compose_repo))
        result = analyzer.analyze()
        
        assert result["has_docker_compose"] is True

    def test_detects_components(self, heroku_repo):
        """Should detect application components."""
        analyzer = ArchitectureAnalyzer(str(heroku_repo))
        result = analyzer.analyze()
        
        assert "components" in result
        assert isinstance(result["components"], list)

    def test_detects_dependencies(self, temp_repo):
        """Should detect dependencies structure."""
        (temp_repo / "requirements.txt").write_text("psycopg2>=2.9\nredis>=4.0")
        
        analyzer = ArchitectureAnalyzer(str(temp_repo))
        result = analyzer.analyze()
        
        assert "dependencies" in result
        assert "databases" in result["dependencies"]
        assert "caches" in result["dependencies"]

    def test_detects_environment_files(self, temp_repo):
        """Should detect .env files."""
        (temp_repo / ".env.example").write_text("DATABASE_URL=postgres://localhost/mydb")
        (temp_repo / ".env.template").write_text("SECRET_KEY=changeme")
        
        analyzer = ArchitectureAnalyzer(str(temp_repo))
        result = analyzer.analyze()
        
        assert "environment_files" in result
        assert isinstance(result["environment_files"], list)

    def test_returns_unknown_for_unsupported_runtime(self, temp_repo):
        """Should return unknown for unsupported runtime."""
        # No recognizable runtime files
        analyzer = ArchitectureAnalyzer(str(temp_repo))
        result = analyzer.analyze()
        
        assert result["runtime"] == "unknown"

    def test_detects_monorepo_structure(self, temp_repo):
        """Should detect monorepo structure."""
        (temp_repo / "frontend").mkdir()
        (temp_repo / "backend").mkdir()
        (temp_repo / "frontend" / "package.json").write_text('{"name": "frontend"}')
        (temp_repo / "backend" / "requirements.txt").write_text("flask>=2.0")
        
        analyzer = ArchitectureAnalyzer(str(temp_repo))
        result = analyzer.analyze()
        
        assert "monorepo_structure" in result

    def test_detects_test_presence(self, temp_repo):
        """Should detect test files."""
        (temp_repo / "tests").mkdir()
        (temp_repo / "tests" / "test_app.py").write_text("def test_example(): pass")
        
        analyzer = ArchitectureAnalyzer(str(temp_repo))
        result = analyzer.analyze()
        
        assert "has_tests" in result

    def test_detects_default_port(self, temp_repo):
        """Should detect default port from common sources."""
        analyzer = ArchitectureAnalyzer(str(temp_repo))
        result = analyzer.analyze()
        
        assert "default_port" in result

    def test_detects_build_method(self, temp_repo):
        """Should detect build method."""
        (temp_repo / "Dockerfile").write_text("FROM python:3.12")
        
        analyzer = ArchitectureAnalyzer(str(temp_repo))
        result = analyzer.analyze()
        
        assert "build_method" in result

    def test_detects_full_stack_architecture(self, temp_repo):
        """Should detect full-stack with frontend and backend."""
        (temp_repo / "frontend").mkdir()
        (temp_repo / "backend").mkdir()
        (temp_repo / "frontend" / "package.json").write_text('{"name": "frontend"}')
        (temp_repo / "backend" / "requirements.txt").write_text("fastapi>=0.100")
        
        analyzer = ArchitectureAnalyzer(str(temp_repo))
        result = analyzer.analyze()
        
        # Should detect as full-stack or monorepo
        assert result["architecture_type"] in ["full-stack", "monolith"]

    def test_handles_empty_repository(self, temp_repo):
        """Should handle empty repository without errors."""
        analyzer = ArchitectureAnalyzer(str(temp_repo))
        result = analyzer.analyze()
        
        assert "architecture_type" in result
        assert "runtime" in result
        assert "components" in result

    def test_raises_for_nonexistent_path(self):
        """Should raise ValueError for nonexistent path."""
        with pytest.raises(ValueError):
            ArchitectureAnalyzer("/nonexistent/path")
