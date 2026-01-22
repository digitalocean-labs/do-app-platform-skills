"""End-to-end workflow tests."""

import pytest
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent.parent / "skills" / "migration" / "scripts"))
sys.path.insert(0, str(Path(__file__).parent.parent.parent / "skills" / "postgres" / "scripts"))


class TestMigrationWorkflow:
    """Tests for complete migration workflow."""

    def test_complete_heroku_migration_workflow(self, heroku_repo):
        """Should complete full migration workflow for Heroku app."""
        from detect_platform import PlatformDetector
        from analyze_architecture import ArchitectureAnalyzer
        from generate_app_spec import AppSpecGenerator
        from generate_checklist import generate_checklist
        
        # Step 1: Detect platform
        detector = PlatformDetector(str(heroku_repo))
        platform_info = detector.detect()
        assert platform_info["primary_platform"] == "heroku"
        
        # Step 2: Analyze architecture
        analyzer = ArchitectureAnalyzer(str(heroku_repo))
        architecture = analyzer.analyze()
        assert "components" in architecture
        
        # Step 3: Generate app spec
        generator = AppSpecGenerator(str(heroku_repo), "test-app", "test")
        spec = generator.generate()
        assert "spec" in spec
        
        # Step 4: Generate checklist
        checklist = generate_checklist(str(heroku_repo), "test-app")
        assert "Migration Report" in checklist
        assert "test-app" in checklist

    def test_docker_compose_migration_workflow(self, docker_compose_repo):
        """Should complete migration workflow for Docker Compose app."""
        from detect_platform import PlatformDetector
        from analyze_architecture import ArchitectureAnalyzer
        from generate_app_spec import AppSpecGenerator
        
        # Detect platform
        detector = PlatformDetector(str(docker_compose_repo))
        platform_info = detector.detect()
        assert platform_info["primary_platform"] == "docker_compose"
        
        # Analyze
        analyzer = ArchitectureAnalyzer(str(docker_compose_repo))
        architecture = analyzer.analyze()
        assert architecture["has_docker_compose"] is True
        
        # Generate spec
        generator = AppSpecGenerator(str(docker_compose_repo), "multi-app", "test")
        spec = generator.generate()
        assert "spec" in spec

    def test_generic_docker_migration_workflow(self, temp_repo):
        """Should handle generic Docker application."""
        from detect_platform import PlatformDetector
        from analyze_architecture import ArchitectureAnalyzer
        from generate_app_spec import AppSpecGenerator
        
        (temp_repo / "Dockerfile").write_text("FROM python:3.12\nCOPY . /app\nCMD python app.py")
        (temp_repo / "requirements.txt").write_text("flask>=2.0")
        
        # Workflow
        detector = PlatformDetector(str(temp_repo))
        platform_info = detector.detect()
        assert platform_info["primary_platform"] == "generic_docker"
        
        analyzer = ArchitectureAnalyzer(str(temp_repo))
        architecture = analyzer.analyze()
        
        generator = AppSpecGenerator(str(temp_repo), "docker-app", "test")
        spec = generator.generate()
        assert spec["spec"]["name"] == "docker-app-test"

    def test_workflow_generates_both_environments(self, heroku_repo):
        """Should generate specs for both test and production."""
        from generate_app_spec import AppSpecGenerator
        
        test_gen = AppSpecGenerator(str(heroku_repo), "myapp", "test")
        prod_gen = AppSpecGenerator(str(heroku_repo), "myapp", "production")
        
        test_spec = test_gen.generate()
        prod_spec = prod_gen.generate()
        
        assert test_spec["spec"]["name"] == "myapp-test"
        assert prod_spec["spec"]["name"] == "myapp-production"
        
        # Should have different configurations
        assert test_spec != prod_spec


class TestDatabaseSetupWorkflow:
    """Tests for database setup workflow."""

    def test_schema_user_creation_workflow(self, tmp_path):
        """Should complete schema and user creation workflow."""
        from create_schema_user import generate_sql
        
        # Generate SQL
        generate_sql("client1", "client1_user", "securepass123", output_dir=str(tmp_path))
        
        # Verify files created
        assert (tmp_path / "db-setup.sql").exists()
        assert (tmp_path / "db-users.sql").exists()
        assert (tmp_path / "db-permissions.sql").exists()
        
        # Verify content
        setup = (tmp_path / "db-setup.sql").read_text()
        assert "CREATE SCHEMA" in setup
        assert "client1" in setup

    def test_add_client_workflow(self, tmp_path):
        """Should add new client to multi-tenant setup."""
        from add_client import generate_password, generate_sql
        
        # Generate password
        password = generate_password(32)
        assert len(password) == 32
        
        # Generate SQL for client
        result_password = generate_sql("acme_corp", "acme_user", password, output_dir=str(tmp_path))
        assert result_password == password
        
        # Verify files
        assert (tmp_path / "db-setup.sql").exists()
        assert (tmp_path / "db-users.sql").exists()
        assert (tmp_path / "db-permissions.sql").exists()

    def test_connection_string_generation_workflow(self, capsys):
        """Should generate connection strings for client."""
        from generate_connection_string import generate_connection_strings
        
        base = "postgresql://admin:adminpass@db.example.com:25060/defaultdb?sslmode=require"
        generate_connection_strings(base, "client_user", "client_pass", schema="client_schema")
        
        output = capsys.readouterr().out
        
        # Should generate multiple formats
        assert "client_user:client_pass@" in output
        assert "DATABASE_URL=" in output
        assert "client_schema" in output

    def test_cleanup_workflow(self):
        """Should generate cleanup SQL for client removal."""
        from cleanup_client import generate_sql as generate_cleanup_sql
        
        sql = generate_cleanup_sql("old_client", keep_user=False)
        
        assert "pg_terminate_backend" in sql
        assert "DROP SCHEMA" in sql
        assert "DROP USER" in sql
        assert "CASCADE" in sql


class TestWorkflowIntegration:
    """Tests for workflow integration and data flow."""

    def test_platform_detection_feeds_architecture_analysis(self, heroku_repo):
        """Platform info should inform architecture analysis."""
        from detect_platform import PlatformDetector
        from analyze_architecture import ArchitectureAnalyzer
        
        detector = PlatformDetector(str(heroku_repo))
        platform_info = detector.detect()
        
        analyzer = ArchitectureAnalyzer(str(heroku_repo))
        architecture = analyzer.analyze()
        
        # Both should detect the same runtime indicators
        assert "has_dockerfile" in platform_info
        assert "has_dockerfile" in architecture

    def test_architecture_analysis_feeds_spec_generation(self, heroku_repo):
        """Architecture analysis should inform spec generation."""
        from analyze_architecture import ArchitectureAnalyzer
        from generate_app_spec import AppSpecGenerator
        
        analyzer = ArchitectureAnalyzer(str(heroku_repo))
        architecture = analyzer.analyze()
        
        generator = AppSpecGenerator(str(heroku_repo), "test-app", "test")
        
        # Generator uses analyzer internally
        assert generator.architecture is not None
        assert "components" in generator.architecture

    def test_all_components_flow_to_checklist(self, heroku_repo):
        """All detected components should appear in checklist."""
        from generate_checklist import generate_checklist
        
        checklist = generate_checklist(str(heroku_repo), "test-app")
        
        # Checklist should include component information
        assert "Component Mapping" in checklist or "components" in checklist.lower()

    def test_workflow_handles_monorepo(self, temp_repo):
        """Should handle monorepo structure throughout workflow."""
        from detect_platform import PlatformDetector
        from analyze_architecture import ArchitectureAnalyzer
        from generate_app_spec import AppSpecGenerator
        
        # Create monorepo structure
        (temp_repo / "frontend").mkdir()
        (temp_repo / "backend").mkdir()
        (temp_repo / "frontend" / "package.json").write_text('{"name": "frontend"}')
        (temp_repo / "backend" / "requirements.txt").write_text("fastapi>=0.100")
        
        # Detect
        detector = PlatformDetector(str(temp_repo))
        platform_info = detector.detect()
        
        # Analyze
        analyzer = ArchitectureAnalyzer(str(temp_repo))
        architecture = analyzer.analyze()
        
        # Generate
        generator = AppSpecGenerator(str(temp_repo), "monorepo-app", "test")
        spec = generator.generate()
        
        # Should handle monorepo
        assert spec is not None


class TestWorkflowErrorRecovery:
    """Tests for workflow error handling and recovery."""

    def test_workflow_continues_with_empty_repo(self, temp_repo):
        """Workflow should handle empty repository gracefully."""
        from detect_platform import PlatformDetector
        from analyze_architecture import ArchitectureAnalyzer
        from generate_app_spec import AppSpecGenerator
        
        # Empty repo
        detector = PlatformDetector(str(temp_repo))
        platform_info = detector.detect()
        assert platform_info["primary_platform"] == "unknown"
        
        analyzer = ArchitectureAnalyzer(str(temp_repo))
        architecture = analyzer.analyze()
        assert architecture["runtime"] == "unknown"
        
        generator = AppSpecGenerator(str(temp_repo), "empty-app", "test")
        spec = generator.generate()
        assert "spec" in spec

    def test_workflow_handles_partial_configuration(self, temp_repo):
        """Should handle repositories with partial configuration."""
        from generate_app_spec import AppSpecGenerator
        
        # Only Procfile, no other config
        (temp_repo / "Procfile").write_text("web: python app.py")
        
        generator = AppSpecGenerator(str(temp_repo), "partial-app", "test")
        spec = generator.generate()
        
        # Should generate something
        assert "spec" in spec
        assert "name" in spec["spec"]

    def test_workflow_tracks_unmapped_items(self, temp_repo):
        """Should track items that couldn't be mapped."""
        from generate_app_spec import AppSpecGenerator
        
        # Create complex unmappable scenario
        (temp_repo / "unusual-config.yaml").write_text("custom: true")
        
        generator = AppSpecGenerator(str(temp_repo), "complex-app", "test")
        generator.generate()
        
        # Unmapped items should be tracked
        assert hasattr(generator, "unmapped_items")
        assert isinstance(generator.unmapped_items, list)
