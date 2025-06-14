"""
Unit tests for task submit functionality
"""

import unittest
from unittest.mock import Mock, patch, MagicMock, call
from pathlib import Path
import subprocess

from src.haconiwa.task.submit import TaskSubmitter, TaskSubmitError


class TestTaskSubmitter(unittest.TestCase):
    """Test TaskSubmitter class"""
    
    def setUp(self):
        """Set up test fixtures"""
        self.space_manager = Mock()
        self.task_manager = Mock()
        self.task_manager.tasks = {}
        self.submitter = TaskSubmitter(self.space_manager, self.task_manager)
    
    def test_prepare_description_inline(self):
        """Test preparing inline description"""
        result = self.submitter._prepare_description("Test description", None)
        self.assertEqual(result, "Test description")
    
    def test_prepare_description_both_specified(self):
        """Test error when both description and file are specified"""
        with self.assertRaises(TaskSubmitError) as cm:
            self.submitter._prepare_description("inline", "file.md")
        self.assertIn("Cannot specify both", str(cm.exception))
    
    @patch('builtins.open', create=True)
    def test_read_description_file(self, mock_open):
        """Test reading description from file"""
        mock_open.return_value.__enter__.return_value.read.return_value = "File content"
        
        with patch('pathlib.Path.exists', return_value=True):
            result = self.submitter._read_description_file("test.md")
            self.assertEqual(result, "File content")
    
    def test_read_description_file_not_found(self):
        """Test error when description file not found"""
        with patch('pathlib.Path.exists', return_value=False):
            with self.assertRaises(FileNotFoundError):
                self.submitter._read_description_file("missing.md")
    
    @patch('subprocess.run')
    def test_validate_company_exists(self, mock_run):
        """Test validating company exists"""
        mock_run.return_value = MagicMock(returncode=0, stdout="company1\ncompany2\n")
        
        self.assertTrue(self.submitter._validate_company("company1"))
        self.assertFalse(self.submitter._validate_company("company3"))
    
    @patch('subprocess.run')
    def test_validate_company_no_sessions(self, mock_run):
        """Test validating company when no sessions exist"""
        mock_run.return_value = MagicMock(returncode=1)
        
        self.assertFalse(self.submitter._validate_company("any-company"))
    
    def test_validate_branch_name(self):
        """Test branch name validation"""
        # Valid names
        self.assertTrue(self.submitter._validate_branch_name("feature/test"))
        self.assertTrue(self.submitter._validate_branch_name("bugfix/issue-123"))
        self.assertTrue(self.submitter._validate_branch_name("release/v1.0.0"))
        
        # Invalid names
        self.assertFalse(self.submitter._validate_branch_name(""))
        self.assertFalse(self.submitter._validate_branch_name("feature test"))  # space
        self.assertFalse(self.submitter._validate_branch_name("feature..test"))  # ..
        self.assertFalse(self.submitter._validate_branch_name("feature~test"))  # ~
        self.assertFalse(self.submitter._validate_branch_name("feature:test"))  # :
    
    @patch('subprocess.run')
    def test_branch_exists(self, mock_run):
        """Test checking if branch exists"""
        # Branch exists
        mock_run.return_value = MagicMock(returncode=0)
        self.assertTrue(self.submitter._branch_exists("existing-branch"))
        
        # Branch doesn't exist
        mock_run.return_value = MagicMock(returncode=1)
        self.assertFalse(self.submitter._branch_exists("new-branch"))
    
    @patch('subprocess.run')
    def test_get_current_branch(self, mock_run):
        """Test getting current branch"""
        mock_run.return_value = MagicMock(returncode=0, stdout="feature/test\n")
        
        result = self.submitter._get_current_branch()
        self.assertEqual(result, "feature/test")
    
    @patch('subprocess.run')
    def test_get_current_branch_error(self, mock_run):
        """Test getting current branch with error"""
        mock_run.return_value = MagicMock(returncode=1)
        
        result = self.submitter._get_current_branch()
        self.assertEqual(result, "main")  # Default
    
    def test_extract_agent_id_from_path(self):
        """Test extracting agent ID from path"""
        # PM in room 1
        self.assertEqual(
            self.submitter._extract_agent_id_from_path("/path/to/org-01/01pm", "0"),
            "org01-pm-r1"
        )
        
        # Worker A in room 1
        self.assertEqual(
            self.submitter._extract_agent_id_from_path("/path/to/org-02/02a", "0"),
            "org02-wk-a-r1"
        )
        
        # PM in room 2
        self.assertEqual(
            self.submitter._extract_agent_id_from_path("/path/to/org-01/11pm", "1"),
            "org01-pm-r2"
        )
        
        # Invalid paths
        self.assertIsNone(self.submitter._extract_agent_id_from_path("/invalid/path", "0"))
        self.assertIsNone(self.submitter._extract_agent_id_from_path("/", "0"))
    
    def test_path_matches_agent(self):
        """Test path matching for agents"""
        # PM matches
        self.assertTrue(self.submitter._path_matches_agent("/org-01/01pm", "org01-pm-r1"))
        self.assertTrue(self.submitter._path_matches_agent("/org-01/11pm", "org01-pm-r2"))
        
        # Worker matches
        self.assertTrue(self.submitter._path_matches_agent("/org-02/02a", "org02-wk-a-r1"))
        self.assertTrue(self.submitter._path_matches_agent("/org-03/13b", "org03-wk-b-r2"))
        
        # Non-matches
        self.assertFalse(self.submitter._path_matches_agent("/org-01/01pm", "org02-pm-r1"))
        self.assertFalse(self.submitter._path_matches_agent("/org-01/01a", "org01-pm-r1"))
    
    @patch('subprocess.run')
    def test_create_worktree_success(self, mock_run):
        """Test successful worktree creation"""
        mock_run.return_value = MagicMock(returncode=0)
        
        with patch('pathlib.Path.mkdir'):
            self.submitter._create_worktree("feature/test", "./tasks/feature/test", "main")
        
        mock_run.assert_called_once_with(
            ["git", "worktree", "add", "-b", "feature/test", "./tasks/feature/test", "main"],
            capture_output=True,
            text=True
        )
    
    @patch('subprocess.run')
    def test_create_worktree_branch_exists(self, mock_run):
        """Test worktree creation when branch already exists"""
        mock_run.return_value = MagicMock(
            returncode=1,
            stderr="already exists"
        )
        
        with self.assertRaises(TaskSubmitError) as cm:
            self.submitter._create_worktree("existing", "./tasks/existing", "main")
        self.assertIn("already exists", str(cm.exception))
    
    @patch('subprocess.run')
    def test_find_agent_pane(self, mock_run):
        """Test finding agent pane"""
        mock_run.return_value = MagicMock(
            returncode=0,
            stdout="0:/path/to/org-01/01pm:PM\n1:/path/to/org-01/01a:Worker A\n"
        )
        
        result = self.submitter._find_agent_pane("company", "org01-pm-r1")
        
        self.assertIsNotNone(result)
        self.assertEqual(result["window_id"], "0")
        self.assertEqual(result["pane_index"], "0")
        self.assertIn("01pm", result["current_path"])
    
    @patch('subprocess.run')
    def test_move_agent_to_worktree(self, mock_run):
        """Test moving agent to worktree"""
        mock_run.return_value = MagicMock(returncode=0)
        
        pane_info = {
            "session": "company",
            "window_id": "0",
            "pane_index": "1"
        }
        
        with patch('pathlib.Path.absolute', return_value=Path("/abs/path")):
            self.submitter._move_agent_to_worktree("company", pane_info, "./tasks/test")
        
        mock_run.assert_called_once()
        call_args = mock_run.call_args[0][0]
        self.assertEqual(call_args[0], "tmux")
        self.assertEqual(call_args[1], "send-keys")
        self.assertIn("cd /abs/path", call_args)
    
    @patch('builtins.open', create=True)
    @patch('pathlib.Path.mkdir')
    def test_create_agent_assignment_log(self, mock_mkdir, mock_open):
        """Test creating agent assignment log"""
        mock_file = MagicMock()
        mock_open.return_value.__enter__.return_value = mock_file
        
        self.submitter._create_agent_assignment_log(
            worktree_path=Path("./tasks/test"),
            assignee="org01-pm-r1",
            task_name="Test Task",
            company="test-company",
            description="Test description"
        )
        
        # Check directory was created
        mock_mkdir.assert_called_once()
        
        # Check files were written
        self.assertEqual(mock_open.call_count, 2)  # JSON and README
    
    @patch('src.haconiwa.task.submit.TaskSubmitter._validate_company')
    @patch('src.haconiwa.task.submit.TaskSubmitter._get_available_agents')
    def test_submit_task_validation_errors(self, mock_agents, mock_validate):
        """Test submit task validation errors"""
        # Company not found
        mock_validate.return_value = False
        
        with self.assertRaises(TaskSubmitError) as cm:
            self.submitter.submit_task(
                company="invalid",
                assignee="agent",
                title="Test",
                branch="test"
            )
        self.assertIn("Company 'invalid' not found", str(cm.exception))
        
        # Agent not found
        mock_validate.return_value = True
        mock_agents.return_value = ["agent1", "agent2"]
        
        with self.assertRaises(TaskSubmitError) as cm:
            self.submitter.submit_task(
                company="company",
                assignee="agent3",
                title="Test",
                branch="test"
            )
        self.assertIn("Agent 'agent3' not found", str(cm.exception))
    
    def test_show_dry_run_summary(self):
        """Test dry run summary display"""
        with patch('builtins.print') as mock_print:
            self.submitter._show_dry_run_summary(
                company="test-company",
                assignee="org01-pm-r1",
                title="Test Task",
                branch="feature/test",
                description="Test description",
                base_branch="main",
                priority="high",
                room="room-alpha",
                worktree_path=Path("./tasks/test")
            )
            
            # Check that summary was printed
            calls = [str(call) for call in mock_print.call_args_list]
            self.assertTrue(any("DRY RUN MODE" in str(call) for call in calls))
            self.assertTrue(any("test-company" in str(call) for call in calls))
            self.assertTrue(any("org01-pm-r1" in str(call) for call in calls))


if __name__ == '__main__':
    unittest.main()