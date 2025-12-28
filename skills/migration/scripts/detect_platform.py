#!/usr/bin/env python3
"""
Platform Detection Script

Detects the source platform of a repository by analyzing configuration files.
Returns a structured report of detected platform and its configuration.

Usage:
    python detect_platform.py /path/to/repo
    python detect_platform.py /path/to/repo --json
"""

import os
import sys
import json
import argparse
from pathlib import Path
from typing import Dict, List, Optional, Any
import re


class PlatformDetector:
    """Detects source platform from repository configuration files."""
    
    PLATFORM_INDICATORS = {
        'heroku': {
            'files': ['Procfile', 'app.json', 'heroku.yml'],
            'priority': 1,
            'description': 'Heroku PaaS'
        },
        'render': {
            'files': ['render.yaml', 'render.yml'],
            'priority': 2,
            'description': 'Render PaaS'
        },
        'railway': {
            'files': ['railway.json', 'railway.toml'],
            'priority': 2,
            'description': 'Railway PaaS'
        },
        'fly': {
            'files': ['fly.toml'],
            'priority': 2,
            'description': 'Fly.io'
        },
        'docker_compose': {
            'files': ['docker-compose.yml', 'docker-compose.yaml', 'compose.yml', 'compose.yaml'],
            'priority': 3,
            'description': 'Docker Compose'
        },
        'aws_ecs': {
            'patterns': ['**/task-definition.json', '**/ecs-task-definition.json', '.aws/task-definition.json'],
            'priority': 4,
            'description': 'AWS ECS'
        },
        'aws_apprunner': {
            'files': ['apprunner.yaml', 'apprunner.yml'],
            'priority': 4,
            'description': 'AWS App Runner'
        },
        'aws_beanstalk': {
            'files': ['Dockerrun.aws.json'],
            'dirs': ['.elasticbeanstalk'],
            'priority': 4,
            'description': 'AWS Elastic Beanstalk'
        },
        'generic_docker': {
            'files': ['Dockerfile'],
            'priority': 10,  # Lowest priority - fallback
            'description': 'Generic Docker'
        }
    }
    
    def __init__(self, repo_path: str):
        self.repo_path = Path(repo_path)
        if not self.repo_path.exists():
            raise ValueError(f"Repository path does not exist: {repo_path}")
        self.files = self._scan_files()
        self.dirs = self._scan_dirs()
    
    def _scan_files(self) -> set:
        """Scan all files in repository."""
        files = set()
        for root, _, filenames in os.walk(self.repo_path):
            # Skip common non-source directories
            rel_root = os.path.relpath(root, self.repo_path)
            if any(skip in rel_root for skip in ['.git', 'node_modules', 'venv', '__pycache__', '.next', 'dist', 'build']):
                continue
            for filename in filenames:
                rel_path = os.path.relpath(os.path.join(root, filename), self.repo_path)
                files.add(rel_path)
        return files
    
    def _scan_dirs(self) -> set:
        """Scan directories in repository."""
        dirs = set()
        for root, dirnames, _ in os.walk(self.repo_path):
            for dirname in dirnames:
                rel_path = os.path.relpath(os.path.join(root, dirname), self.repo_path)
                dirs.add(rel_path)
        return dirs
    
    def _check_patterns(self, patterns: List[str]) -> List[str]:
        """Check for files matching glob patterns."""
        import fnmatch
        matches = []
        for pattern in patterns:
            for filepath in self.files:
                if fnmatch.fnmatch(filepath, pattern):
                    matches.append(filepath)
        return matches
    
    def detect(self) -> Dict[str, Any]:
        """Detect platform and return detailed report."""
        detected_platforms = []
        
        for platform, indicators in self.PLATFORM_INDICATORS.items():
            found_files = []
            found_dirs = []
            
            # Check for specific files
            if 'files' in indicators:
                for f in indicators['files']:
                    if f in self.files:
                        found_files.append(f)
            
            # Check for patterns
            if 'patterns' in indicators:
                found_files.extend(self._check_patterns(indicators['patterns']))
            
            # Check for directories
            if 'dirs' in indicators:
                for d in indicators['dirs']:
                    if d in self.dirs:
                        found_dirs.append(d)
            
            if found_files or found_dirs:
                detected_platforms.append({
                    'platform': platform,
                    'description': indicators['description'],
                    'priority': indicators['priority'],
                    'found_files': found_files,
                    'found_dirs': found_dirs
                })
        
        # Sort by priority (lower = higher priority)
        detected_platforms.sort(key=lambda x: x['priority'])
        
        primary_platform = detected_platforms[0] if detected_platforms else None
        
        return {
            'primary_platform': primary_platform['platform'] if primary_platform else 'unknown',
            'primary_description': primary_platform['description'] if primary_platform else 'Unknown platform',
            'config_files': primary_platform['found_files'] if primary_platform else [],
            'all_detected': detected_platforms,
            'has_dockerfile': 'Dockerfile' in self.files,
            'has_docker_compose': any(f in self.files for f in ['docker-compose.yml', 'docker-compose.yaml', 'compose.yml', 'compose.yaml'])
        }
    
    def get_config_content(self) -> Dict[str, str]:
        """Get content of detected configuration files."""
        result = self.detect()
        contents = {}
        
        for filepath in result.get('config_files', []):
            full_path = self.repo_path / filepath
            if full_path.exists():
                try:
                    contents[filepath] = full_path.read_text()
                except Exception as e:
                    contents[filepath] = f"<error reading file: {e}>"
        
        return contents


def main():
    parser = argparse.ArgumentParser(
        description='Detect source platform of a repository'
    )
    parser.add_argument('repo_path', help='Path to the repository')
    parser.add_argument('--json', action='store_true', help='Output as JSON')
    parser.add_argument('--content', action='store_true', help='Include config file contents')
    
    args = parser.parse_args()
    
    try:
        detector = PlatformDetector(args.repo_path)
        result = detector.detect()
        
        if args.content:
            result['config_contents'] = detector.get_config_content()
        
        if args.json:
            print(json.dumps(result, indent=2))
        else:
            print(f"Primary Platform: {result['primary_description']} ({result['primary_platform']})")
            print(f"Config Files: {', '.join(result['config_files']) or 'None'}")
            print(f"Has Dockerfile: {result['has_dockerfile']}")
            print(f"Has Docker Compose: {result['has_docker_compose']}")
            
            if len(result['all_detected']) > 1:
                print(f"\nOther detected platforms:")
                for p in result['all_detected'][1:]:
                    print(f"  - {p['description']} ({', '.join(p['found_files'])})")
    
    except Exception as e:
        print(f"Error: {e}", file=sys.stderr)
        sys.exit(1)


if __name__ == '__main__':
    main()
