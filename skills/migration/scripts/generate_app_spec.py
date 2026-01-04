#!/usr/bin/env python3
"""
App Spec Generator Script

Generates DigitalOcean App Platform specification from repository analysis.
Creates both testing and production configurations.

Usage:
    python generate_app_spec.py /path/to/repo --name myapp
    python generate_app_spec.py /path/to/repo --name myapp --env production
    python generate_app_spec.py /path/to/repo --name myapp --output .do/app.yaml
"""

import os
import sys
import json
import argparse
from pathlib import Path
from typing import Dict, List, Optional, Any
from datetime import datetime

# Add scripts directory to path for imports
SCRIPT_DIR = Path(__file__).parent
SHARED_DIR = SCRIPT_DIR.parent.parent.parent / 'shared'
sys.path.insert(0, str(SCRIPT_DIR))

from analyze_architecture import ArchitectureAnalyzer
from detect_platform import PlatformDetector


def load_shared_config(filename: str) -> Dict:
    """Load configuration from shared YAML files."""
    try:
        import yaml
        config_path = SHARED_DIR / filename
        if config_path.exists():
            with open(config_path) as f:
                return yaml.safe_load(f)
    except ImportError:
        pass
    return {}


class AppSpecGenerator:
    """Generates App Platform specifications from repository analysis."""

    # Load instance sizes from shared config, with fallback
    _shared_sizes = load_shared_config('instance-sizes.yaml')
    INSTANCE_SIZES = _shared_sizes.get('environment_defaults', {
        'test': {
            'service': 'apps-s-1vcpu-1gb',
            'worker': 'apps-s-1vcpu-0.5gb',
            'job': 'apps-s-1vcpu-0.5gb'
        },
        'production': {
            'service': 'apps-d-1vcpu-2gb',
            'worker': 'apps-d-1vcpu-1gb',
            'job': 'apps-s-1vcpu-1gb'
        }
    })

    # Load region mappings from shared config, with fallback
    _shared_regions = load_shared_config('regions.yaml')
    _platform_mappings = _shared_regions.get('platform_mappings', {})
    REGION_MAP = {
        # Flatten all platform mappings into a single dict
        **_platform_mappings.get('heroku', {'us': 'nyc', 'eu': 'ams'}),
        **_platform_mappings.get('aws', {
            'us-east-1': 'nyc',
            'us-west-2': 'sfo',
            'eu-west-1': 'lon',
            'eu-central-1': 'fra',
            'ap-southeast-1': 'sgp',
            'ap-south-1': 'blr',
        }),
        **_platform_mappings.get('render', {
            'oregon': 'sfo',
            'frankfurt': 'fra',
            'ohio': 'nyc',
            'singapore': 'sgp',
        }),
        # Default
        'default': _shared_regions.get('defaults', {}).get('primary', 'nyc')
    }
    
    def __init__(self, repo_path: str, app_name: str, environment: str = 'test'):
        self.repo_path = Path(repo_path)
        self.app_name = app_name
        self.environment = environment
        
        # Run analysis
        self.platform_detector = PlatformDetector(repo_path)
        self.platform_info = self.platform_detector.detect()
        
        self.architecture_analyzer = ArchitectureAnalyzer(repo_path)
        self.architecture = self.architecture_analyzer.analyze()
        
        # Track unmapped items
        self.unmapped_items = []
        self.warnings = []
    
    def generate(self, repo_url: Optional[str] = None, branch: str = 'main') -> Dict[str, Any]:
        """Generate complete app spec."""
        spec = {
            'spec': {
                'name': f"{self.app_name}-{self.environment}" if self.environment else self.app_name,
                'region': 'nyc',
            }
        }
        
        # Add components based on architecture
        services = []
        workers = []
        jobs = []
        static_sites = []
        databases = []
        
        for component in self.architecture['components']:
            comp_spec = self._generate_component_spec(component, repo_url, branch)
            
            if component['type'] == 'service':
                services.append(comp_spec)
            elif component['type'] == 'worker':
                workers.append(comp_spec)
            elif component['type'] == 'job':
                jobs.append(comp_spec)
            elif component['type'] == 'static_site':
                static_sites.append(comp_spec)
        
        # Add databases
        databases = self._generate_database_specs()
        
        # Build final spec
        if services:
            spec['spec']['services'] = services
        if workers:
            spec['spec']['workers'] = workers
        if jobs:
            spec['spec']['jobs'] = jobs
        if static_sites:
            spec['spec']['static_sites'] = static_sites
        if databases:
            spec['spec']['databases'] = databases
        
        return spec
    
    def _generate_component_spec(self, component: Dict, repo_url: Optional[str], branch: str) -> Dict[str, Any]:
        """Generate spec for a single component."""
        comp_type = component['type']
        instance_sizes = self.INSTANCE_SIZES[self.environment if self.environment in self.INSTANCE_SIZES else 'test']
        
        spec = {
            'name': component['name']
        }
        
        # Git source
        if repo_url:
            spec['git'] = {
                'repo_clone_url': repo_url,
                'branch': branch
            }
        
        # Source directory
        source_dir = component.get('source_dir', '/')
        if source_dir and source_dir != '/':
            spec['source_dir'] = source_dir
        
        # Build configuration
        if component.get('has_dockerfile', self.architecture['has_dockerfile']):
            spec['dockerfile_path'] = 'Dockerfile'
        else:
            # Use buildpack
            runtime = self.architecture['runtime']
            buildpack_map = {
                'nodejs': 'node-js',
                'python': 'python',
                'go': 'go',
                'ruby': 'ruby',
                'php': 'php',
                'bun': 'bun'
            }
            if runtime in buildpack_map:
                spec['environment_slug'] = buildpack_map[runtime]
        
        # Component-type specific settings
        if comp_type == 'service':
            port = component.get('port') or self.architecture['default_port']
            spec['http_port'] = port
            spec['instance_size_slug'] = instance_sizes.get('service', 'apps-s-1vcpu-1gb')
            spec['instance_count'] = 2 if self.environment == 'production' else 1
            
            # Health check
            spec['health_check'] = {
                'http_path': '/health',
                'initial_delay_seconds': 10,
                'period_seconds': 10
            }
            
            # Autoscaling for production
            if self.environment == 'production':
                spec['autoscaling'] = {
                    'min_instance_count': 2,
                    'max_instance_count': 5,
                    'metrics': [{
                        'type': 'CPU',
                        'percent': 80
                    }]
                }
        
        elif comp_type == 'worker':
            spec['instance_size_slug'] = instance_sizes.get('worker', 'apps-s-1vcpu-0.5gb')
            spec['instance_count'] = 2 if self.environment == 'production' else 1
            
            if component.get('command'):
                spec['run_command'] = component['command']
        
        elif comp_type == 'job':
            spec['instance_size_slug'] = instance_sizes.get('job', 'apps-s-1vcpu-0.5gb')
            spec['kind'] = 'PRE_DEPLOY'  # Default for migration jobs
            
            if component.get('command'):
                spec['run_command'] = component['command']
        
        elif comp_type == 'static_site':
            if component.get('build_command'):
                spec['build_command'] = component['build_command']
            else:
                # Infer build command from runtime
                if self.architecture['runtime'] == 'nodejs':
                    spec['build_command'] = 'npm run build'
            
            spec['output_dir'] = component.get('output_dir', 'dist')
        
        # Environment variables
        spec['envs'] = self._generate_env_vars(component)
        
        return spec
    
    def _generate_env_vars(self, component: Dict) -> List[Dict[str, Any]]:
        """Generate environment variables with bindings."""
        envs = []
        deps = self.architecture['dependencies']
        
        # Database bindings
        for db in deps.get('databases', []):
            if db['type'] == 'postgres':
                envs.append({
                    'key': 'DATABASE_URL',
                    'scope': 'RUN_TIME',
                    'value': '${db.DATABASE_URL}'
                })
            elif db['type'] == 'mysql':
                envs.append({
                    'key': 'MYSQL_URL',
                    'scope': 'RUN_TIME',
                    'value': '${db.DATABASE_URL}'
                })
        
        # Cache bindings (Redis -> Valkey)
        for cache in deps.get('caches', []):
            if cache['type'] in ['redis', 'valkey']:
                # Use VALKEY_URL as primary, note original if it was REDIS_URL
                envs.append({
                    'key': 'VALKEY_URL',
                    'scope': 'RUN_TIME',
                    'value': '${cache.DATABASE_URL}'
                })
                # Add alias for backwards compatibility
                envs.append({
                    'key': 'REDIS_URL',
                    'scope': 'RUN_TIME',
                    'value': '${cache.DATABASE_URL}'
                })
        
        # Common application secrets
        common_secrets = ['SECRET_KEY', 'API_KEY', 'JWT_SECRET']
        for secret in common_secrets:
            envs.append({
                'key': secret,
                'scope': 'RUN_TIME',
                'type': 'SECRET'
            })
        
        # PORT environment variable
        envs.append({
            'key': 'PORT',
            'scope': 'RUN_TIME',
            'value': str(self.architecture['default_port'])
        })
        
        return envs
    
    def _generate_database_specs(self) -> List[Dict[str, Any]]:
        """Generate database specifications."""
        databases = []
        deps = self.architecture['dependencies']
        
        # PostgreSQL
        postgres_deps = [d for d in deps.get('databases', []) if d['type'] == 'postgres']
        if postgres_deps:
            db_spec = {
                'name': 'db',
                'engine': 'PG'
            }
            
            # Version
            version = postgres_deps[0].get('version')
            if version:
                # App Platform supports specific versions
                major_version = version.split('.')[0]
                if major_version in ['14', '15', '16']:
                    db_spec['version'] = major_version
            
            # Dev vs Production
            if self.environment == 'production':
                db_spec['production'] = True
                db_spec['cluster_name'] = f"{self.app_name}-db"
                self.warnings.append(
                    f"Production database: Create cluster first with:\n"
                    f"  doctl databases create {self.app_name}-db --engine pg --region nyc --size db-s-1vcpu-1gb"
                )
            else:
                db_spec['production'] = False  # Dev database
            
            databases.append(db_spec)
        
        # MySQL
        mysql_deps = [d for d in deps.get('databases', []) if d['type'] == 'mysql']
        if mysql_deps:
            db_spec = {
                'name': 'mysqldb',
                'engine': 'MYSQL',
                'production': True,  # No dev database for MySQL
                'cluster_name': f"{self.app_name}-mysql"
            }
            databases.append(db_spec)
            self.warnings.append(
                f"MySQL requires managed database (no dev DB option). Create cluster first with:\n"
                f"  doctl databases create {self.app_name}-mysql --engine mysql --region nyc --size db-s-1vcpu-1gb"
            )
        
        # MongoDB
        mongo_deps = [d for d in deps.get('databases', []) if d['type'] == 'mongodb']
        if mongo_deps:
            db_spec = {
                'name': 'mongodb',
                'engine': 'MONGODB',
                'production': True,
                'cluster_name': f"{self.app_name}-mongo"
            }
            databases.append(db_spec)
            self.warnings.append(
                f"MongoDB requires managed database. Create cluster first with:\n"
                f"  doctl databases create {self.app_name}-mongo --engine mongodb --region nyc --size db-s-1vcpu-1gb"
            )
        
        # Valkey (Redis replacement)
        cache_deps = [d for d in deps.get('caches', []) if d['type'] in ['redis', 'valkey']]
        if cache_deps:
            cache_spec = {
                'name': 'cache',
                'engine': 'VALKEY'  # Use Valkey, not Redis (Redis EOL on DO)
            }
            
            if self.environment == 'production':
                cache_spec['production'] = True
                cache_spec['cluster_name'] = f"{self.app_name}-cache"
                self.warnings.append(
                    f"Cache cluster: Create with:\n"
                    f"  doctl databases create {self.app_name}-cache --engine valkey --region nyc --size db-s-1vcpu-1gb"
                )
            else:
                cache_spec['production'] = False  # Dev Valkey
            
            databases.append(cache_spec)
            
            # Note about Redis -> Valkey
            if any(d['type'] == 'redis' for d in cache_deps):
                self.warnings.append(
                    "Redis → Valkey: Redis is EOL on DigitalOcean. Using Valkey (Redis-compatible). "
                    "Update any REDIS_URL references to VALKEY_URL in your code."
                )
        
        # Handle unmappable dependencies
        for queue in deps.get('queues', []):
            if queue['type'] == 'rabbitmq':
                self.unmapped_items.append({
                    'type': 'queue',
                    'name': 'RabbitMQ',
                    'source': queue['source'],
                    'reason': 'No direct equivalent on App Platform',
                    'options': [
                        'Use external RabbitMQ service (CloudAMQP, etc.)',
                        'Consider using Kafka (supported on DO)',
                        'Use Redis/Valkey for simple queue patterns'
                    ]
                })
        
        return databases
    
    def generate_deploy_template(self, repo_url: str) -> Dict[str, Any]:
        """Generate deploy.template.yaml for Deploy-to-DO button."""
        spec = self.generate(repo_url=repo_url, branch='main')
        
        # Modify for template use
        # Remove production-specific settings
        if 'spec' in spec:
            for service in spec['spec'].get('services', []):
                # Remove instance count for button deploys
                if 'instance_count' in service:
                    del service['instance_count']
                # Remove autoscaling
                if 'autoscaling' in service:
                    del service['autoscaling']
            
            # Use dev databases for button deploys
            for db in spec['spec'].get('databases', []):
                if db.get('engine') in ['PG', 'VALKEY']:
                    db['production'] = False
                    if 'cluster_name' in db:
                        del db['cluster_name']
        
        return spec
    
    def get_migration_report(self) -> Dict[str, Any]:
        """Generate migration report with mappings and gaps."""
        return {
            'generated_at': datetime.now().isoformat(),
            'source_platform': self.platform_info['primary_platform'],
            'source_description': self.platform_info['primary_description'],
            'config_files': self.platform_info['config_files'],
            'architecture': {
                'type': self.architecture['architecture_type'],
                'runtime': self.architecture['runtime'],
                'build_method': self.architecture['build_method']
            },
            'components_mapped': len(self.architecture['components']),
            'components': [
                {
                    'name': c['name'],
                    'type': c['type'],
                    'mapped_to': f"App Platform {c['type']}"
                }
                for c in self.architecture['components']
            ],
            'dependencies': self.architecture['dependencies'],
            'unmapped_items': self.unmapped_items,
            'warnings': self.warnings,
            'requires_user_decision': len(self.unmapped_items) > 0
        }


def to_yaml(data: Dict) -> str:
    """Convert dict to YAML string."""
    try:
        import yaml
        return yaml.dump(data, default_flow_style=False, sort_keys=False, allow_unicode=True)
    except ImportError:
        # Fallback to basic formatting
        return json.dumps(data, indent=2)


def main():
    parser = argparse.ArgumentParser(
        description='Generate App Platform specification from repository'
    )
    parser.add_argument('repo_path', help='Path to the repository')
    parser.add_argument('--name', required=True, help='Application name')
    parser.add_argument('--env', choices=['test', 'production'], default='test',
                       help='Target environment (default: test)')
    parser.add_argument('--repo-url', help='Git repository URL for spec')
    parser.add_argument('--branch', default='main', help='Git branch (default: main)')
    parser.add_argument('--output', help='Output file path')
    parser.add_argument('--deploy-template', action='store_true', 
                       help='Generate deploy.template.yaml instead')
    parser.add_argument('--report', action='store_true',
                       help='Generate migration report')
    parser.add_argument('--json', action='store_true', help='Output as JSON')
    
    args = parser.parse_args()
    
    try:
        generator = AppSpecGenerator(args.repo_path, args.name, args.env)
        
        if args.report:
            report = generator.get_migration_report()
            output = json.dumps(report, indent=2) if args.json else json.dumps(report, indent=2)
            
        elif args.deploy_template:
            if not args.repo_url:
                print("Error: --repo-url required for deploy template", file=sys.stderr)
                sys.exit(1)
            spec = generator.generate_deploy_template(args.repo_url)
            output = json.dumps(spec, indent=2) if args.json else to_yaml(spec)
            
        else:
            spec = generator.generate(repo_url=args.repo_url, branch=args.branch)
            output = json.dumps(spec, indent=2) if args.json else to_yaml(spec)
        
        if args.output:
            Path(args.output).parent.mkdir(parents=True, exist_ok=True)
            Path(args.output).write_text(output)
            print(f"Written to: {args.output}")
        else:
            print(output)
        
        # Print warnings
        if generator.warnings:
            print("\n--- Warnings ---", file=sys.stderr)
            for warning in generator.warnings:
                print(f"⚠️  {warning}", file=sys.stderr)
        
        # Print unmapped items
        if generator.unmapped_items:
            print("\n--- Requires Your Decision ---", file=sys.stderr)
            for item in generator.unmapped_items:
                print(f"❓ {item['name']}: {item['reason']}", file=sys.stderr)
                for opt in item.get('options', []):
                    print(f"   • {opt}", file=sys.stderr)
    
    except Exception as e:
        print(f"Error: {e}", file=sys.stderr)
        import traceback
        traceback.print_exc()
        sys.exit(1)


if __name__ == '__main__':
    main()
