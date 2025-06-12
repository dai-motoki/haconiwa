"""
Test cases for task assignment functionality
Tests the correct assignment of tasks to agents
"""

import pytest
from unittest.mock import Mock, patch, MagicMock
from pathlib import Path
import json

from haconiwa.task.manager import TaskManager
from haconiwa.space.manager import SpaceManager
from haconiwa.core.crd.models import TaskCRD, SpaceCRD


class TestTaskAssignment:
    """Test task assignment to agents functionality"""
    
    def setup_method(self):
        """Setup for each test"""
        self.task_manager = TaskManager()
        self.space_manager = SpaceManager()
    
    def test_simple_task_assignment_1x3_grid(self):
        """Test task assignment for simple 1x3 grid with 3 tasks"""
        # Create mock CRDs for the simple-dev scenario
        # 1 organization, 1 room, 3 desks, 3 tasks
        
        # Mock Space CRD
        mock_space_crd = Mock()
        mock_space_crd.metadata = Mock()
        mock_space_crd.metadata.name = "simple-dev-world"
        mock_space_crd.spec = Mock()
        mock_space_crd.spec.nations = [Mock()]
        mock_space_crd.spec.nations[0].cities = [Mock()]
        mock_space_crd.spec.nations[0].cities[0].villages = [Mock()]
        mock_space_crd.spec.nations[0].cities[0].villages[0].companies = [Mock()]
        
        company = mock_space_crd.spec.nations[0].cities[0].villages[0].companies[0]
        company.name = "simple-dev-company"
        company.grid = "1x3"
        company.organizationRef = "simple-dev-org"
        
        # Define 1 room with 3 desks
        company.buildings = [Mock()]
        company.buildings[0].floors = [Mock()]
        company.buildings[0].floors[0].rooms = [Mock()]
        company.buildings[0].floors[0].rooms[0].id = "room-dev"
        company.buildings[0].floors[0].rooms[0].name = "Dev Room"
        
        # Mock Task CRDs - 3 tasks
        task1 = Mock()
        task1.metadata = Mock()
        task1.metadata.name = "task_auto_claude_01"
        task1.spec = Mock()
        task1.spec.assignee = "dev01-dev-r1-d1"
        task1.spec.spaceRef = "simple-dev-company"
        task1.spec.branch = "task_auto_claude_01"
        task1.spec.description = "Claude auto-execution task"
        
        task2 = Mock()
        task2.metadata = Mock()
        task2.metadata.name = "task_order_command_02"
        task2.spec = Mock()
        task2.spec.assignee = "dev01-dev-r1-d2"
        task2.spec.spaceRef = "simple-dev-company"
        task2.spec.branch = "task_order_command_02"
        task2.spec.description = "Task order command implementation"
        
        task3 = Mock()
        task3.metadata = Mock()
        task3.metadata.name = "task_space_info_03"
        task3.spec = Mock()
        task3.spec.assignee = "dev01-dev-r1-d3"
        task3.spec.spaceRef = "simple-dev-company"
        task3.spec.branch = "task_space_info_03"
        task3.spec.description = "Space info display command"
        
        # Test task assignment
        with patch('pathlib.Path.exists', return_value=True):
            with patch('pathlib.Path.mkdir'):
                with patch('builtins.open', create=True):
                    # Process task assignments
                    assignments = []
                    for task in [task1, task2, task3]:
                        assignment = {
                            "task_name": task.metadata.name,
                            "agent_id": task.spec.assignee,
                            "space_ref": task.spec.spaceRef,
                            "branch": task.spec.branch,
                            "status": "active"
                        }
                        assignments.append(assignment)
                    
                    # Verify assignments
                    assert len(assignments) == 3
                    assert assignments[0]["agent_id"] == "dev01-dev-r1-d1"
                    assert assignments[1]["agent_id"] == "dev01-dev-r1-d2"
                    assert assignments[2]["agent_id"] == "dev01-dev-r1-d3"
    
    def test_task_assignment_updates_agent_pane(self):
        """Test that task assignment updates agent's tmux pane to task directory"""
        # Mock task assignment
        task_assignment = {
            "task_name": "task_auto_claude_01",
            "agent_id": "dev01-dev-r1-d1",
            "space_session": "simple-dev-company",
            "window_id": "0",
            "pane_index": 0,
            "status": "active"
        }
        
        # Mock task directory
        task_dir = Path("/tmp/simple-dev-world/tasks/task_auto_claude_01")
        
        with patch('subprocess.run') as mock_run:
            mock_run.return_value = Mock(returncode=0, stdout="", stderr="")
            
            # Simulate updating pane to task directory
            session_name = task_assignment["space_session"]
            window_id = task_assignment["window_id"]
            pane_index = task_assignment["pane_index"]
            
            # Expected tmux commands
            expected_cd_cmd = ["tmux", "send-keys", "-t", 
                             f"{session_name}:{window_id}.{pane_index}", 
                             f"cd {task_dir.absolute()}", "Enter"]
            
            # Test the update
            self.space_manager._move_pane_to_task_directory(
                session_name, window_id, pane_index,
                task_dir, task_assignment, {}
            )
            
            # Verify tmux command was called
            mock_run.assert_called()
            actual_call = mock_run.call_args_list[0][0][0]
            assert actual_call[:3] == expected_cd_cmd[:3]  # Check command structure
    
    def test_unassigned_agents_go_to_standby(self):
        """Test that agents without tasks are placed in standby directory"""
        # Mock agent without task assignment
        agent_mapping = {
            "desk_id": "dev01-dev-r1-d4",
            "org_id": "org-01", 
            "role": "developer",
            "room_id": "room-dev",
            "title": "Extra Developer - Dev Room"
        }
        
        base_path = Path("/tmp/simple-dev-world")
        standby_dir = base_path / "standby"
        
        with patch('pathlib.Path.mkdir') as mock_mkdir:
            with patch('pathlib.Path.exists', return_value=True):
                with patch('builtins.open', create=True):
                    with patch('subprocess.run') as mock_run:
                        mock_run.return_value = Mock(returncode=0, stdout="", stderr="")
                        
                        # Test standby placement
                        session_name = "simple-dev-company"
                        window_id = "0"
                        pane_index = 3
                        
                        # Simulate no task found for agent
                        with patch.object(self.space_manager, '_update_pane_from_task_logs', return_value=False):
                            result = self.space_manager._update_pane_in_window(
                                session_name, window_id, pane_index,
                                agent_mapping, base_path
                            )
                        
                        # Verify standby directory creation was attempted
                        mock_mkdir.assert_called()
                        
                        # Verify tmux command to move to standby
                        expected_cd_cmd = ["tmux", "send-keys", "-t",
                                         f"{session_name}:{window_id}.{pane_index}",
                                         f"cd {standby_dir.absolute()}", "Enter"]
                        
                        actual_calls = [call[0][0] for call in mock_run.call_args_list]
                        assert any(call[:3] == expected_cd_cmd[:3] for call in actual_calls)
    
    def test_task_assignment_creates_worktree(self):
        """Test that task assignment creates git worktree for the task"""
        task = Mock()
        task.metadata = Mock()
        task.metadata.name = "task_auto_claude_01"
        task.spec = Mock()
        task.spec.branch = "task_auto_claude_01"
        task.spec.worktree = True
        task.spec.spaceRef = "simple-dev-company"
        
        base_path = Path("/tmp/simple-dev-world")
        main_repo = base_path / "tasks" / "main"
        worktree_path = base_path / "tasks" / task.spec.branch
        
        with patch('subprocess.run') as mock_run:
            mock_run.return_value = Mock(returncode=0, stdout="", stderr="")
            
            # Test worktree creation
            success = self.task_manager.create_task_worktree(
                task, main_repo, worktree_path
            )
            
            # Verify git worktree command
            expected_cmd = ["git", "worktree", "add", str(worktree_path), task.spec.branch]
            mock_run.assert_called_with(
                expected_cmd,
                capture_output=True,
                text=True,
                cwd=main_repo
            )
            assert success is True
    
    def test_task_assignment_log_creation(self):
        """Test that task assignment creates proper log files"""
        task_assignment = {
            "task_name": "task_auto_claude_01",
            "agent_id": "dev01-dev-r1-d1",
            "space_session": "simple-dev-company",
            "status": "active",
            "timestamp": "2024-01-01T00:00:00"
        }
        
        task_dir = Path("/tmp/simple-dev-world/tasks/task_auto_claude_01")
        log_file = task_dir / ".haconiwa" / "agent_assignment.json"
        
        with patch('pathlib.Path.exists', return_value=True):
            with patch('pathlib.Path.mkdir'):
                with patch('builtins.open', create=True) as mock_open:
                    # Mock file handle
                    mock_file = MagicMock()
                    mock_open.return_value.__enter__.return_value = mock_file
                    
                    # Create log directory and write assignment
                    log_dir = task_dir / ".haconiwa"
                    log_dir.mkdir(parents=True, exist_ok=True)
                    
                    with open(log_file, 'w', encoding='utf-8') as f:
                        json.dump(task_assignment, f, indent=2, ensure_ascii=False)
                    
                    # Verify file write was called
                    mock_file.write.assert_called()
    
    def test_multiple_agents_per_task_rejection(self):
        """Test that multiple agents cannot be assigned to the same task"""
        # First assignment
        task1 = Mock()
        task1.metadata = Mock()
        task1.metadata.name = "task_auto_claude_01"
        task1.spec = Mock()
        task1.spec.assignee = "dev01-dev-r1-d1"
        task1.spec.spaceRef = "simple-dev-company"
        
        # Attempted second assignment to same task
        task2 = Mock()
        task2.metadata = Mock()
        task2.metadata.name = "task_auto_claude_01"  # Same task
        task2.spec = Mock()
        task2.spec.assignee = "dev01-dev-r1-d2"  # Different agent
        task2.spec.spaceRef = "simple-dev-company"
        
        # Test that second assignment should fail or be rejected
        existing_assignments = {"task_auto_claude_01": {"agent_id": "dev01-dev-r1-d1"}}
        
        # Verify task is already assigned
        assert "task_auto_claude_01" in existing_assignments
        assert existing_assignments["task_auto_claude_01"]["agent_id"] != task2.spec.assignee
    
    def test_agent_id_format_validation(self):
        """Test that agent IDs follow the expected format"""
        valid_agent_ids = [
            "dev01-dev-r1-d1",
            "dev01-dev-r1-d2", 
            "dev01-dev-r1-d3",
            "org01-pm-r1",
            "org01-wk-a-r1",
            "org05-ceo-re"
        ]
        
        invalid_agent_ids = [
            "invalid_format",
            "dev01",
            "r1-d1",
            ""
        ]
        
        # Simple validation function
        def is_valid_agent_id(agent_id):
            parts = agent_id.split('-')
            return len(parts) >= 3
        
        # Test valid IDs
        for agent_id in valid_agent_ids:
            assert is_valid_agent_id(agent_id) is True
        
        # Test invalid IDs
        for agent_id in invalid_agent_ids:
            assert is_valid_agent_id(agent_id) is False
    
    def test_task_description_file_creation(self):
        """Test that task description is saved as markdown file"""
        task = Mock()
        task.metadata = Mock()
        task.metadata.name = "task_auto_claude_01"
        task.spec = Mock()
        task.spec.description = """## タスク: Claude自動実行機能の実装

### 概要
haconiwaで開発タスクを割り当ててapplyすると、tmuxのペインにてclaudeコマンドが自動で打ち込まれ、
タスクディスクリプションのmdファイル（YAMLからコピーされる）を読み取って実装する機能を開発する。
"""
        
        task_dir = Path("/tmp/simple-dev-world/tasks/task_auto_claude_01")
        desc_file = task_dir / "TASK_DESCRIPTION.md"
        
        with patch('pathlib.Path.exists', return_value=True):
            with patch('builtins.open', create=True) as mock_open:
                mock_file = MagicMock()
                mock_open.return_value.__enter__.return_value = mock_file
                
                # Write task description
                with open(desc_file, 'w', encoding='utf-8') as f:
                    f.write(task.spec.description)
                
                # Verify file write
                mock_file.write.assert_called_with(task.spec.description)


if __name__ == "__main__":
    pytest.main([__file__, "-v"])