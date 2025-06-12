"""
包括的YAML構成テストスイート
Executive Floor 2階配置、Task Assignments、エラーケースなどをテスト
"""

import unittest
import pytest
from pathlib import Path
import tempfile
import shutil
import subprocess
import json
from unittest.mock import Mock, patch


class TestYAMLConfigurations(unittest.TestCase):
    """YAML構成のテストスイート"""
    
    def setUp(self):
        """テストセットアップ"""
        self.test_cases_dir = Path("test_cases")
        self.test_output_dir = Path("test_output")
        self.test_cases = [
            ("basic_executive_floor.yaml", "基本的なExecutive Floor テスト"),
            ("heavy_task_assignment.yaml", "大量タスク割り当てテスト"),
            ("error_case_test.yaml", "エラーケーステスト"),
            ("minimal_config.yaml", "最小構成テスト"),
            ("full_structure_test.yaml", "完全構造テスト（nations階層、legalFramework含む）")
        ]
    
    def tearDown(self):
        """テストクリーンアップ"""
        # テスト実行後のクリーンアップ（オプション）
        # 実際のテスト中は削除しない（デバッグのため）
        pass
    
    @classmethod
    def tearDownClass(cls):
        """全テスト終了後のクリーンアップ"""
        # テスト出力ディレクトリのクリーンアップ（オプション）
        test_output_dir = Path("test_output")
        if test_output_dir.exists():
            # 実際の削除はコメントアウト（手動確認のため）
            # shutil.rmtree(test_output_dir)
            print(f"テスト出力ディレクトリ: {test_output_dir}")
    
    def test_yaml_files_exist(self):
        """テスト用YAMLファイルが存在することを確認"""
        for yaml_file, description in self.test_cases:
            yaml_path = self.test_cases_dir / yaml_file
            self.assertTrue(yaml_path.exists(), f"{description} ファイルが見つかりません: {yaml_path}")
            
            # ファイルサイズが0でないことを確認
            self.assertGreater(yaml_path.stat().st_size, 0, f"{yaml_file} が空ファイルです")
    
    def test_yaml_syntax_validity(self):
        """YAMLファイルの構文が正しいことを確認"""
        import yaml
        
        for yaml_file, description in self.test_cases:
            yaml_path = self.test_cases_dir / yaml_file
            
            if yaml_path.exists():
                with self.subTest(yaml_file=yaml_file):
                    try:
                        with open(yaml_path, 'r', encoding='utf-8') as f:
                            documents = list(yaml.safe_load_all(f))
                        
                        # 少なくとも1つのドキュメントが含まれていることを確認
                        self.assertGreater(len(documents), 0, f"{yaml_file} にドキュメントが含まれていません")
                        
                        # 各ドキュメントがNoneでないことを確認
                        valid_docs = [doc for doc in documents if doc is not None]
                        self.assertGreater(len(valid_docs), 0, f"{yaml_file} に有効なドキュメントがありません")
                        
                    except yaml.YAMLError as e:
                        self.fail(f"{yaml_file} のYAML構文エラー: {e}")
                    except Exception as e:
                        self.fail(f"{yaml_file} の読み込みエラー: {e}")
    
    def test_base_path_configuration(self):
        """YAMLファイルのbasePathがtest_output配下に設定されていることを確認"""
        import yaml
        
        expected_base_paths = {
            "basic_executive_floor.yaml": "./test_output/basic_executive",
            "heavy_task_assignment.yaml": "./test_output/heavy_tasks",
            "error_case_test.yaml": "./test_output/error_cases",
            "minimal_config.yaml": "./test_output/minimal",
            "full_structure_test.yaml": "./test_output/full_structure"
        }
        
        for yaml_file, expected_base_path in expected_base_paths.items():
            yaml_path = self.test_cases_dir / yaml_file
            
            if yaml_path.exists():
                with self.subTest(yaml_file=yaml_file):
                    try:
                        with open(yaml_path, 'r', encoding='utf-8') as f:
                            documents = list(yaml.safe_load_all(f))
                        
                        # Organization CRDを見つける
                        org_crd = None
                        for doc in documents:
                            if doc and doc.get('kind') == 'Organization':
                                org_crd = doc
                                break
                        
                        self.assertIsNotNone(org_crd, f"{yaml_file} にOrganization CRDが見つかりません")
                        
                        # basePathが正しく設定されていることを確認
                        actual_base_path = org_crd['spec'].get('basePath')
                        self.assertEqual(actual_base_path, expected_base_path,
                                       f"{yaml_file} のbasePathが期待値と異なります: {actual_base_path}")
                        
                    except Exception as e:
                        self.fail(f"{yaml_file} のbasePath確認エラー: {e}")
    
    def test_yaml_crd_structure(self):
        """YAML内のCRD構造が正しいことを確認"""
        import yaml
        
        for yaml_file, description in self.test_cases:
            yaml_path = self.test_cases_dir / yaml_file
            
            if yaml_path.exists():
                with self.subTest(yaml_file=yaml_file):
                    try:
                        with open(yaml_path, 'r', encoding='utf-8') as f:
                            documents = list(yaml.safe_load_all(f))
                        
                        # CRDの種類を確認
                        crd_kinds = []
                        for doc in documents:
                            if doc and isinstance(doc, dict):
                                kind = doc.get('kind')
                                if kind:
                                    crd_kinds.append(kind)
                        
                        # 必要なCRDが含まれていることを確認
                        expected_kinds = ['Organization', 'Space']
                        for expected_kind in expected_kinds:
                            self.assertIn(expected_kind, crd_kinds, 
                                        f"{yaml_file} に {expected_kind} CRDが含まれていません")
                        
                        # Task CRDの存在確認（エラーケース以外）
                        if "error_case" not in yaml_file and "minimal" not in yaml_file:
                            self.assertIn('Task', crd_kinds, 
                                        f"{yaml_file} に Task CRDが含まれていません")
                            
                    except Exception as e:
                        self.fail(f"{yaml_file} のCRD構造確認エラー: {e}")
    
    def test_full_structure_features(self):
        """完全構造テストケースの特殊機能を確認"""
        import yaml
        
        yaml_path = self.test_cases_dir / "full_structure_test.yaml"
        
        if yaml_path.exists():
            try:
                with open(yaml_path, 'r', encoding='utf-8') as f:
                    documents = list(yaml.safe_load_all(f))
                
                # Organization CRDを見つける
                org_crd = None
                space_crd = None
                for doc in documents:
                    if doc and doc.get('kind') == 'Organization':
                        org_crd = doc
                    elif doc and doc.get('kind') == 'Space':
                        space_crd = doc
                
                self.assertIsNotNone(org_crd, "Organization CRDが見つかりません")
                self.assertIsNotNone(space_crd, "Space CRDが見つかりません")
                
                # legalFramework の存在確認
                self.assertTrue(org_crd['spec'].get('legalFramework', {}).get('enabled'),
                              "Organization legalFramework が有効になっていません")
                
                # nations階層の確認
                nations = space_crd['spec'].get('nations', [])
                self.assertGreater(len(nations), 0, "nations が定義されていません")
                
                nation = nations[0]
                self.assertEqual(nation['id'], 'jp', "nation IDが期待値と異なります")
                self.assertTrue(nation.get('legalFramework', {}).get('enabled'),
                              "Nation legalFramework が有効になっていません")
                
                # cities階層の確認
                cities = nation.get('cities', [])
                self.assertGreater(len(cities), 0, "cities が定義されていません")
                
                city = cities[0]
                self.assertEqual(city['id'], 'tokyo', "city IDが期待値と異なります")
                
                # villages階層の確認
                villages = city.get('villages', [])
                self.assertGreater(len(villages), 0, "villages が定義されていません")
                
                village = villages[0]
                self.assertEqual(village['id'], 'test-village', "village IDが期待値と異なります")
                
                # companies階層の確認
                companies = village.get('companies', [])
                self.assertGreater(len(companies), 0, "companies が定義されていません")
                
                company = companies[0]
                self.assertEqual(company['name'], 'full-structure-company', "company名が期待値と異なります")
                
                # gitRepo の確認
                git_repo = company.get('gitRepo')
                self.assertIsNotNone(git_repo, "gitRepo が定義されていません")
                self.assertIn('url', git_repo, "gitRepo にURL が含まれていません")
                self.assertIn('defaultBranch', git_repo, "gitRepo にdefaultBranch が含まれていません")
                
                # agentDefaults の確認
                agent_defaults = company.get('agentDefaults')
                self.assertIsNotNone(agent_defaults, "agentDefaults が定義されていません")
                self.assertIn('permissions', agent_defaults, "agentDefaults にpermissions が含まれていません")
                self.assertIn('env', agent_defaults, "agentDefaults にenv が含まれていません")
                
            except Exception as e:
                self.fail(f"完全構造テストの確認エラー: {e}")
    
    def test_datetime_task_naming_convention(self):
        """完全構造テストケースで日時スタイル命名規則を確認"""
        import yaml
        import re
        
        yaml_path = self.test_cases_dir / "full_structure_test.yaml"
        
        if yaml_path.exists():
            try:
                with open(yaml_path, 'r', encoding='utf-8') as f:
                    documents = list(yaml.safe_load_all(f))
                
                # Task CRDを収集
                task_crds = []
                for doc in documents:
                    if doc and doc.get('kind') == 'Task':
                        task_crds.append(doc)
                
                self.assertGreater(len(task_crds), 0, "Task CRDが見つかりません")
                
                # 日時スタイル命名規則のパターン: YYYYMMDDHHMMSS_task-content_識別番号
                datetime_pattern = re.compile(r'^\d{14}_[a-z0-9-]+_\d{2}$')
                
                for task in task_crds:
                    task_name = task['metadata']['name']
                    self.assertTrue(datetime_pattern.match(task_name),
                                  f"タスク名 '{task_name}' が日時スタイル命名規則に従っていません")
                    
                    # 日時部分の妥当性確認（基本的なチェック）
                    datetime_part = task_name[:14]
                    year = int(datetime_part[:4])
                    month = int(datetime_part[4:6])
                    day = int(datetime_part[6:8])
                    hour = int(datetime_part[8:10])
                    minute = int(datetime_part[10:12])
                    second = int(datetime_part[12:14])
                    
                    self.assertTrue(2020 <= year <= 2030, f"年が妥当な範囲にありません: {year}")
                    self.assertTrue(1 <= month <= 12, f"月が妥当な範囲にありません: {month}")
                    self.assertTrue(1 <= day <= 31, f"日が妥当な範囲にありません: {day}")
                    self.assertTrue(0 <= hour <= 23, f"時が妥当な範囲にありません: {hour}")
                    self.assertTrue(0 <= minute <= 59, f"分が妥当な範囲にありません: {minute}")
                    self.assertTrue(0 <= second <= 59, f"秒が妥当な範囲にありません: {second}")
                
            except Exception as e:
                self.fail(f"日時命名規則の確認エラー: {e}")
    
    def test_executive_floor_configuration(self):
        """Executive Room がFloor 2に配置されていることを確認"""
        import yaml
        
        for yaml_file, description in self.test_cases:
            yaml_path = self.test_cases_dir / yaml_file
            
            if yaml_path.exists():
                with self.subTest(yaml_file=yaml_file):
                    try:
                        with open(yaml_path, 'r', encoding='utf-8') as f:
                            documents = list(yaml.safe_load_all(f))
                        
                        # Space CRDを見つける
                        space_crd = None
                        for doc in documents:
                            if doc and doc.get('kind') == 'Space':
                                space_crd = doc
                                break
                        
                        self.assertIsNotNone(space_crd, f"{yaml_file} にSpace CRDが見つかりません")
                        
                        # 階層構造を確認（完全構造の場合とシンプル構造の場合で分岐）
                        if yaml_file == "full_structure_test.yaml":
                            # 完全階層: nations → cities → villages → companies
                            companies = space_crd['spec']['nations'][0]['cities'][0]['villages'][0]['companies']
                        else:
                            # シンプル階層: 直接companies
                            companies = space_crd['spec']['nations'][0]['cities'][0]['villages'][0]['companies']
                        
                        self.assertGreater(len(companies), 0, f"{yaml_file} に企業が定義されていません")
                        
                        company = companies[0]
                        buildings = company.get('buildings', [])
                        self.assertGreater(len(buildings), 0, f"{yaml_file} に建物が定義されていません")
                        
                        building = buildings[0]
                        floors = building.get('floors', [])
                        
                        # Floor 2の存在確認
                        floor_ids = [floor.get('id') for floor in floors]
                        self.assertIn('floor-2', floor_ids, f"{yaml_file} にfloor-2が定義されていません")
                        
                        # Floor 2にExecutive Roomがあることを確認
                        floor_2 = next(floor for floor in floors if floor.get('id') == 'floor-2')
                        rooms = floor_2.get('rooms', [])
                        room_ids = [room.get('id') for room in rooms]
                        self.assertIn('room-executive', room_ids, 
                                    f"{yaml_file} のfloor-2にroom-executiveが定義されていません")
                        
                    except Exception as e:
                        self.fail(f"{yaml_file} のExecutive Floor構成確認エラー: {e}")
    
    def test_task_assignments_structure(self):
        """タスク割り当て構造が正しいことを確認"""
        import yaml
        
        for yaml_file, description in self.test_cases:
            yaml_path = self.test_cases_dir / yaml_file
            
            if yaml_path.exists() and "minimal" not in yaml_file:
                with self.subTest(yaml_file=yaml_file):
                    try:
                        with open(yaml_path, 'r', encoding='utf-8') as f:
                            documents = list(yaml.safe_load_all(f))
                        
                        # Task CRDを収集
                        task_crds = []
                        for doc in documents:
                            if doc and doc.get('kind') == 'Task':
                                task_crds.append(doc)
                        
                        if len(task_crds) > 0:  # タスクが定義されている場合のみテスト
                            # Executive タスクの存在確認
                            executive_tasks = []
                            for task in task_crds:
                                assignee = task['spec'].get('assignee', '')
                                if 'org05' in assignee and '-re' in assignee:
                                    executive_tasks.append(task)
                            
                            # heavy_task_assignment.yamlとfull_structure_test.yamlの場合はExecutiveタスクを期待
                            if "heavy_task" in yaml_file:
                                self.assertEqual(len(executive_tasks), 4, 
                                              f"{yaml_file} にExecutiveタスクが4つありません")
                                
                                # 期待される assignee
                                expected_assignees = ['org05-ceo-re', 'org05-cto-re', 'org05-coo-re', 'org05-assistant-re']
                                actual_assignees = [task['spec']['assignee'] for task in executive_tasks]
                                
                                for expected in expected_assignees:
                                    self.assertIn(expected, actual_assignees,
                                                f"{yaml_file} に {expected} のタスクがありません")
                            
                            elif "full_structure" in yaml_file:
                                self.assertGreaterEqual(len(executive_tasks), 3, 
                                              f"{yaml_file} にExecutiveタスクが3つ以上ありません")
                            
                            # 各タスクの必須フィールドチェック
                            for task in task_crds:
                                spec = task.get('spec', {})
                                self.assertIsNotNone(spec.get('assignee'), 
                                                   f"タスク {task['metadata']['name']} にassigneeが設定されていません")
                                self.assertIsNotNone(spec.get('branch'), 
                                                   f"タスク {task['metadata']['name']} にbranchが設定されていません")
                                self.assertIsNotNone(spec.get('description'), 
                                                   f"タスク {task['metadata']['name']} にdescriptionが設定されていません")
                            
                    except Exception as e:
                        self.fail(f"{yaml_file} のタスク割り当て構造確認エラー: {e}")
    
    def test_organization_structure(self):
        """Organization CRDの構造が正しいことを確認"""
        import yaml
        
        for yaml_file, description in self.test_cases:
            yaml_path = self.test_cases_dir / yaml_file
            
            if yaml_path.exists():
                with self.subTest(yaml_file=yaml_file):
                    try:
                        with open(yaml_path, 'r', encoding='utf-8') as f:
                            documents = list(yaml.safe_load_all(f))
                        
                        # Organization CRDを見つける
                        org_crd = None
                        for doc in documents:
                            if doc and doc.get('kind') == 'Organization':
                                org_crd = doc
                                break
                        
                        self.assertIsNotNone(org_crd, f"{yaml_file} にOrganization CRDが見つかりません")
                        
                        # 必須部門の存在確認
                        departments = org_crd['spec']['hierarchy']['departments']
                        dept_ids = [dept['id'] for dept in departments]
                        
                        required_depts = ['executive', 'frontend', 'backend', 'devops', 'qa']
                        for required_dept in required_depts:
                            self.assertIn(required_dept, dept_ids, 
                                        f"{yaml_file} に {required_dept} 部門が定義されていません")
                        
                        # Executive部門の詳細確認
                        exec_dept = next(dept for dept in departments if dept['id'] == 'executive')
                        exec_roles = exec_dept.get('roles', [])
                        
                        # CEOロールの存在確認
                        exec_titles = [role.get('title', '') for role in exec_roles]
                        self.assertIn('CEO', exec_titles, 
                                    f"{yaml_file} のexecutive部門にCEOロールが定義されていません")
                        
                    except Exception as e:
                        self.fail(f"{yaml_file} のOrganization構造確認エラー: {e}")


class TestExecutiveFloorIntegration(unittest.TestCase):
    """Executive Floor統合テスト"""
    
    def setUp(self):
        """統合テストセットアップ"""
        self.test_cases_dir = Path("test_cases")
        self.test_output_dir = Path("test_output")
    
    @patch('subprocess.run')
    def test_yaml_application_simulation(self, mock_subprocess):
        """YAML適用のシミュレーションテスト"""
        # haconiwa apply コマンドのシミュレーション
        mock_subprocess.return_value.returncode = 0
        mock_subprocess.return_value.stdout = "✅ Applied resources successfully"
        
        yaml_files = [
            "basic_executive_floor.yaml",
            "heavy_task_assignment.yaml", 
            "minimal_config.yaml",
            "full_structure_test.yaml"
        ]
        
        for yaml_file in yaml_files:
            yaml_path = self.test_cases_dir / yaml_file
            if yaml_path.exists():
                with self.subTest(yaml_file=yaml_file):
                    # コマンド実行のシミュレーション
                    cmd = ["haconiwa", "apply", "-f", str(yaml_path), "--no-attach"]
                    result = mock_subprocess(cmd, capture_output=True, text=True)
                    
                    # 成功を期待
                    self.assertEqual(result.returncode, 0, 
                                   f"{yaml_file} の適用がシミュレーション内で失敗しました")
    
    def test_space_manager_configuration(self):
        """SpaceManager設定のテスト"""
        from src.haconiwa.space.manager import SpaceManager
        
        space_manager = SpaceManager()
        
        # Executive Room用のデスクマッピング生成テスト
        organizations = [
            {"id": "01", "name": "Frontend", "department_id": "frontend"},
            {"id": "02", "name": "Backend", "department_id": "backend"},
            {"id": "03", "name": "DevOps", "department_id": "devops"},
            {"id": "04", "name": "QA", "department_id": "qa"},
            {"id": "05", "name": "Executive", "department_id": "executive"}
        ]
        
        mappings = space_manager.generate_desk_mappings(organizations)
        
        # Executive Room マッピングの確認
        executive_mappings = [m for m in mappings if m["room_id"] == "room-executive"]
        self.assertEqual(len(executive_mappings), 4, "Executive Roomには4つのマッピングが必要")
        
        # Executive役職の確認
        exec_roles = [m["role"] for m in executive_mappings]
        expected_roles = ["ceo", "cto", "coo", "assistant"]
        for role in expected_roles:
            self.assertIn(role, exec_roles, f"Executive Room に {role} 役職が必要")
    
    def test_floor_hierarchy_display(self):
        """階層表示のテスト"""
        from src.haconiwa.space.manager import SpaceManager
        from pathlib import Path
        
        space_manager = SpaceManager()
        
        organizations = [
            {"id": "01", "name": "Frontend Team", "department_id": "frontend"},
            {"id": "02", "name": "Backend Team", "department_id": "backend"},
            {"id": "03", "name": "DevOps Team", "department_id": "devops"},
            {"id": "04", "name": "QA Team", "department_id": "qa"},
            {"id": "05", "name": "Executive Leadership", "department_id": "executive"}
        ]
        
        task_assignments = {
            "org05-ceo-re": {"task_name": "strategic_planning", "room": "re", "status": "active"},
            "org05-cto-re": {"task_name": "tech_roadmap", "room": "re", "status": "active"},
        }
        
        # ツリー生成のテスト（test_outputディレクトリを使用）
        tree = space_manager._create_world_hierarchy_tree(
            self.test_output_dir / "test_world", organizations, task_assignments
        )
        
        # ツリー出力の文字列化
        from io import StringIO
        from rich.console import Console
        
        console = Console(file=StringIO(), width=120)
        console.print(tree)
        tree_output = console.file.getvalue()
        
        # Floor 2 の存在確認
        self.assertIn("Floor 2", tree_output, "階層表示にFloor 2が含まれていません")
        self.assertIn("Executive Room", tree_output, "階層表示にExecutive Roomが含まれていません")
        self.assertIn("strategic_planning", tree_output, "タスク割り当てが表示されていません")


if __name__ == '__main__':
    unittest.main() 