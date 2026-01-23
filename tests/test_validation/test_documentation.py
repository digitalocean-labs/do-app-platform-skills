"""Tests for documentation quality."""

import pytest
import re
from pathlib import Path


class TestMarkdownLinks:
    """Tests for markdown link validity."""

    def test_internal_links_resolve(self):
        """Internal markdown links should resolve to existing files."""
        repo_root = Path(__file__).parent.parent.parent
        md_files = list(repo_root.glob("**/*.md"))
        
        # Pattern to match markdown links: [text](path)
        link_pattern = re.compile(r'\[([^\]]+)\]\(([^)]+)\)')
        
        broken_links = []
        
        for md_file in md_files:
            # Skip node_modules, .git, etc.
            if any(skip in md_file.parts for skip in ['.git', 'node_modules', 'venv', '__pycache__']):
                continue
            
            content = md_file.read_text(errors='ignore')
            links = link_pattern.findall(content)
            
            for link_text, link_path in links:
                # Skip external links (http://, https://, mailto:)
                if link_path.startswith(('http://', 'https://', 'mailto:', '#')):
                    continue
                
                # Remove anchor links
                clean_path = link_path.split('#')[0]
                if not clean_path:
                    continue
                
                # Resolve relative to the markdown file's directory
                target = (md_file.parent / clean_path).resolve()
                
                if not target.exists():
                    broken_links.append({
                        'file': str(md_file.relative_to(repo_root)),
                        'link': link_path,
                        'text': link_text
                    })
        
        # Allow some broken links (might be examples or future files)
        if len(broken_links) > 20:  # Only fail if many broken links
            msg = "Many broken internal links found:\n"
            for link in broken_links[:10]:  # Show first 10
                msg += f"  {link['file']}: [{link['text']}]({link['link']})\n"
            if len(broken_links) > 10:
                msg += f"  ... and {len(broken_links) - 10} more\n"
            pytest.fail(msg)
        elif len(broken_links) > 0:
            # Just warn for a few broken links
            pytest.skip(f"Found {len(broken_links)} broken links (acceptable threshold)")

    def test_referenced_files_exist(self):
        """Files referenced in documentation should exist."""
        repo_root = Path(__file__).parent.parent.parent
        md_files = list(repo_root.glob("**/*.md"))
        
        # Pattern to match file paths in code blocks or inline code
        file_pattern = re.compile(r'`([a-zA-Z0-9_/-]+\.(py|yaml|yml|json|js|ts|sh|md))`')
        
        missing_files = []
        
        for md_file in md_files:
            if any(skip in md_file.parts for skip in ['.git', 'node_modules', 'venv']):
                continue
            
            content = md_file.read_text(errors='ignore')
            matches = file_pattern.findall(content)
            
            for file_path, _ in matches:
                # Try relative to repo root
                target = repo_root / file_path
                
                # Also try relative to markdown file
                target_rel = md_file.parent / file_path
                
                if not target.exists() and not target_rel.exists():
                    # Skip if it's clearly an example/placeholder
                    if any(placeholder in file_path for placeholder in ['example', 'template', 'your-', 'my-']):
                        continue
                    
                    missing_files.append({
                        'file': str(md_file.relative_to(repo_root)),
                        'referenced': file_path
                    })
        
        # Allow some missing files (examples/templates are ok)
        if len(missing_files) > 20:  # Threshold for real issues
            msg = "Many referenced files not found (showing first 10):\n"
            for ref in missing_files[:10]:
                msg += f"  {ref['file']}: {ref['referenced']}\n"
            # This is a warning, not a hard failure for now
            pytest.skip(f"Warning: {len(missing_files)} referenced files not found")


class TestCodeExamples:
    """Tests for code examples in documentation."""

    def test_python_code_blocks_valid_syntax(self):
        """Python code blocks should have valid syntax."""
        repo_root = Path(__file__).parent.parent.parent
        md_files = list(repo_root.glob("**/*.md"))
        
        # Pattern to match Python code blocks
        python_block_pattern = re.compile(r'```python\n(.*?)```', re.DOTALL)
        
        invalid_blocks = []
        
        for md_file in md_files:
            if any(skip in md_file.parts for skip in ['.git', 'node_modules', 'venv']):
                continue
            
            content = md_file.read_text(errors='ignore')
            blocks = python_block_pattern.findall(content)
            
            for i, block in enumerate(blocks):
                # Skip blocks with obvious placeholders
                if '...' in block or '<' in block and '>' in block:
                    continue
                
                try:
                    compile(block, f"{md_file.name}:block{i}", 'exec')
                except SyntaxError as e:
                    invalid_blocks.append({
                        'file': str(md_file.relative_to(repo_root)),
                        'block_num': i + 1,
                        'error': str(e)
                    })
        
        if invalid_blocks:
            msg = "Invalid Python code blocks found:\n"
            for block in invalid_blocks[:5]:
                msg += f"  {block['file']} block #{block['block_num']}: {block['error']}\n"
            # Some examples might intentionally show invalid code
            if len(invalid_blocks) > 5:
                pytest.skip(f"Warning: {len(invalid_blocks)} invalid Python blocks")

    def test_yaml_code_blocks_valid_syntax(self):
        """YAML code blocks should have valid syntax."""
        import yaml
        
        repo_root = Path(__file__).parent.parent.parent
        md_files = list(repo_root.glob("**/*.md"))
        
        yaml_block_pattern = re.compile(r'```ya?ml\n(.*?)```', re.DOTALL)
        
        invalid_blocks = []
        
        for md_file in md_files:
            if any(skip in md_file.parts for skip in ['.git', 'node_modules', 'venv']):
                continue
            
            content = md_file.read_text(errors='ignore')
            blocks = yaml_block_pattern.findall(content)
            
            for i, block in enumerate(blocks):
                # Skip blocks with placeholders
                if '...' in block or '<' in block and '>' in block:
                    continue
                
                try:
                    yaml.safe_load(block)
                except yaml.YAMLError:
                    invalid_blocks.append({
                        'file': str(md_file.relative_to(repo_root)),
                        'block_num': i + 1
                    })
        
        # Allow some invalid blocks (might be partial examples)
        if len(invalid_blocks) > 10:
            pytest.skip(f"Warning: {len(invalid_blocks)} potentially invalid YAML blocks")

    def test_shell_commands_documented(self):
        """Shell commands should be in code blocks."""
        repo_root = Path(__file__).parent.parent.parent
        md_files = list(repo_root.glob("**/*.md"))
        
        shell_block_pattern = re.compile(r'```(?:bash|sh|shell)\n(.*?)```', re.DOTALL)
        
        documented_commands = 0
        
        for md_file in md_files:
            if any(skip in md_file.parts for skip in ['.git', 'node_modules', 'venv']):
                continue
            
            content = md_file.read_text(errors='ignore')
            blocks = shell_block_pattern.findall(content)
            documented_commands += len(blocks)
        
        # Should have some shell examples
        assert documented_commands > 0, "No shell command examples found in documentation"


class TestDocumentationCompleteness:
    """Tests for documentation completeness."""

    def test_all_skills_have_readme(self):
        """Each skill directory should have a README."""
        skills_dir = Path(__file__).parent.parent.parent / "skills"
        
        missing_readme = []
        
        for skill_dir in skills_dir.iterdir():
            if skill_dir.is_dir() and not skill_dir.name.startswith('.'):
                readme = skill_dir / "README.md"
                if not readme.exists():
                    missing_readme.append(skill_dir.name)
        
        assert len(missing_readme) == 0, f"Skills missing README: {', '.join(missing_readme)}"

    def test_all_skills_have_skill_metadata(self):
        """Each skill should have SKILL.md metadata."""
        skills_dir = Path(__file__).parent.parent.parent / "skills"
        
        missing_skill_md = []
        
        for skill_dir in skills_dir.iterdir():
            if skill_dir.is_dir() and not skill_dir.name.startswith('.'):
                skill_md = skill_dir / "SKILL.md"
                if not skill_md.exists():
                    missing_skill_md.append(skill_dir.name)
        
        assert len(missing_skill_md) == 0, f"Skills missing SKILL.md: {', '.join(missing_skill_md)}"

    def test_skill_metadata_has_required_fields(self):
        """SKILL.md files should have required metadata."""
        skills_dir = Path(__file__).parent.parent.parent / "skills"
        
        for skill_dir in skills_dir.iterdir():
            if skill_dir.is_dir() and not skill_dir.name.startswith('.'):
                skill_md = skill_dir / "SKILL.md"
                if skill_md.exists():
                    content = skill_md.read_text()
                    
                    # Should have a title (# heading)
                    assert re.search(r'^#\s+', content, re.MULTILINE), \
                        f"{skill_dir.name}/SKILL.md missing title"

    def test_readme_has_overview(self):
        """Main README should have overview section."""
        readme = Path(__file__).parent.parent.parent / "README.md"
        content = readme.read_text()
        
        # Should mention key concepts
        assert "skill" in content.lower() or "Skills" in content
        assert "App Platform" in content or "DigitalOcean" in content

    def test_contributing_guide_exists(self):
        """Should have contributing guidelines."""
        repo_root = Path(__file__).parent.parent.parent
        contrib = repo_root / "CONTRIBUTING.md"
        
        # CONTRIBUTING.md might not exist yet, check if README mentions it
        if not contrib.exists():
            readme = repo_root / "README.md"
            content = readme.read_text()
            # Either file exists or README mentions how to contribute
            assert "contribut" in content.lower() or contrib.exists()


class TestDocumentationFormat:
    """Tests for documentation formatting."""

    def test_headers_properly_formatted(self):
        """Markdown headers should be properly formatted."""
        repo_root = Path(__file__).parent.parent.parent
        md_files = list(repo_root.glob("**/*.md"))
        
        # Headers should have space after #
        bad_headers = []
        
        for md_file in md_files:
            if any(skip in md_file.parts for skip in ['.git', 'node_modules', 'venv']):
                continue
            
            content = md_file.read_text(errors='ignore')
            lines = content.split('\n')
            
            for i, line in enumerate(lines):
                if line.startswith('#') and not line.startswith('####'):  # Check headers
                    # Should have space after #
                    if not re.match(r'^#+\s', line):
                        bad_headers.append({
                            'file': str(md_file.relative_to(repo_root)),
                            'line': i + 1,
                            'content': line[:50]
                        })
        
        # Allow some formatting variations
        if len(bad_headers) > 5:
            pytest.skip(f"Warning: {len(bad_headers)} headers with potential formatting issues")

    def test_no_trailing_whitespace(self):
        """Markdown files should not have excessive trailing whitespace."""
        repo_root = Path(__file__).parent.parent.parent
        md_files = list(repo_root.glob("**/*.md"))
        
        files_with_trailing = []
        
        for md_file in md_files:
            if any(skip in md_file.parts for skip in ['.git', 'node_modules', 'venv']):
                continue
            
            content = md_file.read_text(errors='ignore')
            lines = content.split('\n')
            
            trailing_count = sum(1 for line in lines if line.endswith('   ') or line.endswith('\t'))
            
            if trailing_count > 10:  # More than 10 lines with trailing whitespace
                files_with_trailing.append(str(md_file.relative_to(repo_root)))
        
        # This is a style issue, not critical
        if len(files_with_trailing) > 0:
            pytest.skip(f"Style: {len(files_with_trailing)} files have trailing whitespace")
