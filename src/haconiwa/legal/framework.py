"""
Hierarchical Legal Framework Module
階層的法的フレームワークモジュール

このモジュールは、YAML設定に基づいて階層的な法的フレームワークディレクトリ構造を作成し、
各階層レベルで適切な法的文書、システムプロンプト、権限ファイルを生成します。
"""

import os
import yaml
from pathlib import Path
from typing import Dict, Any, List, Optional
import logging

logger = logging.getLogger(__name__)


class HierarchicalLegalFramework:
    """階層的法的フレームワーククラス"""

    def __init__(self, base_path: Path):
        """
        Args:
            base_path: ベースディレクトリパス
        """
        self.base_path = Path(base_path)
        self.created_directories = []

    def create_framework_from_yaml(self, yaml_spec: Dict[str, Any]) -> bool:
        """
        YAML設定から階層的法的フレームワークを作成
        
        Args:
            yaml_spec: YAML設定辞書
            
        Returns:
            作成成功時True、失敗時False
        """
        try:
            logger.info("階層的法的フレームワークの作成を開始します")
            
            # Nations (国) レベルの処理
            nations = yaml_spec.get('spec', {}).get('nations', [])
            for nation in nations:
                self._create_nation_framework(nation)
                
            logger.info(f"階層的法的フレームワークの作成が完了しました。作成されたディレクトリ数: {len(self.created_directories)}")
            return True
            
        except Exception as e:
            logger.error(f"階層的法的フレームワークの作成中にエラーが発生しました: {e}")
            return False

    def _create_nation_framework(self, nation: Dict[str, Any]) -> None:
        """国レベルの法的フレームワークを作成"""
        nation_id = nation.get('id')
        nation_name = nation.get('name')
        legal_framework = nation.get('legalFramework', {})
        
        if not legal_framework.get('enabled', False):
            return
            
        # 国ディレクトリ作成
        nation_path = self.base_path / nation_id
        self._create_law_directory(
            nation_path, 
            legal_framework, 
            'nation',
            nation_name,
            "グローバル原則とコア標準を定義"
        )
        
        # Cities (市) レベルの処理
        cities = nation.get('cities', [])
        for city in cities:
            self._create_city_framework(nation_path, city)

    def _create_city_framework(self, nation_path: Path, city: Dict[str, Any]) -> None:
        """市レベルの法的フレームワークを作成"""
        city_id = city.get('id')
        city_name = city.get('name')
        legal_framework = city.get('legalFramework', {})
        
        if not legal_framework.get('enabled', False):
            return
            
        # 市ディレクトリ作成
        city_path = nation_path / city_id
        self._create_law_directory(
            city_path, 
            legal_framework, 
            'city',
            city_name,
            "地域ガイドラインとコンプライアンス要件を定義"
        )
        
        # Villages (村) レベルの処理
        villages = city.get('villages', [])
        for village in villages:
            self._create_village_framework(city_path, village)

    def _create_village_framework(self, city_path: Path, village: Dict[str, Any]) -> None:
        """村レベルの法的フレームワークを作成"""
        village_id = village.get('id')
        village_name = village.get('name')
        legal_framework = village.get('legalFramework', {})
        
        if not legal_framework.get('enabled', False):
            return
            
        # 村ディレクトリ作成
        village_path = city_path / village_id
        self._create_law_directory(
            village_path, 
            legal_framework, 
            'village',
            village_name,
            "コミュニティプラクティスとローカルワークフローを定義"
        )
        
        # Companies (会社) レベルの処理
        companies = village.get('companies', [])
        for company in companies:
            self._create_company_framework(village_path, company)

    def _create_company_framework(self, village_path: Path, company: Dict[str, Any]) -> None:
        """会社レベルの法的フレームワークを作成"""
        company_name = company.get('name')
        legal_framework = company.get('legalFramework', {})
        
        if not legal_framework.get('enabled', False):
            return
            
        # 会社ディレクトリ作成
        company_path = village_path / company_name
        self._create_law_directory(
            company_path, 
            legal_framework, 
            'company',
            company_name,
            "プロジェクト管理ポリシーとビジネスロジック制約を定義"
        )
        
        # Buildings (建物) レベルの処理
        buildings = company.get('buildings', [])
        for building in buildings:
            self._create_building_framework(company_path, building)

    def _create_building_framework(self, company_path: Path, building: Dict[str, Any]) -> None:
        """建物レベルの法的フレームワークを作成"""
        building_id = building.get('id')
        building_name = building.get('name')
        legal_framework = building.get('legalFramework', {})
        
        if not legal_framework.get('enabled', False):
            return
            
        # 建物ディレクトリ作成
        building_path = company_path / building_id
        self._create_law_directory(
            building_path, 
            legal_framework, 
            'building',
            building_name,
            "建物固有の手続きと物理スペース管理を定義"
        )
        
        # Floors (階層) レベルの処理
        floors = building.get('floors', [])
        for floor in floors:
            self._create_floor_framework(building_path, floor)

    def _create_floor_framework(self, building_path: Path, floor: Dict[str, Any]) -> None:
        """階層レベルの法的フレームワークを作成"""
        floor_level = floor.get('level')
        legal_framework = floor.get('legalFramework', {})
        
        if not legal_framework.get('enabled', False):
            return
            
        # 階層ディレクトリ作成
        floor_path = building_path / f"floor-{floor_level}"
        self._create_law_directory(
            floor_path, 
            legal_framework, 
            'floor',
            f"Floor {floor_level}",
            "フロアレベル調整とリソース配分を定義"
        )
        
        # Rooms (部屋) レベルの処理
        rooms = floor.get('rooms', [])
        for room in rooms:
            self._create_room_framework(floor_path, room)

    def _create_room_framework(self, floor_path: Path, room: Dict[str, Any]) -> None:
        """部屋レベルの法的フレームワークを作成"""
        room_id = room.get('id')
        room_name = room.get('name')
        legal_framework = room.get('legalFramework', {})
        
        if not legal_framework.get('enabled', False):
            return
            
        # 部屋ディレクトリ作成
        room_path = floor_path / room_id
        self._create_law_directory(
            room_path, 
            legal_framework, 
            'room',
            room_name,
            "チーム固有手続きと役割ベース責任を定義"
        )
        
        # Desks (デスク) レベルの処理
        desks_law = legal_framework.get('desksLaw', {})
        if desks_law.get('enabled', False):
            self._create_desk_framework(room_path, desks_law)

    def _create_desk_framework(self, room_path: Path, desks_law: Dict[str, Any]) -> None:
        """デスクレベルの法的フレームワークを作成"""
        # デスクディレクトリ作成
        desks_path = room_path / "desks"
        self._create_law_directory(
            desks_path, 
            desks_law, 
            'desk',
            "Agent Desks",
            "個人エージェント行動と個人生産性標準を定義"
        )

    def _create_law_directory(self, path: Path, legal_framework: Dict[str, Any], 
                            level: str, name: str, description: str) -> None:
        """法ディレクトリとその内容を作成"""
        law_dir = legal_framework.get('lawDirectory', 'law')
        law_path = path / law_dir
        
        # ディレクトリ作成
        law_path.mkdir(parents=True, exist_ok=True)
        self.created_directories.append(str(law_path))
        
        # 規則文書作成
        self._create_rules_document(law_path, legal_framework, level, name, description)
        
        # システムプロンプト作成
        self._create_system_prompts(law_path, legal_framework, level, name)
        
        # 権限ファイル作成
        self._create_permissions(law_path, legal_framework, level, name)

    def _create_rules_document(self, law_path: Path, legal_framework: Dict[str, Any], 
                             level: str, name: str, description: str) -> None:
        """規則文書を作成"""
        # レベル別の規則ファイル名を取得
        rules_mapping = {
            'nation': 'globalRules',
            'city': 'regionalRules', 
            'village': 'localRules',
            'company': 'projectRules',
            'building': 'buildingRules',
            'floor': 'floorRules',
            'room': 'teamRules',
            'desk': 'agentRules'
        }
        
        rules_key = rules_mapping.get(level, 'rules')
        rules_filename = legal_framework.get(rules_key, f"{level}-rules.md")
        rules_file = law_path / rules_filename
        
        # 規則文書内容作成
        content = self._generate_rules_content(level, name, description)
        
        with open(rules_file, 'w', encoding='utf-8') as f:
            f.write(content)

    def _create_system_prompts(self, law_path: Path, legal_framework: Dict[str, Any], 
                             level: str, name: str) -> None:
        """システムプロンプトを作成"""
        prompts_dir = legal_framework.get('systemPrompts', 'system-prompts')
        prompts_path = law_path / prompts_dir
        prompts_path.mkdir(parents=True, exist_ok=True)
        
        prompt_file = prompts_path / f"{level}-agent-prompt.md"
        content = self._generate_prompt_content(level, name)
        
        with open(prompt_file, 'w', encoding='utf-8') as f:
            f.write(content)

    def _create_permissions(self, law_path: Path, legal_framework: Dict[str, Any], 
                          level: str, name: str) -> None:
        """権限ファイルを作成"""
        permissions_dir = legal_framework.get('permissions', 'permissions')
        permissions_path = law_path / permissions_dir
        permissions_path.mkdir(parents=True, exist_ok=True)
        
        # コード権限ファイル
        code_permissions = self._generate_code_permissions(level, name)
        with open(permissions_path / "code-permissions.yaml", 'w', encoding='utf-8') as f:
            yaml.dump(code_permissions, f, default_flow_style=False, allow_unicode=True)
        
        # ファイル権限ファイル
        file_permissions = self._generate_file_permissions(level, name)
        with open(permissions_path / "file-permissions.yaml", 'w', encoding='utf-8') as f:
            yaml.dump(file_permissions, f, default_flow_style=False, allow_unicode=True)

    def _generate_rules_content(self, level: str, name: str, description: str) -> str:
        """規則文書の内容を生成"""
        level_mapping = {
            'nation': ('グローバル規則', 'Global Rules', 'Universal principles'),
            'city': ('地域規則', 'Regional Rules', 'Regional guidelines'),
            'village': ('ローカル規則', 'Local Rules', 'Local practices'),
            'company': ('プロジェクト規則', 'Project Rules', 'Project policies'),
            'building': ('建物規則', 'Building Rules', 'Building procedures'),
            'floor': ('階層規則', 'Floor Rules', 'Floor coordination'),
            'room': ('チーム規則', 'Team Rules', 'Team procedures'),
            'desk': ('エージェント規則', 'Agent Rules', 'Agent behavior')
        }
        
        japanese_title, english_title, english_desc = level_mapping.get(level, ('規則', 'Rules', 'Guidelines'))
        
        return f"""# {japanese_title} ({english_title})

## 概要 (Overview)
{description}
{english_desc} for {name}

## 階層レベル (Hierarchy Level)
- **レベル**: {level.title()}
- **名前**: {name}
- **適用範囲**: {level}レベルのすべてのエージェント

## 基本原則 (Basic Principles)

### 1. 規則継承 (Rule Inheritance)
- 上位階層の規則をすべて継承する
- 下位階層は追加制約のみ設定可能
- 上位規則に矛盾する規則は禁止

### 2. コンプライアンス (Compliance)
- 自動規則チェック機能の有効化
- 違反時の自動警告システム
- 規則更新時の自動通知

### 3. 権限管理 (Permission Management)
- コード権限: code-permissions.yaml 参照
- ファイル権限: file-permissions.yaml 参照
- システムプロンプト: system-prompts/ 参照

## 改訂履歴 (Revision History)
- 初版: {level}レベル法的フレームワーク作成

---
*このドキュメントは階層的法的フレームワークの一部です*
"""

    def _generate_prompt_content(self, level: str, name: str) -> str:
        """システムプロンプトの内容を生成"""
        return f"""# {level.title()} Level Agent System Prompt

## エージェント役割 (Agent Role)
あなたは{name}の{level}レベルエージェントです。

## 基本行動指針 (Basic Guidelines)
1. **規則遵守**: {level}レベルの規則を厳密に遵守する
2. **階層認識**: 自分の階層レベルと権限範囲を理解する
3. **継承遵守**: 上位階層の規則をすべて継承し従う
4. **連携協力**: 同階層および隣接階層との協力体制維持

## 権限範囲 (Permission Scope)
- コード権限: ../permissions/code-permissions.yaml で定義
- ファイル権限: ../permissions/file-permissions.yaml で定義

## エスカレーション (Escalation)
階層を超えた権限が必要な場合は、上位階層エージェントに相談してください。

## 禁止事項 (Prohibited Actions)
- 上位階層規則への違反行為
- 権限範囲外のシステム変更
- 他階層への無許可アクセス

---
*この指示は階層的法的フレームワークに基づいています*
"""

    def _generate_code_permissions(self, level: str, name: str) -> Dict[str, Any]:
        """コード権限設定を生成"""
        return {
            f"{level}_level": {
                "name": name,
                "level": level,
                "code_access": {
                    "read": True,
                    "write": True,
                    "execute": True,
                    "delete": False
                },
                "restricted_operations": [
                    "system_level_changes",
                    "security_modifications",
                    "cross_hierarchy_access"
                ],
                "allowed_languages": [
                    "python",
                    "javascript", 
                    "typescript",
                    "bash",
                    "yaml",
                    "markdown"
                ],
                "inheritance": {
                    "inherits_from_parent": True,
                    "can_override": False
                }
            }
        }

    def _generate_file_permissions(self, level: str, name: str) -> Dict[str, Any]:
        """ファイル権限設定を生成"""
        return {
            f"{level}_level": {
                "name": name,
                "level": level,
                "file_access": {
                    "read": True,
                    "write": True,
                    "create": True,
                    "delete": False
                },
                "allowed_directories": [
                    f"/{level}/**",
                    "/tasks/**",
                    "/standby/**"
                ],
                "restricted_directories": [
                    "/system/**",
                    "/config/**",
                    "/../**"
                ],
                "file_types": {
                    "allowed": [".md", ".py", ".js", ".ts", ".yaml", ".yml", ".json", ".txt"],
                    "restricted": [".exe", ".sh", ".bat", ".env"]
                },
                "inheritance": {
                    "inherits_from_parent": True,
                    "can_override": False
                }
            }
        } 