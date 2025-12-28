#!/usr/bin/env python3
"""
Architecture Analyzer Script

Analyzes repository structure to determine architecture type, runtime,
dependencies, and component structure for App Platform migration.

Usage:
    python analyze_architecture.py /path/to/repo
    python analyze_architecture.py /path/to/repo --json
"""

import os
import sys
import json
import argparse
from pathlib import Path
from typing import Dict, List, Optional, Set, Any
import re


class ArchitectureAnalyzer:
    """Analyzes repository architecture for App Platform migration."""
    
    def __init__(self, repo_path: str):
        self.repo_path = Path(repo_path)
        if not self.repo_path.exists():
            raise ValueError(f"Repository path does not exist: {repo_path}")
        self.files = self._scan_files()
    
    def _scan_files(self) -> Set[str]:
        """Scan all files in repository."""
        files = set()
        skip_dirs = {'.git', 'node_modules', 'venv', '__pycache__', '.next', 'dist', 'build', '.cache'}
        
        for root, dirs, filenames in os.walk(self.repo_path):
            # Filter out skip directories
            dirs[:] = [d for d in dirs if d not in skip_dirs]
            
            for filename in filenames:
                rel_path = os.path.relpath(os.path.join(root, filename), self.repo_path)
                files.add(rel_path)
        return files
    
    def analyze(self) -> Dict[str, Any]:
        """Perform complete repository analysis."""
        return {
            'architecture_type': self._detect_architecture_type(),
            'runtime': self._detect_runtime(),
            'runtime_version': self._detect_runtime_version(),
            'build_method': self._detect_build_method(),
            'components': self._detect_components(),
            'dependencies': self._detect_dependencies(),
            'default_port': self._detect_default_port(),
            'environment_files': self._detect_env_files(),
            'has_dockerfile': 'Dockerfile' in self.files,
            'has_docker_compose': any(f in self.files for f in ['docker-compose.yml', 'docker-compose.yaml']),
            'has_tests': self._detect_tests(),
            'monorepo_structure': self._detect_monorepo_structure(),
        }
    
    def _detect_architecture_type(self) -> str:
        """Detect the architecture type of the repository."""
        # Check for docker-compose (likely microservices)
        if any(f in self.files for f in ['docker-compose.yml', 'docker-compose.yaml']):
            services = self._parse_docker_compose_services()
            # More than 2 app services (excluding db/cache) = microservices
            app_services = [s for s in services if not self._is_infrastructure_service(s)]
            if len(app_services) > 2:
                return 'microservices'
        
        # Check for monorepo structure (frontend + backend)
        frontend_dirs = ['frontend', 'client', 'web', 'ui', 'app', 'packages/frontend', 'apps/web', 'packages/web']
        backend_dirs = ['backend', 'server', 'api', 'services', 'packages/backend', 'apps/api', 'packages/api']
        
        has_frontend = any(any(f.startswith(d + '/') for f in self.files) for d in frontend_dirs)
        has_backend = any(any(f.startswith(d + '/') for f in self.files) for d in backend_dirs)
        
        if has_frontend and has_backend:
            return 'full-stack'
        
        # Check for static site generators
        static_indicators = ['gatsby-config.js', 'next.config.js', 'nuxt.config.js', 'astro.config.mjs', 
                           'vite.config.js', 'vite.config.ts', 'config.toml', '_config.yml', 'hugo.toml']
        if any(f in self.files for f in static_indicators):
            # Check if it's SSR or static
            if 'next.config.js' in self.files or 'next.config.mjs' in self.files:
                return 'full-stack'  # Next.js is typically SSR
            return 'static-site'
        
        # Check if purely frontend
        if has_frontend and not has_backend:
            return 'static-site'
        
        # Default to monolith
        return 'monolith'
    
    def _detect_runtime(self) -> str:
        """Detect the primary runtime/language."""
        runtime_indicators = {
            'nodejs': ['package.json'],
            'python': ['requirements.txt', 'Pipfile', 'pyproject.toml', 'setup.py'],
            'go': ['go.mod', 'go.sum'],
            'ruby': ['Gemfile', 'Gemfile.lock'],
            'php': ['composer.json', 'composer.lock'],
            'java': ['pom.xml', 'build.gradle', 'build.gradle.kts'],
            'rust': ['Cargo.toml'],
            'dotnet': [f for f in self.files if f.endswith('.csproj') or f.endswith('.fsproj')],
            'elixir': ['mix.exs'],
            'bun': ['bun.lockb'],  # Bun-specific lockfile
        }
        
        for runtime, indicators in runtime_indicators.items():
            if runtime == 'dotnet':
                if any(f.endswith('.csproj') or f.endswith('.fsproj') for f in self.files):
                    return 'dotnet'
            elif any(f in self.files for f in indicators):
                return runtime
        
        return 'unknown'
    
    def _detect_runtime_version(self) -> Optional[str]:
        """Detect runtime version from configuration files."""
        runtime = self._detect_runtime()
        
        if runtime == 'nodejs':
            # Check package.json engines
            if 'package.json' in self.files:
                try:
                    pkg = json.loads((self.repo_path / 'package.json').read_text())
                    engines = pkg.get('engines', {})
                    if 'node' in engines:
                        return engines['node']
                except Exception:
                    pass
            # Check .nvmrc
            if '.nvmrc' in self.files:
                try:
                    return (self.repo_path / '.nvmrc').read_text().strip()
                except Exception:
                    pass
            # Check .node-version
            if '.node-version' in self.files:
                try:
                    return (self.repo_path / '.node-version').read_text().strip()
                except Exception:
                    pass
        
        elif runtime == 'python':
            # Check .python-version
            if '.python-version' in self.files:
                try:
                    return (self.repo_path / '.python-version').read_text().strip()
                except Exception:
                    pass
            # Check pyproject.toml
            if 'pyproject.toml' in self.files:
                try:
                    content = (self.repo_path / 'pyproject.toml').read_text()
                    match = re.search(r'python\s*[=><!]+\s*["\']?(\d+\.\d+)', content)
                    if match:
                        return match.group(1)
                except Exception:
                    pass
        
        elif runtime == 'go':
            if 'go.mod' in self.files:
                try:
                    content = (self.repo_path / 'go.mod').read_text()
                    match = re.search(r'go\s+(\d+\.\d+)', content)
                    if match:
                        return match.group(1)
                except Exception:
                    pass
        
        return None
    
    def _detect_build_method(self) -> str:
        """Detect how the application should be built."""
        if 'Dockerfile' in self.files:
            return 'dockerfile'
        
        compose_files = ['docker-compose.yml', 'docker-compose.yaml', 'compose.yml', 'compose.yaml']
        if any(f in self.files for f in compose_files):
            return 'docker-compose'
        
        runtime = self._detect_runtime()
        if runtime != 'unknown':
            return f'buildpack-{runtime}'
        
        return 'buildpack'
    
    def _detect_components(self) -> List[Dict[str, Any]]:
        """Detect individual components/services."""
        components = []
        
        # Parse Procfile for Heroku-style apps
        if 'Procfile' in self.files:
            components.extend(self._parse_procfile())
        
        # Parse docker-compose for multi-service apps
        elif any(f in self.files for f in ['docker-compose.yml', 'docker-compose.yaml']):
            components.extend(self._parse_docker_compose_components())
        
        # Parse render.yaml
        elif any(f in self.files for f in ['render.yaml', 'render.yml']):
            components.extend(self._parse_render_yaml())
        
        # Parse fly.toml
        elif 'fly.toml' in self.files:
            components.extend(self._parse_fly_toml())
        
        # Default: single service
        if not components:
            port = self._detect_default_port()
            components.append({
                'name': 'web',
                'type': 'service',
                'source_dir': '/',
                'port': port,
                'has_dockerfile': 'Dockerfile' in self.files
            })
        
        return components
    
    def _parse_procfile(self) -> List[Dict[str, Any]]:
        """Parse Heroku Procfile."""
        components = []
        try:
            content = (self.repo_path / 'Procfile').read_text()
            for line in content.strip().split('\n'):
                if ':' in line and not line.strip().startswith('#'):
                    name, command = line.split(':', 1)
                    name = name.strip()
                    command = command.strip()
                    
                    comp_type = 'service' if name == 'web' else 'worker'
                    if name == 'release':
                        comp_type = 'job'
                    
                    components.append({
                        'name': name,
                        'type': comp_type,
                        'command': command,
                        'source_dir': '/',
                        'port': self._detect_default_port() if comp_type == 'service' else None
                    })
        except Exception as e:
            pass
        return components
    
    def _parse_docker_compose_services(self) -> Dict[str, Any]:
        """Parse docker-compose.yml and return services dict."""
        try:
            import yaml
        except ImportError:
            return {}
        
        compose_files = ['docker-compose.yml', 'docker-compose.yaml', 'compose.yml', 'compose.yaml']
        for cf in compose_files:
            if cf in self.files:
                try:
                    content = (self.repo_path / cf).read_text()
                    compose = yaml.safe_load(content)
                    return compose.get('services', {})
                except Exception:
                    pass
        return {}
    
    def _parse_docker_compose_components(self) -> List[Dict[str, Any]]:
        """Parse docker-compose for components."""
        components = []
        services = self._parse_docker_compose_services()
        
        for name, config in services.items():
            # Skip infrastructure services
            if self._is_infrastructure_service(name):
                continue
            
            image = config.get('image', '')
            if self._is_database_image(image):
                continue
            
            ports = config.get('ports', [])
            has_ports = len(ports) > 0
            
            comp_type = 'service' if has_ports else 'worker'
            port = None
            if has_ports:
                port_mapping = str(ports[0])
                if ':' in port_mapping:
                    port = int(port_mapping.split(':')[1].split('/')[0])
                else:
                    port = int(port_mapping.split('/')[0])
            
            # Detect source directory
            build_config = config.get('build', {})
            if isinstance(build_config, str):
                source_dir = build_config
            elif isinstance(build_config, dict):
                source_dir = build_config.get('context', '/')
            else:
                source_dir = '/'
            
            components.append({
                'name': name,
                'type': comp_type,
                'source_dir': source_dir,
                'port': port,
                'has_dockerfile': True if build_config else False,
                'image': image if not build_config else None,
                'environment': config.get('environment', []),
                'command': config.get('command')
            })
        
        return components
    
    def _parse_render_yaml(self) -> List[Dict[str, Any]]:
        """Parse render.yaml for components."""
        components = []
        try:
            import yaml
            for rf in ['render.yaml', 'render.yml']:
                if rf in self.files:
                    content = (self.repo_path / rf).read_text()
                    render_config = yaml.safe_load(content)
                    
                    for service in render_config.get('services', []):
                        svc_type = service.get('type', 'web')
                        comp_type = {
                            'web': 'service',
                            'worker': 'worker',
                            'cron': 'job',
                            'static': 'static_site'
                        }.get(svc_type, 'service')
                        
                        components.append({
                            'name': service.get('name', 'web'),
                            'type': comp_type,
                            'source_dir': service.get('rootDir', '/'),
                            'port': service.get('port'),
                            'build_command': service.get('buildCommand'),
                            'start_command': service.get('startCommand'),
                            'health_check_path': service.get('healthCheckPath')
                        })
                    break
        except Exception:
            pass
        return components
    
    def _parse_fly_toml(self) -> List[Dict[str, Any]]:
        """Parse fly.toml for components."""
        components = []
        try:
            content = (self.repo_path / 'fly.toml').read_text()
            
            # Simple TOML parsing for key fields
            app_name = None
            port = 8080
            
            for line in content.split('\n'):
                line = line.strip()
                if line.startswith('app = '):
                    app_name = line.split('=')[1].strip().strip('"\'')
                elif 'internal_port' in line:
                    match = re.search(r'internal_port\s*=\s*(\d+)', line)
                    if match:
                        port = int(match.group(1))
            
            components.append({
                'name': app_name or 'web',
                'type': 'service',
                'source_dir': '/',
                'port': port,
                'has_dockerfile': 'Dockerfile' in self.files
            })
        except Exception:
            pass
        return components
    
    def _is_infrastructure_service(self, name: str) -> bool:
        """Check if service name indicates infrastructure (db, cache, etc)."""
        infra_names = ['db', 'database', 'postgres', 'postgresql', 'mysql', 'mariadb', 
                       'mongo', 'mongodb', 'redis', 'cache', 'memcached', 'rabbitmq', 
                       'kafka', 'elasticsearch', 'opensearch', 'minio', 'localstack']
        return name.lower() in infra_names
    
    def _is_database_image(self, image: str) -> bool:
        """Check if Docker image is a database/infrastructure image."""
        db_images = ['postgres', 'mysql', 'mariadb', 'mongo', 'redis', 'memcached',
                    'rabbitmq', 'kafka', 'elasticsearch', 'opensearch', 'minio']
        image_lower = image.lower()
        return any(db in image_lower for db in db_images)
    
    def _detect_dependencies(self) -> Dict[str, List[Dict[str, Any]]]:
        """Detect dependencies like databases, caches, queues."""
        deps = {
            'databases': [],
            'caches': [],
            'queues': [],
            'storage': []
        }
        
        # Check docker-compose for services
        services = self._parse_docker_compose_services()
        for name, config in services.items():
            image = config.get('image', '').lower()
            
            # Databases
            if 'postgres' in image or 'postgresql' in image:
                version = self._extract_image_version(image)
                deps['databases'].append({
                    'type': 'postgres',
                    'source': f'docker: {image}',
                    'version': version,
                    'service_name': name
                })
            elif 'mysql' in image or 'mariadb' in image:
                version = self._extract_image_version(image)
                deps['databases'].append({
                    'type': 'mysql',
                    'source': f'docker: {image}',
                    'version': version,
                    'service_name': name
                })
            elif 'mongo' in image:
                version = self._extract_image_version(image)
                deps['databases'].append({
                    'type': 'mongodb',
                    'source': f'docker: {image}',
                    'version': version,
                    'service_name': name
                })
            
            # Caches
            elif 'redis' in image:
                version = self._extract_image_version(image)
                deps['caches'].append({
                    'type': 'redis',
                    'source': f'docker: {image}',
                    'version': version,
                    'service_name': name,
                    'note': 'Redis EOL on DO - will map to Valkey'
                })
            elif 'memcached' in image:
                deps['caches'].append({
                    'type': 'memcached',
                    'source': f'docker: {image}',
                    'service_name': name,
                    'note': 'Use Valkey instead'
                })
            
            # Queues
            elif 'rabbitmq' in image:
                deps['queues'].append({
                    'type': 'rabbitmq',
                    'source': f'docker: {image}',
                    'service_name': name,
                    'note': 'No direct equivalent - consider external'
                })
            elif 'kafka' in image:
                deps['queues'].append({
                    'type': 'kafka',
                    'source': f'docker: {image}',
                    'service_name': name
                })
            
            # Storage
            elif 'minio' in image:
                deps['storage'].append({
                    'type': 's3',
                    'source': f'docker: {image}',
                    'service_name': name,
                    'note': 'Map to Spaces'
                })
        
        # Check Heroku app.json for addons
        if 'app.json' in self.files:
            try:
                app_json = json.loads((self.repo_path / 'app.json').read_text())
                for addon in app_json.get('addons', []):
                    addon_name = addon if isinstance(addon, str) else addon.get('plan', '')
                    if 'postgresql' in addon_name.lower() or 'postgres' in addon_name.lower():
                        deps['databases'].append({
                            'type': 'postgres',
                            'source': f'heroku: {addon_name}',
                            'heroku_addon': addon_name
                        })
                    elif 'redis' in addon_name.lower():
                        deps['caches'].append({
                            'type': 'redis',
                            'source': f'heroku: {addon_name}',
                            'heroku_addon': addon_name,
                            'note': 'Redis EOL on DO - will map to Valkey'
                        })
            except Exception:
                pass
        
        # Check for database mentions in env files and code
        deps = self._enhance_deps_from_code(deps)
        
        return deps
    
    def _extract_image_version(self, image: str) -> Optional[str]:
        """Extract version from Docker image tag."""
        if ':' in image:
            tag = image.split(':')[1]
            # Extract version number
            match = re.match(r'(\d+(?:\.\d+)*)', tag)
            if match:
                return match.group(1)
        return None
    
    def _enhance_deps_from_code(self, deps: Dict[str, List]) -> Dict[str, List]:
        """Look for database/service mentions in code and env files."""
        env_files = [f for f in self.files if '.env' in f.lower()]
        
        for env_file in env_files:
            try:
                content = (self.repo_path / env_file).read_text().lower()
                
                # Check for PostgreSQL
                if 'postgres' in content and not any(d['type'] == 'postgres' for d in deps['databases']):
                    deps['databases'].append({
                        'type': 'postgres',
                        'source': f'env file: {env_file}',
                        'inferred': True
                    })
                
                # Check for MySQL
                if 'mysql' in content and not any(d['type'] == 'mysql' for d in deps['databases']):
                    deps['databases'].append({
                        'type': 'mysql',
                        'source': f'env file: {env_file}',
                        'inferred': True
                    })
                
                # Check for Redis
                if 'redis' in content and not any(d['type'] == 'redis' for d in deps['caches']):
                    deps['caches'].append({
                        'type': 'redis',
                        'source': f'env file: {env_file}',
                        'inferred': True,
                        'note': 'Redis EOL on DO - will map to Valkey'
                    })
                
                # Check for S3/Spaces
                if ('s3' in content or 'aws_access' in content or 'spaces' in content) and not deps['storage']:
                    deps['storage'].append({
                        'type': 's3',
                        'source': f'env file: {env_file}',
                        'inferred': True
                    })
            except Exception:
                pass
        
        return deps
    
    def _detect_default_port(self) -> int:
        """Detect the default port the application runs on."""
        # Check Dockerfile EXPOSE
        if 'Dockerfile' in self.files:
            try:
                dockerfile = (self.repo_path / 'Dockerfile').read_text()
                for line in dockerfile.split('\n'):
                    if line.strip().upper().startswith('EXPOSE'):
                        parts = line.split()
                        if len(parts) > 1:
                            port_str = parts[1].split('/')[0]
                            return int(port_str)
            except Exception:
                pass
        
        # Check for common port patterns in config
        runtime = self._detect_runtime()
        
        # Framework-specific defaults
        if runtime == 'nodejs':
            if 'next.config.js' in self.files or 'next.config.mjs' in self.files:
                return 3000
            if 'nuxt.config.js' in self.files or 'nuxt.config.ts' in self.files:
                return 3000
            return 3000
        elif runtime == 'python':
            return 8000
        elif runtime == 'go':
            return 8080
        elif runtime == 'ruby':
            return 3000
        elif runtime == 'php':
            return 8080
        elif runtime == 'java':
            return 8080
        
        return 8080
    
    def _detect_env_files(self) -> List[str]:
        """Find environment variable template files."""
        env_patterns = ['.env.example', '.env.sample', '.env.template', 'env.example']
        found = []
        for pattern in env_patterns:
            if pattern in self.files:
                found.append(pattern)
        return found
    
    def _detect_tests(self) -> bool:
        """Check if repository has tests."""
        test_indicators = ['test/', 'tests/', 'spec/', '__tests__/', 
                         'test.py', 'tests.py', 'test.js', 'test.ts',
                         'pytest.ini', 'jest.config.js', 'jest.config.ts']
        return any(any(t in f for t in test_indicators) for f in self.files)
    
    def _detect_monorepo_structure(self) -> Optional[Dict[str, str]]:
        """Detect if this is a monorepo and identify directories."""
        frontend_dirs = ['frontend', 'client', 'web', 'ui', 'packages/frontend', 'apps/web']
        backend_dirs = ['backend', 'server', 'api', 'packages/backend', 'apps/api']
        
        found = {}
        
        for fd in frontend_dirs:
            if any(f.startswith(fd + '/') for f in self.files):
                found['frontend'] = '/' + fd
                break
        
        for bd in backend_dirs:
            if any(f.startswith(bd + '/') for f in self.files):
                found['backend'] = '/' + bd
                break
        
        return found if found else None


def main():
    parser = argparse.ArgumentParser(
        description='Analyze repository architecture for App Platform migration'
    )
    parser.add_argument('repo_path', help='Path to the repository')
    parser.add_argument('--json', action='store_true', help='Output as JSON')
    
    args = parser.parse_args()
    
    try:
        analyzer = ArchitectureAnalyzer(args.repo_path)
        result = analyzer.analyze()
        
        if args.json:
            print(json.dumps(result, indent=2, default=str))
        else:
            print(f"Architecture Type: {result['architecture_type']}")
            print(f"Runtime: {result['runtime']}" + (f" {result['runtime_version']}" if result['runtime_version'] else ""))
            print(f"Build Method: {result['build_method']}")
            print(f"Default Port: {result['default_port']}")
            print(f"\nComponents ({len(result['components'])}):")
            for comp in result['components']:
                print(f"  - {comp['name']} ({comp['type']})" + (f" port:{comp.get('port')}" if comp.get('port') else ""))
            
            deps = result['dependencies']
            if deps['databases']:
                print(f"\nDatabases ({len(deps['databases'])}):")
                for db in deps['databases']:
                    print(f"  - {db['type']} from {db['source']}")
            if deps['caches']:
                print(f"\nCaches ({len(deps['caches'])}):")
                for cache in deps['caches']:
                    print(f"  - {cache['type']} from {cache['source']}")
            if deps['queues']:
                print(f"\nQueues ({len(deps['queues'])}):")
                for queue in deps['queues']:
                    print(f"  - {queue['type']} from {queue['source']}")
            if deps['storage']:
                print(f"\nStorage ({len(deps['storage'])}):")
                for store in deps['storage']:
                    print(f"  - {store['type']} from {store['source']}")
    
    except Exception as e:
        print(f"Error: {e}", file=sys.stderr)
        sys.exit(1)


if __name__ == '__main__':
    main()
