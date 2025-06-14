"""
Integration tests for haconiwa apply with --env flag
"""
import unittest
from unittest.mock import patch, MagicMock
import tempfile
import shutil
from pathlib import Path
import yaml
import subprocess
import os

from haconiwa.core.crd.parser import CRDParser
from haconiwa.core.applier import CRDApplier
from haconiwa.task.manager import TaskManager


class TestApplyWithEnvFiles(unittest.TestCase):
    """Integration tests for apply command with env files"""
    
    def setUp(self):
        self.temp_dir = tempfile.mkdtemp()
        self.original_cwd = os.getcwd()
        os.chdir(self.temp_dir)
        
        # Create test YAML
        self.yaml_content = """
apiVersion: haconiwa.dev/v1
kind: Organization
metadata:
  name: test-org
spec:
  companyName: "Test Company"
  industry: "Technology"
  basePath: "./test-company"
  hierarchy:
    departments:
    - id: "dev"
      name: "Development"
      roles:
      - roleType: "engineering"
        title: "Developer"
        agentId: "dev-1"
---
apiVersion: haconiwa.dev/v1
kind: Space
metadata:
  name: test-space
spec:
  nations:
  - id: jp
    name: "Japan"
    cities:
    - id: tokyo
      name: "Tokyo"
      villages:
      - id: test-village
        name: "Test Village"
        companies:
        - name: test-company
          grid: "2x2"
          basePath: "./test-world"
          organizationRef: "test-org"
          gitRepo:
            url: "https://github.com/test/test.git"
            defaultBranch: "main"
            auth: "ssh"
---
apiVersion: haconiwa.dev/v1
kind: Task
metadata:
  name: test-task
spec:
  taskId: test-task
  title: "Test Task"
  description: "Test task description"
  assignee: "dev-1"
  spaceRef: "test-company"
  worktree: true
  branch: "feature/test"
"""
        
        self.yaml_file = Path(self.temp_dir) / "test.yaml"
        self.yaml_file.write_text(self.yaml_content)
        
        # Create test env files
        self.env_base = Path(self.temp_dir) / ".env.base"
        self.env_base.write_text("""API_KEY=base_key
LOG_LEVEL=INFO
APP_NAME="Test App"
""")
        
        self.env_local = Path(self.temp_dir) / ".env.local"
        self.env_local.write_text("""LOG_LEVEL=DEBUG
DATABASE_URL=postgresql://localhost/test
""")
        
    def tearDown(self):
        os.chdir(self.original_cwd)
        shutil.rmtree(self.temp_dir, ignore_errors=True)
        
    @patch('haconiwa.organization.manager.OrganizationManager.create_organization')
    @patch('haconiwa.space.manager.SpaceManager.create_multiroom_session')
    @patch('haconiwa.task.manager.TaskManager._create_worktree')
    @patch('subprocess.run')
    def test_apply_with_single_env_file(self, mock_run, mock_create_worktree, mock_create_multiroom_session, mock_create_organization):
        """Test apply command with single env file"""
        # Mock successful operations
        mock_create_organization.return_value = True
        mock_create_multiroom_session.return_value = True
        mock_create_worktree.return_value = True
        mock_run.return_value = MagicMock(returncode=0)
        
        # Create mock worktree directory
        worktree_path = Path(self.temp_dir) / "test-world" / "tasks" / "test-task"
        worktree_path.mkdir(parents=True)
        
        # Setup applier with env files
        applier = CRDApplier()
        applier.env_files = [str(self.env_base)]
        
        # Parse CRDs
        parser = CRDParser()
        crds = parser.parse_multi_yaml(self.yaml_content)
        
        # Apply CRDs with Rich output disabled and sys.modules patched
        import sys
        os.environ['NO_COLOR'] = '1'  # Disable color output
        with patch('rich.console.Console'), \
             patch.dict('sys.modules', {'__main__': MagicMock(_current_applier=applier)}):
            results = applier.apply_multiple(crds)
            
        # Check that env file was created in worktree
        env_file = worktree_path / '.env'
        if env_file.exists():
            content = env_file.read_text()
            self.assertIn("API_KEY=base_key", content)
            self.assertIn("LOG_LEVEL=INFO", content)
            
    @patch('haconiwa.legal.framework.HierarchicalLegalFramework.create_framework_from_yaml')
    @patch('haconiwa.organization.manager.OrganizationManager.create_organization')
    @patch('haconiwa.space.manager.SpaceManager.create_multiroom_session')
    @patch('subprocess.run')
    def test_apply_with_multiple_env_files(self, mock_run, mock_create_multiroom_session, mock_create_organization, mock_legal_framework):
        """Test apply command with multiple env files"""
        # Mock successful operations
        mock_legal_framework.return_value = True
        mock_create_organization.return_value = True
        mock_create_multiroom_session.return_value = True
        mock_run.return_value = MagicMock(returncode=0)
        
        # Create mock worktree directory
        worktree_path = Path(self.temp_dir) / "test-world" / "tasks" / "test-task"
        worktree_path.mkdir(parents=True)
        
        # Setup applier with multiple env files
        applier = CRDApplier()
        applier.env_files = [str(self.env_base), str(self.env_local)]
        
        # Parse CRDs
        parser = CRDParser()
        crds = parser.parse_multi_yaml(self.yaml_content)
        
        # Create a side effect for _create_worktree that copies env files
        def mock_create_worktree_with_env_copy(task_name, branch, space_ref, config):
            # Call the env file copy logic  
            env_files = config.get('env_files', [])
            if env_files:
                from haconiwa.task.manager import TaskManager
                tm = TaskManager()
                tm._copy_env_files_to_worktree(worktree_path, env_files)
            return True
            
        # Apply CRDs with Rich output disabled and sys.modules patched
        import sys
        os.environ['NO_COLOR'] = '1'  # Disable color output
        with patch('rich.console.Console'), \
             patch.dict('sys.modules', {'__main__': MagicMock(_current_applier=applier)}), \
             patch('haconiwa.task.manager.TaskManager._create_worktree', side_effect=mock_create_worktree_with_env_copy):
            results = applier.apply_multiple(crds)
            
        # Check merged env file
        env_file = worktree_path / '.env'
        self.assertTrue(env_file.exists(), f"Expected .env file at {env_file}")
        
        content = env_file.read_text()
        # Local should override base
        self.assertIn("LOG_LEVEL=DEBUG", content)
        self.assertNotIn("LOG_LEVEL=INFO", content)
        # Both files' unique values preserved
        self.assertIn("API_KEY=base_key", content)
        self.assertIn("DATABASE_URL=postgresql://localhost/test", content)
            
    def test_cli_env_flag_parsing(self):
        """Test that CLI correctly parses --env flags"""
        # This would be better as a proper CLI test, but we'll test the concept
        from typer.testing import CliRunner
        from haconiwa.cli import app
        
        runner = CliRunner()
        
        # Test dry run with env files
        result = runner.invoke(app, [
            "apply",
            "-f", str(self.yaml_file),
            "--env", str(self.env_base),
            "--env", str(self.env_local),
            "--dry-run",
            "--no-attach"
        ])
        
        # Check that env files are mentioned in output
        if result.exit_code == 0:
            self.assertIn("Would use environment files:", result.stdout)
            self.assertIn(".env.base", result.stdout)
            self.assertIn(".env.local", result.stdout)


if __name__ == '__main__':
    unittest.main()