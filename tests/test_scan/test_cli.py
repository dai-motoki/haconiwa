"""
Tests for the scan CLI commands
"""

import pytest
from typer.testing import CliRunner
from pathlib import Path
import tempfile
import json
from haconiwa.scan.cli import scan_app


class TestScanCLI:
    """Test cases for scan CLI commands"""
    
    @pytest.fixture
    def runner(self):
        """Create a CLI runner"""
        return CliRunner()
    
    @pytest.fixture
    def temp_model_dir(self):
        """Create a temporary directory with test models"""
        with tempfile.TemporaryDirectory() as tmpdir:
            base_path = Path(tmpdir)
            
            # Create test model structure
            model_dir = base_path / "models" / "test" / "o1-mini"
            model_dir.mkdir(parents=True)
            
            # Create config
            config = {
                "model_name": "o1-mini",
                "model_type": "language",
                "parameters": "3B"
            }
            with open(model_dir / "config.json", "w") as f:
                json.dump(config, f)
            
            # Create model file
            (model_dir / "model.pt").touch()
            
            # Create example
            with open(model_dir / "example.py", "w") as f:
                f.write("# Example for o1-mini\nprint('Hello from o1-mini')")
            
            yield base_path
    
    def test_scan_model_command(self, runner, temp_model_dir):
        """Test the scan model command"""
        result = runner.invoke(
            scan_app,
            ["model", "o1-mini", "--path", str(temp_model_dir), "--format", "json"]
        )
        
        assert result.exit_code == 0
        output = json.loads(result.stdout)
        assert output['model_name'] == "o1-mini"
        assert output['total_files'] > 0
    
    def test_scan_content_command(self, runner, temp_model_dir):
        """Test the scan content command"""
        result = runner.invoke(
            scan_app,
            ["content", "Hello", "--path", str(temp_model_dir), "--type", ".py"]
        )
        
        assert result.exit_code == 0
        assert "Hello from o1-mini" in result.stdout
    
    def test_scan_analyze_command(self, runner, temp_model_dir):
        """Test the scan analyze command"""
        result = runner.invoke(
            scan_app,
            ["analyze", "--path", str(temp_model_dir), "--format", "summary"]
        )
        
        assert result.exit_code == 0
        assert "Model Analysis Summary" in result.stdout
    
    def test_scan_list_command(self, runner, temp_model_dir):
        """Test the scan list command"""
        result = runner.invoke(
            scan_app,
            ["list", "--path", str(temp_model_dir), "--format", "table"]
        )
        
        assert result.exit_code == 0
        assert "Available AI Models" in result.stdout
    
    def test_scan_compare_command(self, runner, temp_model_dir):
        """Test the scan compare command"""
        # Create another model for comparison
        model2_dir = temp_model_dir / "models" / "test" / "gpt-4"
        model2_dir.mkdir(parents=True)
        
        config2 = {
            "model_name": "gpt-4",
            "model_type": "language",
            "parameters": "175B"
        }
        with open(model2_dir / "config.json", "w") as f:
            json.dump(config2, f)
        
        result = runner.invoke(
            scan_app,
            ["compare", "o1-mini", "gpt-4", "--path", str(temp_model_dir), "--format", "json"]
        )
        
        assert result.exit_code == 0
        output = json.loads(result.stdout)
        assert 'capabilities' in output
    
    def test_scan_guide_command(self, runner, temp_model_dir):
        """Test the scan guide command"""
        result = runner.invoke(
            scan_app,
            ["guide", "o1-mini", "--path", str(temp_model_dir), "--type", "development"]
        )
        
        assert result.exit_code == 0
        assert "Development Guide: o1-mini" in result.stdout
        assert "## Overview" in result.stdout
    
    def test_scan_model_with_options(self, runner, temp_model_dir):
        """Test scan model with various options"""
        # Test with content inclusion
        result = runner.invoke(
            scan_app,
            ["model", "o1-mini", "--path", str(temp_model_dir), "--content", "--format", "yaml"]
        )
        
        assert result.exit_code == 0
        assert "model_name: o1-mini" in result.stdout
        
        # Test with no prefix stripping
        result = runner.invoke(
            scan_app,
            ["model", "o1-mini", "--path", str(temp_model_dir), "--no-strip-prefix"]
        )
        
        assert result.exit_code == 0
    
    def test_scan_content_with_context(self, runner, temp_model_dir):
        """Test content search with context lines"""
        result = runner.invoke(
            scan_app,
            ["content", "Hello", "--path", str(temp_model_dir), "--context", "5", "--format", "json"]
        )
        
        assert result.exit_code == 0
        output = json.loads(result.stdout)
        assert 'matches' in output
        if output['matches']:
            assert 'context' in output['matches'][0]
    
    def test_scan_analyze_with_category(self, runner, temp_model_dir):
        """Test analyze with specific category"""
        result = runner.invoke(
            scan_app,
            ["analyze", "--path", str(temp_model_dir), "--category", "general", "--format", "json"]
        )
        
        assert result.exit_code == 0
        output = json.loads(result.stdout)
        assert output['category'] == 'general'
    
    def test_scan_list_with_filters(self, runner, temp_model_dir):
        """Test list with provider and category filters"""
        result = runner.invoke(
            scan_app,
            ["list", "--path", str(temp_model_dir), "--provider", "unknown", "--format", "json"]
        )
        
        assert result.exit_code == 0
        output = json.loads(result.stdout)
        assert isinstance(output, list)
    
    def test_scan_guide_types(self, runner, temp_model_dir):
        """Test different guide types"""
        guide_types = ["development", "usage", "integration", "quickstart"]
        
        for guide_type in guide_types:
            result = runner.invoke(
                scan_app,
                ["guide", "o1-mini", "--path", str(temp_model_dir), "--type", guide_type]
            )
            
            assert result.exit_code == 0
            assert "o1-mini" in result.stdout
    
    def test_scan_generate_parallel_config_example(self, runner):
        """Test generate-parallel-config with example option"""
        with tempfile.TemporaryDirectory() as tmpdir:
            output_path = Path(tmpdir) / "test-parallel.yaml"
            
            result = runner.invoke(
                scan_app,
                ["generate-parallel-config", "--example", "--output", str(output_path)]
            )
            
            assert result.exit_code == 0
            assert "Generated example parallel-dev.yaml" in result.stdout
            assert output_path.exists()
            
            # Check generated YAML content
            import yaml
            with open(output_path, 'r') as f:
                config = yaml.safe_load(f)
            
            assert config['provider'] == 'claude'
            assert len(config['tasks']) == 5
            assert config['options']['max_concurrent'] == 3
    
    def test_scan_generate_parallel_config_from_model(self, runner, temp_model_dir):
        """Test generate-parallel-config from model search"""
        with tempfile.TemporaryDirectory() as tmpdir:
            output_path = Path(tmpdir) / "parallel-dev.yaml"
            
            # Change to temp_model_dir before running command
            import os
            original_cwd = os.getcwd()
            try:
                os.chdir(temp_model_dir)
                result = runner.invoke(
                    scan_app,
                    ["generate-parallel-config", 
                     "--source", "model:o1-mini", 
                     "--action", "add_tests",
                     "--output", str(output_path)]
                )
            finally:
                os.chdir(original_cwd)
            
            assert result.exit_code == 0
            assert "Generated parallel-dev YAML" in result.stdout
            assert output_path.exists()
    
    def test_scan_generate_parallel_config_migration(self, runner):
        """Test generate-parallel-config for model migration"""
        with tempfile.TemporaryDirectory() as tmpdir:
            output_path = Path(tmpdir) / "migration.yaml"
            
            result = runner.invoke(
                scan_app,
                ["generate-parallel-config",
                 "--migration", "gpt-3.5:gpt-4",
                 "--max-files", "5",
                 "--output", str(output_path)]
            )
            
            assert result.exit_code == 0
            assert "Generated migration YAML" in result.stdout
    
    def test_scan_generate_parallel_config_pattern_fix(self, runner):
        """Test generate-parallel-config for pattern fix"""
        with tempfile.TemporaryDirectory() as tmpdir:
            output_path = Path(tmpdir) / "pattern-fix.yaml"
            
            result = runner.invoke(
                scan_app,
                ["generate-parallel-config",
                 "--pattern-fix", "old_func:replace with new_func",
                 "--output", str(output_path)]
            )
            
            assert result.exit_code == 0
            assert "Generated pattern fix YAML" in result.stdout
    
    def test_scan_generate_parallel_config_project_wide(self, runner, temp_model_dir):
        """Test generate-parallel-config for project-wide changes"""
        with tempfile.TemporaryDirectory() as tmpdir:
            output_path = Path(tmpdir) / "project-wide.yaml"
            
            # Change to temp_model_dir before running command
            import os
            original_cwd = os.getcwd()
            try:
                os.chdir(temp_model_dir)
                result = runner.invoke(
                    scan_app,
                    ["generate-parallel-config",
                     "--project-wide", "*.py",
                     "--action", "add_type_hints",
                     "--output", str(output_path)]
                )
            finally:
                os.chdir(original_cwd)
            
            assert result.exit_code == 0
            assert "Generated project-wide YAML" in result.stdout
    
    def test_scan_main_help(self, runner):
        """Test main scan help"""
        result = runner.invoke(scan_app, ["--help"])
        
        assert result.exit_code == 0
        assert "Universal AI model search" in result.stdout
        
        # Test help command
        result = runner.invoke(scan_app, ["help"])
        
        assert result.exit_code == 0
        assert "Haconiwa Scan Command" in result.stdout
        assert "generate-parallel-config" in result.stdout