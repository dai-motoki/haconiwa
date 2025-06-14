"""
Test AICodeConfig functionality
AICodeConfig機能のテストケース
"""

import pytest
from pathlib import Path
from unittest.mock import Mock, patch, MagicMock
import logging

from haconiwa.core.crd.models import AICodeConfigCRD, AICodeConfigSpec, ClaudeConfig, Metadata
from haconiwa.core.applier import CRDApplier
from haconiwa.task.manager import TaskManager


class TestAICodeConfigApplier:
    """AICodeConfig適用のテストクラス"""
    
    def setup_method(self):
        """各テストメソッドの前に実行される初期化"""
        self.applier = CRDApplier()
        
    def test_apply_aicode_config_claude_provider(self):
        """Claudeプロバイダーの適用テスト"""
        # AICodeConfig CRDを作成
        crd = AICodeConfigCRD(
            apiVersion="haconiwa.dev/v1",
            kind="AICodeConfig",
            metadata=Metadata(name="test-claude-config"),
            spec=AICodeConfigSpec(
                provider="claude",
                claude=ClaudeConfig(
                    settingsFile="./test-settings.json",
                    guidelinesFile="./test-guidelines.md"
                ),
                targetCompany="test-company"
            )
        )
        
        # 適用
        result = self.applier._apply_aicode_config_crd(crd)
        
        assert result is True
        assert "test-company" in self.applier.ai_code_configs
        assert self.applier.ai_code_configs["test-company"] == crd
        
    def test_apply_aicode_config_unsupported_provider(self):
        """サポートされていないプロバイダーの適用テスト"""
        # AICodeConfig CRDを作成（サポートされていないプロバイダー）
        crd = AICodeConfigCRD(
            apiVersion="haconiwa.dev/v1",
            kind="AICodeConfig",
            metadata=Metadata(name="test-copilot-config"),
            spec=AICodeConfigSpec(
                provider="copilot",  # サポートされていない
                targetCompany="test-company"
            )
        )
        
        # 適用
        result = self.applier._apply_aicode_config_crd(crd)
        
        assert result is False  # サポートされていないので失敗
        assert "test-company" not in self.applier.ai_code_configs


class TestAICodeConfigFileCopy:
    """AICodeConfigファイルコピー機能のテストクラス"""
    
    def setup_method(self):
        """各テストメソッドの前に実行される初期化"""
        self.task_manager = TaskManager()
        
    @patch('haconiwa.task.manager.Path')
    @patch('shutil.copy2')
    def test_copy_aicode_config_files_success(self, mock_copy, mock_path):
        """AICodeConfigファイルの正常コピーテスト"""
        # モックの設定
        worktree_path = Mock(spec=Path)
        claude_dir = Mock(spec=Path)
        worktree_path.__truediv__.return_value = claude_dir
        
        # ファイルパスのモック
        settings_path = Mock(spec=Path)
        settings_path.exists.return_value = True
        guidelines_path = Mock(spec=Path)
        guidelines_path.exists.return_value = True
        
        mock_path.side_effect = lambda x: settings_path if "settings" in x else guidelines_path
        
        # AICodeConfig CRDを作成
        crd = AICodeConfigCRD(
            apiVersion="haconiwa.dev/v1",
            kind="AICodeConfig",
            metadata=Metadata(name="test-config"),
            spec=AICodeConfigSpec(
                provider="claude",
                claude=ClaudeConfig(
                    settingsFile="./settings.json",
                    guidelinesFile="./guidelines.md"
                ),
                targetCompany="test-company"
            )
        )
        
        # Applierのモック
        with patch('sys.modules') as mock_modules:
            mock_applier = Mock()
            mock_applier.ai_code_configs = {"test-company": crd}
            mock_modules.get.return_value.__dict__ = {'_current_applier': mock_applier}
            
            # ファイルコピーを実行
            self.task_manager._copy_aicode_config_files_to_worktree(worktree_path, "test-company")
            
        # コピーが2回呼ばれたことを確認（settings.json と guidelines.md）
        assert mock_copy.call_count == 2
        
    @patch('haconiwa.task.manager.Path')
    @patch('shutil.copy2')
    def test_copy_aicode_config_files_not_found(self, mock_copy, mock_path):
        """AICodeConfigファイルが存在しない場合のテスト"""
        # モックの設定
        worktree_path = Mock(spec=Path)
        
        # ファイルパスのモック（存在しない）
        settings_path = Mock(spec=Path)
        settings_path.exists.return_value = False
        guidelines_path = Mock(spec=Path)
        guidelines_path.exists.return_value = False
        
        mock_path.side_effect = lambda x: settings_path if "settings" in x else guidelines_path
        
        # AICodeConfig CRDを作成
        crd = AICodeConfigCRD(
            apiVersion="haconiwa.dev/v1",
            kind="AICodeConfig",
            metadata=Metadata(name="test-config"),
            spec=AICodeConfigSpec(
                provider="claude",
                claude=ClaudeConfig(
                    settingsFile="./missing-settings.json",
                    guidelinesFile="./missing-guidelines.md"
                ),
                targetCompany="test-company"
            )
        )
        
        # Applierのモック
        with patch('sys.modules') as mock_modules:
            mock_applier = Mock()
            mock_applier.ai_code_configs = {"test-company": crd}
            mock_modules.get.return_value.__dict__ = {'_current_applier': mock_applier}
            
            # ログのキャプチャ
            with patch('haconiwa.task.manager.logger') as mock_logger:
                # ファイルコピーを実行
                self.task_manager._copy_aicode_config_files_to_worktree(worktree_path, "test-company")
                
                # ワーニングログが出力されたことを確認
                assert mock_logger.warning.call_count == 2
                mock_logger.warning.assert_any_call("Settings file not found: ./missing-settings.json")
                mock_logger.warning.assert_any_call("Guidelines file not found: ./missing-guidelines.md")
        
        # コピーは呼ばれていない
        assert mock_copy.call_count == 0
        
    @patch('sys.modules')
    def test_copy_aicode_config_no_config_found(self, mock_modules):
        """該当する会社のAICodeConfigが見つからない場合のテスト"""
        # Applierのモック（AICodeConfigなし）
        mock_applier = Mock()
        mock_applier.ai_code_configs = {}  # 空
        mock_modules.get.return_value.__dict__ = {'_current_applier': mock_applier}
        
        worktree_path = Mock(spec=Path)
        
        # ログのキャプチャ
        with patch('haconiwa.task.manager.logger') as mock_logger:
            # ファイルコピーを実行
            self.task_manager._copy_aicode_config_files_to_worktree(worktree_path, "nonexistent-company")
            
            # デバッグログが出力されたことを確認
            mock_logger.debug.assert_called_with("No AICodeConfig found for company: nonexistent-company")


class TestAICodeConfigIntegration:
    """AICodeConfig統合テスト"""
    
    @patch('subprocess.run')
    @patch('haconiwa.task.manager.Path')
    @patch('shutil.copy2')
    def test_task_creation_with_aicode_config(self, mock_copy, mock_path, mock_subprocess):
        """タスク作成時のAICodeConfig適用テスト"""
        # サブプロセスのモック（git worktree作成）
        mock_subprocess.return_value.returncode = 0
        
        # パスのモック
        base_path = Mock(spec=Path)
        base_path.exists.return_value = True
        tasks_path = Mock(spec=Path)
        base_path.__truediv__.return_value = tasks_path
        tasks_path.__truediv__.return_value = Mock(spec=Path)
        
        # ファイルパスのモック
        settings_path = Mock(spec=Path)
        settings_path.exists.return_value = True
        guidelines_path = Mock(spec=Path) 
        guidelines_path.exists.return_value = True
        
        mock_path.side_effect = lambda x: (
            settings_path if "settings" in str(x) 
            else guidelines_path if "guidelines" in str(x)
            else base_path
        )
        
        # AICodeConfig CRDを作成
        crd = AICodeConfigCRD(
            apiVersion="haconiwa.dev/v1",
            kind="AICodeConfig",
            metadata=Metadata(name="test-config"),
            spec=AICodeConfigSpec(
                provider="claude",
                claude=ClaudeConfig(
                    settingsFile="./settings.json",
                    guidelinesFile="./guidelines.md"
                ),
                targetCompany="test-company"
            )
        )
        
        # TaskManagerとApplierを設定
        task_manager = TaskManager()
        with patch('sys.modules') as mock_modules:
            mock_applier = Mock()
            mock_applier.ai_code_configs = {"test-company": crd}
            mock_modules.get.return_value.__dict__ = {'_current_applier': mock_applier}
            
            # SpaceManagerのモック
            with patch('haconiwa.task.manager.SpaceManager') as mock_space_manager:
                mock_space_manager.return_value.active_sessions = {
                    "test-company": {
                        "config": {
                            "name": "test-company",
                            "base_path": "./test-company"
                        }
                    }
                }
                
                # タスクを作成
                config = {
                    "name": "test-task",
                    "branch": "test/branch",
                    "worktree": True,
                    "assignee": "test-agent",
                    "space_ref": "test-company",
                    "description": "Test task"
                }
                
                result = task_manager.create_task(config)
                
                assert result is True
                # ファイルコピーが呼ばれたことを確認
                assert mock_copy.call_count >= 2  # settings.json と guidelines.md