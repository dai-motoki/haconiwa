"""
Claude Code Integration Module
Claude Code統合モジュール

このモジュールは、Claude Code エージェントとの統合を提供し、
適切な設定ファイル（.claude/settings.local.json）を自動生成します。
"""

import json
import logging
from pathlib import Path
from typing import Dict, Any, Optional, List
from copy import deepcopy

logger = logging.getLogger(__name__)


class ClaudeCodeIntegration:
    """Claude Code統合クラス"""

    def __init__(self):
        """初期化"""
        pass

    def create_claude_settings(self, task_dir: Path, company_defaults: Dict[str, Any], 
                             task_config: Optional[Dict[str, Any]] = None) -> bool:
        """
        Claude Code設定ファイルを作成
        
        Args:
            task_dir: タスクディレクトリパス
            company_defaults: 会社レベルのデフォルト設定
            task_config: タスクレベルの設定（オプション）
            
        Returns:
            作成成功時True、失敗時False
        """
        try:
            # Claude Code以外のエージェントタイプの場合はスキップ
            if not self._is_claude_code_agent(company_defaults, task_config):
                logger.debug("Non-Claude Code agent, skipping .claude/settings.local.json creation")
                return True

            # .claude ディレクトリを作成
            claude_dir = task_dir / ".claude"
            claude_dir.mkdir(exist_ok=True)

            # 設定をマージ
            merged_settings = self._merge_agent_settings(company_defaults, task_config)

            # Claude Code形式に変換
            claude_settings = self._convert_to_claude_format(merged_settings)

            # settings.local.json ファイルに書き込み
            settings_file = claude_dir / "settings.local.json"
            with open(settings_file, 'w', encoding='utf-8') as f:
                json.dump(claude_settings, f, indent=2, ensure_ascii=False)

            logger.info(f"📁 Created Claude Code settings: {settings_file}")
            return True

        except Exception as e:
            logger.error(f"Failed to create Claude Code settings: {e}")
            return False

    def _is_claude_code_agent(self, company_defaults: Dict[str, Any], 
                            task_config: Optional[Dict[str, Any]] = None) -> bool:
        """
        Claude Codeエージェントかどうかを判定
        
        Args:
            company_defaults: 会社レベルのデフォルト設定
            task_config: タスクレベルの設定
            
        Returns:
            Claude Codeエージェントの場合True
        """
        # タスクレベルの設定を優先
        if task_config and task_config.get('type') == 'claude-code':
            return True
        
        # 会社レベルのデフォルト設定を確認
        if company_defaults.get('type') == 'claude-code':
            return True
        
        return False

    def _merge_agent_settings(self, company_defaults: Dict[str, Any], 
                            task_config: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        """
        会社デフォルト設定とタスク設定をマージ
        
        Args:
            company_defaults: 会社レベルのデフォルト設定
            task_config: タスクレベルの設定
            
        Returns:
            マージされた設定
        """
        # 会社デフォルト設定をベースにコピー
        merged = deepcopy(company_defaults)
        
        if not task_config:
            return merged
        
        # タスクレベルの設定をマージ
        
        # エージェントタイプ（タスクレベルが優先）
        if 'type' in task_config:
            merged['type'] = task_config['type']
        
        # 環境変数のマージ
        if 'env' in task_config:
            if 'env' not in merged:
                merged['env'] = {}
            merged['env'].update(task_config['env'])
        
        # パーミッションのマージ
        if 'additionalPermissions' in task_config:
            additional_perms = task_config['additionalPermissions']
            
            # パーミッション構造を初期化
            if 'permissions' not in merged:
                merged['permissions'] = {'allow': [], 'deny': []}
            
            # allow パーミッションの追加
            if 'allow' in additional_perms:
                if 'allow' not in merged['permissions']:
                    merged['permissions']['allow'] = []
                merged['permissions']['allow'].extend(additional_perms['allow'])
            
            # deny パーミッションの追加
            if 'deny' in additional_perms:
                if 'deny' not in merged['permissions']:
                    merged['permissions']['deny'] = []
                merged['permissions']['deny'].extend(additional_perms['deny'])
        
        return merged

    def _convert_to_claude_format(self, agent_settings: Dict[str, Any]) -> Dict[str, Any]:
        """
        エージェント設定をClaude Code形式に変換
        
        Args:
            agent_settings: マージされたエージェント設定
            
        Returns:
            Claude Code形式の設定
        """
        claude_settings = {}
        
        # パーミッション設定
        if 'permissions' in agent_settings:
            permissions = agent_settings['permissions']
            claude_settings['permissions'] = {}
            
            # allow パーミッション
            if 'allow' in permissions:
                claude_settings['permissions']['allow'] = permissions['allow']
            
            # deny パーミッション
            if 'deny' in permissions:
                claude_settings['permissions']['deny'] = permissions['deny']
        
        # 環境変数設定
        if 'env' in agent_settings:
            claude_settings['env'] = agent_settings['env']
        
        return claude_settings

    def validate_claude_settings(self, settings_file: Path) -> bool:
        """
        Claude設定ファイルの妥当性を検証
        
        Args:
            settings_file: 設定ファイルパス
            
        Returns:
            妥当性検証結果
        """
        try:
            if not settings_file.exists():
                logger.warning(f"Claude settings file not found: {settings_file}")
                return False
            
            with open(settings_file, 'r', encoding='utf-8') as f:
                settings = json.load(f)
            
            # 基本構造の確認
            if not isinstance(settings, dict):
                logger.error("Claude settings must be a JSON object")
                return False
            
            # permissions セクションの確認
            if 'permissions' in settings:
                permissions = settings['permissions']
                if not isinstance(permissions, dict):
                    logger.error("permissions must be an object")
                    return False
                
                # allow/deny の確認
                for key in ['allow', 'deny']:
                    if key in permissions:
                        if not isinstance(permissions[key], list):
                            logger.error(f"permissions.{key} must be an array")
                            return False
            
            # env セクションの確認
            if 'env' in settings:
                env = settings['env']
                if not isinstance(env, dict):
                    logger.error("env must be an object")
                    return False
            
            logger.debug(f"Claude settings validation passed: {settings_file}")
            return True
            
        except json.JSONDecodeError as e:
            logger.error(f"Invalid JSON in Claude settings file: {e}")
            return False
        except Exception as e:
            logger.error(f"Error validating Claude settings: {e}")
            return False 