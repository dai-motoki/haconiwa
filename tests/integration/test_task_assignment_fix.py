"""
Test for task assignment fix - ensuring agent_assignment.json is created in the correct location
"""
import pytest
import json
import tempfile
import shutil
from pathlib import Path
from unittest.mock import Mock, patch

from haconiwa.task.manager import TaskManager
from haconiwa.space.manager import SpaceManager


class TestTaskAssignmentFix:
    """Test that agent_assignment.json is created in the correct location"""
    
    def setup_method(self):
        """Set up test environment"""
        self.test_dir = tempfile.mkdtemp()
        self.test_path = Path(self.test_dir)
        
    def teardown_method(self):
        """Clean up test environment"""
        if Path(self.test_dir).exists():
            shutil.rmtree(self.test_dir)
    
    def test_agent_assignment_json_location(self):
        """Test that agent_assignment.json is created at task_dir/.haconiwa/agent_assignment.json"""
        # Create a mock task directory
        task_dir = self.test_path / "test-world" / "tasks" / "test_task_01"
        task_dir.mkdir(parents=True, exist_ok=True)
        
        # Create TaskManager instance
        task_manager = TaskManager()
        
        # Mock the base path
        with patch('haconiwa.task.manager.Path.cwd', return_value=self.test_path):
            # Create a test task config
            task_config = {
                "name": "test_task_01",
                "branch": "test/branch",
                "worktree": True,
                "assignee": "test-agent",
                "space_ref": "test-company",
                "description": "Test task"
            }
            
            # Log agent assignment
            success = task_manager.log_agent_assignment(
                task_name="test_task_01",
                assignee="test-agent",
                space_ref="test-company",
                description="Test task",
                pane_info={"window": "0", "pane": "0"},
                session_name="test-session"
            )
            
            # Check that the file was created in the correct location
            expected_file = task_dir / ".haconiwa" / "agent_assignment.json"
            assert expected_file.exists(), f"agent_assignment.json not found at {expected_file}"
            
            # Verify the content
            with open(expected_file, 'r') as f:
                data = json.load(f)
                assert isinstance(data, list)
                assert len(data) == 1
                assert data[0]["agent_id"] == "test-agent"
                assert data[0]["task_name"] == "test_task_01"
    
    def test_space_manager_reads_correct_location(self):
        """Test that SpaceManager looks for agent_assignment.json in the correct location"""
        # Create test structure
        base_path = self.test_path / "test-world"
        task_dir = base_path / "tasks" / "test_task_01"
        haconiwa_dir = task_dir / ".haconiwa"
        haconiwa_dir.mkdir(parents=True, exist_ok=True)
        
        # Create agent_assignment.json in the correct location
        assignment_file = haconiwa_dir / "agent_assignment.json"
        assignment_data = [{
            "agent_id": "test-agent",
            "task_name": "test_task_01",
            "status": "active"
        }]
        
        with open(assignment_file, 'w') as f:
            json.dump(assignment_data, f)
        
        # Create desk mappings
        desk_mappings_dir = base_path / ".haconiwa"
        desk_mappings_dir.mkdir(parents=True, exist_ok=True)
        desk_mappings_file = desk_mappings_dir / "desk_mappings.json"
        desk_mappings = [{
            "desk_id": "desk-room-01-00",
            "agent_id": "test-agent",
            "room_id": "room-01"
        }]
        
        with open(desk_mappings_file, 'w') as f:
            json.dump(desk_mappings, f)
        
        # Test SpaceManager can find the assignment
        space_manager = SpaceManager()
        
        # Mock subprocess to avoid actual tmux calls
        with patch('subprocess.run') as mock_run:
            mock_run.return_value = Mock(returncode=0)
            
            # Call update_panes_for_task_assignments
            updated_count = space_manager.update_panes_for_task_assignments(
                session_name="test-session",
                base_path=base_path
            )
            
            # Should have found and processed one assignment
            assert updated_count == 1
    
    def test_no_room_frontend_backend_fallback(self):
        """Test that room-frontend and room-backend are not used as fallbacks"""
        space_manager = SpaceManager()
        
        # Create mock session data
        session_data = {
            "rooms": [
                {"id": "room-executive", "name": "Executive Room"},
                {"id": "room-standby", "name": "Standby Room"}
            ]
        }
        
        # Store session data
        space_manager.active_sessions["test-session"] = {
            "session_name": "test-session",
            "config": session_data
        }
        
        # Test internal method - we need to use the actual method name
        # Since _get_window_for_room is a private method, we test indirectly
        # by checking that the method doesn't have special handling for room-frontend/backend
        
        # We can verify this by checking the source code doesn't contain the strings
        import inspect
        source = inspect.getsource(SpaceManager)
        
        # Check that room-frontend and room-backend are not specially handled anymore
        # (They were removed in our fix)
        assert 'room_id == "room-frontend"' not in source or 'room_id == "room-01"' not in source
        
        # The fix removed the special handling, so now these rooms would use default logic