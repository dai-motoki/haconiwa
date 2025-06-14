"""
Unit tests for room-window mapping functionality
Tests that hardcoded mappings are removed and dynamic mapping works correctly
"""

import unittest
from unittest.mock import Mock, patch, MagicMock
import json
import tempfile
from pathlib import Path

from haconiwa.space.manager import SpaceManager


class TestRoomWindowMapping(unittest.TestCase):
    """Test room-window mapping without hardcoding"""
    
    def setUp(self):
        """Set up test fixtures"""
        # Reset singleton instance
        SpaceManager._instance = None
        SpaceManager._initialized = False
        
        self.config = Mock()
        self.config.base_path = Path(tempfile.mkdtemp())
        self.space_manager = SpaceManager()
        self.space_manager.config = self.config
        
        # Create .haconiwa directory
        self.haconiwa_dir = self.config.base_path / ".haconiwa"
        self.haconiwa_dir.mkdir(exist_ok=True)
        
    def tearDown(self):
        """Clean up test fixtures"""
        import shutil
        if self.config.base_path.exists():
            shutil.rmtree(self.config.base_path)
    
    def test_no_hardcoded_room_names(self):
        """Test that hardcoded room names are not present in the code"""
        # Read the source file
        import inspect
        source_file = inspect.getfile(SpaceManager)
        with open(source_file, 'r') as f:
            source_code = f.read()
        
        # Check that hardcoded room names are not in the fallback logic
        hardcoded_patterns = [
            'room_id == "room-01"',
            'room_id == "room-02"',
            'room_id == "room-executive"',
            'room_id == "room-standby"'
        ]
        
        for pattern in hardcoded_patterns:
            self.assertNotIn(pattern, source_code, 
                f"Found hardcoded pattern '{pattern}' in source code. Hardcoding should be removed.")
    
    def test_room_window_mapping_saved_on_creation(self):
        """Test that room-window mapping is saved when windows are created"""
        session_name = "test-session"
        rooms = [
            {"name": "Alpha Room", "id": "room-alpha"},
            {"name": "Beta Room", "id": "room-beta"},
            {"name": "Gamma Room", "id": "room-gamma"}
        ]
        
        with patch('subprocess.run') as mock_run:
            mock_run.return_value.returncode = 0
            result = self.space_manager._create_windows_for_rooms(session_name, rooms)
        
        self.assertTrue(result)
        
        # Check that mapping file was created
        mapping_file = self.haconiwa_dir / "room_window_mapping.json"
        self.assertTrue(mapping_file.exists())
        
        # Verify mapping content
        with open(mapping_file, 'r') as f:
            mappings = json.load(f)
        
        expected_mapping = {
            "room-alpha": 0,
            "room-beta": 1,
            "room-gamma": 2
        }
        
        self.assertEqual(mappings[session_name], expected_mapping)
    
    def test_load_room_window_mapping(self):
        """Test loading room-window mapping from file"""
        session_name = "test-session"
        test_mapping = {
            "room-frontend": 0,
            "room-backend": 1,
            "room-database": 2
        }
        
        # Create mapping file
        mapping_file = self.haconiwa_dir / "room_window_mapping.json"
        with open(mapping_file, 'w') as f:
            json.dump({session_name: test_mapping}, f)
        
        # Test loading
        loaded_mapping = self.space_manager._load_room_window_mapping(session_name)
        self.assertEqual(loaded_mapping, test_mapping)
    
    def test_get_window_id_uses_saved_mapping(self):
        """Test that _get_window_id_for_room uses saved mapping instead of hardcoding"""
        session_name = "test-session"
        test_mapping = {
            "room-executive": 2,  # Not hardcoded to 0
            "room-standby": 3,    # Not hardcoded to 1
            "room-01": 5,         # Not hardcoded to 0
            "room-02": 4          # Not hardcoded to 1
        }
        
        # Create mapping file
        mapping_file = self.haconiwa_dir / "room_window_mapping.json"
        with open(mapping_file, 'w') as f:
            json.dump({session_name: test_mapping}, f)
        
        # Mock active_sessions to include session name
        self.space_manager.active_sessions = {session_name: {}}
        
        # Test each room
        for room_id, expected_window in test_mapping.items():
            window_id = self.space_manager._get_window_id_for_room(room_id)
            self.assertEqual(window_id, str(expected_window),
                f"Room {room_id} should map to window {expected_window}, not {window_id}")
    
    def test_fallback_without_hardcoding(self):
        """Test fallback behavior when no mapping exists (should not use hardcoded values)"""
        # No active sessions, no saved mapping
        self.space_manager.active_sessions = {}
        
        # Test rooms that were previously hardcoded
        test_cases = [
            ("room-executive", "0"),  # Should default to 0, not hardcoded
            ("room-standby", "0"),    # Should default to 0, not hardcoded
            ("room-01", "0"),         # Should default to 0, not hardcoded
            ("room-02", "0"),         # Should default to 0, not hardcoded
            ("room-unknown", "0")     # Should default to 0
        ]
        
        for room_id, expected in test_cases:
            with self.subTest(room_id=room_id):
                window_id = self.space_manager._get_window_id_for_room(room_id)
                self.assertEqual(window_id, expected,
                    f"Room {room_id} should default to window 0 without hardcoding")
    
    def test_dynamic_room_assignment(self):
        """Test that rooms are dynamically assigned based on their order in YAML"""
        session_name = "dynamic-test"
        
        # Simulate different room orders
        room_sets = [
            # Set 1: Executive room is third
            [
                {"name": "Development Room", "id": "room-dev"},
                {"name": "Marketing Room", "id": "room-marketing"},
                {"name": "Executive Room", "id": "room-executive"},
                {"name": "Standby Room", "id": "room-standby"}
            ],
            # Set 2: Different order
            [
                {"name": "Standby Room", "id": "room-standby"},
                {"name": "Executive Room", "id": "room-executive"},
                {"name": "Room 01", "id": "room-01"},
                {"name": "Room 02", "id": "room-02"}
            ]
        ]
        
        for i, rooms in enumerate(room_sets):
            with self.subTest(room_set=i):
                with patch('subprocess.run') as mock_run:
                    mock_run.return_value.returncode = 0
                    result = self.space_manager._create_windows_for_rooms(f"{session_name}-{i}", rooms)
                
                self.assertTrue(result)
                
                # Verify the mapping reflects the actual order
                mapping_file = self.haconiwa_dir / "room_window_mapping.json"
                with open(mapping_file, 'r') as f:
                    mappings = json.load(f)
                
                session_mapping = mappings[f"{session_name}-{i}"]
                
                # Check that each room is mapped to its index position
                for idx, room in enumerate(rooms):
                    room_id = room["id"]
                    self.assertEqual(session_mapping[room_id], idx,
                        f"Room {room_id} should be mapped to window {idx} based on its position")


if __name__ == '__main__':
    unittest.main()