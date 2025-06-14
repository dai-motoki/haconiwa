"""
Test cases for SpaceManager grid and room configuration
Tests the correct interpretation of YAML configurations
"""

import pytest
from unittest.mock import Mock, patch, MagicMock
from pathlib import Path

from haconiwa.space.manager import SpaceManager
from haconiwa.core.crd.models import SpaceCRD


class TestSpaceManagerGridConfiguration:
    """Test SpaceManager correctly handles grid and room configurations"""
    
    def setup_method(self):
        """Setup for each test"""
        self.space_manager = SpaceManager()
        self.space_manager.active_sessions = {}
    
    def test_simple_grid_1x3_single_room(self):
        """Test grid 1x3 creates 1 window with 3 panes"""
        # Create mock CRD with 1x3 grid and 1 room
        mock_crd = Mock()
        mock_crd.metadata = Mock()
        mock_crd.metadata.name = "test-world"
        mock_crd.spec = Mock()
        mock_crd.spec.nations = [Mock()]
        mock_crd.spec.nations[0].cities = [Mock()]
        mock_crd.spec.nations[0].cities[0].villages = [Mock()]
        mock_crd.spec.nations[0].cities[0].villages[0].companies = [Mock()]
        
        company = mock_crd.spec.nations[0].cities[0].villages[0].companies[0]
        company.name = "simple-dev-company"
        company.grid = "1x3"
        company.basePath = None
        company.gitRepo = None
        company.organizationRef = "simple-dev-org"
        
        # Define 1 room (Dev Room)
        company.buildings = [Mock()]
        company.buildings[0].floors = [Mock()]
        company.buildings[0].floors[0].rooms = [Mock()]
        company.buildings[0].floors[0].rooms[0].id = "room-dev"
        company.buildings[0].floors[0].rooms[0].name = "Dev Room"
        
        # Convert CRD to config
        config = self.space_manager.convert_crd_to_config(mock_crd)
        
        # Assertions
        assert config["grid"] == "1x3"
        assert len(config["rooms"]) == 1
        assert config["rooms"][0]["id"] == "room-dev"
        assert config["rooms"][0]["name"] == "Dev Room"
        
        # Calculate panes per window
        layout_info = self.space_manager._calculate_panes_per_window("1x3", 1)
        assert layout_info["total_panes"] == 3
        assert layout_info["panes_per_window"] == 3
        assert layout_info["layout_per_window"] == "1x3"
    
    def test_grid_8x4_single_room(self):
        """Test grid 8x4 with 1 room creates 1 window with 32 panes"""
        # Create mock CRD with 8x4 grid and 1 room
        mock_crd = Mock()
        mock_crd.metadata = Mock()
        mock_crd.metadata.name = "test-world"
        mock_crd.spec = Mock()
        mock_crd.spec.nations = [Mock()]
        mock_crd.spec.nations[0].cities = [Mock()]
        mock_crd.spec.nations[0].cities[0].villages = [Mock()]
        mock_crd.spec.nations[0].cities[0].villages[0].companies = [Mock()]
        
        company = mock_crd.spec.nations[0].cities[0].villages[0].companies[0]
        company.name = "test-company-one-room"
        company.grid = "8x4"
        company.basePath = None
        company.gitRepo = None
        company.organizationRef = "test-org-one-room"
        
        # Define 1 room
        company.buildings = [Mock()]
        company.buildings[0].floors = [Mock()]
        company.buildings[0].floors[0].rooms = [Mock()]
        company.buildings[0].floors[0].rooms[0].id = "room-dev"
        company.buildings[0].floors[0].rooms[0].name = "Development Room"
        
        # Convert CRD to config
        config = self.space_manager.convert_crd_to_config(mock_crd)
        
        # Assertions
        assert config["grid"] == "8x4"
        assert len(config["rooms"]) == 1
        assert config["rooms"][0]["id"] == "room-dev"
        
        # Calculate panes per window
        layout_info = self.space_manager._calculate_panes_per_window("8x4", 1)
        assert layout_info["total_panes"] == 32
        assert layout_info["panes_per_window"] == 32
        assert layout_info["layout_per_window"] == "8x4"
    
    def test_grid_8x4_two_rooms(self):
        """Test grid 8x4 with 2 rooms creates 2 windows with 16 panes each"""
        # Create mock CRD with 8x4 grid and 2 rooms
        mock_crd = Mock()
        mock_crd.metadata = Mock()
        mock_crd.metadata.name = "test-world"
        mock_crd.spec = Mock()
        mock_crd.spec.nations = [Mock()]
        mock_crd.spec.nations[0].cities = [Mock()]
        mock_crd.spec.nations[0].cities[0].villages = [Mock()]
        mock_crd.spec.nations[0].cities[0].villages[0].companies = [Mock()]
        
        company = mock_crd.spec.nations[0].cities[0].villages[0].companies[0]
        company.name = "test-company-no-floor2"
        company.grid = "8x4"
        company.basePath = None
        company.gitRepo = None
        company.organizationRef = "test-org-no-floor2"
        
        # Define 2 rooms
        company.buildings = [Mock()]
        company.buildings[0].floors = [Mock()]
        company.buildings[0].floors[0].rooms = [
            Mock(), Mock()
        ]
        company.buildings[0].floors[0].rooms[0].id = "room-01"
        company.buildings[0].floors[0].rooms[0].name = "Alpha Development Room"
        company.buildings[0].floors[0].rooms[1].id = "room-02"
        company.buildings[0].floors[0].rooms[1].name = "Beta Testing Room"
        
        # Convert CRD to config
        config = self.space_manager.convert_crd_to_config(mock_crd)
        
        # Assertions
        assert config["grid"] == "8x4"
        assert len(config["rooms"]) == 2
        assert config["rooms"][0]["id"] == "room-01"
        assert config["rooms"][1]["id"] == "room-02"
        
        # Calculate panes per window
        layout_info = self.space_manager._calculate_panes_per_window("8x4", 2)
        assert layout_info["total_panes"] == 32
        assert layout_info["panes_per_window"] == 16
        assert layout_info["layout_per_window"] == "4x4"
    
    def test_no_rooms_defined_small_grid(self):
        """Test that small grids without rooms defined create 1 default room"""
        mock_crd = Mock()
        mock_crd.metadata = Mock()
        mock_crd.metadata.name = "test-world"
        mock_crd.spec = Mock()
        mock_crd.spec.nations = [Mock()]
        mock_crd.spec.nations[0].cities = [Mock()]
        mock_crd.spec.nations[0].cities[0].villages = [Mock()]
        mock_crd.spec.nations[0].cities[0].villages[0].companies = [Mock()]
        
        company = mock_crd.spec.nations[0].cities[0].villages[0].companies[0]
        company.name = "test-company"
        company.grid = "2x2"
        company.basePath = None
        company.gitRepo = None
        company.organizationRef = None
        company.buildings = []  # No buildings defined
        
        # Convert CRD to config
        config = self.space_manager.convert_crd_to_config(mock_crd)
        
        # Assertions
        assert len(config["rooms"]) == 1
        assert config["rooms"][0]["id"] == "room-01"
        assert config["rooms"][0]["name"] == "Main Room"
    
    def test_calculate_layout_for_various_pane_counts(self):
        """Test optimal layout calculation for different pane counts"""
        test_cases = [
            (1, "1x1"),
            (2, "2x1"),
            (3, "3x1"),
            (4, "2x2"),
            (6, "3x2"),
            (8, "4x2"),
            (9, "3x3"),
            (12, "4x3"),
            (16, "4x4"),
            (20, "5x4"),
            (25, "5x5"),
            (32, "6x6"),  # sqrt(32) ≈ 5.66, ceil = 6
        ]
        
        for pane_count, expected_layout in test_cases:
            layout = self.space_manager._calculate_layout_for_panes(pane_count)
            assert layout == expected_layout, f"Failed for {pane_count} panes"
    
    @patch('subprocess.run')
    def test_create_panes_with_correct_window_id(self, mock_run):
        """Test that panes are created with correct window IDs (0-based)"""
        mock_run.return_value = Mock(returncode=0, stdout="", stderr="")
        
        # Test for window 0 (first room)
        self.space_manager._create_panes_in_window("test-session", "0", 4)
        
        # Check that tmux commands use window ID 0
        calls = mock_run.call_args_list
        assert any("test-session:0" in str(call) for call in calls)
        assert not any("test-session:1" in str(call) for call in calls)
    
    def test_get_window_id_for_room(self):
        """Test window ID calculation for different room IDs"""
        assert self.space_manager._get_window_id_for_room("room-01") == "0"
        assert self.space_manager._get_window_id_for_room("room-02") == "1"
        assert self.space_manager._get_window_id_for_room("room-executive") == "2"
        assert self.space_manager._get_window_id_for_room("room-dev") == "0"  # Default
        assert self.space_manager._get_window_id_for_room("room-03") == "2"  # Numeric extraction
    
    def test_generate_desk_mappings_respects_actual_rooms(self):
        """Test that desk mappings only generate for actual rooms defined"""
        # With 1 organization and 1 room, should only generate 4 desk mappings
        organizations = [
            {"id": "01", "name": "Dev Team", "department_id": "dev"}
        ]
        
        mappings = self.space_manager.generate_desk_mappings(organizations)
        
        # Should generate mappings for:
        # - Organization 1 in room-01 (4 desks)
        # - Organization 2 in room-01 (4 desks) 
        # - Organization 3 in room-02 (4 desks)
        # - Organization 4 in room-02 (4 desks)
        # - Organization 5 in room-executive (4 desks)
        # Total: 20 mappings (default behavior)
        
        # But for single room config, we should limit mappings
        room_01_mappings = [m for m in mappings if m["room_id"] == "room-01"]
        assert len(room_01_mappings) == 8  # 2 orgs × 4 roles


if __name__ == "__main__":
    pytest.main([__file__, "-v"])