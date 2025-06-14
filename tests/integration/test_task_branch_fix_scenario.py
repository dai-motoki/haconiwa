#!/usr/bin/env python3
"""
タスクブランチ修正のシナリオテスト:
1. YAMLでdefaultBranch: "dev"を指定した設定を適用
2. リポジトリがクローンされ、devブランチがチェックアウトされることを確認
3. タスクワークツリーが全てdevブランチから作成されることを確認
4. 既存の誤ったブランチがあれば自動修正されることを確認
"""

import subprocess
import time
import json
import os
import sys
from pathlib import Path
from typing import List, Dict, Tuple, Optional
import pytest
import shutil
import tempfile
import yaml


class TaskBranchFixScenarioTest:
    """タスクブランチ修正のシナリオテスト"""
    
    def __init__(self):
        self.test_passed = False
        self.temp_dir = None
        self.yaml_file = None
        self.company_name = "test-task-branch-company"
        self.session_name = "test-task-branch-session"
        self.world_path = None
        
    def setup(self) -> bool:
        """テスト環境のセットアップ"""
        print("\n🔧 セットアップ中...")
        
        # 一時ディレクトリの作成
        self.temp_dir = tempfile.mkdtemp(prefix="haconiwa_test_")
        self.world_path = Path(self.temp_dir) / f"{self.company_name}-world"
        
        # テスト用YAML設定の作成
        self.yaml_file = Path(self.temp_dir) / "test-task-branch.yaml"
        
        yaml_content = {
            "apiVersion": "haconiwa.dev/v1",
            "kind": "Organization",
            "metadata": {
                "name": f"{self.company_name}-org"
            },
            "spec": {
                "companyName": "Test Task Branch Company",
                "industry": "Software Development",
                "basePath": str(self.temp_dir),
                "hierarchy": {
                    "departments": [
                        {
                            "id": "engineering",
                            "name": "Engineering Team",
                            "description": "Test engineering team",
                            "roles": [
                                {
                                    "roleType": "engineering",
                                    "title": "Senior Engineer",
                                    "agentId": "test-engineer-01",
                                    "responsibilities": ["Test development"]
                                },
                                {
                                    "roleType": "engineering",
                                    "title": "Engineer",
                                    "agentId": "test-engineer-02",
                                    "responsibilities": ["Test support"]
                                }
                            ]
                        }
                    ]
                }
            }
        }
        
        with open(self.yaml_file, 'w') as f:
            yaml.dump(yaml_content, f)
            f.write("\n---\n\n")
        
        # World設定を追加
        world_yaml = {
            "apiVersion": "haconiwa.dev/v1",
            "kind": "World",
            "metadata": {
                "name": "test-task-branch-world"
            },
            "spec": {
                "areas": [
                    {
                        "id": "tokyo",
                        "name": "Tokyo",
                        "villages": [
                            {
                                "id": "test-village",
                                "name": "Test Village",
                                "companies": [
                                    {
                                        "name": self.company_name,
                                        "grid": "2x2",
                                        "basePath": str(self.world_path),
                                        "organizationRef": f"{self.company_name}-org",
                                        "gitRepo": {
                                            "url": "https://github.com/dai-motoki/haconiwa",
                                            "defaultBranch": "dev",
                                            "auth": "https"
                                        },
                                        "buildings": [
                                            {
                                                "id": "test-building",
                                                "name": "Test Building",
                                                "floors": [
                                                    {
                                                        "id": "test-floor",
                                                        "name": "Test Floor",
                                                        "rooms": [
                                                            {
                                                                "id": "test-room",
                                                                "name": "Test Room",
                                                                "description": "Test room for branch testing"
                                                            }
                                                        ]
                                                    }
                                                ]
                                            }
                                        ]
                                    }
                                ]
                            }
                        ]
                    }
                ]
            }
        }
        
        with open(self.yaml_file, 'a') as f:
            yaml.dump(world_yaml, f)
            f.write("\n---\n\n")
        
        # タスク設定を追加
        tasks = [
            {"name": "task_test_branch_01", "description": "Test task 1", "branch": "test/branch-fix-01"},
            {"name": "task_test_branch_02", "description": "Test task 2", "branch": "test/branch-fix-02"},
            {"name": "task_test_branch_03", "description": "Test task 3", "branch": "test/branch-fix-03"}
        ]
        
        for task in tasks:
            task_yaml = {
                "apiVersion": "haconiwa.dev/v1",
                "kind": "Task",
                "metadata": {
                    "name": task["name"]
                },
                "spec": {
                    "taskId": task["name"],
                    "title": task["description"],
                    "description": f"Testing branch creation from dev branch",
                    "assignee": "test-engineer-01",
                    "spaceRef": self.company_name,
                    "priority": "medium",
                    "worktree": True,
                    "branch": task["branch"]
                }
            }
            
            with open(self.yaml_file, 'a') as f:
                yaml.dump(task_yaml, f)
                f.write("\n---\n\n")
        
        print(f"✅ テスト用YAML作成: {self.yaml_file}")
        return True
    
    def run_command(self, cmd: List[str], check: bool = True, cwd: Optional[str] = None) -> Tuple[int, str, str]:
        """コマンドを実行"""
        print(f"🔧 実行中: {' '.join(cmd)}")
        result = subprocess.run(cmd, capture_output=True, text=True, check=False, cwd=cwd)
        
        if check and result.returncode != 0:
            print(f"❌ コマンド失敗: {' '.join(cmd)}")
            print(f"   stderr: {result.stderr}")
            raise RuntimeError(f"コマンド失敗: {' '.join(cmd)}")
            
        return result.returncode, result.stdout, result.stderr
    
    def apply_yaml(self) -> bool:
        """YAML設定を適用"""
        print(f"\n📋 ステップ1: YAML設定の適用")
        
        # 作業ディレクトリを一時ディレクトリに変更
        original_cwd = os.getcwd()
        os.chdir(self.temp_dir)
        
        try:
            cmd = ["haconiwa", "apply", "-f", str(self.yaml_file), "--no-attach"]
            returncode, stdout, stderr = self.run_command(cmd)
            
            if returncode == 0:
                print("✅ YAMLの適用に成功")
                return True
            else:
                print(f"❌ YAMLの適用に失敗")
                return False
        finally:
            os.chdir(original_cwd)
    
    def wait_for_setup(self, timeout: int = 30) -> bool:
        """セットアップの完了を待機"""
        print(f"\n⏳ ステップ2: セットアップの完了を待機中...")
        
        start_time = time.time()
        while time.time() - start_time < timeout:
            # リポジトリディレクトリの存在を確認
            if self.world_path.exists() and (self.world_path / ".git").exists():
                print(f"✅ リポジトリのセットアップが完了")
                time.sleep(2)  # 完全に初期化されるまで待つ
                return True
            time.sleep(1)
        
        print(f"❌ セットアップがタイムアウト")
        return False
    
    def verify_default_branch(self) -> Dict[str, any]:
        """デフォルトブランチがdevになっているか確認"""
        print(f"\n🔍 ステップ3: デフォルトブランチの確認")
        
        main_repo_path = self.world_path / "main"
        
        if not main_repo_path.exists():
            print(f"❌ メインリポジトリが見つかりません: {main_repo_path}")
            return {"success": False, "branch": None}
        
        # 現在のブランチを確認
        cmd = ["git", "branch", "--show-current"]
        returncode, stdout, stderr = self.run_command(cmd, cwd=str(main_repo_path))
        
        current_branch = stdout.strip()
        print(f"   現在のブランチ: {current_branch}")
        
        # 最新コミットを確認
        cmd = ["git", "log", "--oneline", "-1"]
        returncode, stdout, stderr = self.run_command(cmd, cwd=str(main_repo_path))
        
        latest_commit = stdout.strip()
        print(f"   最新コミット: {latest_commit}")
        
        return {
            "success": current_branch == "dev",
            "branch": current_branch,
            "latest_commit": latest_commit
        }
    
    def verify_task_branches(self) -> Dict[str, any]:
        """タスクブランチが全てdevから作成されているか確認"""
        print(f"\n🔍 ステップ4: タスクブランチの確認")
        
        tasks_dir = self.world_path / "tasks"
        if not tasks_dir.exists():
            print(f"❌ タスクディレクトリが見つかりません: {tasks_dir}")
            return {"success": False, "tasks": {}}
        
        task_results = {}
        all_from_dev = True
        
        # 各タスクディレクトリを確認
        for task_dir in tasks_dir.iterdir():
            if task_dir.is_dir() and task_dir.name.startswith("task_"):
                print(f"\n   タスク: {task_dir.name}")
                
                # 現在のブランチを確認
                cmd = ["git", "branch", "--show-current"]
                returncode, stdout, stderr = self.run_command(cmd, cwd=str(task_dir), check=False)
                
                if returncode != 0:
                    print(f"     ⚠️  ブランチ情報を取得できません")
                    task_results[task_dir.name] = {
                        "branch": None,
                        "from_dev": False,
                        "error": stderr.strip()
                    }
                    all_from_dev = False
                    continue
                
                current_branch = stdout.strip()
                print(f"     ブランチ: {current_branch}")
                
                # ブランチの親を確認（merge-baseを使用）
                cmd = ["git", "merge-base", current_branch, "dev"]
                returncode, merge_base_dev, _ = self.run_command(cmd, cwd=str(task_dir), check=False)
                
                cmd = ["git", "merge-base", current_branch, "main"]
                returncode, merge_base_main, _ = self.run_command(cmd, cwd=str(task_dir), check=False)
                
                # 現在のブランチの最初のコミットを確認
                cmd = ["git", "log", "--oneline", "-1", "--reverse", current_branch]
                returncode, first_commit, _ = self.run_command(cmd, cwd=str(task_dir), check=False)
                
                # devブランチの最新コミットと比較
                cmd = ["git", "log", "--oneline", "-1", "dev"]
                returncode, dev_latest, _ = self.run_command(cmd, cwd=str(task_dir), check=False)
                
                from_dev = merge_base_dev.strip() == dev_latest.strip()[:7] if merge_base_dev else False
                
                task_results[task_dir.name] = {
                    "branch": current_branch,
                    "from_dev": from_dev,
                    "merge_base_dev": merge_base_dev.strip() if merge_base_dev else None,
                    "merge_base_main": merge_base_main.strip() if merge_base_main else None
                }
                
                if from_dev:
                    print(f"     ✅ devブランチから作成されています")
                else:
                    print(f"     ❌ devブランチから作成されていません")
                    all_from_dev = False
        
        return {
            "success": all_from_dev,
            "tasks": task_results,
            "total_tasks": len(task_results),
            "tasks_from_dev": sum(1 for t in task_results.values() if t.get("from_dev", False))
        }
    
    def simulate_wrong_branch_fix(self) -> Dict[str, any]:
        """既存の誤ったブランチの修正をシミュレート"""
        print(f"\n🔍 ステップ5: 誤ったブランチの自動修正を確認")
        
        # 一度スペースを削除
        print("   既存のスペースを削除中...")
        cmd = ["haconiwa", "space", "delete", "-c", self.session_name, "--clean-dirs", "--force"]
        self.run_command(cmd, check=False)
        
        # 少し待つ
        time.sleep(2)
        
        # 再度適用
        print("   再度YAML設定を適用...")
        if not self.apply_yaml():
            return {"success": False, "message": "再適用に失敗"}
        
        # セットアップ完了を待つ
        if not self.wait_for_setup():
            return {"success": False, "message": "セットアップタイムアウト"}
        
        # タスクブランチを再確認
        result = self.verify_task_branches()
        
        return {
            "success": result["success"],
            "message": "全てのタスクがdevブランチから作成されました" if result["success"] else "一部のタスクがdevブランチから作成されていません",
            "details": result
        }
    
    def run_assertions(self, results: Dict[str, any]) -> bool:
        """収集した結果に対してアサーション実行"""
        print(f"\n🧪 ステップ6: アサーションの実行")
        
        failures = []
        
        # デフォルトブランチの確認
        if not results.get("default_branch", {}).get("success"):
            failures.append(f"デフォルトブランチがdevではありません: {results['default_branch'].get('branch')}")
        
        # タスクブランチの確認
        task_results = results.get("task_branches", {})
        if not task_results.get("success"):
            failures.append(f"全てのタスクがdevブランチから作成されていません: {task_results.get('tasks_from_dev')}/{task_results.get('total_tasks')}")
        
        # 自動修正の確認
        fix_results = results.get("branch_fix", {})
        if not fix_results.get("success"):
            failures.append(f"ブランチの自動修正が機能していません: {fix_results.get('message')}")
        
        # 結果を表示
        if failures:
            print("❌ アサーション失敗:")
            for failure in failures:
                print(f"   - {failure}")
            return False
        else:
            print("✅ 全てのアサーションが成功!")
            return True
    
    def cleanup(self) -> bool:
        """テスト環境のクリーンアップ"""
        print(f"\n🧹 クリーンアップ中...")
        
        # haconiwaコマンドでクリーンアップ
        cmd = ["haconiwa", "space", "delete", "-c", self.session_name, "--clean-dirs", "--force"]
        self.run_command(cmd, check=False)
        
        # tmuxセッションを確実に削除
        cmd = ["tmux", "kill-session", "-t", self.session_name]
        self.run_command(cmd, check=False)
        
        # 一時ディレクトリを削除
        if self.temp_dir and Path(self.temp_dir).exists():
            shutil.rmtree(self.temp_dir)
            print(f"✅ 一時ディレクトリを削除: {self.temp_dir}")
        
        return True
    
    def run_full_scenario(self) -> bool:
        """完全なテストシナリオを実行"""
        print("🚀 タスクブランチ修正シナリオテスト開始")
        print("=" * 60)
        
        results = {}
        
        try:
            # セットアップ
            if not self.setup():
                return False
            
            # ステップ1: YAML適用
            if not self.apply_yaml():
                return False
            
            # ステップ2: セットアップ待機
            if not self.wait_for_setup():
                return False
            
            # ステップ3: デフォルトブランチ確認
            results['default_branch'] = self.verify_default_branch()
            
            # ステップ4: タスクブランチ確認
            results['task_branches'] = self.verify_task_branches()
            
            # ステップ5: ブランチ修正のシミュレート
            results['branch_fix'] = self.simulate_wrong_branch_fix()
            
            # ステップ6: アサーション実行
            self.test_passed = self.run_assertions(results)
            
            return self.test_passed
            
        except Exception as e:
            print(f"\n❌ テストが例外で失敗: {e}")
            import traceback
            traceback.print_exc()
            return False
            
        finally:
            # 必ずクリーンアップ
            self.cleanup()
            
            # 最終サマリー
            print("\n" + "=" * 60)
            if self.test_passed:
                print("✅ タスクブランチ修正シナリオテスト成功!")
            else:
                print("❌ タスクブランチ修正シナリオテスト失敗!")
            print("=" * 60)


def test_task_branch_fix():
    """タスクブランチ修正のpytestテスト関数"""
    test = TaskBranchFixScenarioTest()
    assert test.run_full_scenario()


if __name__ == "__main__":
    # 直接実行時
    test = TaskBranchFixScenarioTest()
    success = test.run_full_scenario()
    sys.exit(0 if success else 1)