"""
Unit tests for CRDApplier env files functionality
"""
import unittest
from unittest.mock import patch, MagicMock
import tempfile
import shutil
from pathlib import Path
import os

from haconiwa.core.applier import CRDApplier
from haconiwa.core.crd.models import TaskCRD, TaskSpec, Metadata


class TestApplierEnvFiles(unittest.TestCase):
    """Test CRDApplier env files functionality"""
    
    def setUp(self):
        self.temp_dir = tempfile.mkdtemp()
        self.original_cwd = os.getcwd()
        os.chdir(self.temp_dir)
        
    def tearDown(self):
        os.chdir(self.original_cwd)
        shutil.rmtree(self.temp_dir, ignore_errors=True)
        
    def test_applier_env_files_passed_to_task_config(self):
        """Test that applier.env_files are passed to task config"""
        # Create applier with env files
        applier = CRDApplier()
        applier.env_files = ['.env.base', '.env.local']
        
        # Create a TaskCRD
        task_crd = TaskCRD(
            apiVersion='haconiwa.dev/v1',
            kind='Task',
            metadata=Metadata(name='test-task'),
            spec=TaskSpec(
                branch='feature/test',
                worktree=True,
                assignee='test-agent',
                spaceRef='test-space'
            )
        )
        
        # Mock TaskManager
        with patch('haconiwa.task.manager.TaskManager') as mock_tm_class:
            mock_tm_instance = MagicMock()
            mock_tm_class.return_value = mock_tm_instance
            mock_tm_instance.create_task.return_value = True
            
            # Apply the task CRD
            result = applier._apply_task_crd(task_crd)
            
            # Check that create_task was called
            self.assertTrue(mock_tm_instance.create_task.called)
            
            # Get the config passed to create_task
            call_args = mock_tm_instance.create_task.call_args
            task_config = call_args[0][0]
            
            # Verify env_files were included
            self.assertIn('env_files', task_config)
            self.assertEqual(task_config['env_files'], ['.env.base', '.env.local'])
            
    def test_task_spec_env_files_override_applier(self):
        """Test that TaskSpec.envFiles take precedence over applier.env_files"""
        # Create applier with env files
        applier = CRDApplier()
        applier.env_files = ['.env.base']
        
        # Create a TaskCRD with its own envFiles
        task_crd = TaskCRD(
            apiVersion='haconiwa.dev/v1',
            kind='Task',
            metadata=Metadata(name='test-task'),
            spec=TaskSpec(
                branch='feature/test',
                worktree=True,
                assignee='test-agent',
                spaceRef='test-space',
                envFiles=['.env.task', '.env.override']
            )
        )
        
        # Mock TaskManager
        with patch('haconiwa.task.manager.TaskManager') as mock_tm_class:
            mock_tm_instance = MagicMock()
            mock_tm_class.return_value = mock_tm_instance
            mock_tm_instance.create_task.return_value = True
            
            # Apply the task CRD
            result = applier._apply_task_crd(task_crd)
            
            # Get the config passed to create_task
            call_args = mock_tm_instance.create_task.call_args
            task_config = call_args[0][0]
            
            # Verify combined env_files (task files first, then applier files)
            self.assertIn('env_files', task_config)
            self.assertEqual(task_config['env_files'], ['.env.task', '.env.override', '.env.base'])
            
    def test_no_env_files_specified(self):
        """Test that no env_files key is added when none are specified"""
        # Create applier without env files
        applier = CRDApplier()
        
        # Create a TaskCRD without envFiles
        task_crd = TaskCRD(
            apiVersion='haconiwa.dev/v1',
            kind='Task',
            metadata=Metadata(name='test-task'),
            spec=TaskSpec(
                branch='feature/test',
                worktree=True,
                assignee='test-agent',
                spaceRef='test-space'
            )
        )
        
        # Mock TaskManager
        with patch('haconiwa.task.manager.TaskManager') as mock_tm_class:
            mock_tm_instance = MagicMock()
            mock_tm_class.return_value = mock_tm_instance
            mock_tm_instance.create_task.return_value = True
            
            # Apply the task CRD
            result = applier._apply_task_crd(task_crd)
            
            # Get the config passed to create_task
            call_args = mock_tm_instance.create_task.call_args
            task_config = call_args[0][0]
            
            # Verify no env_files key was added
            self.assertNotIn('env_files', task_config)


if __name__ == '__main__':
    unittest.main()