"""
Generate Parallel Development YAML Implementation

Generates parallel-dev.yaml files for Claude Code SDK based on
AI model search results and analysis.
"""

import yaml
from pathlib import Path
from typing import Dict, Any, List, Optional
from datetime import datetime

class ParallelYAMLGenerator:
    """Generates parallel development YAML configurations"""
    
    def __init__(self, base_path: Path):
        self.base_path = Path(base_path)
        
        # Default prompts for different file types and patterns
        self.default_prompts = {
            'model': {
                'validation': "Add comprehensive validation methods with type hints and error handling",
                'optimization': "Optimize model inference performance and add caching",
                'documentation': "Add detailed docstrings and usage examples",
                'testing': "Implement unit tests with various edge cases",
                'refactoring': "Refactor for better maintainability and code organization"
            },
            'api': {
                'endpoints': "Implement RESTful CRUD endpoints with proper error handling",
                'authentication': "Add JWT authentication and authorization",
                'validation': "Add request/response validation with schemas",
                'documentation': "Add OpenAPI/Swagger documentation",
                'rate_limiting': "Implement rate limiting and request throttling"
            },
            'utils': {
                'type_hints': "Add comprehensive type hints to all functions",
                'error_handling': "Implement robust error handling and logging",
                'optimization': "Optimize performance for large-scale operations",
                'documentation': "Add detailed docstrings with examples",
                'testing': "Create comprehensive unit tests"
            },
            'config': {
                'validation': "Add configuration validation and type checking",
                'environment': "Implement environment-specific configurations",
                'documentation': "Document all configuration options",
                'defaults': "Add sensible defaults with overrides",
                'schema': "Create configuration schema validation"
            },
            'service': {
                'implementation': "Implement core service functionality with error handling",
                'dependency_injection': "Add dependency injection patterns",
                'async': "Convert to async/await for better performance",
                'monitoring': "Add monitoring and metrics collection",
                'testing': "Implement integration and unit tests"
            }
        }
        
        # Task templates for common scenarios
        self.task_templates = {
            'add_type_hints': "Add comprehensive type hints to all functions and methods",
            'add_validation': "Implement input validation and error handling",
            'add_tests': "Create unit tests with pytest covering edge cases",
            'add_docs': "Add detailed docstrings following Google style guide",
            'refactor': "Refactor for better readability and maintainability",
            'optimize': "Optimize performance and reduce computational complexity",
            'security': "Implement security best practices and input sanitization",
            'async_conversion': "Convert synchronous code to async/await pattern",
            'error_handling': "Add comprehensive error handling and logging",
            'api_implementation': "Implement RESTful API endpoints with validation"
        }
    
    def generate_from_scan_results(self, 
                                 scan_results: Dict[str, Any],
                                 action: str = 'refactor',
                                 max_files: int = 10,
                                 custom_prompts: Optional[Dict[str, str]] = None) -> Dict[str, Any]:
        """Generate parallel-dev.yaml from scan results"""
        
        tasks = []
        
        # Extract files from scan results
        if 'matches' in scan_results:  # Model search results
            files = self._extract_files_from_matches(scan_results['matches'], max_files)
        elif 'files' in scan_results:  # Directory analysis results
            files = list(scan_results['files'].keys())[:max_files]
        else:
            files = []
        
        # Generate tasks for each file
        for file_path in files:
            prompt = self._generate_prompt_for_file(file_path, action, custom_prompts)
            tasks.append({
                'file': file_path,
                'prompt': prompt
            })
        
        # Generate YAML configuration
        config = {
            'provider': 'claude',
            'metadata': {
                'generated_at': datetime.now().isoformat(),
                'source': 'haconiwa scan generate-parallel-config',
                'action': action,
                'total_tasks': len(tasks)
            },
            'tasks': tasks,
            'options': {
                'max_concurrent': min(5, max(1, len(tasks) // 2)),  # Dynamic concurrency
                'timeout': 120,  # 2 minutes per task
                'allowed_tools': ['Read', 'Write', 'Edit', 'MultiEdit'],
                'permission_mode': 'confirmEach',
                'output_dir': './parallel-dev-results'
            }
        }
        
        return config
    
    def generate_for_model_migration(self,
                                   old_model: str,
                                   new_model: str,
                                   files: List[str]) -> Dict[str, Any]:
        """Generate YAML for model migration tasks"""
        
        tasks = []
        
        for file_path in files:
            prompt = f"Migrate code from {old_model} to {new_model}. Update import statements, " \
                    f"API calls, method names, and parameters. Ensure compatibility with {new_model} " \
                    f"while maintaining existing functionality. Add migration comments where significant changes are made."
            
            tasks.append({
                'file': file_path,
                'prompt': prompt
            })
        
        config = {
            'provider': 'claude',
            'metadata': {
                'generated_at': datetime.now().isoformat(),
                'source': 'haconiwa scan generate-parallel-config',
                'migration': f"{old_model} -> {new_model}",
                'total_tasks': len(tasks)
            },
            'tasks': tasks,
            'options': {
                'max_concurrent': 3,
                'timeout': 180,  # 3 minutes for migration tasks
                'allowed_tools': ['Read', 'Write', 'Edit', 'MultiEdit'],
                'permission_mode': 'confirmEach',
                'output_dir': f'./migration-{old_model}-to-{new_model}'
            }
        }
        
        return config
    
    def generate_for_pattern_fix(self,
                               pattern: str,
                               fix_description: str,
                               files: List[str]) -> Dict[str, Any]:
        """Generate YAML for fixing specific patterns across files"""
        
        tasks = []
        
        for file_path in files:
            prompt = f"Find all occurrences of pattern '{pattern}' and {fix_description}. " \
                    f"Ensure the changes maintain code functionality and follow best practices. " \
                    f"Add comments explaining significant changes."
            
            tasks.append({
                'file': file_path,
                'prompt': prompt
            })
        
        config = {
            'provider': 'claude',
            'metadata': {
                'generated_at': datetime.now().isoformat(),
                'source': 'haconiwa scan generate-parallel-config',
                'pattern': pattern,
                'fix': fix_description,
                'total_tasks': len(tasks)
            },
            'tasks': tasks,
            'options': {
                'max_concurrent': 5,
                'timeout': 90,
                'allowed_tools': ['Read', 'Write', 'Edit', 'MultiEdit'],
                'permission_mode': 'acceptEdits',  # Auto-accept for pattern fixes
                'output_dir': './pattern-fix-results'
            }
        }
        
        return config
    
    def generate_project_wide(self,
                            action: str,
                            file_pattern: str = "*.py",
                            exclude_patterns: Optional[List[str]] = None) -> Dict[str, Any]:
        """Generate YAML for project-wide changes"""
        
        from .scanner import ModelScanner
        
        scanner = ModelScanner(self.base_path)
        files = []
        
        # Find all matching files
        for file_path in scanner._iter_files([file_pattern]):
            if exclude_patterns:
                skip = False
                for pattern in exclude_patterns:
                    if pattern in str(file_path):
                        skip = True
                        break
                if skip:
                    continue
            
            files.append(str(file_path.relative_to(self.base_path)))
        
        # Generate tasks
        tasks = []
        for file_path in files[:50]:  # Limit to 50 files for safety
            prompt = self._get_action_prompt(action)
            tasks.append({
                'file': file_path,
                'prompt': prompt
            })
        
        config = {
            'provider': 'claude',
            'metadata': {
                'generated_at': datetime.now().isoformat(),
                'source': 'haconiwa scan generate-parallel-config',
                'action': action,
                'file_pattern': file_pattern,
                'total_tasks': len(tasks)
            },
            'tasks': tasks,
            'options': {
                'max_concurrent': 5,
                'timeout': 120,
                'allowed_tools': ['Read', 'Write', 'Edit', 'MultiEdit'],
                'permission_mode': 'confirmEach',
                'output_dir': f'./project-wide-{action}'
            }
        }
        
        return config
    
    def save_yaml(self, config: Dict[str, Any], output_path: Path) -> Path:
        """Save configuration to YAML file"""
        
        output_path = Path(output_path)
        output_path.parent.mkdir(parents=True, exist_ok=True)
        
        with open(output_path, 'w', encoding='utf-8') as f:
            yaml.dump(config, f, default_flow_style=False, sort_keys=False, allow_unicode=True)
        
        return output_path
    
    def _extract_files_from_matches(self, matches: Dict[str, List[Any]], max_files: int) -> List[str]:
        """Extract file paths from scan match results"""
        files = []
        
        for category, file_list in matches.items():
            for file_info in file_list:
                if 'path' in file_info:
                    files.append(file_info['path'])
                    if len(files) >= max_files:
                        return files
        
        return files
    
    def _generate_prompt_for_file(self, 
                                file_path: str, 
                                action: str,
                                custom_prompts: Optional[Dict[str, str]] = None) -> str:
        """Generate appropriate prompt based on file type and action"""
        
        # Check custom prompts first
        if custom_prompts and file_path in custom_prompts:
            return custom_prompts[file_path]
        
        # Determine file category
        file_path_lower = file_path.lower()
        
        if 'model' in file_path_lower:
            category = 'model'
        elif 'api' in file_path_lower or 'route' in file_path_lower:
            category = 'api'
        elif 'util' in file_path_lower or 'helper' in file_path_lower:
            category = 'utils'
        elif 'config' in file_path_lower or 'setting' in file_path_lower:
            category = 'config'
        elif 'service' in file_path_lower:
            category = 'service'
        else:
            # Default based on action
            return self._get_action_prompt(action)
        
        # Get category-specific prompt
        if category in self.default_prompts and action in self.default_prompts[category]:
            return self.default_prompts[category][action]
        
        # Fallback to general action prompt
        return self._get_action_prompt(action)
    
    def _get_action_prompt(self, action: str) -> str:
        """Get general action prompt"""
        if action in self.task_templates:
            return self.task_templates[action]
        
        # Default prompt
        return f"Perform {action} on this file following best practices"
    
    def create_example_yaml(self) -> Dict[str, Any]:
        """Create an example parallel-dev.yaml configuration"""
        
        example_config = {
            'provider': 'claude',
            'metadata': {
                'generated_at': datetime.now().isoformat(),
                'source': 'haconiwa scan generate-parallel-config',
                'description': 'Example parallel development configuration'
            },
            'tasks': [
                {
                    'file': 'src/models/user.py',
                    'prompt': 'Add validation methods and type hints'
                },
                {
                    'file': 'src/models/product.py',
                    'prompt': 'Implement inventory tracking'
                },
                {
                    'file': 'src/models/order.py',
                    'prompt': 'Add status management'
                },
                {
                    'file': 'src/api/routes/users.py',
                    'prompt': 'Implement CRUD endpoints with validation'
                },
                {
                    'file': 'src/services/auth.py',
                    'prompt': 'Add JWT authentication'
                }
            ],
            'options': {
                'max_concurrent': 3,
                'timeout': 90,
                'allowed_tools': ['Read', 'Write', 'Edit', 'MultiEdit'],
                'permission_mode': 'confirmEach',
                'output_dir': './parallel-dev-results'
            }
        }
        
        return example_config