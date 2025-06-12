#!/usr/bin/env python3
"""
haconiwaの包括的なシナリオテスト:
1. YAML設定の適用
2. 全ペインが正しく作成されたことを検証
3. ペインタイトルとウィンドウ構造の検証
4. タスク割り当ての検証
5. 全てをクリーンアップ
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


class HaconiwaScenarioTest:
    """haconiwaのフルライフサイクルテスト: apply -> verify -> cleanup"""
    
    def __init__(self, yaml_file: str, session_name: str):
        self.yaml_file = yaml_file
        self.session_name = session_name
        self.test_passed = False
        
    def run_command(self, cmd: List[str], check: bool = True) -> Tuple[int, str, str]:
        """コマンドを実行して (returncode, stdout, stderr) を返す"""
        print(f"🔧 実行中: {' '.join(cmd)}")
        result = subprocess.run(cmd, capture_output=True, text=True, check=False)
        
        if check and result.returncode != 0:
            print(f"❌ コマンド失敗: {' '.join(cmd)}")
            print(f"   stderr: {result.stderr}")
            raise RuntimeError(f"コマンド失敗: {' '.join(cmd)}")
            
        return result.returncode, result.stdout, result.stderr
    
    def apply_yaml(self) -> bool:
        """YAML設定を適用"""
        print(f"\n📋 ステップ1: YAML設定ファイルの適用: {self.yaml_file}")
        
        # --no-attachフラグを付けて適用
        cmd = ["haconiwa", "apply", "-f", self.yaml_file, "--no-attach"]
        returncode, stdout, stderr = self.run_command(cmd)
        
        if returncode == 0:
            print("✅ YAMLの適用に成功しました")
            print(f"   出力: {stdout}")
            return True
        else:
            print(f"❌ YAMLの適用に失敗しました")
            print(f"   stderr: {stderr}")
            return False
    
    def wait_for_session(self, timeout: int = 30) -> bool:
        """tmuxセッションの準備を待機"""
        print(f"\n⏳ ステップ2: セッション '{self.session_name}' の準備を待機中...")
        
        start_time = time.time()
        while time.time() - start_time < timeout:
            returncode, _, _ = self.run_command(
                ["tmux", "has-session", "-t", self.session_name], 
                check=False
            )
            if returncode == 0:
                print(f"✅ セッション '{self.session_name}' の準備が完了しました")
                time.sleep(2)  # 完全に初期化されるまで少し待つ
                return True
            time.sleep(1)
        
        print(f"❌ セッション '{self.session_name}' の待機がタイムアウトしました")
        return False
    
    def verify_windows_and_panes(self) -> Dict[str, any]:
        """ウィンドウとペインの構造を検証"""
        print(f"\n🔍 ステップ3: ウィンドウとペインの検証...")
        
        # Get window list
        cmd = ["tmux", "list-windows", "-t", self.session_name, "-F", 
               "#{window_index}:#{window_name}:#{window_panes}"]
        _, stdout, _ = self.run_command(cmd)
        
        windows = {}
        total_panes = 0
        
        for line in stdout.strip().split('\n'):
            if line:
                parts = line.split(':')
                if len(parts) >= 3:
                    window_index = parts[0]
                    window_name = parts[1]
                    pane_count = int(parts[2])
                    windows[window_index] = {
                        'name': window_name,
                        'pane_count': pane_count
                    }
                    total_panes += pane_count
                    print(f"   ウィンドウ {window_index} ({window_name}): {pane_count} ペイン")
        
        print(f"✅ 総ウィンドウ数: {len(windows)}, 総ペイン数: {total_panes}")
        
        return {
            'windows': windows,
            'total_panes': total_panes,
            'window_count': len(windows)
        }
    
    def verify_pane_titles(self) -> Dict[str, List[str]]:
        """各ウィンドウのペインタイトルを検証"""
        print(f"\n🔍 ステップ4: ペインタイトルの検証...")
        
        pane_titles = {}
        
        # Get all panes with their titles
        cmd = ["tmux", "list-panes", "-a", "-t", self.session_name, "-F",
               "#{window_index}:#{pane_index}:#{pane_title}:#{pane_current_path}"]
        _, stdout, _ = self.run_command(cmd)
        
        for line in stdout.strip().split('\n'):
            if line:
                parts = line.split(':', 3)
                if len(parts) >= 4:
                    window_index = parts[0]
                    pane_index = parts[1]
                    pane_title = parts[2]
                    pane_path = parts[3]
                    
                    if window_index not in pane_titles:
                        pane_titles[window_index] = []
                    
                    pane_titles[window_index].append({
                        'index': pane_index,
                        'title': pane_title,
                        'path': pane_path
                    })
        
        # サマリーを表示
        for window_index, panes in pane_titles.items():
            print(f"\n   ウィンドウ {window_index}:")
            titled_panes = [p for p in panes if p['title'] and p['title'] != 'tmux']
            print(f"     タイトル付きペイン: {len(titled_panes)}/{len(panes)}")
            
            # 最初のいくつかのタイトルを表示
            for pane in panes[:3]:
                if pane['title'] and pane['title'] != 'tmux':
                    print(f"     ペイン {pane['index']}: '{pane['title']}' 場所: {pane['path']}")
        
        return pane_titles
    
    def verify_task_assignments(self) -> Dict[str, any]:
        """ログファイルからタスク割り当てを検証"""
        print(f"\n🔍 ステップ5: タスク割り当ての検証...")
        
        task_assignments = {}
        tasks_dir = Path(f"./{self.session_name}/tasks")
        
        if not tasks_dir.exists():
            print(f"⚠️  タスクディレクトリが見つかりません: {tasks_dir}")
            return {}
        
        # 全てのエージェント割り当てファイルを検索
        assignment_files = list(tasks_dir.glob("*/.haconiwa/agent_assignment.json"))
        
        for assignment_file in assignment_files:
            try:
                with open(assignment_file, 'r') as f:
                    assignments = json.load(f)
                    for assignment in assignments:
                        agent_id = assignment.get('agent_id')
                        task_name = assignment.get('task_name')
                        if agent_id and task_name:
                            task_assignments[agent_id] = {
                                'task': task_name,
                                'status': assignment.get('status'),
                                'directory': assignment.get('task_directory')
                            }
                            print(f"   ✅ {agent_id} -> {task_name}")
            except Exception as e:
                print(f"   ⚠️  読み取りエラー {assignment_file}: {e}")
        
        print(f"✅ 見つかったタスク割り当て総数: {len(task_assignments)}")
        return task_assignments
    
    def verify_claude_commands(self) -> Dict[str, int]:
        """claudeコマンドがペインに送信されたことを検証"""
        print(f"\n🔍 ステップ6: claudeコマンドの検証...")
        
        # Check pane content for claude command
        cmd = ["tmux", "list-panes", "-a", "-t", self.session_name, "-F",
               "#{window_index}:#{pane_index}:#{pane_current_command}"]
        _, stdout, _ = self.run_command(cmd)
        
        claude_count = 0
        total_count = 0
        
        for line in stdout.strip().split('\n'):
            if line:
                total_count += 1
                parts = line.split(':', 2)
                if len(parts) >= 3:
                    current_command = parts[2]
                    if 'claude' in current_command.lower():
                        claude_count += 1
        
        print(f"✅ claudeコマンド: {claude_count}/{total_count} ペイン")
        
        return {
            'claude_count': claude_count,
            'total_panes': total_count,
            'percentage': (claude_count / total_count * 100) if total_count > 0 else 0
        }
    
    def run_assertions(self, results: Dict[str, any]) -> bool:
        """収集した結果に対してアサーションを実行"""
        print(f"\n🧪 ステップ7: アサーションの実行...")
        
        failures = []
        
        # ウィンドウ数をチェック (multiroomでは2であるべき)
        if results['structure']['window_count'] != 2:
            failures.append(f"期待値: 2ウィンドウ、実際: {results['structure']['window_count']}")
        
        # 総ペイン数をチェック (8x4グリッドでは32であるべき)
        if results['structure']['total_panes'] != 32:
            failures.append(f"期待値: 32ペイン、実際: {results['structure']['total_panes']}")
        
        # 各ウィンドウのペイン数をチェック (2ルームでそれぞれ16であるべき)
        for window_id, window_info in results['structure']['windows'].items():
            if window_info['pane_count'] != 16:
                failures.append(f"ウィンドウ {window_id} は {window_info['pane_count']} ペイン、期待値: 16")
        
        # タスク割り当てをチェック (いくつか存在するはず)
        if len(results['task_assignments']) == 0:
            failures.append("タスク割り当てが見つかりません")
        
        # ペインタイトルの存在をチェック
        total_titled_panes = 0
        for window_id, panes in results['pane_titles'].items():
            titled = [p for p in panes if p['title'] and p['title'] != 'tmux']
            total_titled_panes += len(titled)
        
        if total_titled_panes == 0:
            failures.append("ペインタイトルが見つかりません")
        
        # 結果を表示
        if failures:
            print("❌ アサーション失敗:")
            for failure in failures:
                print(f"   - {failure}")
            return False
        else:
            print("✅ 全てのアサーションが成功しました!")
            return True
    
    def cleanup(self) -> bool:
        """haconiwaコマンドを使用してセッションとディレクトリをクリーンアップ"""
        print(f"\n🧹 ステップ8: クリーンアップ...")
        
        # Use haconiwa space delete command with --clean-dirs flag
        cmd = ["haconiwa", "space", "delete", "-c", self.session_name, "--clean-dirs", "--force"]
        returncode, stdout, stderr = self.run_command(cmd, check=False)
        
        if returncode == 0:
            print(f"✅ haconiwaコマンドでクリーンアップに成功しました")
            print(f"   出力: {stdout}")
        else:
            print(f"⚠️  クリーンアップが部分的に失敗した可能性があります")
            print(f"   stderr: {stderr}")
            
            # フォールバックとして手動クリーンアップを試行
            print("   手動クリーンアップを試行中...")
            
            # Kill tmux session manually
            cmd = ["tmux", "kill-session", "-t", self.session_name]
            self.run_command(cmd, check=False)
            
            # Clean up directories manually
            dirs_to_clean = [
                f"./{self.session_name}",
                f"./{self.session_name}-desks",
                "./test-world-multiroom-tasks",
                "./test-multiroom-desks"
            ]
            
            for dir_path in dirs_to_clean:
                if Path(dir_path).exists():
                    try:
                        shutil.rmtree(dir_path)
                        print(f"   ✅ 手動で削除しました: {dir_path}")
                    except Exception as e:
                        print(f"   ⚠️  削除に失敗しました {dir_path}: {e}")
        
        return True
    
    def run_full_scenario(self) -> bool:
        """完全なテストシナリオを実行"""
        print(f"🚀 フルシナリオテスト開始: {self.yaml_file}")
        print("=" * 60)
        
        results = {}
        
        try:
            # ステップ1: YAML適用
            if not self.apply_yaml():
                return False
            
            # ステップ2: セッション待機
            if not self.wait_for_session():
                return False
            
            # ステップ3: 構造検証
            results['structure'] = self.verify_windows_and_panes()
            
            # ステップ4: ペインタイトル検証
            results['pane_titles'] = self.verify_pane_titles()
            
            # ステップ5: タスク割り当て検証
            results['task_assignments'] = self.verify_task_assignments()
            
            # ステップ6: claudeコマンド検証
            results['claude_commands'] = self.verify_claude_commands()
            
            # ステップ7: アサーション実行
            self.test_passed = self.run_assertions(results)
            
            return self.test_passed
            
        except Exception as e:
            print(f"\n❌ テストが例外で失敗しました: {e}")
            import traceback
            traceback.print_exc()
            return False
            
        finally:
            # 必ずクリーンアップ
            self.cleanup()
            
            # 最終サマリー
            print("\n" + "=" * 60)
            if self.test_passed:
                print("✅ シナリオテスト成功!")
            else:
                print("❌ シナリオテスト失敗!")
            print("=" * 60)


def test_multiroom_tasks_scenario():
    """タスク付きマルチルーム設定のテスト"""
    test = HaconiwaScenarioTest(
        yaml_file="test-multiroom-with-tasks.yaml",
        session_name="test-company-multiroom-tasks"
    )
    assert test.run_full_scenario()


def test_simple_dev_scenario():
    """シンプルな開発設定のテスト"""
    test = HaconiwaScenarioTest(
        yaml_file="haconiwa-simple-dev.yaml",
        session_name="haconiwa-dev-company"
    )
    assert test.run_full_scenario()


def test_world_scenario():
    """ワールド設定のテスト"""
    test = HaconiwaScenarioTest(
        yaml_file="haconiwa-world.yaml",
        session_name="synergy-development-company"
    )
    assert test.run_full_scenario()


if __name__ == "__main__":
    # コマンドライン引数に基づいて特定のテストを実行
    if len(sys.argv) > 1:
        yaml_file = sys.argv[1]
        
        # YAMLファイルからセッション名を決定
        session_name_map = {
            "test-multiroom-with-tasks.yaml": "test-company-multiroom-tasks",
            "haconiwa-simple-dev.yaml": "haconiwa-dev-company",
            "haconiwa-world.yaml": "synergy-development-company"
        }
        
        session_name = session_name_map.get(
            Path(yaml_file).name,
            Path(yaml_file).stem.replace('_', '-')
        )
        
        test = HaconiwaScenarioTest(yaml_file, session_name)
        success = test.run_full_scenario()
        sys.exit(0 if success else 1)
    else:
        # 全てのテストを実行
        print("全てのシナリオテストを実行中...\n")
        
        tests = [
            ("test-multiroom-with-tasks.yaml", "test-company-multiroom-tasks"),
            ("haconiwa-simple-dev.yaml", "haconiwa-dev-company"),
            ("haconiwa-world.yaml", "synergy-development-company")
        ]
        
        results = []
        for yaml_file, session_name in tests:
            if Path(yaml_file).exists():
                print(f"\n{'='*60}")
                print(f"テスト中: {yaml_file}")
                print(f"{'='*60}")
                
                test = HaconiwaScenarioTest(yaml_file, session_name)
                success = test.run_full_scenario()
                results.append((yaml_file, success))
                
                # テスト間で少し待つ
                time.sleep(3)
        
        # サマリーを表示
        print("\n" + "="*60)
        print("サマリー:")
        print("="*60)
        
        for yaml_file, success in results:
            status = "✅ 成功" if success else "❌ 失敗"
            print(f"{status}: {yaml_file}")
        
        all_passed = all(success for _, success in results)
        sys.exit(0 if all_passed else 1)