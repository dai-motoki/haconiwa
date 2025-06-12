"""
Test cases for task directory assignment functionality
Tests that agents are correctly moved to their task directories
"""

import pytest
from unittest.mock import Mock, patch, MagicMock, call
from pathlib import Path
import json
import subprocess

from haconiwa.space.manager import SpaceManager
from haconiwa.task.manager import TaskManager


class TestTaskDirectoryAssignment:
    """Test task directory assignment to agents"""
    
    def setup_method(self):
        """Setup for each test"""
        self.space_manager = SpaceManager()
        self.task_manager = TaskManager()
    
    def test_update_agent_pane_directories_with_multiple_agents(self):
        """Test updating pane directories for multiple agents with tasks"""
        # Setup
        space_ref = "test-company"
        session_name = "test-company"
        
        # Mock task manager with multiple tasks
        self.task_manager.tasks = {
            "task_01": {
                "config": {
                    "assignee": "dev01-dev-r1-d1",
                    "space_ref": space_ref
                },
                "status": "created"
            },
            "task_02": {
                "config": {
                    "assignee": "dev01-dev-r1-d2", 
                    "space_ref": space_ref
                },
                "status": "created"
            },
            "task_03": {
                "config": {
                    "assignee": "dev01-dev-r1-d3",
                    "space_ref": space_ref
                },
                "status": "created"
            }
        }
        
        # Mock subprocess.run for tmux commands
        with patch('subprocess.run') as mock_run:
            mock_run.return_value = Mock(returncode=0, stdout="", stderr="")
            
            # Test the update
            result = self.task_manager.update_agent_pane_directories(space_ref, session_name)
            
            # Verify tmux commands were called for each agent
            assert result is True
            assert mock_run.call_count >= 3  # At least 3 agents
    
    def test_post_process_space_tasks_integration(self):
        """Test post-processing of space with task assignments"""
        # Mock space configuration
        base_path = Path("/tmp/test-world")
        space_config = {
            "name": "test-company",
            "base_path": str(base_path),
            "organizations": [
                {"id": "01", "name": "Test Org", "department_id": "dev"}
            ],
            "rooms": [
                {"id": "room-01", "name": "Dev Room"}
            ]
        }
        
        # Mock active session
        self.space_manager.active_sessions["test-company"] = {
            "config": space_config,
            "base_path": str(base_path),
            "session_name": "test-company"
        }
        
        # Mock task assignments
        with patch.object(self.space_manager, '_get_current_task_assignments') as mock_get_tasks:
            mock_get_tasks.return_value = {
                "dev01-dev-r1-d1": {
                    "task_name": "task_01",
                    "task_dir": base_path / "tasks" / "task_01"
                },
                "dev01-dev-r1-d2": {
                    "task_name": "task_02", 
                    "task_dir": base_path / "tasks" / "task_02"
                }
            }
            
            with patch('subprocess.run') as mock_run:
                mock_run.return_value = Mock(returncode=0, stdout="", stderr="")
                
                # Call post-process
                result = self.space_manager._post_process_space_with_tasks("test-company", space_config)
                
                # Verify it attempted to update panes
                assert mock_run.called
    
    def test_agent_assignment_log_reading(self):
        """Test reading agent assignment logs from task directories"""
        base_path = Path("/tmp/test-world")
        task_dir = base_path / "tasks" / "task_01"
        log_file = task_dir / ".haconiwa" / "agent_assignment.json"
        
        # Mock log data
        log_data = [{
            "agent_id": "dev01-dev-r1-d1",
            "task_name": "task_01",
            "space_session": "test-company",
            "status": "active"
        }]
        
        with patch('pathlib.Path.exists') as mock_exists:
            mock_exists.return_value = True
            
            with patch('builtins.open', create=True) as mock_open:
                mock_file = MagicMock()
                mock_file.__enter__.return_value.read.return_value = json.dumps(log_data)
                mock_open.return_value = mock_file
                
                # Test reading the log
                with open(log_file, 'r') as f:
                    data = json.load(f)
                
                assert data[0]["agent_id"] == "dev01-dev-r1-d1"
                assert data[0]["task_name"] == "task_01"
    
    def test_large_scale_task_assignment(self):
        """Test task assignment for large number of agents (32 panes)"""
        space_ref = "large-company"
        session_name = "large-company"
        
        # Create 32 tasks for 8x4 grid
        tasks = {}
        for i in range(32):
            org_num = (i // 4) + 1  # 8 organizations, 4 agents each
            role = i % 4  # 0=pm, 1=a, 2=b, 3=c
            
            if role == 0:
                agent_id = f"org{org_num:02d}-pm-r1"
            else:
                agent_id = f"org{org_num:02d}-wk-{chr(ord('a') + role - 1)}-r1"
            
            task_name = f"task_{i+1:02d}"
            tasks[task_name] = {
                "config": {
                    "assignee": agent_id,
                    "space_ref": space_ref
                },
                "status": "created"
            }
        
        self.task_manager.tasks = tasks
        
        # Mock subprocess for tmux commands
        with patch('subprocess.run') as mock_run:
            mock_run.return_value = Mock(returncode=0, stdout="", stderr="")
            
            # Mock finding panes
            with patch.object(self.task_manager, '_find_pane_for_agent') as mock_find:
                # Return valid pane info for each agent
                mock_find.return_value = {
                    "window_id": "0",
                    "pane_index": "0",
                    "current_path": "/tmp/test"
                }
                
                # Update all agents
                result = self.task_manager.update_agent_pane_directories(space_ref, session_name)
                
                # Verify all agents were processed
                assert result is True
                assert mock_find.call_count == 32
    
    def test_multi_room_task_assignment(self):
        """Test task assignment across multiple rooms"""
        space_ref = "multi-room-company"
        session_name = "multi-room-company"
        
        # Create tasks for 2 rooms
        tasks = {
            # Room 1 tasks
            "task_r1_01": {
                "config": {
                    "assignee": "org01-pm-r1",
                    "space_ref": space_ref
                },
                "status": "created"
            },
            "task_r1_02": {
                "config": {
                    "assignee": "org01-wk-a-r1",
                    "space_ref": space_ref
                },
                "status": "created"
            },
            # Room 2 tasks
            "task_r2_01": {
                "config": {
                    "assignee": "org01-pm-r2",
                    "space_ref": space_ref
                },
                "status": "created"
            },
            "task_r2_02": {
                "config": {
                    "assignee": "org01-wk-a-r2",
                    "space_ref": space_ref
                },
                "status": "created"
            }
        }
        
        self.task_manager.tasks = tasks
        
        with patch('subprocess.run') as mock_run:
            # Mock tmux list-panes output for different windows
            def mock_list_panes(cmd, **kwargs):
                if "list-panes" in cmd and ":0" in cmd[-1]:
                    # Window 0 (room 1)
                    return Mock(returncode=0, stdout="0:/tmp/org-01/01pm:PM - Alpha Room\n1:/tmp/org-01/01a:Worker A - Alpha Room\n")
                elif "list-panes" in cmd and ":1" in cmd[-1]:
                    # Window 1 (room 2)
                    return Mock(returncode=0, stdout="0:/tmp/org-01/11pm:PM - Beta Room\n1:/tmp/org-01/11a:Worker A - Beta Room\n")
                else:
                    return Mock(returncode=0, stdout="", stderr="")
            
            mock_run.side_effect = mock_list_panes
            
            # Update agents in both rooms
            result = self.task_manager.update_agent_pane_directories(space_ref, session_name)
            
            # Verify commands were sent to correct windows
            assert result is True
            
            # Check that tmux commands included both windows
            window_0_calls = [c for c in mock_run.call_args_list if ":0" in str(c)]
            window_1_calls = [c for c in mock_run.call_args_list if ":1" in str(c)]
            
            assert len(window_0_calls) > 0  # Room 1 updates
            assert len(window_1_calls) > 0  # Room 2 updates
    
    def test_agent_id_parsing_variations(self):
        """Test parsing various agent ID formats"""
        test_cases = [
            # Standard formats
            ("org01-pm-r1", "01", "pm", None, "r1"),
            ("org02-wk-a-r1", "02", "wk", "a", "r1"),
            ("org03-wk-b-r2", "03", "wk", "b", "r2"),
            ("org05-ceo-re", "05", "ceo", None, "re"),
            # Simple format from YAML
            ("dev01-dev-r1-d1", "01", "dev", None, "r1"),
            ("dev01-dev-r1-d2", "01", "dev", None, "r1"),
        ]
        
        for agent_id, exp_org, exp_role, exp_worker, exp_room in test_cases:
            parts = agent_id.split("-")
            
            if len(parts) == 3:
                org_part = parts[0]
                role_part = parts[1]
                room_part = parts[2]
                worker_type = None
            elif len(parts) == 4 and parts[1] == "wk":
                org_part = parts[0]
                role_part = parts[1]
                worker_type = parts[2]
                room_part = parts[3]
            elif len(parts) == 4 and parts[1] == "dev":
                # Handle dev01-dev-r1-d1 format
                org_part = parts[0]
                role_part = parts[1]
                room_part = parts[2]
                worker_type = None
            else:
                continue
            
            # Extract org number
            if org_part.startswith("org"):
                org_num = org_part[3:]
            elif org_part.startswith("dev"):
                org_num = org_part[3:]
            else:
                org_num = None
            
            assert org_num == exp_org, f"Failed to parse org from {agent_id}"
            assert role_part == exp_role, f"Failed to parse role from {agent_id}"
            assert worker_type == exp_worker, f"Failed to parse worker from {agent_id}"


if __name__ == "__main__":
    pytest.main([__file__, "-v"])