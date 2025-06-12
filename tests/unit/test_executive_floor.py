"""
TDD テスト: Executive Room 2階配置とTask Assignments修正
"""

import pytest
import unittest
from unittest.mock import Mock, patch
from pathlib import Path
import json


class TestExecutiveFloor(unittest.TestCase):
    """Executive Room 2階配置のテスト"""
    
    def setUp(self):
        """テストセットアップ"""
        from src.haconiwa.space.manager import SpaceManager
        from src.haconiwa.core.crd.models import SpaceCRD
        
        self.space_manager = SpaceManager()
        
        # Mock organization data with 5 departments including executive
        self.mock_organizations = [
            {"id": "01", "name": "Frontend Development Team", "department_id": "frontend"},
            {"id": "02", "name": "Backend Development Team", "department_id": "backend"},
            {"id": "03", "name": "DevOps Infrastructure Team", "department_id": "devops"},
            {"id": "04", "name": "Quality Assurance Team", "department_id": "qa"},
            {"id": "05", "name": "Executive Leadership", "department_id": "executive"}
        ]
        
        # Mock task assignments
        self.mock_task_assignments = {
            "org01-pm-r1": {"task_name": "frontend-ui-design", "room": "r1", "status": "active"},
            "org02-pm-r1": {"task_name": "backend-api-development", "room": "r1", "status": "active"},
            "org03-pm-r1": {"task_name": "database-schema-design", "room": "r1", "status": "active"},
            "org04-pm-r1": {"task_name": "devops-ci-cd-pipeline", "room": "r1", "status": "active"},
            "org05-ceo-re": {"task_name": "executive-dashboard", "room": "re", "status": "active"},
            "org05-cto-re": {"task_name": "business-intelligence", "room": "re", "status": "active"},
            "org05-coo-re": {"task_name": "operations-automation", "room": "re", "status": "active"},
        }
    
    def test_generate_desk_mappings_includes_executive_room(self):
        """Executive Room（room-executive）のデスクマッピングが生成されることをテスト"""
        mappings = self.space_manager.generate_desk_mappings(self.mock_organizations)
        
        # Executive Room マッピングの存在確認
        executive_mappings = [m for m in mappings if m["room_id"] == "room-executive"]
        self.assertEqual(len(executive_mappings), 4, "Executive Roomには4つのデスクが必要")
        
        # Executive 役職の確認
        exec_roles = [m["role"] for m in executive_mappings]
        expected_roles = ["ceo", "cto", "coo", "assistant"]
        for role in expected_roles:
            self.assertIn(role, exec_roles, f"Executive Room に {role} 役職が必要")
    
    def test_window_id_mapping_for_executive_room(self):
        """Executive Room が window 2 にマッピングされることをテスト"""
        window_id = self.space_manager._get_window_id_for_room("room-executive")
        self.assertEqual(window_id, "2", "Executive Room は window 2 にマッピングされる必要がある")
    
    def test_calculate_panes_per_window_for_executive_layout(self):
        """Executive Room の1x4レイアウト（4ペーン）が計算されることをテスト"""
        layout_info = self.space_manager._calculate_panes_per_window("8x4", 3)
        
        self.assertIn("panes_per_window", layout_info)
        panes_per_window = layout_info["panes_per_window"]
        
        if isinstance(panes_per_window, dict):
            self.assertEqual(panes_per_window.get("room-executive"), 4, 
                           "Executive Room は 4ペーンである必要がある")
    
    def test_executive_floor_hierarchy_display(self):
        """Executive Room が Floor 2 として表示されることをテスト"""
        # モックデータでツリー生成をテスト
        mock_base_path = Path("./test-world")
        
        with patch.object(self.space_manager, '_get_organization_data', return_value=self.mock_organizations):
            with patch.object(self.space_manager, '_get_current_task_assignments', return_value=self.mock_task_assignments):
                tree = self.space_manager._create_world_hierarchy_tree(
                    mock_base_path, self.mock_organizations, self.mock_task_assignments
                )
                
                # ツリー文字列を取得
                from io import StringIO
                from rich.console import Console
                
                console = Console(file=StringIO(), width=120)
                console.print(tree)
                tree_output = console.file.getvalue()
                
                # Floor 2 の存在確認
                self.assertIn("Floor 2", tree_output, "Executive Room は Floor 2 に表示される必要がある")
                self.assertIn("Executive Room", tree_output, "Executive Room が表示される必要がある")


class TestTaskAssignments(unittest.TestCase):
    """Task Assignments テーブルの修正テスト"""
    
    def setUp(self):
        """テストセットアップ"""
        from src.haconiwa.space.manager import SpaceManager
        
        self.space_manager = SpaceManager()
        
        # Mock task assignments with actual tasks
        self.mock_task_assignments = {
            "org01-pm-r1": {"task_name": "frontend-ui-design", "room": "r1", "status": "active"},
            "org02-pm-r1": {"task_name": "backend-api-development", "room": "r1", "status": "active"},
            "org03-pm-r1": {"task_name": "database-schema-design", "room": "r1", "status": "active"},
            "org04-pm-r1": {"task_name": "devops-ci-cd-pipeline", "room": "r1", "status": "active"},
            "org05-ceo-re": {"task_name": "executive-dashboard", "room": "re", "status": "active"},
            "org05-cto-re": {"task_name": "business-intelligence", "room": "re", "status": "active"},
            "org05-coo-re": {"task_name": "operations-automation", "room": "re", "status": "active"},
        }
        
        self.space_manager.set_task_assignments(self.mock_task_assignments)
    
    def test_task_assignment_table_shows_actual_tasks(self):
        """Task Assignmentsテーブルで実際のタスクが表示されることをテスト"""
        table = self.space_manager._create_task_assignment_table(self.mock_task_assignments)
        
        # テーブル内容を文字列として取得
        from io import StringIO
        from rich.console import Console
        
        console = Console(file=StringIO(), width=120)
        console.print(table)
        table_output = console.file.getvalue()
        
        # 実際のタスク名が表示されることを確認
        self.assertIn("frontend-ui-design", table_output, "フロントエンドタスクが表示される必要がある")
        self.assertIn("executive-dashboard", table_output, "Executiveタスクが表示される必要がある")
        self.assertIn("business-intelligence", table_output, "CTOタスクが表示される必要がある")
        
        # standby の数が減っていることを確認
        standby_count = table_output.count("standby")
        total_rows = table_output.count("org0")  # エージェント行数の概算
        
        self.assertLess(standby_count, total_rows, "standby状態のエージェントが減っている必要がある")
    
    def test_task_assignment_table_column_order(self):
        """Task Assignmentsテーブルの列順序がTask, Room, Role, Agentであることをテスト"""
        table = self.space_manager._create_task_assignment_table(self.mock_task_assignments)
        
        # テーブルヘッダーの順序確認
        from io import StringIO
        from rich.console import Console
        
        console = Console(file=StringIO(), width=120)
        console.print(table)
        table_output = console.file.getvalue()
        
        # ヘッダー行を探してカラム順序を確認
        lines = table_output.split('\n')
        header_line = None
        for line in lines:
            if 'Task' in line and 'Room' in line and 'Role' in line and 'Agent' in line:
                header_line = line
                break
        
        self.assertIsNotNone(header_line, "テーブルヘッダーが見つからない")
        
        # Task が最初の列であることを確認
        task_pos = header_line.find('Task')
        room_pos = header_line.find('Room')
        role_pos = header_line.find('Role')
        agent_pos = header_line.find('Agent')
        
        self.assertLess(task_pos, room_pos, "Task列がRoom列より前にある必要がある")
        self.assertLess(room_pos, role_pos, "Room列がRole列より前にある必要がある")
        self.assertLess(role_pos, agent_pos, "Role列がAgent列より前にある必要がある")
    
    def test_get_task_by_assignee_returns_correct_task(self):
        """assigneeによるタスク取得が正しく動作することをテスト"""
        # タスク割り当てを設定
        self.space_manager.set_task_assignments(self.mock_task_assignments)
        
        # CEO のタスクを取得
        ceo_task = self.space_manager.get_task_by_assignee("org05-ceo-re")
        self.assertIsNotNone(ceo_task, "CEO にタスクが割り当てられている必要がある")
        self.assertEqual(ceo_task["task_name"], "executive-dashboard", "CEO に正しいタスクが割り当てられている必要がある")
        
        # 存在しないエージェントの場合
        nonexistent_task = self.space_manager.get_task_by_assignee("nonexistent-agent")
        self.assertIsNone(nonexistent_task, "存在しないエージェントにはタスクがない")


class TestSpaceManagerFloorIntegration(unittest.TestCase):
    """SpaceManager の Floor 統合テスト"""
    
    def setUp(self):
        """テストセットアップ"""
        from src.haconiwa.space.manager import SpaceManager
        
        self.space_manager = SpaceManager()
    
    def test_create_panes_in_window_executive_layout(self):
        """Executive Room の1x4レイアウトでペインが作成されることをテスト"""
        # Executive Room (window 2) で4ペーンの作成をテスト
        session_name = "test-session"
        window_id = "2"
        pane_count = 4
        
        # tmux コマンドをモック
        with patch('subprocess.run') as mock_run:
            mock_run.return_value.returncode = 0
            
            result = self.space_manager._create_panes_in_window(session_name, window_id, pane_count)
            
            self.assertTrue(result, "Executive Room のペイン作成が成功する必要がある")
            
            # 1x4レイアウト用のコマンドが実行されることを確認
            call_args_list = [call.args[0] for call in mock_run.call_args_list]
            
            # split-window コマンドが適切に呼ばれることを確認
            split_commands = [cmd for cmd in call_args_list if cmd[1] == "split-window"]
            self.assertGreater(len(split_commands), 0, "split-window コマンドが実行される必要がある")


if __name__ == '__main__':
    unittest.main() 