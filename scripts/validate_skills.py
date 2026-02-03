#!/usr/bin/env python3
"""
Validate SKILL.md frontmatter against the skill schema.

This script extracts YAML frontmatter from SKILL.md files and validates
it against the JSON Schema defined in shared/skill-schema.json.

Usage:
    python scripts/validate_skills.py [--verbose]
"""

import argparse
import json
import re
import sys
from pathlib import Path

# Defer import error to runtime, not module load time
yaml = None
jsonschema = None

def _check_imports():
    """Check required packages are installed."""
    global yaml, jsonschema
    try:
        import yaml as _yaml
        import jsonschema as _jsonschema
        yaml = _yaml
        jsonschema = _jsonschema
        return True
    except ImportError:
        print("Error: Required packages not installed.")
        print("Install with: pip install pyyaml jsonschema")
        return False


def extract_frontmatter(content: str) -> dict | None:
    """Extract YAML frontmatter from markdown content."""
    if yaml is None:
        _check_imports()
    pattern = r'^---\s*\n(.*?)\n---'
    match = re.match(pattern, content, re.DOTALL)
    if match:
        try:
            return yaml.safe_load(match.group(1))
        except yaml.YAMLError as e:
            print(f"  YAML parse error: {e}")
            return None
    return None


def find_skill_files(root: Path) -> list[Path]:
    """Find all SKILL.md files in the repository."""
    skill_files = []
    
    # Root SKILL.md
    root_skill = root / "SKILL.md"
    if root_skill.exists():
        skill_files.append(root_skill)
    
    # Skills directory
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
    
    if verbose:
        print(f"  Frontmatter: {json.dumps(frontmatter, indent=2)}")
    
    validator = jsonschema.Draft7Validator(schema)
    validation_errors = list(validator.iter_errors(frontmatter))
    
    for error in validation_errors:
        path = ".".join(str(p) for p in error.absolute_path) if error.absolute_path else "root"
        errors.append(f"{path}: {error.message}")
    
    return len(errors) == 0, errors


def main():
    parser = argparse.ArgumentParser(description="Validate SKILL.md frontmatter")
    parser.add_argument("--verbose", "-v", action="store_true", help="Show detailed output")
    args = parser.parse_args()
    
    # Check imports at runtime
    if not _check_imports():
        sys.exit(1)
    
    # Find repository root
    script_path = Path(__file__).resolve()
    repo_root = script_path.parent.parent
    
    # Load schema
    schema_path = repo_root / "shared" / "skill-schema.json"
    if not schema_path.exists():
        print(f"Error: Schema not found at {schema_path}")
        sys.exit(1)
    
    with open(schema_path) as f:
        schema = json.load(f)
    
    # Find and validate all SKILL.md files
    skill_files = find_skill_files(repo_root)
    
    if not skill_files:
        print("No SKILL.md files found")
        sys.exit(1)
    
    print(f"Validating {len(skill_files)} SKILL.md files...\n")
    
    all_valid = True
    results = []
    
    for skill_path in skill_files:
        relative_path = skill_path.relative_to(repo_root)
        valid, errors = validate_skill(skill_path, schema, args.verbose)
        
        if valid:
            results.append((relative_path, "✅ Valid", []))
        else:
            all_valid = False
            results.append((relative_path, "❌ Invalid", errors))
    
    # Print results
    print("Results:")
    print("-" * 60)
    
    for path, status, errors in results:
        print(f"{status} {path}")
        for error in errors:
            print(f"     └─ {error}")
    
    print("-" * 60)
    valid_count = sum(1 for _, status, _ in results if "Valid" in status)
    print(f"\n{valid_count}/{len(results)} skills valid")
    
    if all_valid:
        print("\n✅ All SKILL.md files are valid!")
        sys.exit(0)
    else:
        print("\n❌ Some SKILL.md files have validation errors")
        sys.exit(1)


if __name__ == "__main__":
    main()
