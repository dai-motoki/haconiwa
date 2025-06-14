"""Test for .haconiwa directory structure in task directories"""

import json
import os
import tempfile
import shutil
from pathlib import Path
from unittest.mock import Mock, patch, MagicMock

import pytest

from haconiwa.task.manager import TaskManager


class TestHaconiwaDirectoryStructure:
    """Test .haconiwa directory structure with task name subdirectories"""
    
    @pytest.fixture(autouse=True)
    def setup(self):
        """Set up test environment"""
        # Reset TaskManager singleton before each test
        TaskManager._instance = None
        TaskManager._initialized = False
        
        self.temp_dir = tempfile.mkdtemp()
        self.task_manager = TaskManager()
        yield
        
        # Clean up after test
        shutil.rmtree(self.temp_dir, ignore_errors=True)
        
        # Reset TaskManager singleton after each test to prevent side effects
        if hasattr(self.task_manager, 'tasks'):
            self.task_manager.tasks.clear()
        TaskManager._instance = None
        TaskManager._initialized = False
    
    def test_create_immediate_agent_assignment_log_structure(self):
        """Test that _create_immediate_agent_assignment_log creates correct directory structure"""
        # Create a mock task directory
        task_name = "test_task_frontend_01"
        base_path = Path(self.temp_dir) / "test_world"
        tasks_path = base_path / "tasks"
        task_dir = tasks_path / task_name
        task_dir.mkdir(parents=True, exist_ok=True)
        
        # Mock the _find_space_base_path method
        with patch.object(self.task_manager, '_find_space_base_path', return_value=base_path):
            with patch.object(self.task_manager, '_get_session_name_from_space_ref', return_value="test-session"):
                # Call the method
                result = self.task_manager._create_immediate_agent_assignment_log(
                    task_name=task_name,
                    assignee="test-agent-01",
                    space_ref="test-space",
                    description="Test task description"
                )
        
        # Verify the result
        assert result is True
        
        # Check directory structure
        haconiwa_dir = task_dir / ".haconiwa" / task_name
        assert haconiwa_dir.exists()
        assert haconiwa_dir.is_dir()
        
        # Check files exist
        json_file = haconiwa_dir / "agent_assignment.json"
        readme_file = haconiwa_dir / "README.md"
        assert json_file.exists()
        assert readme_file.exists()
        
        # Verify JSON content
        with open(json_file, 'r') as f:
            data = json.load(f)
        assert isinstance(data, list)
        assert len(data) == 1
        assert data[0]["agent_id"] == "test-agent-01"
        assert data[0]["task_name"] == task_name
    
    def test_create_agent_assignment_log_structure(self):
        """Test that _create_agent_assignment_log creates correct directory structure"""
        # Create a mock task directory
        task_name = "test_task_backend_02"
        task_dir = Path(self.temp_dir) / "tasks" / task_name
        task_dir.mkdir(parents=True, exist_ok=True)
        
        # Call the method
        result = self.task_manager._create_agent_assignment_log(
            task_dir=str(task_dir),
            assignee="test-agent-02",
            task_name=task_name,
            session_name="test-session",
            window_id="0",
            pane_index="1"
        )
        
        # Verify the result
        assert result is True
        
        # Check directory structure
        haconiwa_dir = task_dir / ".haconiwa" / task_name
        assert haconiwa_dir.exists()
        assert haconiwa_dir.is_dir()
        
        # Check files exist
        json_file = haconiwa_dir / "agent_assignment.json"
        readme_file = haconiwa_dir / "README.md"
        assert json_file.exists()
        assert readme_file.exists()
        
        # Verify JSON content
        with open(json_file, 'r') as f:
            data = json.load(f)
        assert isinstance(data, list)
        assert len(data) == 1
        assert data[0]["agent_id"] == "test-agent-02"
        assert data[0]["task_name"] == task_name
        assert data[0]["tmux_window"] == "0"
        assert data[0]["tmux_pane"] == "1"
    
    def test_multiple_tasks_no_conflict(self):
        """Test that multiple tasks don't conflict in .haconiwa directory"""
        # Create multiple task directories
        task_names = ["task_ui_design_01", "task_api_dev_02", "task_db_schema_03"]
        base_path = Path(self.temp_dir) / "test_world"
        tasks_path = base_path / "tasks"
        
        for task_name in task_names:
            task_dir = tasks_path / task_name
            task_dir.mkdir(parents=True, exist_ok=True)
            
            # Mock the _find_space_base_path method
            with patch.object(self.task_manager, '_find_space_base_path', return_value=base_path):
                with patch.object(self.task_manager, '_get_session_name_from_space_ref', return_value="test-session"):
                    # Create assignment for each task
                    result = self.task_manager._create_immediate_agent_assignment_log(
                        task_name=task_name,
                        assignee=f"agent-{task_name}",
                        space_ref="test-space",
                        description=f"Description for {task_name}"
                    )
                    assert result is True
        
        # Verify each task has its own subdirectory
        for task_name in task_names:
            task_dir = tasks_path / task_name
            haconiwa_dir = task_dir / ".haconiwa" / task_name
            assert haconiwa_dir.exists()
            
            # Check files
            json_file = haconiwa_dir / "agent_assignment.json"
            assert json_file.exists()
            
            # Verify content is unique
            with open(json_file, 'r') as f:
                data = json.load(f)
            assert data[0]["agent_id"] == f"agent-{task_name}"
            assert data[0]["task_name"] == task_name
    
    def test_append_to_existing_assignment(self):
        """Test appending to existing assignment log"""
        # Create a task directory
        task_name = "test_task_append"
        task_dir = Path(self.temp_dir) / "tasks" / task_name
        task_dir.mkdir(parents=True, exist_ok=True)
        
        # First assignment
        result1 = self.task_manager._create_agent_assignment_log(
            task_dir=str(task_dir),
            assignee="agent-01",
            task_name=task_name,
            session_name="session-1",
            window_id="0",
            pane_index="0"
        )
        assert result1 is True
        
        # Second assignment (should append)
        result2 = self.task_manager._create_agent_assignment_log(
            task_dir=str(task_dir),
            assignee="agent-02",
            task_name=task_name,
            session_name="session-1",
            window_id="0",
            pane_index="1"
        )
        assert result2 is True
        
        # Check that both assignments are in the file
        haconiwa_dir = task_dir / ".haconiwa" / task_name
        json_file = haconiwa_dir / "agent_assignment.json"
        
        with open(json_file, 'r') as f:
            data = json.load(f)
        
        assert isinstance(data, list)
        assert len(data) == 2
        assert data[0]["agent_id"] == "agent-01"
        assert data[1]["agent_id"] == "agent-02"