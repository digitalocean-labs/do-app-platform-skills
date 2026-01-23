"""Tests for validate_skills.py - SKILL.md schema validation."""

import os
import sys
import tempfile
import re
import pytest
from pathlib import Path

import yaml

try:
    import jsonschema
    HAS_JSONSCHEMA = True
except ImportError:
    HAS_JSONSCHEMA = False
    jsonschema = None

pytestmark = pytest.mark.skipif(not HAS_JSONSCHEMA, reason="jsonschema not installed")


def extract_frontmatter(content: str) -> dict | None:
    """Extract YAML frontmatter from markdown content."""
    pattern = r'^---\s*\n(.*?)\n---'
    match = re.match(pattern, content, re.DOTALL)
    if match:
        try:
            return yaml.safe_load(match.group(1))
        except yaml.YAMLError:
            return None
    return None


def find_skill_files(root: Path) -> list[Path]:
    """Find all SKILL.md files in the repository."""
    skill_files = []
    
    root_skill = root / "SKILL.md"
    if root_skill.exists():
        skill_files.append(root_skill)
    
    skills_dir = root / "skills"
    if skills_dir.exists():
        for skill_dir in skills_dir.iterdir():
            if skill_dir.is_dir():
                skill_file = skill_dir / "SKILL.md"
                if skill_file.exists():
                    skill_files.append(skill_file)
    
    return sorted(skill_files)


def validate_skill(skill_path: Path, schema: dict, verbose: bool = False) -> tuple[bool, list[str]]:
    """Validate a single SKILL.md file."""
    errors = []
    
    try:
        content = skill_path.read_text()
    except Exception as e:
        return False, [f"Could not read file: {e}"]
    
    frontmatter = extract_frontmatter(content)
    if frontmatter is None:
        return False, ["No valid YAML frontmatter found"]
    
    validator = jsonschema.Draft7Validator(schema)
    validation_errors = list(validator.iter_errors(frontmatter))
    
    for error in validation_errors:
        path = ".".join(str(p) for p in error.absolute_path) if error.absolute_path else "root"
        errors.append(f"{path}: {error.message}")
    
    return len(errors) == 0, errors


class TestExtractFrontmatter:
    """Tests for YAML frontmatter extraction."""
    
    def test_extracts_valid_frontmatter(self):
        """Should extract valid YAML frontmatter."""
        content = """---
name: test-skill
version: 1.0.0
description: A test skill for testing purposes.
---

# Test Skill

Some content here.
"""
        result = extract_frontmatter(content)
        
        assert result is not None
        assert result['name'] == 'test-skill'
        assert result['version'] == '1.0.0'
    
    def test_returns_none_for_missing_frontmatter(self):
        """Should return None if no frontmatter found."""
        content = """# Test Skill

No frontmatter here.
"""
        result = extract_frontmatter(content)
        assert result is None
    
    def test_returns_none_for_unclosed_frontmatter(self):
        """Should return None if frontmatter not properly closed."""
        content = """---
name: test-skill
version: 1.0.0

# Missing closing ---
"""
        result = extract_frontmatter(content)
        assert result is None
    
    def test_handles_complex_yaml(self):
        """Should handle complex YAML structures."""
        content = """---
name: complex-skill
version: 2.0.0
description: A complex skill.
related_skills:
  - skill-a
  - skill-b
deprecated: false
---
"""
        result = extract_frontmatter(content)
        
        assert result is not None
        assert result['related_skills'] == ['skill-a', 'skill-b']
        assert result['deprecated'] is False
    
    def test_handles_multiline_description(self):
        """Should handle multiline YAML values."""
        content = """---
name: multiline-skill
version: 1.0.0
description: >
  This is a longer description
  that spans multiple lines.
---
"""
        result = extract_frontmatter(content)
        
        assert result is not None
        assert 'longer description' in result['description']


class TestFindSkillFiles:
    """Tests for finding SKILL.md files."""
    
    def test_finds_root_skill(self):
        """Should find SKILL.md in root directory."""
        with tempfile.TemporaryDirectory() as tmpdir:
            root = Path(tmpdir)
            (root / "SKILL.md").write_text("---\nname: root\n---")
            
            files = find_skill_files(root)
            
            assert len(files) == 1
            assert files[0].name == "SKILL.md"
    
    def test_finds_skills_in_subdirectories(self):
        """Should find SKILL.md in skills subdirectories."""
        with tempfile.TemporaryDirectory() as tmpdir:
            root = Path(tmpdir)
            skills_dir = root / "skills"
            
            (skills_dir / "skill-a").mkdir(parents=True)
            (skills_dir / "skill-a" / "SKILL.md").write_text("---\nname: a\n---")
            
            (skills_dir / "skill-b").mkdir(parents=True)
            (skills_dir / "skill-b" / "SKILL.md").write_text("---\nname: b\n---")
            
            files = find_skill_files(root)
            
            assert len(files) == 2
    
    def test_returns_sorted_list(self):
        """Should return files in sorted order."""
        with tempfile.TemporaryDirectory() as tmpdir:
            root = Path(tmpdir)
            skills_dir = root / "skills"
            
            for name in ["zebra", "alpha", "beta"]:
                (skills_dir / name).mkdir(parents=True)
                (skills_dir / name / "SKILL.md").write_text(f"---\nname: {name}\n---")
            
            files = find_skill_files(root)
            names = [f.parent.name for f in files]
            
            assert names == sorted(names)
    
    def test_ignores_non_directories(self):
        """Should ignore files in skills directory."""
        with tempfile.TemporaryDirectory() as tmpdir:
            root = Path(tmpdir)
            skills_dir = root / "skills"
            skills_dir.mkdir()
            
            # Create a file, not a directory
            (skills_dir / "README.md").write_text("# Skills")
            
            files = find_skill_files(root)
            
            assert len(files) == 0


class TestValidateSkill:
    """Tests for skill validation."""
    
    @pytest.fixture
    def valid_schema(self):
        """Provide a valid schema for testing."""
        return {
            "type": "object",
            "required": ["name", "version", "description"],
            "properties": {
                "name": {"type": "string", "pattern": "^[a-z][a-z0-9-]*$"},
                "version": {"type": "string", "pattern": "^[0-9]+\\.[0-9]+\\.[0-9]+"},
                "description": {"type": "string", "minLength": 10},
                "related_skills": {"type": "array", "items": {"type": "string"}},
                "deprecated": {"type": "boolean"}
            }
        }
    
    def test_validates_correct_skill(self, valid_schema):
        """Should pass for valid SKILL.md."""
        with tempfile.TemporaryDirectory() as tmpdir:
            skill_path = Path(tmpdir) / "SKILL.md"
            skill_path.write_text("""---
name: valid-skill
version: 1.0.0
description: This is a valid skill description.
---

# Valid Skill
""")
            
            is_valid, errors = validate_skill(skill_path, valid_schema)
            
            assert is_valid is True
            assert errors == []
    
    def test_fails_for_missing_required_field(self, valid_schema):
        """Should fail if required field is missing."""
        with tempfile.TemporaryDirectory() as tmpdir:
            skill_path = Path(tmpdir) / "SKILL.md"
            skill_path.write_text("""---
name: incomplete-skill
description: Missing version field.
---
""")
            
            is_valid, errors = validate_skill(skill_path, valid_schema)
            
            assert is_valid is False
            assert any("version" in e.lower() for e in errors)
    
    def test_fails_for_invalid_version_format(self, valid_schema):
        """Should fail if version doesn't match semver pattern."""
        with tempfile.TemporaryDirectory() as tmpdir:
            skill_path = Path(tmpdir) / "SKILL.md"
            skill_path.write_text("""---
name: bad-version
version: v1.0
description: This skill has an invalid version format.
---
""")
            
            is_valid, errors = validate_skill(skill_path, valid_schema)
            
            assert is_valid is False
    
    def test_fails_for_invalid_name_pattern(self, valid_schema):
        """Should fail if name doesn't match pattern."""
        with tempfile.TemporaryDirectory() as tmpdir:
            skill_path = Path(tmpdir) / "SKILL.md"
            skill_path.write_text("""---
name: Invalid_Name
version: 1.0.0
description: This skill has an invalid name format.
---
""")
            
            is_valid, errors = validate_skill(skill_path, valid_schema)
            
            assert is_valid is False
    
    def test_fails_for_missing_frontmatter(self, valid_schema):
        """Should fail if no frontmatter found."""
        with tempfile.TemporaryDirectory() as tmpdir:
            skill_path = Path(tmpdir) / "SKILL.md"
            skill_path.write_text("""# No Frontmatter

This file has no YAML frontmatter.
""")
            
            is_valid, errors = validate_skill(skill_path, valid_schema)
            
            assert is_valid is False
            assert any("frontmatter" in e.lower() for e in errors)
    
    def test_handles_file_read_error(self, valid_schema):
        """Should handle file read errors gracefully."""
        non_existent_path = Path("/non/existent/SKILL.md")
        
        is_valid, errors = validate_skill(non_existent_path, valid_schema)
        
        assert is_valid is False
        assert len(errors) > 0


class TestSchemaValidation:
    """Tests for JSON Schema compliance."""
    
    def test_validates_related_skills_array(self):
        """Should validate related_skills as array of strings."""
        schema = {
            "type": "object",
            "properties": {
                "related_skills": {
                    "type": "array",
                    "items": {"type": "string"}
                }
            }
        }
        
        with tempfile.TemporaryDirectory() as tmpdir:
            skill_path = Path(tmpdir) / "SKILL.md"
            skill_path.write_text("""---
related_skills:
  - skill-a
  - skill-b
---
""")
            
            is_valid, errors = validate_skill(skill_path, schema)
            
            assert is_valid is True
    
    def test_fails_for_invalid_related_skills_type(self):
        """Should fail if related_skills contains non-strings."""
        schema = {
            "type": "object",
            "properties": {
                "related_skills": {
                    "type": "array",
                    "items": {"type": "string"}
                }
            }
        }
        
        with tempfile.TemporaryDirectory() as tmpdir:
            skill_path = Path(tmpdir) / "SKILL.md"
            skill_path.write_text("""---
related_skills:
  - 123
  - true
---
""")
            
            is_valid, errors = validate_skill(skill_path, schema)
            
            assert is_valid is False
