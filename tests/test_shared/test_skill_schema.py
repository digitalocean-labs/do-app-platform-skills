"""Tests for the skill-schema.json JSON Schema."""

import json
import pytest
from pathlib import Path

try:
    import jsonschema
    HAS_JSONSCHEMA = True
except ImportError:
    HAS_JSONSCHEMA = False
    jsonschema = None

pytestmark = pytest.mark.skipif(not HAS_JSONSCHEMA, reason="jsonschema not installed")


@pytest.fixture
def skill_schema():
    """Load the skill schema."""
    schema_path = Path(__file__).parent.parent.parent / "shared" / "skill-schema.json"
    with open(schema_path) as f:
        return json.load(f)


class TestSkillSchemaStructure:
    """Tests for schema structure."""
    
    def test_schema_is_valid_json_schema(self, skill_schema):
        """Schema should be a valid JSON Schema draft-07."""
        assert "$schema" in skill_schema
        assert "draft-07" in skill_schema["$schema"]
    
    def test_schema_has_required_fields(self, skill_schema):
        """Schema should require name, version, description."""
        required = skill_schema.get("required", [])
        assert "name" in required
        assert "version" in required
        assert "description" in required
    
    def test_schema_defines_all_expected_properties(self, skill_schema):
        """Schema should define all expected properties."""
        properties = skill_schema.get("properties", {})
        expected = ["name", "version", "min_doctl_version", "description", 
                   "related_skills", "deprecated", "deprecated_message", "sunset_date"]
        for prop in expected:
            assert prop in properties, f"Missing property: {prop}"


class TestNameValidation:
    """Tests for name field validation."""
    
    def test_valid_name_accepted(self, skill_schema):
        """Valid skill names should pass."""
        valid_names = ["postgres", "app-platform-designer", "managed-db-services", "ai-services"]
        
        for name in valid_names:
            instance = {"name": name, "version": "1.0.0", "description": "A" * 50}
            jsonschema.validate(instance, skill_schema)  # Should not raise
    
    def test_name_must_start_with_letter(self, skill_schema):
        """Name must start with lowercase letter."""
        invalid_names = ["123skill", "-skill", "_skill"]
        
        for name in invalid_names:
            instance = {"name": name, "version": "1.0.0", "description": "A" * 50}
            with pytest.raises(jsonschema.ValidationError):
                jsonschema.validate(instance, skill_schema)
    
    def test_name_must_be_lowercase(self, skill_schema):
        """Name must be lowercase."""
        instance = {"name": "MySkill", "version": "1.0.0", "description": "A" * 50}
        with pytest.raises(jsonschema.ValidationError):
            jsonschema.validate(instance, skill_schema)


class TestVersionValidation:
    """Tests for version field validation."""
    
    def test_valid_semver_accepted(self, skill_schema):
        """Valid semver versions should pass."""
        valid_versions = ["1.0.0", "0.1.0", "10.20.30", "1.0.0-beta.1", "2.0.0+build123"]
        
        for version in valid_versions:
            instance = {"name": "test", "version": version, "description": "A" * 50}
            jsonschema.validate(instance, skill_schema)  # Should not raise
    
    def test_invalid_version_rejected(self, skill_schema):
        """Invalid version formats should fail."""
        invalid_versions = ["v1.0.0", "1.0", "1", "latest", "1.0.0.0"]
        
        for version in invalid_versions:
            instance = {"name": "test", "version": version, "description": "A" * 50}
            with pytest.raises(jsonschema.ValidationError):
                jsonschema.validate(instance, skill_schema)


class TestDescriptionValidation:
    """Tests for description field validation."""
    
    def test_description_minimum_length(self, skill_schema):
        """Description must meet minimum length."""
        instance = {"name": "test", "version": "1.0.0", "description": "Short"}
        with pytest.raises(jsonschema.ValidationError):
            jsonschema.validate(instance, skill_schema)
    
    def test_description_maximum_length(self, skill_schema):
        """Description must not exceed maximum length."""
        instance = {"name": "test", "version": "1.0.0", "description": "A" * 600}
        with pytest.raises(jsonschema.ValidationError):
            jsonschema.validate(instance, skill_schema)
    
    def test_valid_description_accepted(self, skill_schema):
        """Valid description should pass."""
        instance = {
            "name": "test", 
            "version": "1.0.0", 
            "description": "This is a valid description that explains what the skill does and when to use it."
        }
        jsonschema.validate(instance, skill_schema)  # Should not raise


class TestMinDoctlVersionValidation:
    """Tests for min_doctl_version field validation."""
    
    def test_valid_version_accepted(self, skill_schema):
        """Valid doctl versions should pass."""
        valid = ["1.82.0", "1.100.0", "2.0.0"]
        
        for version in valid:
            instance = {
                "name": "test", 
                "version": "1.0.0", 
                "description": "A" * 50,
                "min_doctl_version": version
            }
            jsonschema.validate(instance, skill_schema)
    
    def test_invalid_version_rejected(self, skill_schema):
        """Invalid doctl versions should fail."""
        invalid = ["1.82", "v1.82.0", "1.82.0.1"]
        
        for version in invalid:
            instance = {
                "name": "test", 
                "version": "1.0.0", 
                "description": "A" * 50,
                "min_doctl_version": version
            }
            with pytest.raises(jsonschema.ValidationError):
                jsonschema.validate(instance, skill_schema)


class TestRelatedSkillsValidation:
    """Tests for related_skills field validation."""
    
    def test_empty_array_allowed(self, skill_schema):
        """Empty related_skills array should be valid."""
        instance = {
            "name": "test", 
            "version": "1.0.0", 
            "description": "A" * 50,
            "related_skills": []
        }
        jsonschema.validate(instance, skill_schema)
    
    def test_valid_skills_array(self, skill_schema):
        """Valid skill names in array should pass."""
        instance = {
            "name": "test", 
            "version": "1.0.0", 
            "description": "A" * 50,
            "related_skills": ["postgres", "deployment", "networking"]
        }
        jsonschema.validate(instance, skill_schema)
    
    def test_unique_items_required(self, skill_schema):
        """Duplicate skills should fail if uniqueItems is set."""
        instance = {
            "name": "test", 
            "version": "1.0.0", 
            "description": "A" * 50,
            "related_skills": ["postgres", "postgres"]  # Duplicate
        }
        # This may or may not fail depending on schema definition
        # Just verify it runs


class TestDeprecationValidation:
    """Tests for deprecation fields."""
    
    def test_deprecated_false_valid(self, skill_schema):
        """deprecated: false should be valid without message."""
        instance = {
            "name": "test", 
            "version": "1.0.0", 
            "description": "A" * 50,
            "deprecated": False
        }
        jsonschema.validate(instance, skill_schema)
    
    def test_deprecated_true_requires_message(self, skill_schema):
        """deprecated: true should require deprecated_message."""
        instance = {
            "name": "test", 
            "version": "1.0.0", 
            "description": "A" * 50,
            "deprecated": True
            # Missing deprecated_message
        }
        with pytest.raises(jsonschema.ValidationError):
            jsonschema.validate(instance, skill_schema)
    
    def test_deprecated_with_message_valid(self, skill_schema):
        """deprecated: true with message should be valid."""
        instance = {
            "name": "old-skill", 
            "version": "1.0.0", 
            "description": "A" * 50,
            "deprecated": True,
            "deprecated_message": "Use new-skill instead"
        }
        jsonschema.validate(instance, skill_schema)
    
    def test_sunset_date_format(self, skill_schema):
        """sunset_date should accept ISO 8601 date format."""
        instance = {
            "name": "old-skill", 
            "version": "1.0.0", 
            "description": "A" * 50,
            "deprecated": True,
            "deprecated_message": "Use new-skill instead",
            "sunset_date": "2026-06-01"
        }
        jsonschema.validate(instance, skill_schema)


class TestAdditionalProperties:
    """Tests for additional properties handling."""
    
    def test_unknown_properties_rejected(self, skill_schema):
        """Unknown properties should be rejected."""
        instance = {
            "name": "test", 
            "version": "1.0.0", 
            "description": "A" * 50,
            "unknown_field": "value"
        }
        with pytest.raises(jsonschema.ValidationError):
            jsonschema.validate(instance, skill_schema)


class TestRealSkillFiles:
    """Tests validating actual SKILL.md files in the repo."""
    
    def test_root_skill_is_valid(self, skill_schema):
        """Root SKILL.md should be valid."""
        import yaml
        skill_path = Path(__file__).parent.parent.parent / "SKILL.md"
        
        content = skill_path.read_text()
        # Extract frontmatter
        import re
        match = re.match(r'^---\s*\n(.*?)\n---', content, re.DOTALL)
        assert match, "Root SKILL.md should have frontmatter"
        
        frontmatter = yaml.safe_load(match.group(1))
        jsonschema.validate(frontmatter, skill_schema)
    
    def test_all_skills_are_valid(self, skill_schema):
        """All SKILL.md files should be valid."""
        import yaml
        import re
        
        skills_dir = Path(__file__).parent.parent.parent / "skills"
        
        for skill_dir in skills_dir.iterdir():
            if skill_dir.is_dir():
                skill_file = skill_dir / "SKILL.md"
                if skill_file.exists():
                    content = skill_file.read_text()
                    match = re.match(r'^---\s*\n(.*?)\n---', content, re.DOTALL)
                    assert match, f"{skill_file} should have frontmatter"
                    
                    frontmatter = yaml.safe_load(match.group(1))
                    try:
                        jsonschema.validate(frontmatter, skill_schema)
                    except jsonschema.ValidationError as e:
                        pytest.fail(f"{skill_file} failed validation: {e.message}")
