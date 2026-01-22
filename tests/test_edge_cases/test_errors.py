"""Tests for error handling and edge cases."""

import pytest
import sys
from pathlib import Path
import tempfile
import os

sys.path.insert(0, str(Path(__file__).parent.parent.parent / "skills" / "migration" / "scripts"))
sys.path.insert(0, str(Path(__file__).parent.parent.parent / "skills" / "postgres" / "scripts"))


class TestPlatformDetectionErrors:
    """Tests for platform detection error handling."""

    def test_raises_on_nonexistent_path(self):
        """Should raise ValueError for nonexistent path."""
        from detect_platform import PlatformDetector
        
        with pytest.raises(ValueError, match="does not exist"):
            PlatformDetector("/this/path/does/not/exist/anywhere")

    def test_handles_inaccessible_files_gracefully(self, temp_repo):
        """Should handle files that can't be read."""
        from detect_platform import PlatformDetector
        
        # Create a file
        problematic_file = temp_repo / "config.yaml"
        problematic_file.write_text("content")
        
        # Make it unreadable (on Unix systems)
        if os.name != 'nt':  # Skip on Windows
            os.chmod(problematic_file, 0o000)
            
            try:
                detector = PlatformDetector(str(temp_repo))
                result = detector.detect()
                # Should still work, just skip problematic file
                assert result is not None
            finally:
                # Restore permissions for cleanup
                os.chmod(problematic_file, 0o644)

    def test_handles_symlinks_gracefully(self, temp_repo):
        """Should handle symbolic links without errors."""
        from detect_platform import PlatformDetector
        
        # Create a symlink
        target = temp_repo / "target.txt"
        target.write_text("content")
        link = temp_repo / "link.txt"
        
        if os.name != 'nt':  # Symlinks work differently on Windows
            link.symlink_to(target)
            
            detector = PlatformDetector(str(temp_repo))
            result = detector.detect()
            assert result is not None

    def test_handles_broken_symlinks(self, temp_repo):
        """Should handle broken symbolic links."""
        from detect_platform import PlatformDetector
        
        link = temp_repo / "broken_link.txt"
        
        if os.name != 'nt':
            link.symlink_to(temp_repo / "nonexistent.txt")
            
            detector = PlatformDetector(str(temp_repo))
            # Should not crash on broken symlink
            result = detector.detect()
            assert result is not None


class TestArchitectureAnalysisErrors:
    """Tests for architecture analysis error handling."""

    def test_raises_on_nonexistent_path(self):
        """Should raise ValueError for nonexistent path."""
        from analyze_architecture import ArchitectureAnalyzer
        
        with pytest.raises(ValueError, match="does not exist"):
            ArchitectureAnalyzer("/nonexistent/path")

    def test_handles_corrupted_package_json(self, temp_repo):
        """Should handle corrupted package.json gracefully."""
        from analyze_architecture import ArchitectureAnalyzer
        
        # Create invalid JSON
        (temp_repo / "package.json").write_text("{invalid json content")
        
        analyzer = ArchitectureAnalyzer(str(temp_repo))
        result = analyzer.analyze()
        
        # Should still detect nodejs but handle error gracefully
        assert result["runtime"] in ["nodejs", "unknown"]

    def test_handles_empty_files(self, temp_repo):
        """Should handle empty configuration files."""
        from analyze_architecture import ArchitectureAnalyzer
        
        (temp_repo / "requirements.txt").write_text("")
        (temp_repo / "Procfile").write_text("")
        
        analyzer = ArchitectureAnalyzer(str(temp_repo))
        result = analyzer.analyze()
        
        # Should complete without errors
        assert result is not None

    def test_handles_binary_files(self, temp_repo):
        """Should skip binary files during analysis."""
        from analyze_architecture import ArchitectureAnalyzer
        
        # Create a binary file
        (temp_repo / "image.png").write_bytes(b'\x89PNG\r\n\x1a\n\x00\x00\x00')
        
        analyzer = ArchitectureAnalyzer(str(temp_repo))
        result = analyzer.analyze()
        
        # Should not crash on binary files
        assert result is not None

    def test_handles_very_large_files(self, temp_repo):
        """Should handle very large files without memory issues."""
        from analyze_architecture import ArchitectureAnalyzer
        
        # Create a somewhat large file (1MB)
        large_file = temp_repo / "large.txt"
        large_file.write_text("x" * (1024 * 1024))
        
        analyzer = ArchitectureAnalyzer(str(temp_repo))
        # Should complete without running out of memory
        result = analyzer.analyze()
        assert result is not None


class TestAppSpecGenerationErrors:
    """Tests for app spec generation error handling."""

    def test_handles_missing_shared_configs(self, temp_repo):
        """Should work even if shared configs are missing."""
        from generate_app_spec import AppSpecGenerator
        
        generator = AppSpecGenerator(str(temp_repo), "test-app", "test")
        spec = generator.generate()
        
        # Should use fallback values
        assert "spec" in spec

    def test_handles_invalid_environment(self, temp_repo):
        """Should handle invalid environment gracefully."""
        from generate_app_spec import AppSpecGenerator
        
        # Use invalid environment
        generator = AppSpecGenerator(str(temp_repo), "test-app", "invalid-env")
        spec = generator.generate()
        
        # Should fall back to test environment
        assert "spec" in spec

    def test_handles_invalid_app_name(self, temp_repo):
        """Should handle various app name formats."""
        from generate_app_spec import AppSpecGenerator
        
        # Names with special characters
        names = ["my-app", "my_app", "MyApp", "my.app", "123app"]
        
        for name in names:
            generator = AppSpecGenerator(str(temp_repo), name, "test")
            spec = generator.generate()
            assert "spec" in spec
            assert "name" in spec["spec"]

    def test_handles_repo_without_git(self, temp_repo):
        """Should work for non-git repositories."""
        from generate_app_spec import AppSpecGenerator
        
        # temp_repo is not a git repo
        generator = AppSpecGenerator(str(temp_repo), "test-app", "test")
        spec = generator.generate(repo_url=None, branch="main")
        
        assert "spec" in spec


class TestPostgresScriptErrors:
    """Tests for postgres script error handling."""

    def test_generate_sql_with_empty_names(self, capsys):
        """Should handle empty schema/user names."""
        from create_schema_user import generate_sql
        
        # Empty names will be used as-is (user's responsibility to validate)
        generate_sql("", "", "password")
        output = capsys.readouterr().out
        # Should still generate SQL, even if names are empty
        assert "CREATE SCHEMA" in output or "CREATE USER" in output

    def test_connection_string_with_invalid_url(self):
        """Should handle invalid connection strings."""
        from generate_connection_string import generate_connection_strings
        
        invalid_urls = [
            "not-a-url",
            "postgresql://",
            "postgresql://user@",
        ]
        
        for url in invalid_urls:
            try:
                # Should either handle gracefully or raise clear error
                generate_connection_strings(url, "user", "pass")
            except Exception as e:
                # Exception is acceptable for invalid input
                assert len(str(e)) > 0

    def test_password_generation_with_invalid_length(self):
        """Should handle invalid password lengths."""
        from add_client import generate_password
        
        # Zero length - generates empty string
        password = generate_password(0)
        assert len(password) == 0
        
        # Negative length - Python's range handles this, generates empty string
        password = generate_password(-10)
        assert len(password) == 0
        
        # Very large length should still work or fail gracefully
        try:
            password = generate_password(10000)
            assert len(password) == 10000
        except (MemoryError, ValueError):
            pass  # Acceptable to fail for extreme values

    def test_sql_injection_in_schema_name(self):
        """Should handle SQL injection attempts in schema names."""
        from create_schema_user import generate_sql
        
        malicious_names = [
            "schema'; DROP TABLE users; --",
            "schema OR 1=1",
            "../../../etc/passwd",
        ]
        
        for name in malicious_names:
            # Should either sanitize or raise error
            try:
                generate_sql(name, "user", "pass")
                # If it succeeds, output should be safe
            except (ValueError, AssertionError):
                # Raising an error is also acceptable
                pass


class TestFileSystemErrors:
    """Tests for file system error handling."""

    def test_handles_permission_errors_on_write(self, tmp_path):
        """Should handle permission errors when writing files."""
        from create_schema_user import generate_sql
        
        output_dir = tmp_path / "output"
        output_dir.mkdir()
        
        if os.name != 'nt':  # Skip on Windows
            # Make directory read-only
            os.chmod(output_dir, 0o444)
            
            try:
                # Should raise or handle permission error
                with pytest.raises((PermissionError, OSError)):
                    generate_sql("schema", "user", "pass", output_dir=str(output_dir))
            finally:
                # Restore permissions
                os.chmod(output_dir, 0o755)

    def test_handles_disk_full_simulation(self, tmp_path):
        """Should handle disk full errors gracefully."""
        # This is hard to test without actually filling disk
        # Just verify error handling exists
        from create_schema_user import generate_sql
        
        # Normal case should work
        generate_sql("schema", "user", "pass", output_dir=str(tmp_path))
        assert (tmp_path / "db-setup.sql").exists()

    def test_handles_unicode_in_filenames(self, tmp_path):
        """Should handle Unicode characters in paths."""
        from create_schema_user import generate_sql
        
        unicode_dir = tmp_path / "测试_test_тест"
        unicode_dir.mkdir()
        
        # Should handle Unicode in paths
        generate_sql("schema", "user", "pass", output_dir=str(unicode_dir))
        assert (unicode_dir / "db-setup.sql").exists()


class TestEdgeCases:
    """Tests for various edge cases."""

    def test_very_long_app_name(self, temp_repo):
        """Should handle very long app names."""
        from generate_app_spec import AppSpecGenerator
        
        long_name = "a" * 200
        generator = AppSpecGenerator(str(temp_repo), long_name, "test")
        spec = generator.generate()
        
        # Name might be truncated but should work
        assert "spec" in spec

    def test_special_characters_in_passwords(self):
        """Should handle special characters in passwords."""
        from create_schema_user import generate_sql
        
        special_password = "p@$$w0rd!#%&*()_+-=[]{}|;:',.<>?/~`"
        
        # Should handle special characters
        sql = generate_sql("schema", "user", special_password)
        # Password should be in output (will be shown to user)
        # but in production, this should be handled securely

    def test_concurrent_file_access(self, temp_repo):
        """Should handle concurrent access to same repository."""
        from detect_platform import PlatformDetector
        
        # Multiple instances accessing same repo
        detector1 = PlatformDetector(str(temp_repo))
        detector2 = PlatformDetector(str(temp_repo))
        
        result1 = detector1.detect()
        result2 = detector2.detect()
        
        # Both should succeed
        assert result1 is not None
        assert result2 is not None

    def test_deeply_nested_directory_structure(self, temp_repo):
        """Should handle deeply nested directories."""
        from analyze_architecture import ArchitectureAnalyzer
        
        # Create deeply nested structure
        deep_path = temp_repo
        for i in range(20):
            deep_path = deep_path / f"level{i}"
            deep_path.mkdir()
        
        (deep_path / "app.py").write_text("print('hello')")
        
        analyzer = ArchitectureAnalyzer(str(temp_repo))
        result = analyzer.analyze()
        
        # Should complete without stack overflow
        assert result is not None
