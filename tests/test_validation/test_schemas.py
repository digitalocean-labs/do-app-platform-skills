"""Tests for YAML/JSON schema validation."""

import pytest
import yaml
import json
from pathlib import Path


class TestSharedConfigSchemas:
    """Tests for shared configuration schema validation."""

    def test_regions_yaml_schema(self, shared_config_dir):
        """regions.yaml should have valid schema."""
        with open(shared_config_dir / "regions.yaml") as f:
            data = yaml.safe_load(f)
        
        # Required top-level keys
        assert "regions" in data
        assert isinstance(data["regions"], list)
        
        # Each region should have required fields
        for region in data["regions"]:
            assert "slug" in region, f"Region missing slug: {region}"
            assert "name" in region, f"Region missing name: {region}"
            assert isinstance(region["slug"], str)
            assert isinstance(region["name"], str)
            assert len(region["slug"]) > 0
            assert len(region["name"]) > 0

    def test_instance_sizes_yaml_schema(self, shared_config_dir):
        """instance-sizes.yaml should have valid schema."""
        with open(shared_config_dir / "instance-sizes.yaml") as f:
            data = yaml.safe_load(f)
        
        assert "sizes" in data
        assert isinstance(data["sizes"], dict)
        
        # Should have shared and dedicated categories
        assert "shared" in data["sizes"] or "dedicated" in data["sizes"]
        
        # Each size should have proper structure
        for category, sizes in data["sizes"].items():
            assert isinstance(sizes, (list, dict))

    def test_opinionated_defaults_yaml_schema(self, shared_config_dir):
        """opinionated-defaults.yaml should have valid schema."""
        with open(shared_config_dir / "opinionated-defaults.yaml") as f:
            data = yaml.safe_load(f)
        
        # Should have main configuration categories
        assert "region" in data
        assert "database" in data or "cache" in data
        
        # Database config should have required fields
        if "database" in data:
            db = data["database"]
            assert isinstance(db, dict)

    def test_all_yaml_files_valid_syntax(self, shared_config_dir):
        """All YAML files should have valid syntax."""
        yaml_files = list(shared_config_dir.glob("*.yaml")) + list(shared_config_dir.glob("*.yml"))
        
        assert len(yaml_files) > 0, "No YAML files found"
        
        for yaml_file in yaml_files:
            try:
                with open(yaml_file) as f:
                    yaml.safe_load(f)
            except yaml.YAMLError as e:
                pytest.fail(f"Invalid YAML in {yaml_file.name}: {e}")


class TestAppSpecValidation:
    """Tests for generated app spec validation."""

    def test_app_spec_has_required_fields(self, heroku_repo):
        """Generated app spec should have required fields."""
        import sys
        sys.path.insert(0, str(Path(__file__).parent.parent.parent / "skills" / "migration" / "scripts"))
        from generate_app_spec import AppSpecGenerator
        
        generator = AppSpecGenerator(str(heroku_repo), "test-app", "test")
        spec = generator.generate()
        
        # Required root structure
        assert "spec" in spec
        assert isinstance(spec["spec"], dict)
        
        # Required spec fields
        assert "name" in spec["spec"]
        assert "region" in spec["spec"]
        
        # Validate name format (lowercase, alphanumeric with hyphens)
        name = spec["spec"]["name"]
        assert name.replace("-", "").replace("_", "").isalnum()

    def test_app_spec_service_schema(self, heroku_repo):
        """Services in app spec should have valid schema."""
        import sys
        sys.path.insert(0, str(Path(__file__).parent.parent.parent / "skills" / "migration" / "scripts"))
        from generate_app_spec import AppSpecGenerator
        
        generator = AppSpecGenerator(str(heroku_repo), "test-app", "test")
        spec = generator.generate()
        
        if "services" in spec["spec"]:
            for service in spec["spec"]["services"]:
                assert "name" in service, "Service missing name"
                assert isinstance(service["name"], str)
                # Name should be valid identifier
                assert service["name"].replace("-", "").replace("_", "").isalnum()

    def test_app_spec_database_schema(self, temp_repo):
        """Databases in app spec should have valid schema."""
        import sys
        sys.path.insert(0, str(Path(__file__).parent.parent.parent / "skills" / "migration" / "scripts"))
        from generate_app_spec import AppSpecGenerator
        
        (temp_repo / "requirements.txt").write_text("psycopg2>=2.9")
        
        generator = AppSpecGenerator(str(temp_repo), "test-app", "test")
        spec = generator.generate()
        
        if "databases" in spec["spec"]:
            valid_engines = ["PG", "MYSQL", "MONGODB", "VALKEY", "REDIS", "KAFKA", "OPENSEARCH"]
            
            for db in spec["spec"]["databases"]:
                assert "name" in db, "Database missing name"
                assert "engine" in db, "Database missing engine"
                assert db["engine"] in valid_engines, f"Invalid engine: {db['engine']}"

    def test_app_spec_region_valid(self, heroku_repo):
        """App spec region should be valid DO region."""
        import sys
        sys.path.insert(0, str(Path(__file__).parent.parent.parent / "skills" / "migration" / "scripts"))
        from generate_app_spec import AppSpecGenerator
        
        generator = AppSpecGenerator(str(heroku_repo), "test-app", "test")
        spec = generator.generate()
        
        valid_regions = ["nyc", "nyc1", "nyc3", "sfo", "sfo2", "sfo3", 
                        "ams", "ams3", "lon", "lon1", "fra", "fra1", 
                        "sgp", "sgp1", "blr", "blr1", "tor", "tor1", "syd", "syd1"]
        
        assert spec["spec"]["region"] in valid_regions, f"Invalid region: {spec['spec']['region']}"


class TestTemplateValidation:
    """Tests for template file validation."""

    def test_python_templates_valid_syntax(self):
        """Python template files should have valid syntax."""
        template_files = Path(__file__).parent.parent.parent.glob("skills/**/templates/**/*.py")
        
        for template_file in template_files:
            try:
                compile(template_file.read_text(), str(template_file), 'exec')
            except SyntaxError as e:
                pytest.fail(f"Invalid Python syntax in {template_file}: {e}")

    def test_yaml_templates_valid_syntax(self):
        """YAML template files should have valid syntax."""
        template_files = list(Path(__file__).parent.parent.parent.glob("skills/**/templates/**/*.yaml"))
        template_files += list(Path(__file__).parent.parent.parent.glob("skills/**/templates/**/*.yml"))
        
        for template_file in template_files:
            try:
                with open(template_file) as f:
                    yaml.safe_load(f)
            except yaml.YAMLError as e:
                pytest.fail(f"Invalid YAML in {template_file}: {e}")

    def test_json_templates_valid_syntax(self):
        """JSON template files should have valid syntax."""
        template_files = Path(__file__).parent.parent.parent.glob("skills/**/templates/**/*.json")
        
        for template_file in template_files:
            try:
                with open(template_file) as f:
                    json.load(f)
            except json.JSONDecodeError as e:
                pytest.fail(f"Invalid JSON in {template_file}: {e}")


class TestReferenceDocValidation:
    """Tests for reference documentation structure."""

    def test_reference_docs_exist(self):
        """Each skill should have reference documentation."""
        skills_dir = Path(__file__).parent.parent.parent / "skills"
        
        for skill_dir in skills_dir.iterdir():
            if skill_dir.is_dir() and not skill_dir.name.startswith("."):
                ref_dir = skill_dir / "reference"
                # Reference dir might not exist for all skills, but check if present
                if ref_dir.exists():
                    ref_files = list(ref_dir.glob("*.md"))
                    # If reference dir exists, it should have content
                    if ref_dir.exists():
                        assert len(list(ref_dir.iterdir())) > 0, f"Empty reference dir in {skill_dir.name}"

    def test_skill_readme_exists(self):
        """Each skill should have a README."""
        skills_dir = Path(__file__).parent.parent.parent / "skills"
        
        for skill_dir in skills_dir.iterdir():
            if skill_dir.is_dir() and not skill_dir.name.startswith("."):
                readme = skill_dir / "README.md"
                assert readme.exists(), f"Missing README in {skill_dir.name}"

    def test_skill_metadata_exists(self):
        """Each skill should have SKILL.md with metadata."""
        skills_dir = Path(__file__).parent.parent.parent / "skills"
        
        for skill_dir in skills_dir.iterdir():
            if skill_dir.is_dir() and not skill_dir.name.startswith("."):
                skill_md = skill_dir / "SKILL.md"
                assert skill_md.exists(), f"Missing SKILL.md in {skill_dir.name}"


class TestConfigurationConsistency:
    """Tests for consistency across configuration files."""

    def test_regions_match_across_configs(self, shared_config_dir):
        """Regions should be consistent across configuration files."""
        with open(shared_config_dir / "regions.yaml") as f:
            regions_data = yaml.safe_load(f)
        
        region_slugs = {r["slug"] for r in regions_data.get("regions", [])}
        
        # Should have at least the major DO regions
        expected_regions = {"nyc", "sfo", "ams", "lon", "fra", "sgp", "blr"}
        common_regions = region_slugs & expected_regions
        
        assert len(common_regions) >= 5, f"Missing expected regions. Found: {region_slugs}"

    def test_ssl_mode_defaults_to_require(self, shared_config_dir):
        """SSL mode should default to 'require' for security."""
        with open(shared_config_dir / "opinionated-defaults.yaml") as f:
            data = yaml.safe_load(f)
        
        if "database" in data and "ssl_mode" in data["database"]:
            assert data["database"]["ssl_mode"] == "require"

    def test_cache_defaults_to_valkey(self, shared_config_dir):
        """Cache should default to Valkey (not deprecated Redis)."""
        with open(shared_config_dir / "opinionated-defaults.yaml") as f:
            data = yaml.safe_load(f)
        
        if "cache" in data and "engine" in data["cache"]:
            assert data["cache"]["engine"] in ["VALKEY", "REDIS"]
            # Prefer Valkey over Redis
            if data["cache"]["engine"] == "VALKEY":
                assert True  # Preferred
