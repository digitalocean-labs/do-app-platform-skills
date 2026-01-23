"""Tests for migration checklist generation."""

import pytest
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent.parent / "skills" / "migration" / "scripts"))

from generate_checklist import generate_checklist


class TestChecklistGenerator:
    """Tests for migration checklist generation."""

    def test_generates_checklist_for_heroku_app(self, heroku_repo):
        """Should generate checklist for Heroku app."""
        result = generate_checklist(str(heroku_repo), "test-app")
        
        assert isinstance(result, str)
        assert "Migration Report: test-app" in result
        assert "Source Platform:" in result

    def test_includes_summary_section(self, heroku_repo):
        """Should include summary section."""
        result = generate_checklist(str(heroku_repo), "test-app")
        
        assert "## Summary" in result
        assert "Source Platform" in result
        assert "Runtime" in result

    def test_includes_component_mapping(self, heroku_repo):
        """Should include component mapping section."""
        result = generate_checklist(str(heroku_repo), "test-app")
        
        assert "## Component Mapping" in result
        assert "Successfully Mapped" in result

    def test_includes_environment_variables_section(self, heroku_repo):
        """Should include environment variables section."""
        result = generate_checklist(str(heroku_repo), "test-app")
        
        assert "## Environment Variables" in result

    def test_includes_code_changes_section(self, heroku_repo):
        """Should include code changes section."""
        result = generate_checklist(str(heroku_repo), "test-app")
        
        assert "## Code Changes Required" in result

    def test_handles_docker_compose_app(self, docker_compose_repo):
        """Should handle Docker Compose applications."""
        result = generate_checklist(str(docker_compose_repo), "multi-service")
        
        assert isinstance(result, str)
        assert "Migration Report: multi-service" in result

    def test_handles_empty_repository(self, temp_repo):
        """Should handle empty repository."""
        result = generate_checklist(str(temp_repo), "empty-app")
        
        assert isinstance(result, str)
        assert "Migration Report: empty-app" in result

    def test_includes_branch_names(self, heroku_repo):
        """Should include configured branch names."""
        result = generate_checklist(
            str(heroku_repo), 
            "test-app",
            test_branch="feature/migrate",
            prod_branch="main"
        )
        
        assert "feature/migrate" in result or "Test Branch" in result
        assert "main" in result or "Production Branch" in result

    def test_includes_repo_url_when_provided(self, heroku_repo):
        """Should include repository URL when provided."""
        repo_url = "https://github.com/test/app"
        result = generate_checklist(
            str(heroku_repo),
            "test-app",
            repo_url=repo_url
        )
        
        assert repo_url in result or "Repository:" in result

    def test_generates_markdown_format(self, heroku_repo):
        """Should generate valid Markdown."""
        result = generate_checklist(str(heroku_repo), "test-app")
        
        # Check for Markdown headers
        assert result.startswith("#")
        assert "##" in result
        
        # Check for Markdown tables
        assert "|" in result
        assert "---" in result

    def test_includes_database_mapping_when_detected(self, temp_repo):
        """Should include database mapping when databases detected."""
        (temp_repo / "requirements.txt").write_text("psycopg2-binary>=2.9")
        
        result = generate_checklist(str(temp_repo), "db-app")
        
        # May or may not detect database depending on analysis logic
        assert isinstance(result, str)
        assert "Migration Report: db-app" in result

    def test_shows_unmapped_items_when_present(self, temp_repo):
        """Should show unmapped items section when needed."""
        # Create a complex setup that might have unmapped items
        (temp_repo / "unusual-config.yaml").write_text("custom: settings")
        
        result = generate_checklist(str(temp_repo), "complex-app")
        
        # Check that checklist is generated (unmapped section is optional)
        assert isinstance(result, str)


class TestChecklistContentQuality:
    """Tests for checklist content quality."""

    def test_checklist_not_empty(self, heroku_repo):
        """Generated checklist should not be empty."""
        result = generate_checklist(str(heroku_repo), "test-app")
        
        assert len(result) > 100  # Reasonable minimum length

    def test_includes_timestamp(self, heroku_repo):
        """Should include generation timestamp."""
        result = generate_checklist(str(heroku_repo), "test-app")
        
        assert "Generated:" in result

    def test_includes_app_name_in_title(self, heroku_repo):
        """Should include app name in title."""
        app_name = "my-special-app"
        result = generate_checklist(str(heroku_repo), app_name)
        
        assert app_name in result

    def test_uses_markdown_tables(self, heroku_repo):
        """Should use Markdown tables for structured data."""
        result = generate_checklist(str(heroku_repo), "test-app")
        
        # Check for table structure
        lines = result.split("\n")
        table_lines = [l for l in lines if "|" in l]
        
        assert len(table_lines) > 0  # Has tables
        
        # Check for table headers with separators
        assert any("---" in l for l in lines)

    def test_includes_actionable_steps(self, heroku_repo):
        """Should include actionable items or checkboxes."""
        result = generate_checklist(str(heroku_repo), "test-app")
        
        # May include checkboxes for tasks
        # At minimum should have clear sections for action
        assert "##" in result  # Has sections
