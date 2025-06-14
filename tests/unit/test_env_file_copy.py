"""
Unit tests for .env file auto-copy functionality
"""
import unittest
from unittest.mock import patch, MagicMock, mock_open
from pathlib import Path
import tempfile
import shutil
import os

from haconiwa.task.manager import TaskManager
from haconiwa.core.applier import CRDApplier


class TestEnvFileCopy(unittest.TestCase):
    """Test .env file auto-copy functionality"""
    
    def setUp(self):
        self.temp_dir = tempfile.mkdtemp()
        self.task_manager = TaskManager()
        self.applier = CRDApplier()
        
    def tearDown(self):
        shutil.rmtree(self.temp_dir, ignore_errors=True)
        
    def test_env_files_attribute_in_applier(self):
        """Test that CRDApplier has env_files attribute"""
        self.assertTrue(hasattr(self.applier, 'env_files'))
        self.assertEqual(self.applier.env_files, [])
        
        # Test setting env files
        self.applier.env_files = ['.env.base', '.env.local']
        self.assertEqual(self.applier.env_files, ['.env.base', '.env.local'])
        
    def test_copy_env_files_to_worktree_no_env_files(self):
        """Test _copy_env_files_to_worktree when no env files are specified"""
        worktree_path = Path(self.temp_dir) / "test_worktree"
        worktree_path.mkdir(parents=True)
        
        # No env files specified
        self.task_manager._copy_env_files_to_worktree(worktree_path, [])
            
        # No .env file should be created
        env_file = worktree_path / '.env'
        self.assertFalse(env_file.exists())
        
    def test_copy_single_env_file(self):
        """Test copying a single .env file"""
        worktree_path = Path(self.temp_dir) / "test_worktree"
        worktree_path.mkdir(parents=True)
        
        # Create test .env file
        env_content = """API_KEY=test123
LOG_LEVEL=DEBUG
DATABASE_URL=postgresql://localhost/test"""
        
        env_file_path = Path(self.temp_dir) / ".env.test"
        env_file_path.write_text(env_content)
        
        # Call with env files
        self.task_manager._copy_env_files_to_worktree(worktree_path, [str(env_file_path)])
            
        # Check .env file was created
        target_env = worktree_path / '.env'
        self.assertTrue(target_env.exists())
        
        # Check content
        content = target_env.read_text()
        self.assertIn("API_KEY=test123", content)
        self.assertIn("LOG_LEVEL=DEBUG", content)
        self.assertIn("DATABASE_URL=postgresql://localhost/test", content)
        
    def test_merge_multiple_env_files(self):
        """Test merging multiple .env files with override behavior"""
        worktree_path = Path(self.temp_dir) / "test_worktree"
        worktree_path.mkdir(parents=True)
        
        # Create test .env files
        env_base = Path(self.temp_dir) / ".env.base"
        env_base.write_text("""API_KEY=base_key
LOG_LEVEL=INFO
APP_NAME="Base App"
""")
        
        env_local = Path(self.temp_dir) / ".env.local"
        env_local.write_text("""LOG_LEVEL=DEBUG
DATABASE_URL=postgresql://localhost/dev
API_KEY=local_key
""")
        
        # Call with env files
        self.task_manager._copy_env_files_to_worktree(worktree_path, [str(env_base), str(env_local)])
            
        # Check merged content
        target_env = worktree_path / '.env'
        content = target_env.read_text()
        
        # Local should override base
        self.assertIn("API_KEY=local_key", content)
        self.assertIn("LOG_LEVEL=DEBUG", content)
        self.assertIn("APP_NAME=\"Base App\"", content)
        self.assertIn("DATABASE_URL=postgresql://localhost/dev", content)
        
    def test_env_file_with_comments_and_empty_lines(self):
        """Test handling of comments and empty lines in .env files"""
        worktree_path = Path(self.temp_dir) / "test_worktree"
        worktree_path.mkdir(parents=True)
        
        env_file = Path(self.temp_dir) / ".env"
        env_file.write_text("""# This is a comment
API_KEY=test123

# Another comment
LOG_LEVEL=DEBUG
  
# Empty lines above and below

DATABASE_URL=postgresql://localhost/test
""")
        
        # Call with env files
        self.task_manager._copy_env_files_to_worktree(worktree_path, [str(env_file)])
            
        target_env = worktree_path / '.env'
        content = target_env.read_text()
        
        # Comments and empty lines should be ignored
        self.assertIn("API_KEY=test123", content)
        self.assertIn("LOG_LEVEL=DEBUG", content)
        self.assertIn("DATABASE_URL=postgresql://localhost/test", content)
        self.assertNotIn("# This is a comment", content)
        
    def test_quote_handling(self):
        """Test proper handling of quoted values"""
        worktree_path = Path(self.temp_dir) / "test_worktree"
        worktree_path.mkdir(parents=True)
        
        env_file = Path(self.temp_dir) / ".env"
        env_file.write_text("""QUOTED_DOUBLE="value with spaces"
QUOTED_SINGLE='another value'
UNQUOTED=simple_value
SPACE_VALUE=needs quotes here
""")
        
        # Call with env files
        self.task_manager._copy_env_files_to_worktree(worktree_path, [str(env_file)])
            
        target_env = worktree_path / '.env'
        content = target_env.read_text()
        
        # Check quote handling
        self.assertIn('QUOTED_DOUBLE="value with spaces"', content)
        self.assertIn('QUOTED_SINGLE="another value"', content)  # Converted to double quotes
        self.assertIn("UNQUOTED=simple_value", content)
        self.assertIn('SPACE_VALUE="needs quotes here"', content)  # Auto-quoted
        
    def test_gitignore_creation(self):
        """Test .gitignore is created with .env exclusions"""
        worktree_path = Path(self.temp_dir) / "test_worktree"
        worktree_path.mkdir(parents=True)
        
        env_file = Path(self.temp_dir) / ".env"
        env_file.write_text("TEST=value")
        
        # Call with env files
        self.task_manager._copy_env_files_to_worktree(worktree_path, [str(env_file)])
            
        gitignore = worktree_path / '.gitignore'
        self.assertTrue(gitignore.exists())
        
        content = gitignore.read_text()
        self.assertIn(".env", content)
        self.assertIn(".env.local", content)
        self.assertIn(".env.*.local", content)
        
    def test_gitignore_update_existing(self):
        """Test updating existing .gitignore file"""
        worktree_path = Path(self.temp_dir) / "test_worktree"
        worktree_path.mkdir(parents=True)
        
        # Create existing .gitignore
        gitignore = worktree_path / '.gitignore'
        gitignore.write_text("node_modules/\n*.log\n")
        
        env_file = Path(self.temp_dir) / ".env"
        env_file.write_text("TEST=value")
        
        # Call with env files
        self.task_manager._copy_env_files_to_worktree(worktree_path, [str(env_file)])
            
        content = gitignore.read_text()
        # Original content preserved
        self.assertIn("node_modules/", content)
        self.assertIn("*.log", content)
        # New content added
        self.assertIn(".env", content)
        self.assertIn(".env.local", content)
        
    def test_nonexistent_env_file(self):
        """Test handling of nonexistent env files"""
        worktree_path = Path(self.temp_dir) / "test_worktree"
        worktree_path.mkdir(parents=True)
        
        # Should not raise exception
        self.task_manager._copy_env_files_to_worktree(worktree_path, ["/nonexistent/.env"])
            
        # No .env file should be created
        env_file = worktree_path / '.env'
        self.assertFalse(env_file.exists())


if __name__ == '__main__':
    unittest.main()