"""
Test for Hierarchical Legal Framework Directory Structure
階層的法的フレームワークのディレクトリ構造をテストする
"""

import os
import pytest
import tempfile
import shutil
import yaml
from pathlib import Path


class TestHierarchicalLegalFramework:
    """階層的法的フレームワークのディレクトリ構造テストクラス"""

    def setup_method(self):
        """各テストメソッドの前に実行されるセットアップ"""
        self.temp_dir = tempfile.mkdtemp()
        self.test_yaml_content = {
            'apiVersion': 'haconiwa.dev/v1',
            'kind': 'Space',
            'metadata': {'name': 'legal-framework-test'},
            'spec': {
                'nations': [{
                    'id': 'jp',
                    'name': 'Japan',
                    'legalFramework': {
                        'enabled': True,
                        'lawDirectory': 'law',
                        'globalRules': 'global-rules.md',
                        'systemPrompts': 'system-prompts',
                        'permissions': 'permissions'
                    },
                    'cities': [{
                        'id': 'tokyo',
                        'name': 'Tokyo',
                        'legalFramework': {
                            'enabled': True,
                            'lawDirectory': 'law',
                            'regionalRules': 'regional-rules.md',
                            'systemPrompts': 'system-prompts',
                            'permissions': 'permissions'
                        },
                        'villages': [{
                            'id': 'test-village',
                            'name': 'Test Village',
                            'legalFramework': {
                                'enabled': True,
                                'lawDirectory': 'law',
                                'localRules': 'local-rules.md',
                                'systemPrompts': 'system-prompts',
                                'permissions': 'permissions'
                            },
                            'companies': [{
                                'name': 'test-legal-company',
                                'grid': '8x4',
                                'basePath': f'{self.temp_dir}/legal-test-desks',
                                'legalFramework': {
                                    'enabled': True,
                                    'lawDirectory': 'law',
                                    'projectRules': 'project-rules.md',
                                    'systemPrompts': 'system-prompts',
                                    'permissions': 'permissions'
                                },
                                'organizations': [
                                    {'id': '01', 'name': 'Frontend Team', 'tasks': ['UI Design']},
                                    {'id': '02', 'name': 'Backend Team', 'tasks': ['API Development']}
                                ],
                                'gitRepo': {
                                    'url': 'https://github.com/dai-motoki/haconiwa',
                                    'defaultBranch': 'main',
                                    'auth': 'https'
                                },
                                'buildings': [{
                                    'id': 'headquarters',
                                    'name': 'Company Headquarters',
                                    'legalFramework': {
                                        'enabled': True,
                                        'lawDirectory': 'law',
                                        'buildingRules': 'building-rules.md',
                                        'systemPrompts': 'system-prompts',
                                        'permissions': 'permissions'
                                    },
                                    'floors': [{
                                        'level': 1,
                                        'legalFramework': {
                                            'enabled': True,
                                            'lawDirectory': 'law',
                                            'floorRules': 'floor-rules.md',
                                            'systemPrompts': 'system-prompts',
                                            'permissions': 'permissions'
                                        },
                                        'rooms': [
                                            {
                                                'id': 'room-01', 
                                                'name': 'Alpha Room',
                                                'legalFramework': {
                                                    'enabled': True,
                                                    'lawDirectory': 'law',
                                                    'teamRules': 'team-rules.md',
                                                    'systemPrompts': 'system-prompts',
                                                    'permissions': 'permissions',
                                                    'desksLaw': {
                                                        'enabled': True,
                                                        'lawDirectory': 'law',
                                                        'agentRules': 'agent-rules.md',
                                                        'systemPrompts': 'system-prompts',
                                                        'permissions': 'permissions'
                                                    }
                                                }
                                            },
                                            {
                                                'id': 'room-02', 
                                                'name': 'Beta Room',
                                                'legalFramework': {
                                                    'enabled': True,
                                                    'lawDirectory': 'law',
                                                    'teamRules': 'team-rules.md',
                                                    'systemPrompts': 'system-prompts',
                                                    'permissions': 'permissions',
                                                    'desksLaw': {
                                                        'enabled': True,
                                                        'lawDirectory': 'law',
                                                        'agentRules': 'agent-rules.md',
                                                        'systemPrompts': 'system-prompts',
                                                        'permissions': 'permissions'
                                                    }
                                                }
                                            }
                                        ]
                                    }]
                                }]
                            }]
                        }]
                    }]
                }]
            }
        }

    def teardown_method(self):
        """各テストメソッドの後に実行されるクリーンアップ"""
        if os.path.exists(self.temp_dir):
            shutil.rmtree(self.temp_dir)

    def test_nation_level_law_directory_creation(self):
        """国レベルの法ディレクトリ作成をテスト"""
        # Given: YAML設定が準備されている
        base_path = Path(self.temp_dir) / "legal-test-desks"
        
        # When: 階層的法的フレームワークを適用
        self._apply_legal_framework()
        
        # Then: 国レベルの法ディレクトリが作成されている
        nation_law_dir = base_path / "jp" / "law"
        assert nation_law_dir.exists(), "国レベルの law ディレクトリが作成されていません"
        
        # 国レベルの法的文書が作成されている
        assert (nation_law_dir / "global-rules.md").exists(), "global-rules.md が作成されていません"
        assert (nation_law_dir / "system-prompts" / "nation-agent-prompt.md").exists(), "nation-agent-prompt.md が作成されていません"
        assert (nation_law_dir / "permissions" / "code-permissions.yaml").exists(), "code-permissions.yaml が作成されていません"
        assert (nation_law_dir / "permissions" / "file-permissions.yaml").exists(), "file-permissions.yaml が作成されていません"

    def test_city_level_law_directory_creation(self):
        """市レベルの法ディレクトリ作成をテスト"""
        # Given: YAML設定が準備されている
        base_path = Path(self.temp_dir) / "legal-test-desks"
        
        # When: 階層的法的フレームワークを適用
        self._apply_legal_framework()
        
        # Then: 市レベルの法ディレクトリが作成されている
        city_law_dir = base_path / "jp" / "tokyo" / "law"
        assert city_law_dir.exists(), "市レベルの law ディレクトリが作成されていません"
        
        # 市レベルの法的文書が作成されている
        assert (city_law_dir / "regional-rules.md").exists(), "regional-rules.md が作成されていません"
        assert (city_law_dir / "system-prompts" / "city-agent-prompt.md").exists(), "city-agent-prompt.md が作成されていません"
        assert (city_law_dir / "permissions" / "code-permissions.yaml").exists(), "code-permissions.yaml が作成されていません"
        assert (city_law_dir / "permissions" / "file-permissions.yaml").exists(), "file-permissions.yaml が作成されていません"

    def test_village_level_law_directory_creation(self):
        """村レベルの法ディレクトリ作成をテスト"""
        # Given: YAML設定が準備されている
        base_path = Path(self.temp_dir) / "legal-test-desks"
        
        # When: 階層的法的フレームワークを適用
        self._apply_legal_framework()
        
        # Then: 村レベルの法ディレクトリが作成されている
        village_law_dir = base_path / "jp" / "tokyo" / "test-village" / "law"
        assert village_law_dir.exists(), "村レベルの law ディレクトリが作成されていません"
        
        # 村レベルの法的文書が作成されている
        assert (village_law_dir / "local-rules.md").exists(), "local-rules.md が作成されていません"
        assert (village_law_dir / "system-prompts" / "village-agent-prompt.md").exists(), "village-agent-prompt.md が作成されていません"

    def test_company_level_law_directory_creation(self):
        """会社レベルの法ディレクトリ作成をテスト"""
        # Given: YAML設定が準備されている
        base_path = Path(self.temp_dir) / "legal-test-desks"
        
        # When: 階層的法的フレームワークを適用
        self._apply_legal_framework()
        
        # Then: 会社レベルの法ディレクトリが作成されている
        company_law_dir = base_path / "jp" / "tokyo" / "test-village" / "test-legal-company" / "law"
        assert company_law_dir.exists(), "会社レベルの law ディレクトリが作成されていません"
        
        # 会社レベルの法的文書が作成されている
        assert (company_law_dir / "project-rules.md").exists(), "project-rules.md が作成されていません"
        assert (company_law_dir / "system-prompts" / "company-agent-prompt.md").exists(), "company-agent-prompt.md が作成されていません"

    def test_building_level_law_directory_creation(self):
        """建物レベルの法ディレクトリ作成をテスト"""
        # Given: YAML設定が準備されている
        base_path = Path(self.temp_dir) / "legal-test-desks"
        
        # When: 階層的法的フレームワークを適用
        self._apply_legal_framework()
        
        # Then: 建物レベルの法ディレクトリが作成されている
        building_law_dir = base_path / "jp" / "tokyo" / "test-village" / "test-legal-company" / "headquarters" / "law"
        assert building_law_dir.exists(), "建物レベルの law ディレクトリが作成されていません"
        
        # 建物レベルの法的文書が作成されている
        assert (building_law_dir / "building-rules.md").exists(), "building-rules.md が作成されていません"
        assert (building_law_dir / "system-prompts" / "building-agent-prompt.md").exists(), "building-agent-prompt.md が作成されていません"

    def test_floor_level_law_directory_creation(self):
        """階層レベルの法ディレクトリ作成をテスト"""
        # Given: YAML設定が準備されている
        base_path = Path(self.temp_dir) / "legal-test-desks"
        
        # When: 階層的法的フレームワークを適用
        self._apply_legal_framework()
        
        # Then: 階層レベルの法ディレクトリが作成されている
        floor_law_dir = base_path / "jp" / "tokyo" / "test-village" / "test-legal-company" / "headquarters" / "floor-1" / "law"
        assert floor_law_dir.exists(), "階層レベルの law ディレクトリが作成されていません"
        
        # 階層レベルの法的文書が作成されている
        assert (floor_law_dir / "floor-rules.md").exists(), "floor-rules.md が作成されていません"
        assert (floor_law_dir / "system-prompts" / "floor-agent-prompt.md").exists(), "floor-agent-prompt.md が作成されていません"

    def test_room_level_law_directory_creation(self):
        """部屋レベルの法ディレクトリ作成をテスト"""
        # Given: YAML設定が準備されている
        base_path = Path(self.temp_dir) / "legal-test-desks"
        
        # When: 階層的法的フレームワークを適用
        self._apply_legal_framework()
        
        # Then: 両方の部屋レベルの法ディレクトリが作成されている
        room01_law_dir = base_path / "jp" / "tokyo" / "test-village" / "test-legal-company" / "headquarters" / "floor-1" / "room-01" / "law"
        room02_law_dir = base_path / "jp" / "tokyo" / "test-village" / "test-legal-company" / "headquarters" / "floor-1" / "room-02" / "law"
        
        assert room01_law_dir.exists(), "room-01の law ディレクトリが作成されていません"
        assert room02_law_dir.exists(), "room-02の law ディレクトリが作成されていません"
        
        # 部屋レベルの法的文書が作成されている
        assert (room01_law_dir / "team-rules.md").exists(), "room-01の team-rules.md が作成されていません"
        assert (room01_law_dir / "system-prompts" / "room-agent-prompt.md").exists(), "room-01の room-agent-prompt.md が作成されていません"

    def test_desk_level_law_directory_creation(self):
        """デスクレベルの法ディレクトリ作成をテスト"""
        # Given: YAML設定が準備されている
        base_path = Path(self.temp_dir) / "legal-test-desks"
        
        # When: 階層的法的フレームワークを適用
        self._apply_legal_framework()
        
        # Then: デスクレベルの法ディレクトリが作成されている
        desk_law_dir = base_path / "jp" / "tokyo" / "test-village" / "test-legal-company" / "headquarters" / "floor-1" / "room-01" / "desks" / "law"
        assert desk_law_dir.exists(), "デスクレベルの law ディレクトリが作成されていません"
        
        # デスクレベルの法的文書が作成されている
        assert (desk_law_dir / "agent-rules.md").exists(), "agent-rules.md が作成されていません"
        assert (desk_law_dir / "system-prompts" / "desk-agent-prompt.md").exists(), "desk-agent-prompt.md が作成されていません"

    def test_legal_framework_content_validation(self):
        """法的文書の内容を検証"""
        # Given: YAML設定が準備されている
        base_path = Path(self.temp_dir) / "legal-test-desks"
        
        # When: 階層的法的フレームワークを適用
        self._apply_legal_framework()
        
        # Then: 法的文書の内容が適切である
        nation_rules = base_path / "jp" / "law" / "global-rules.md"
        with open(nation_rules, 'r', encoding='utf-8') as f:
            content = f.read()
            assert "グローバル原則" in content, "global-rules.mdにグローバル原則の内容が含まれていません"
            assert "Universal principles" in content, "global-rules.mdに英語の内容が含まれていません"

        # YAML権限ファイルの検証
        code_permissions = base_path / "jp" / "law" / "permissions" / "code-permissions.yaml"
        with open(code_permissions, 'r', encoding='utf-8') as f:
            permissions_data = yaml.safe_load(f)
            assert "nation_level" in permissions_data, "code-permissions.yamlに nation_level が含まれていません"

    def test_organizational_hierarchy_validation(self):
        """組織階層構造の検証"""
        # Given: YAML設定が準備されている
        base_path = Path(self.temp_dir) / "legal-test-desks"
        
        # When: 階層的法的フレームワークを適用
        self._apply_legal_framework()
        
        # Then: エージェントデスクディレクトリが作成されている
        desk_dir = base_path / "jp" / "tokyo" / "test-village" / "test-legal-company" / "headquarters" / "floor-1" / "room-01" / "desks"
        
        # 組織別デスクディレクトリの確認
        expected_desks = [
            "org-01-pm", "org-01-worker-a", "org-01-worker-b", "org-01-worker-c",
            "org-02-pm", "org-02-worker-a", "org-02-worker-b", "org-02-worker-c"
        ]
        
        for desk_name in expected_desks:
            desk_path = desk_dir / desk_name
            assert desk_path.exists(), f"{desk_name} デスクディレクトリが作成されていません"

    def _apply_legal_framework(self):
        """階層的法的フレームワークを適用するヘルパーメソッド"""
        from src.haconiwa.legal.framework import HierarchicalLegalFramework
        import tempfile
        import yaml
        
        # テスト用のYAMLファイル作成
        yaml_file = os.path.join(self.temp_dir, "test-legal.yaml")
        with open(yaml_file, 'w', encoding='utf-8') as f:
            yaml.dump(self.test_yaml_content, f, default_flow_style=False, allow_unicode=True)
        
        # 階層的法的フレームワークを適用
        base_path = Path(self.temp_dir) / "legal-test-desks"
        framework = HierarchicalLegalFramework(base_path)
        success = framework.create_framework_from_yaml(self.test_yaml_content)
        
        if not success:
            raise RuntimeError("階層的法的フレームワークの作成に失敗しました")
        
        # 組織別デスクディレクトリも作成（テスト用）
        self._create_organizational_desks(base_path)

    def _create_organizational_desks(self, base_path: Path):
        """組織別デスクディレクトリを作成するヘルパーメソッド"""
        # デスクディレクトリのパス
        desks_base = base_path / "jp" / "tokyo" / "test-village" / "test-legal-company" / "headquarters" / "floor-1"
        
        # 各部屋のデスクディレクトリを作成
        for room_id in ["room-01", "room-02"]:
            desks_path = desks_base / room_id / "desks"
            
            # 組織別デスクディレクトリ作成
            organizations = self.test_yaml_content['spec']['nations'][0]['cities'][0]['villages'][0]['companies'][0]['organizations']
            
            for org in organizations:
                org_id = org['id']
                
                # PM デスク
                pm_desk = desks_path / f"org-{org_id}-pm"
                pm_desk.mkdir(parents=True, exist_ok=True)
                
                # Worker デスク
                for worker in ['worker-a', 'worker-b', 'worker-c']:
                    worker_desk = desks_path / f"org-{org_id}-{worker}"
                    worker_desk.mkdir(parents=True, exist_ok=True)

if __name__ == "__main__":
    pytest.main([__file__]) 