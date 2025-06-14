"""Tests for parallel-dev functionality."""

import asyncio
import json
from pathlib import Path
from unittest.mock import AsyncMock, MagicMock, patch

import pytest
from typer.testing import CliRunner

from haconiwa.cli import app
from haconiwa.tool.parallel_dev import ParallelDevManager


@pytest.fixture
def runner():
    """Create a CLI runner."""
    return CliRunner()


@pytest.fixture
def temp_files(tmp_path):
    """Create temporary test files."""
    files = {
        "src/main.py": 'def main():\n    print("Hello")\n',
        "src/utils.py": 'def helper():\n    return 42\n',
        "src/api.py": 'class API:\n    pass\n'
    }
    
    for file_path, content in files.items():
        file = tmp_path / file_path
        file.parent.mkdir(parents=True, exist_ok=True)
        file.write_text(content)
    
    return tmp_path


@pytest.fixture
def yaml_config(tmp_path):
    """Create a test YAML configuration."""
    config = {
        "provider": "claude",
        "tasks": [
            {"file": "src/main.py", "prompt": "Add type hints"},
            {"file": "src/utils.py", "prompt": "Add docstrings"}
        ],
        "options": {
            "max_concurrent": 2,
            "timeout": 30
        }
    }
    
    config_file = tmp_path / "test-config.yaml"
    import yaml
    with open(config_file, 'w') as f:
        yaml.dump(config, f)
    
    return config_file


class TestParallelDevManager:
    """Test ParallelDevManager class."""
    
    @pytest.mark.asyncio
    async def test_process_file_success(self):
        """Test successful file processing."""
        manager = ParallelDevManager()
        
        # Mock Claude Code SDK
        with patch('haconiwa.tool.parallel_dev.query') as mock_query:
            mock_message = MagicMock()
            mock_message.content = "File edited successfully"
            mock_query.return_value = AsyncMock()
            mock_query.return_value.__aiter__.return_value = [mock_message]
            
            result = await manager.process_file(
                "test.py",
                "Add type hints",
                MagicMock(),
                "task-001"
            )
            
            assert result["status"] == "success"
            assert result["file"] == "test.py"
            assert result["prompt"] == "Add type hints"
            assert len(result["messages"]) == 1
    
    @pytest.mark.asyncio
    async def test_process_file_error(self):
        """Test file processing with error."""
        manager = ParallelDevManager()
        
        # Mock Claude Code SDK to raise error
        with patch('haconiwa.tool.parallel_dev.query') as mock_query:
            mock_query.side_effect = Exception("API Error")
            
            result = await manager.process_file(
                "test.py",
                "Add type hints",
                MagicMock(),
                "task-001"
            )
            
            assert result["status"] == "error"
            assert "API Error" in result["error"]
    
    @pytest.mark.asyncio
    async def test_parallel_execute(self):
        """Test parallel execution of multiple files."""
        manager = ParallelDevManager()
        
        files_and_prompts = [
            ("file1.py", "prompt1"),
            ("file2.py", "prompt2"),
            ("file3.py", "prompt3")
        ]
        
        # Mock process_file
        async def mock_process(file, prompt, options, task_id):
            return {
                "task_id": task_id,
                "file": file,
                "prompt": prompt,
                "status": "success",
                "messages": [],
                "duration": 1.0
            }
        
        manager.process_file = mock_process
        
        results = await manager.parallel_execute(
            files_and_prompts,
            max_concurrent=2
        )
        
        assert len(results) == 3
        assert all(r["status"] == "success" for r in results)
    
    def test_save_results(self, tmp_path):
        """Test saving results to file."""
        manager = ParallelDevManager()
        manager.results_dir = tmp_path / "results"
        
        results = [
            {
                "task_id": "task-001",
                "file": "test.py",
                "prompt": "Add types",
                "status": "success",
                "messages": ["Done"],
                "duration": 1.5
            }
        ]
        
        summary_file = manager.save_results(results, "test-session")
        
        assert summary_file.exists()
        
        with open(summary_file, 'r') as f:
            summary = json.load(f)
        
        assert summary["session_id"] == "test-session"
        assert summary["total_tasks"] == 1
        assert summary["successful"] == 1


class TestParallelDevCLI:
    """Test CLI commands."""
    
    def test_tool_list(self, runner):
        """Test tool list command."""
        result = runner.invoke(app, ["tool", "list"])
        assert result.exit_code == 0
        assert "Available Tools" in result.stdout
        assert "claude-code" in result.stdout
    
    def test_tool_install(self, runner):
        """Test tool install command."""
        result = runner.invoke(app, ["tool", "install", "claude-code"])
        assert result.exit_code == 0
        assert "Installing claude-code" in result.stdout
    
    def test_parallel_dev_help(self, runner):
        """Test parallel-dev help."""
        result = runner.invoke(app, ["tool", "parallel-dev", "--help"])
        assert result.exit_code == 0
        assert "parallel-dev" in result.stdout
    
    def test_parallel_dev_claude_help(self, runner):
        """Test parallel-dev claude help."""
        result = runner.invoke(app, ["tool", "parallel-dev", "claude", "--help"])
        assert result.exit_code == 0
        assert "Execute parallel file edits" in result.stdout
    
    def test_parallel_dev_dry_run(self, runner, temp_files):
        """Test dry run mode."""
        result = runner.invoke(app, [
            "tool", "parallel-dev", "claude",
            "-f", "src/main.py,src/utils.py",
            "-p", "Add type hints,Add docstrings",
            "--dry-run"
        ])
        
        assert result.exit_code == 0
        assert "Dry run" in result.stdout
        assert "src/main.py: Add type hints" in result.stdout
    
    def test_parallel_dev_missing_args(self, runner):
        """Test with missing arguments."""
        result = runner.invoke(app, ["tool", "parallel-dev", "claude"])
        assert result.exit_code == 1
        assert "Must specify" in result.stdout
    
    def test_parallel_dev_mismatched_counts(self, runner):
        """Test with mismatched file and prompt counts."""
        result = runner.invoke(app, [
            "tool", "parallel-dev", "claude",
            "-f", "file1.py,file2.py",
            "-p", "prompt1"
        ])
        assert result.exit_code == 1
        assert "must match" in result.stdout
    
    @patch('haconiwa.tool.parallel_dev.manager')
    def test_parallel_dev_yaml_config(self, mock_manager, runner, yaml_config):
        """Test with YAML configuration."""
        # Mock the execution
        mock_manager.parallel_execute = AsyncMock(return_value=[
            {"status": "success", "file": "src/main.py"},
            {"status": "success", "file": "src/utils.py"}
        ])
        mock_manager.save_results = MagicMock(return_value=Path("results.json"))
        
        result = runner.invoke(app, [
            "tool", "parallel-dev", "claude",
            "--from-yaml", str(yaml_config)
        ], input="y\n")  # Auto-confirm
        
        assert result.exit_code == 0
    
    def test_parallel_dev_status(self, runner):
        """Test status command."""
        result = runner.invoke(app, ["tool", "parallel-dev", "status"])
        assert result.exit_code == 0
        assert "No active tasks" in result.stdout or "Active Tasks" in result.stdout
    
    def test_parallel_dev_history(self, runner):
        """Test history command."""
        result = runner.invoke(app, ["tool", "parallel-dev", "history"])
        assert result.exit_code == 0
        assert "No execution history" in result.stdout or "Recent Executions" in result.stdout