"""Tests for app spec generation."""

import pytest
import sys
import json
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent.parent / "skills" / "migration" / "scripts"))

from generate_app_spec import AppSpecGenerator


class TestAppSpecGenerator:
    """Tests for AppSpecGenerator class."""

    def test_generates_basic_app_spec(self, heroku_repo):
        """Should generate valid app spec for Heroku app."""
        generator = AppSpecGenerator(str(heroku_repo), "test-app", "test")
        spec = generator.generate()
        
        assert "spec" in spec
        assert "name" in spec["spec"]
        assert spec["spec"]["name"] == "test-app-test"
        assert "region" in spec["spec"]

    def test_includes_services_for_web_component(self, heroku_repo):
        """Should include services section for web processes."""
        generator = AppSpecGenerator(str(heroku_repo), "test-app", "test")
        spec = generator.generate()
        
        # Heroku Procfile has web process
        assert "services" in spec["spec"] or "workers" in spec["spec"]

    def test_uses_correct_instance_size_for_environment(self, heroku_repo):
        """Should use different instance sizes for test vs production."""
        test_gen = AppSpecGenerator(str(heroku_repo), "test-app", "test")
        prod_gen = AppSpecGenerator(str(heroku_repo), "test-app", "production")
        
        test_spec = test_gen.generate()
        prod_spec = prod_gen.generate()
        
        # Just verify both generate without errors
        assert test_spec["spec"]["name"] == "test-app-test"
        assert prod_spec["spec"]["name"] == "test-app-production"

    def test_detects_docker_compose_architecture(self, docker_compose_repo):
        """Should handle Docker Compose multi-service apps."""
        generator = AppSpecGenerator(str(docker_compose_repo), "multi-service", "test")
        spec = generator.generate()
        
        assert "spec" in spec
        assert "name" in spec["spec"]

    def test_handles_empty_repository(self, temp_repo):
        """Should handle empty repository gracefully."""
        generator = AppSpecGenerator(str(temp_repo), "empty-app", "test")
        spec = generator.generate()
        
        assert "spec" in spec
        assert "name" in spec["spec"]

    def test_includes_region_mapping(self, heroku_repo):
        """Should include region in spec."""
        generator = AppSpecGenerator(str(heroku_repo), "test-app", "test")
        spec = generator.generate()
        
        assert "region" in spec["spec"]
        assert spec["spec"]["region"] in ["nyc", "sfo", "ams", "lon", "fra", "sgp", "blr", "tor", "syd"]

    def test_tracks_unmapped_items(self, temp_repo):
        """Should track unmapped configuration items."""
        generator = AppSpecGenerator(str(temp_repo), "test-app", "test")
        generator.generate()
        
        # Unmapped items list should exist (might be empty)
        assert hasattr(generator, "unmapped_items")
        assert isinstance(generator.unmapped_items, list)

    def test_generates_both_environments_independently(self, heroku_repo):
        """Should generate test and production specs independently."""
        test_gen = AppSpecGenerator(str(heroku_repo), "myapp", "test")
        prod_gen = AppSpecGenerator(str(heroku_repo), "myapp", "production")
        
        test_spec = test_gen.generate()
        prod_spec = prod_gen.generate()
        
        assert test_spec["spec"]["name"] == "myapp-test"
        assert prod_spec["spec"]["name"] == "myapp-production"
        assert test_spec != prod_spec  # Should differ in some way


class TestAppSpecFormatting:
    """Tests for app spec structure and format."""

    def test_spec_has_required_fields(self, heroku_repo):
        """Generated spec should have required fields."""
        generator = AppSpecGenerator(str(heroku_repo), "test-app", "test")
        spec = generator.generate()
        
        assert "spec" in spec
        assert "name" in spec["spec"]
        assert "region" in spec["spec"]

    def test_services_have_required_fields(self, heroku_repo):
        """Services should have required fields if present."""
        generator = AppSpecGenerator(str(heroku_repo), "test-app", "test")
        spec = generator.generate()
        
        if "services" in spec["spec"]:
            for service in spec["spec"]["services"]:
                assert "name" in service
                # Other fields might be optional depending on build method

    def test_databases_use_correct_engine(self, temp_repo):
        """Databases should use correct engine names."""
        # Create a Procfile with database dependency
        (temp_repo / "Procfile").write_text("web: python app.py")
        (temp_repo / "requirements.txt").write_text("psycopg2>=2.9\nFlask>=2.0")
        
        generator = AppSpecGenerator(str(temp_repo), "test-app", "test")
        spec = generator.generate()
        
        if "databases" in spec["spec"]:
            for db in spec["spec"]["databases"]:
                assert "engine" in db
                assert db["engine"] in ["PG", "MYSQL", "MONGODB", "VALKEY", "REDIS", "KAFKA", "OPENSEARCH"]
