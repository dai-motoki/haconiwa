"""
Test for Agent Attributes and Claude Code Integration
エージェント属性とClaude Code統合のテスト
"""

import os
import pytest
import tempfile
import shutil
import yaml
import json
from pathlib import Path


class TestAgentAttributes:
    """エージェント属性のテストクラス"""

    def setup_method(self):
        """各テストメソッドの前に実行されるセットアップ"""
        self.temp_dir = tempfile.mkdtemp()
        self.test_yaml_content = {
            'apiVersion': 'haconiwa.dev/v1',
            'kind': 'Space',
            'metadata': {'name': 'agent-test-world'},
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
                            'id': 'agent-village',
                            'name': 'Agent Village',
                            'legalFramework': {
                                'enabled': True,
                                'lawDirectory': 'law',
                                'localRules': 'local-rules.md',
                                'systemPrompts': 'system-prompts',
                                'permissions': 'permissions'
                            },
                            'companies': [{
                                'name': 'claude-code-company',
                                'grid': '8x4',
                                'legalFramework': {
                                    'enabled': True,
                                    'lawDirectory': 'law',
                                    'projectRules': 'project-rules.md',
                                    'systemPrompts': 'system-prompts',
                                    'permissions': 'permissions'
                                },
                                'agentDefaults': {
                                    'type': 'claude-code',
                                    'permissions': {
                                        'allow': [
                                            'Bash(npm run lint)',
                                            'Bash(npm run test:*)',
                                            'Read(~/.zshrc)'
                                        ],
                                        'deny': [
                                            'Bash(curl:*)'
                                        ]
                                    },
                                    'env': {
                                        'CLAUDE_CODE_ENABLE_TELEMETRY': '1',
                                        'OTEL_METRICS_EXPORTER': 'otlp'
                                    }
                                },
                                'organizations': [{
                                    'id': 'org01',
                                    'name': 'フロントエンド部',
                                    'tasks': [{
                                        'id': 'frontend-task',
                                        'title': 'UI設計',
                                        'assignee': 'org01-pm-r1',
                                        'description': 'Claude Code でフロントエンド開発',
                                        'agentConfig': {
                                            'type': 'claude-code',
                                            'additionalPermissions': {
                                                'allow': [
                                                    'Bash(npm run dev)',
                                                    'Read(package.json)'
                                                ]
                                            }
                                        }
                                    }]
                                }],
                                'buildings': [{
                                    'id': 'headquarters',
                                    'name': 'Headquarters',
                                    'legalFramework': {
                                        'enabled': True,
                                        'lawDirectory': 'law',
                                        'buildingRules': 'building-rules.md',
                                        'systemPrompts': 'system-prompts',
                                        'permissions': 'permissions'
                                    },
                                    'floors': [{
                                        'id': 'floor-1',
                                        'name': 'Floor 1',
                                        'legalFramework': {
                                            'enabled': True,
                                            'lawDirectory': 'law',
                                            'floorRules': 'floor-rules.md',
                                            'systemPrompts': 'system-prompts',
                                            'permissions': 'permissions'
                                        },
                                        'rooms': [{
                                            'id': 'room-01',
                                            'name': 'Alpha Room',
                                            'legalFramework': {
                                                'enabled': True,
                                                'lawDirectory': 'law',
                                                'teamRules': 'team-rules.md',
                                                'systemPrompts': 'system-prompts',
                                                'permissions': 'permissions'
                                            },
                                            'desks': [{
                                                'id': 'org01-pm-r1',
                                                'name': 'PM Desk',
                                                'legalFramework': {
                                                    'enabled': True,
                                                    'lawDirectory': 'law',
                                                    'agentRules': 'agent-rules.md',
                                                    'systemPrompts': 'system-prompts',
                                                    'permissions': 'permissions'
                                                }
                                            }]
                                        }]
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
        shutil.rmtree(self.temp_dir)

    def test_agent_defaults_in_company_config(self):
        """会社レベルでエージェントデフォルト設定が定義できることをテスト"""
        # YAMLから会社設定を取得
        company = self.test_yaml_content['spec']['nations'][0]['cities'][0]['villages'][0]['companies'][0]
        
        # エージェントデフォルト設定の存在を確認
        assert 'agentDefaults' in company
        agent_defaults = company['agentDefaults']
        
        # エージェントタイプの確認
        assert agent_defaults['type'] == 'claude-code'
        
        # パーミッション設定の確認
        permissions = agent_defaults['permissions']
        assert 'allow' in permissions
        assert 'deny' in permissions
        assert 'Bash(npm run lint)' in permissions['allow']
        assert 'Bash(curl:*)' in permissions['deny']
        
        # 環境変数設定の確認
        env = agent_defaults['env']
        assert 'CLAUDE_CODE_ENABLE_TELEMETRY' in env
        assert env['CLAUDE_CODE_ENABLE_TELEMETRY'] == '1'

    def test_task_level_agent_config(self):
        """タスクレベルでエージェント設定が定義できることをテスト"""
        # YAMLからタスク設定を取得
        task = self.test_yaml_content['spec']['nations'][0]['cities'][0]['villages'][0]['companies'][0]['organizations'][0]['tasks'][0]
        
        # タスクレベルのエージェント設定の存在を確認
        assert 'agentConfig' in task
        agent_config = task['agentConfig']
        
        # エージェントタイプの確認
        assert agent_config['type'] == 'claude-code'
        
        # 追加パーミッションの確認
        additional_perms = agent_config['additionalPermissions']
        assert 'allow' in additional_perms
        assert 'Bash(npm run dev)' in additional_perms['allow']

    def test_claude_settings_json_creation(self):
        """Claude Code設定JSON作成のテスト"""
        from src.haconiwa.task.manager import TaskManager
        from src.haconiwa.agent.claude_integration import ClaudeCodeIntegration
        
        # TaskManagerとClaude統合を使用してテスト
        task_manager = TaskManager()
        claude_integration = ClaudeCodeIntegration()
        
        # テスト用のタスクディレクトリを作成
        task_dir = Path(self.temp_dir) / "test-task"
        task_dir.mkdir(parents=True)
        
        # 会社デフォルト設定とタスク設定をマージしてClaude設定を作成
        company_defaults = self.test_yaml_content['spec']['nations'][0]['cities'][0]['villages'][0]['companies'][0]['agentDefaults']
        task_config = self.test_yaml_content['spec']['nations'][0]['cities'][0]['villages'][0]['companies'][0]['organizations'][0]['tasks'][0]['agentConfig']
        
        # Claude設定JSON作成
        success = claude_integration.create_claude_settings(task_dir, company_defaults, task_config)
        assert success
        
        # .claude/settings.local.json の存在確認
        claude_settings_file = task_dir / ".claude" / "settings.local.json"
        assert claude_settings_file.exists()
        
        # JSONの内容確認
        with open(claude_settings_file, 'r', encoding='utf-8') as f:
            settings = json.load(f)
        
        # 基本構造の確認
        assert 'permissions' in settings
        assert 'env' in settings
        
        # パーミッション設定の確認
        permissions = settings['permissions']
        assert 'allow' in permissions
        assert 'deny' in permissions
        
        # デフォルト + 追加パーミッションがマージされていることを確認
        allow_perms = permissions['allow']
        assert 'Bash(npm run lint)' in allow_perms  # デフォルトから
        assert 'Bash(npm run dev)' in allow_perms   # タスクレベルから
        assert 'Read(package.json)' in allow_perms  # タスクレベルから
        
        # 拒否設定の確認
        deny_perms = permissions['deny']
        assert 'Bash(curl:*)' in deny_perms
        
        # 環境変数の確認
        env = settings['env']
        assert env['CLAUDE_CODE_ENABLE_TELEMETRY'] == '1'
        assert env['OTEL_METRICS_EXPORTER'] == 'otlp'

    def test_non_claude_code_agent_no_settings_created(self):
        """Claude Code以外のエージェントの場合は設定ファイルが作成されないことをテスト"""
        from src.haconiwa.agent.claude_integration import ClaudeCodeIntegration
        
        claude_integration = ClaudeCodeIntegration()
        
        # テスト用のタスクディレクトリを作成
        task_dir = Path(self.temp_dir) / "non-claude-task"
        task_dir.mkdir(parents=True)
        
        # 非Claude Codeエージェント設定
        non_claude_config = {
            'type': 'human-agent',
            'tools': ['text-editor', 'terminal']
        }
        
        # Claude設定作成を試行（但し、claude-code以外なので何もしない）
        success = claude_integration.create_claude_settings(task_dir, {}, non_claude_config)
        
        # Claude Code以外の場合は処理をスキップするため、Trueを返すが設定ファイルは作成されない
        assert success
        
        # .claude/settings.local.json が作成されていないことを確認
        claude_settings_file = task_dir / ".claude" / "settings.local.json"
        assert not claude_settings_file.exists()

    def test_apply_yaml_with_agent_attributes(self):
        """エージェント属性付きYAMLの適用テスト"""
        # この部分は実際にYAMLを適用して、Claude設定が正しく作成されることをテストする
        # 統合テストとして実装
        pass  # 実装は後で行う 