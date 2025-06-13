"""
Tests for the generate_parallel module

Tests cover the ParallelYAMLGenerator class and its various generation modes
including example generation, model migration, pattern fixes, and project-wide changes.
"""

import pytest
from pathlib import Path
import tempfile
import yaml
from datetime import datetime
from unittest.mock import Mock, patch

from haconiwa.scan.generate_parallel import ParallelYAMLGenerator


class TestParallelYAMLGenerator:
    """Test ParallelYAMLGenerator class"""
    
    def setup_method(self):
        """Setup test environment"""
        self.temp_dir = Path(tempfile.mkdtemp())
        self.generator = ParallelYAMLGenerator(base_path=self.temp_dir)
    
    def teardown_method(self):
        """Cleanup test environment"""
        import shutil
        if self.temp_dir.exists():
            shutil.rmtree(self.temp_dir)
    
    def test_init(self):
        """Test generator initialization"""
        assert self.generator.base_path == self.temp_dir
        assert isinstance(self.generator.default_prompts, dict)
        assert isinstance(self.generator.task_templates, dict)
        assert 'model' in self.generator.default_prompts
        assert 'add_type_hints' in self.generator.task_templates
    
    def test_create_example_yaml(self):
        """Test example YAML generation"""
        config = self.generator.create_example_yaml()
        
        assert config['provider'] == 'claude'
        assert 'metadata' in config
        assert config['metadata']['source'] == 'haconiwa scan generate-parallel'
        assert 'tasks' in config
        assert len(config['tasks']) == 5
        assert config['tasks'][0]['file'] == 'src/models/user.py'
        assert config['tasks'][0]['prompt'] == 'Add validation methods and type hints'
        assert 'options' in config
        assert config['options']['max_concurrent'] == 3
        assert config['options']['timeout'] == 90
        assert 'Read' in config['options']['allowed_tools']
    
    def test_save_yaml(self):
        """Test YAML file saving"""
        config = {
            'provider': 'claude',
            'tasks': [
                {'file': 'test.py', 'prompt': 'Add tests'}
            ],
            'options': {
                'max_concurrent': 1,
                'timeout': 60
            }
        }
        
        output_path = self.temp_dir / 'test-output.yaml'
        saved_path = self.generator.save_yaml(config, output_path)
        
        assert saved_path == output_path
        assert output_path.exists()
        
        # Load and verify saved content
        with open(output_path, 'r') as f:
            loaded_config = yaml.safe_load(f)
        
        assert loaded_config['provider'] == 'claude'
        assert len(loaded_config['tasks']) == 1
        assert loaded_config['tasks'][0]['file'] == 'test.py'
    
    def test_generate_from_scan_results_with_matches(self):
        """Test generation from scan results with matches"""
        scan_results = {
            'model_name': 'gpt-4',
            'matches': {
                'model': [
                    {'path': 'models/gpt4/model.py', 'type': 'python'},
                    {'path': 'models/gpt4/config.py', 'type': 'python'}
                ],
                'api': [
                    {'path': 'api/gpt4_api.py', 'type': 'python'}
                ]
            }
        }
        
        config = self.generator.generate_from_scan_results(
            scan_results,
            action='add_tests',
            max_files=2
        )
        
        assert config['provider'] == 'claude'
        assert len(config['tasks']) == 2
        assert config['metadata']['action'] == 'add_tests'
        assert config['options']['max_concurrent'] == 1  # min(5, max(1, 2//2))
        
        # Check that appropriate prompts were generated
        for task in config['tasks']:
            assert 'file' in task
            assert 'prompt' in task
            assert len(task['prompt']) > 0
    
    def test_generate_from_scan_results_with_files(self):
        """Test generation from directory analysis results"""
        scan_results = {
            'files': {
                'src/utils/helper.py': {'category': 'utils'},
                'src/api/routes.py': {'category': 'api'},
                'src/models/user.py': {'category': 'model'}
            }
        }
        
        config = self.generator.generate_from_scan_results(
            scan_results,
            action='refactor',
            max_files=2
        )
        
        assert len(config['tasks']) == 2
        assert config['metadata']['action'] == 'refactor'
    
    def test_generate_for_model_migration(self):
        """Test model migration YAML generation"""
        files = [
            'src/models/old_model.py',
            'src/api/old_api.py',
            'tests/test_old.py'
        ]
        
        config = self.generator.generate_for_model_migration(
            'gpt-3.5',
            'gpt-4',
            files
        )
        
        assert config['provider'] == 'claude'
        assert config['metadata']['migration'] == 'gpt-3.5 -> gpt-4'
        assert len(config['tasks']) == 3
        
        # Check migration prompts
        for task in config['tasks']:
            assert 'Migrate code from gpt-3.5 to gpt-4' in task['prompt']
            assert task['file'] in files
        
        assert config['options']['timeout'] == 180  # Longer timeout for migration
        assert config['options']['output_dir'] == './migration-gpt-3.5-to-gpt-4'
    
    def test_generate_for_pattern_fix(self):
        """Test pattern fix YAML generation"""
        pattern = "deprecated_api\\(\\)"
        fix_description = "replace with new_api()"
        files = [
            'src/main.py',
            'src/utils.py',
            'src/api.py'
        ]
        
        config = self.generator.generate_for_pattern_fix(
            pattern,
            fix_description,
            files
        )
        
        assert config['provider'] == 'claude'
        assert config['metadata']['pattern'] == pattern
        assert config['metadata']['fix'] == fix_description
        assert len(config['tasks']) == 3
        
        # Check pattern fix prompts
        for task in config['tasks']:
            assert f"Find all occurrences of pattern '{pattern}'" in task['prompt']
            assert fix_description in task['prompt']
        
        assert config['options']['permission_mode'] == 'acceptEdits'  # Auto-accept
    
    def test_generate_project_wide(self):
        """Test project-wide YAML generation"""
        # Create test files in temp directory
        src_dir = self.temp_dir / 'src'
        src_dir.mkdir()
        models_dir = src_dir / 'models'
        models_dir.mkdir()
        tests_dir = self.temp_dir / 'tests'
        tests_dir.mkdir()
        
        # Create test files
        (src_dir / 'main.py').write_text('def main(): pass')
        (src_dir / 'utils.py').write_text('def helper(): pass')
        (models_dir / 'user.py').write_text('class User: pass')
        (tests_dir / 'test_main.py').write_text('def test_main(): pass')
        
        config = self.generator.generate_project_wide(
            action='add_type_hints',
            file_pattern='*.py',
            exclude_patterns=['tests/']
        )
        
        assert config['provider'] == 'claude'
        assert config['metadata']['action'] == 'add_type_hints'
        assert config['metadata']['file_pattern'] == '*.py'
        
        # Should exclude test files
        file_names = [task['file'] for task in config['tasks']]
        assert 'tests/test_main.py' not in file_names
        for task in config['tasks']:
            assert 'tests/' not in task['file']
            assert task['prompt'] == 'Add comprehensive type hints to all functions and methods'
    
    def test_generate_prompt_for_file_with_custom_prompts(self):
        """Test prompt generation with custom prompts"""
        custom_prompts = {
            'src/special.py': 'Custom prompt for special file'
        }
        
        prompt = self.generator._generate_prompt_for_file(
            'src/special.py',
            'refactor',
            custom_prompts
        )
        
        assert prompt == 'Custom prompt for special file'
    
    def test_generate_prompt_for_file_by_category(self):
        """Test prompt generation based on file category"""
        # Model file
        prompt = self.generator._generate_prompt_for_file(
            'src/models/user.py',
            'validation',
            None
        )
        assert 'validation methods' in prompt
        
        # API file
        prompt = self.generator._generate_prompt_for_file(
            'src/api/routes.py',
            'endpoints',
            None
        )
        assert 'RESTful CRUD endpoints' in prompt
        
        # Utils file
        prompt = self.generator._generate_prompt_for_file(
            'src/utils/helpers.py',
            'type_hints',
            None
        )
        assert 'type hints' in prompt
        
        # Config file
        prompt = self.generator._generate_prompt_for_file(
            'src/config/settings.py',
            'validation',
            None
        )
        assert 'configuration validation' in prompt
        
        # Service file
        prompt = self.generator._generate_prompt_for_file(
            'src/services/auth.py',
            'implementation',
            None
        )
        assert 'service functionality' in prompt
    
    def test_generate_prompt_for_file_fallback(self):
        """Test prompt generation fallback for unknown categories"""
        prompt = self.generator._generate_prompt_for_file(
            'src/unknown/file.py',
            'add_tests',
            None
        )
        
        assert prompt == 'Create unit tests with pytest covering edge cases'
    
    def test_get_action_prompt(self):
        """Test action prompt retrieval"""
        # Known action
        prompt = self.generator._get_action_prompt('add_type_hints')
        assert 'type hints' in prompt
        
        # Unknown action
        prompt = self.generator._get_action_prompt('unknown_action')
        assert prompt == 'Perform unknown_action on this file following best practices'
    
    def test_extract_files_from_matches(self):
        """Test file extraction from match results"""
        matches = {
            'model': [
                {'path': 'file1.py'},
                {'path': 'file2.py'}
            ],
            'api': [
                {'path': 'file3.py'},
                {'path': 'file4.py'}
            ]
        }
        
        files = self.generator._extract_files_from_matches(matches, max_files=3)
        
        assert len(files) == 3
        assert 'file1.py' in files
        assert 'file2.py' in files
        assert 'file3.py' in files
    
    def test_metadata_generation(self):
        """Test metadata is properly generated"""
        config = self.generator.create_example_yaml()
        
        assert 'metadata' in config
        assert 'generated_at' in config['metadata']
        assert 'source' in config['metadata']
        
        # Check timestamp format
        timestamp = config['metadata']['generated_at']
        # Should be able to parse it
        datetime.fromisoformat(timestamp)
    
    def test_dynamic_concurrency_calculation(self):
        """Test dynamic max_concurrent calculation"""
        scan_results = {
            'files': {f'file{i}.py': {} for i in range(20)}
        }
        
        config = self.generator.generate_from_scan_results(
            scan_results,
            action='refactor',
            max_files=20
        )
        
        # Should be min(5, max(1, 20//2)) = 5
        assert config['options']['max_concurrent'] == 5
        
        # Test with fewer files
        scan_results = {
            'files': {'file1.py': {}, 'file2.py': {}}
        }
        
        config = self.generator.generate_from_scan_results(
            scan_results,
            action='refactor',
            max_files=2
        )
        
        # Should be min(5, max(1, 2//2)) = 1
        assert config['options']['max_concurrent'] == 1


class TestGenerateParallelIntegration:
    """Integration tests for generate_parallel functionality"""
    
    @pytest.mark.integration
    def test_full_workflow(self):
        """Test complete workflow from scan results to YAML generation"""
        with tempfile.TemporaryDirectory() as temp_dir:
            temp_path = Path(temp_dir)
            
            # Create test files
            model_dir = temp_path / 'models'
            model_dir.mkdir()
            (model_dir / 'user.py').write_text('class User: pass')
            (model_dir / 'product.py').write_text('class Product: pass')
            
            api_dir = temp_path / 'api'
            api_dir.mkdir()
            (api_dir / 'routes.py').write_text('def get_users(): pass')
            
            # Create generator
            generator = ParallelYAMLGenerator(base_path=temp_path)
            
            # Simulate scan results
            scan_results = {
                'matches': {
                    'model': [
                        {'path': 'models/user.py', 'type': 'python'},
                        {'path': 'models/product.py', 'type': 'python'}
                    ],
                    'api': [
                        {'path': 'api/routes.py', 'type': 'python'}
                    ]
                }
            }
            
            # Generate YAML
            config = generator.generate_from_scan_results(
                scan_results,
                action='add_type_hints',
                max_files=10
            )
            
            # Save YAML
            output_path = temp_path / 'parallel-dev.yaml'
            generator.save_yaml(config, output_path)
            
            # Verify
            assert output_path.exists()
            
            with open(output_path, 'r') as f:
                loaded = yaml.safe_load(f)
            
            assert loaded['provider'] == 'claude'
            assert len(loaded['tasks']) == 3
            assert loaded['metadata']['action'] == 'add_type_hints'
            
            # Check task content
            file_paths = [task['file'] for task in loaded['tasks']]
            assert 'models/user.py' in file_paths
            assert 'models/product.py' in file_paths
            assert 'api/routes.py' in file_paths