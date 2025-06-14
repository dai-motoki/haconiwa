"""
Test CRD (Custom Resource Definition) Parser
CRDパーサーのテストケース
"""

import pytest
import yaml
from pathlib import Path
from typing import Dict, Any
from unittest.mock import patch, mock_open

from haconiwa.core.crd.parser import CRDParser, CRDValidationError
from haconiwa.core.crd.models import (
    SpaceCRD, AgentCRD, TaskCRD, PathScanCRD, DatabaseCRD, CommandPolicyCRD, AICodeConfigCRD
)


class TestCRDParser:
    """CRDパーサーのテストクラス"""
    
    def setup_method(self):
        """各テストメソッドの前に実行される初期化"""
        self.parser = CRDParser()
    
    def test_parse_space_crd_valid(self):
        """有効なSpace CRDのパースをテスト"""
        space_yaml = """
apiVersion: haconiwa.dev/v1
kind: Space
metadata:
  name: dev-world
spec:
  nations:
  - id: jp
    name: 日本
    cities:
    - id: tokyo
      name: 東京
      villages:
      - id: chiyoda
        name: 千代田
        companies:
        - name: haconiwa-company
          grid: 8x4
          basePath: /desks/haconiwa-company
          gitRepo:
            url: https://github.com/example-org/haconiwa-monorepo.git
            defaultBranch: main
            auth: ssh
          organizations:
          - {id: "01", name: Frontend Dept., tasks: ["UI設計"]}
          - {id: "02", name: Backend Dept., tasks: ["API開発"]}
          buildings:
          - id: hq
            name: Main Building
            floors:
            - level: 1
              rooms:
              - id: room-01
                name: Alpha Room
                desks:
                - id: desk-0100
                  agent: {name: org01-pm-r1, role: pm, model: o3}
        """
        
        crd = self.parser.parse_yaml(space_yaml)
        
        assert isinstance(crd, SpaceCRD)
        assert crd.metadata.name == "dev-world"
        assert crd.spec.nations[0].id == "jp"
        assert crd.spec.nations[0].cities[0].villages[0].companies[0].name == "haconiwa-company"
        assert crd.spec.nations[0].cities[0].villages[0].companies[0].grid == "8x4"
        
    def test_parse_agent_crd_valid(self):
        """有効なAgent CRDのパースをテスト"""
        agent_yaml = """
apiVersion: haconiwa.dev/v1
kind: Agent
metadata:
  name: org02-pm
spec:
  role: pm
  model: o3
  spaceRef: haconiwa-company
  systemPromptPath: prompts/org02/system_prompt.txt
  env:
    OPENAI_API_KEY: ${OPENAI_API_KEY}
        """
        
        crd = self.parser.parse_yaml(agent_yaml)
        
        assert isinstance(crd, AgentCRD)
        assert crd.metadata.name == "org02-pm"
        assert crd.spec.role == "pm"
        assert crd.spec.model == "o3"
        assert crd.spec.spaceRef == "haconiwa-company"
        assert crd.spec.systemPromptPath == "prompts/org02/system_prompt.txt"
        
    def test_parse_task_crd_valid(self):
        """有効なTask CRDのパースをテスト"""
        task_yaml = """
apiVersion: haconiwa.dev/v1
kind: Task
metadata:
  name: feature-login
spec:
  branch: feature/login
  worktree: true
  assignee: org01-wk-a-r1
  spaceRef: haconiwa-company
  description: "ログイン機能の実装"
        """
        
        crd = self.parser.parse_yaml(task_yaml)
        
        assert isinstance(crd, TaskCRD)
        assert crd.metadata.name == "feature-login"
        assert crd.spec.branch == "feature/login"
        assert crd.spec.worktree is True
        assert crd.spec.assignee == "org01-wk-a-r1"
        assert crd.spec.spaceRef == "haconiwa-company"
        
    def test_parse_pathscan_crd_valid(self):
        """有効なPathScan CRDのパースをテスト"""
        pathscan_yaml = """
apiVersion: haconiwa.dev/v1
kind: PathScan
metadata:
  name: default-scan
spec:
  include: ["src/**/*.py"]
  exclude: [".venv/**", "tests/**"]
        """
        
        crd = self.parser.parse_yaml(pathscan_yaml)
        
        assert isinstance(crd, PathScanCRD)
        assert crd.metadata.name == "default-scan"
        assert "src/**/*.py" in crd.spec.include
        assert ".venv/**" in crd.spec.exclude
        
    def test_parse_database_crd_valid(self):
        """有効なDatabase CRDのパースをテスト"""
        database_yaml = """
apiVersion: haconiwa.dev/v1
kind: Database
metadata:
  name: local-postgres
spec:
  dsn: "postgresql://postgres:postgres@127.0.0.1:5432/app"
  useSSL: false
        """
        
        crd = self.parser.parse_yaml(database_yaml)
        
        assert isinstance(crd, DatabaseCRD)
        assert crd.metadata.name == "local-postgres"
        assert "postgresql://" in crd.spec.dsn
        assert crd.spec.useSSL is False
        
    def test_parse_commandpolicy_crd_valid(self):
        """有効なCommandPolicy CRDのパースをテスト"""
        policy_yaml = """
apiVersion: haconiwa.dev/v1
kind: CommandPolicy
metadata:
  name: default-command-whitelist
spec:
  global:
    docker: [build, pull, run, images, ps]
    kubectl: [get, describe, apply, logs]
    git: [clone, pull, commit, push, worktree]
  roles:
    pm:
      allow: {kubectl: [scale, rollout]}
    worker:
      deny: {docker: [system prune]}
        """
        
        crd = self.parser.parse_yaml(policy_yaml)
        
        assert isinstance(crd, CommandPolicyCRD)
        assert crd.metadata.name == "default-command-whitelist"
        assert "docker" in crd.spec.global_commands
        assert "build" in crd.spec.global_commands["docker"]
        assert "pm" in crd.spec.roles
        assert "kubectl" in crd.spec.roles["pm"].allow
        
    def test_parse_invalid_api_version(self):
        """無効なAPIバージョンでエラーとなることをテスト"""
        invalid_yaml = """
apiVersion: invalid/v1
kind: Space
metadata:
  name: test
spec: {}
        """
        
        with pytest.raises(CRDValidationError, match="Unsupported apiVersion"):
            self.parser.parse_yaml(invalid_yaml)
            
    def test_parse_invalid_kind(self):
        """無効なkindでエラーとなることをテスト"""
        invalid_yaml = """
apiVersion: haconiwa.dev/v1
kind: InvalidKind
metadata:
  name: test
spec: {}
        """
        
        with pytest.raises(CRDValidationError, match="Unsupported kind"):
            self.parser.parse_yaml(invalid_yaml)
            
    def test_parse_missing_metadata(self):
        """metadataが欠けている場合のエラーテスト"""
        invalid_yaml = """
apiVersion: haconiwa.dev/v1
kind: Space
spec: {}
        """
        
        with pytest.raises(CRDValidationError, match="metadata is required"):
            self.parser.parse_yaml(invalid_yaml)
            
    def test_parse_missing_spec(self):
        """specが欠けている場合のエラーテスト"""
        invalid_yaml = """
apiVersion: haconiwa.dev/v1
kind: Space
metadata:
  name: test
        """
        
        with pytest.raises(CRDValidationError, match="spec is required"):
            self.parser.parse_yaml(invalid_yaml)
            
    def test_parse_multi_document_yaml(self):
        """複数ドキュメントYAMLのパースをテスト"""
        multi_yaml = """
apiVersion: haconiwa.dev/v1
kind: PathScan
metadata:
  name: default-scan
spec:
  include: ["src/**/*.py"]
  exclude: [".venv/**"]
---
apiVersion: haconiwa.dev/v1
kind: Database
metadata:
  name: local-postgres
spec:
  dsn: "postgresql://postgres:postgres@127.0.0.1:5432/app"
  useSSL: false
        """
        
        crds = self.parser.parse_multi_yaml(multi_yaml)
        
        assert len(crds) == 2
        assert isinstance(crds[0], PathScanCRD)
        assert isinstance(crds[1], DatabaseCRD)
        
    def test_parse_file(self):
        """ファイルからのパースをテスト（mock使用）"""
        yaml_content = """
apiVersion: haconiwa.dev/v1
kind: Agent
metadata:
  name: test-agent
spec:
  role: worker
  model: gpt-4o
        """
        
        with patch("builtins.open", mock_open(read_data=yaml_content)):
            crd = self.parser.parse_file(Path("test.yaml"))
            
        assert isinstance(crd, AgentCRD)
        assert crd.metadata.name == "test-agent"
        
    def test_validate_space_crd_required_fields(self):
        """Space CRDの必須フィールド検証をテスト"""
        invalid_space_yaml = """
apiVersion: haconiwa.dev/v1
kind: Space
metadata:
  name: test
spec:
  nations: []
        """
        
        with pytest.raises(CRDValidationError, match="nations cannot be empty"):
            self.parser.parse_yaml(invalid_space_yaml)
            
    def test_validate_agent_crd_role_values(self):
        """Agent CRDの役割値検証をテスト"""
        invalid_agent_yaml = """
apiVersion: haconiwa.dev/v1
kind: Agent
metadata:
  name: test-agent
spec:
  role: invalid_role
  model: o3
        """
        
        with pytest.raises(CRDValidationError, match="role must be 'pm' or 'worker'"):
            self.parser.parse_yaml(invalid_agent_yaml)
            
    def test_validate_task_crd_branch_format(self):
        """Task CRDのブランチ名形式検証をテスト"""
        invalid_task_yaml = """
apiVersion: haconiwa.dev/v1
kind: Task
metadata:
  name: test-task
spec:
  branch: "invalid branch name with spaces"
  worktree: true
        """
        
        with pytest.raises(CRDValidationError, match="branch name contains invalid characters"):
            self.parser.parse_yaml(invalid_task_yaml)
            
    def test_parse_aicode_config_crd_valid(self):
        """有効なAICodeConfig CRDのパースをテスト"""
        aicode_yaml = """
apiVersion: haconiwa.dev/v1
kind: AICodeConfig
metadata:
  name: claude-config
spec:
  provider: claude
  claude:
    settingsFile: ./claude-settings/settings.local.json
    guidelinesFile: ./claude-settings/CLAUDE.md
  targetCompany: test-company
        """
        
        crd = self.parser.parse_yaml(aicode_yaml)
        
        assert isinstance(crd, AICodeConfigCRD)
        assert crd.metadata.name == "claude-config"
        assert crd.spec.provider == "claude"
        assert crd.spec.claude.settingsFile == "./claude-settings/settings.local.json"
        assert crd.spec.claude.guidelinesFile == "./claude-settings/CLAUDE.md"
        assert crd.spec.targetCompany == "test-company"
        
    def test_parse_aicode_config_invalid_provider(self):
        """無効なプロバイダーでのAICodeConfigパースをテスト"""
        invalid_yaml = """
apiVersion: haconiwa.dev/v1
kind: AICodeConfig
metadata:
  name: invalid-config
spec:
  provider: invalid-provider
  targetCompany: test-company
        """
        
        # パース自体は成功するが、プロバイダーが無効
        crd = self.parser.parse_yaml(invalid_yaml)
        assert isinstance(crd, AICodeConfigCRD)
        assert crd.spec.provider == "invalid-provider"
        assert crd.spec.claude is None  # claudeプロバイダーではないのでNone
        
    def test_parse_aicode_config_missing_claude_fields(self):
        """Claude設定が不完全なAICodeConfigのパースをテスト"""
        invalid_yaml = """
apiVersion: haconiwa.dev/v1
kind: AICodeConfig
metadata:
  name: incomplete-config
spec:
  provider: claude
  claude:
    settingsFile: ./settings.json
    # guidelinesFile is missing
  targetCompany: test-company
        """
        
        # Pydanticの検証でエラーになる
        with pytest.raises(Exception):  # ValidationError or similar
            self.parser.parse_yaml(invalid_yaml) 