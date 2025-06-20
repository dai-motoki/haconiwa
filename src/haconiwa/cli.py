import typer
from typing import Optional, List
from pathlib import Path
import logging
import sys
import yaml

from haconiwa.core.cli import core_app
from haconiwa.world.cli import world_app
from haconiwa.space.cli import company_app as original_company_app
from haconiwa.resource.cli import resource_app as original_resource_app
from haconiwa.agent.cli import agent_app
from haconiwa.task.cli import task_app
from haconiwa.watch.cli import watch_app
from haconiwa.monitor import TmuxMonitor
from haconiwa.scan.cli import scan_app

# Import new v1.0 components
from haconiwa.core.crd.parser import CRDParser, CRDValidationError
from haconiwa.core.applier import CRDApplier
from haconiwa.core.policy.engine import PolicyEngine
from haconiwa.space.manager import SpaceManager

app = typer.Typer(
    name="haconiwa",
    help="AI協調開発支援Python CLIツール v1.0 - 宣言型YAML + tmux + Git worktree",
    no_args_is_help=True
)

def setup_logging(verbose: bool):
    level = logging.DEBUG if verbose else logging.INFO
    logging.basicConfig(
        level=level,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    )

def version_callback(value: bool):
    if value:
        from haconiwa import __version__
        typer.echo(f"haconiwa version {__version__}")
        raise typer.Exit()

@app.callback()
def main(
    verbose: bool = typer.Option(False, "--verbose", "-v", help="詳細なログ出力を有効化"),
    config: Optional[Path] = typer.Option(None, "--config", "-c", help="設定ファイルのパス"),
    version: bool = typer.Option(False, "--version", callback=version_callback, help="バージョン情報を表示"),
):
    """箱庭 (haconiwa) v1.0 - 宣言型YAML + tmux + Git worktreeフレームワーク"""
    setup_logging(verbose)
    if config:
        try:
            from haconiwa.core.config import load_config
            load_config(config)
        except Exception as e:
            typer.echo(f"設定ファイルの読み込みに失敗: {e}", err=True)
            sys.exit(1)

# =====================================================================
# v1.0 新コマンド
# =====================================================================

@app.command()
def init(
    force: bool = typer.Option(False, "--force", "-f", help="既存設定を上書き")
):
    """Haconiwa設定を初期化"""
    config_dir = Path.home() / ".haconiwa"
    config_file = config_dir / "config.yaml"
    
    if config_file.exists() and not force:
        overwrite = typer.confirm("設定が既に存在します。上書きしますか？")
        if not overwrite:
            typer.echo("❌ 初期化がキャンセルされました")
            return
    
    # Create config directory
    config_dir.mkdir(parents=True, exist_ok=True)
    
    # Create default configuration
    default_config = {
        "version": "v1",
        "default_base_path": "./workspaces",
        "tmux": {
            "default_session_prefix": "haconiwa",
            "default_layout": "tiled"
        },
        "policy": {
            "default_policy": "default-command-whitelist"
        }
    }
    
    with open(config_file, 'w') as f:
        yaml.dump(default_config, f, default_flow_style=False)
    
    typer.echo(f"✅ Haconiwa設定を初期化しました: {config_file}")

@app.command()
def apply(
    file: str = typer.Option(..., "-f", "--file", help="YAML ファイルパス"),
    dry_run: bool = typer.Option(False, "--dry-run", help="適用をシミュレート"),
    force_clone: bool = typer.Option(False, "--force-clone", help="既存ディレクトリを確認なしで削除してGitクローン"),
    no_attach: bool = typer.Option(False, "--no-attach", help="適用後にセッションにアタッチしない"),
    room: str = typer.Option("room-01", "-r", "--room", help="アタッチするルーム"),
    env: List[str] = typer.Option([], "--env", help="環境変数ファイル（複数指定可）"),
):
    """CRD定義ファイルを適用"""
    file_path = Path(file)
    
    if not file_path.exists():
        typer.echo(f"❌ ファイルが見つかりません: {file}", err=True)
        raise typer.Exit(1)
    
    # By default, attach unless --no-attach is specified
    should_attach = not no_attach
    
    parser = CRDParser()
    applier = CRDApplier()
    
    # Register applier in __main__ for TaskManager to access
    import __main__
    setattr(__main__, "_current_applier", applier)
    
    # Set force_clone flag in applier
    applier.force_clone = force_clone
    
    # Set env files in applier
    if env:
        applier.env_files = env
    
    if dry_run:
        typer.echo("🔍 ドライランモード - 変更は適用されません")
        if should_attach:
            typer.echo(f"🔗 適用後に会社に入室します (ルーム: {room})")
        else:
            typer.echo("🔗 会社に入室しません (--no-attach が指定されています)")
        if env:
            typer.echo(f"🔧 環境変数ファイルを使用します: {', '.join(env)}")
    
    def extract_all_company_names(crd):
        """Extract all company names from a Space CRD"""
        company_names = []
        if crd.kind == "Space":
            for nation in crd.spec.nations:
                for city in nation.cities:
                    for village in city.villages:
                        for company in village.companies:
                            company_names.append(company.name)
        return company_names
    
    created_sessions = []  # Track created sessions for attach
    
    try:
        # Check if file contains multiple documents
        with open(file_path, 'r') as f:
            content = f.read()
        
        if '---' in content:
            # Multi-document YAML
            crds = parser.parse_multi_yaml(content)
            typer.echo(f"📄 {file} に {len(crds)} 個の設定を発見しました")
            
            if not dry_run:
                results = applier.apply_multiple(crds)
                success_count = sum(results)
                typer.echo(f"✅ {success_count}/{len(crds)} 個の設定を正常に適用しました")
                
                # Extract session names from applied Space CRDs
                for i, (crd, result) in enumerate(zip(crds, results)):
                    if result and crd.kind == "Space":
                        company_names = extract_all_company_names(crd)
                        created_sessions.extend(company_names)
            else:
                for crd in crds:
                    typer.echo(f"  - {crd.kind}: {crd.metadata.name}")
                    if crd.kind == "Space":
                        company_names = extract_all_company_names(crd)
                        created_sessions.extend(company_names)
        else:
            # Single document
            crd = parser.parse_file(file_path)
            typer.echo(f"📄 設定を発見: {crd.kind}/{crd.metadata.name}")
            
            if not dry_run:
                success = applier.apply(crd)
                if success:
                    typer.echo("✅ 1個の設定を正常に適用しました")
                    
                    # Extract session names for Space CRD
                    if crd.kind == "Space":
                        company_names = extract_all_company_names(crd)
                        created_sessions.extend(company_names)
                else:
                    typer.echo("❌ 設定の適用に失敗しました", err=True)
                    raise typer.Exit(1)
            else:
                if crd.kind == "Space":
                    company_names = extract_all_company_names(crd)
                    created_sessions.extend(company_names)
        
        # Auto-attach to session if requested
        if should_attach and created_sessions and not dry_run:
            session_name = created_sessions[0]  # Attach to first created session
            typer.echo(f"\n🔗 会社に自動入室中: {session_name} (ルーム: {room})")
            
            # Import subprocess for tmux attach
            import subprocess
            import os
            
            try:
                # Check if session exists
                result = subprocess.run(['tmux', 'has-session', '-t', session_name], 
                                       capture_output=True, text=True)
                if result.returncode != 0:
                    typer.echo(f"❌ 入室用の会社 '{session_name}' が見つかりません", err=True)
                    raise typer.Exit(1)
                
                # Switch to specific room first
                space_manager = SpaceManager()
                space_manager.switch_to_room(session_name, room)
                
                # Attach to session (this will transfer control to tmux)
                typer.echo(f"🚀 {session_name}/{room} に入室中...")
                typer.echo("💡 tmuxセッションからデタッチするには Ctrl+B の後 D を押してください")
                typer.echo(f"🗑️ 削除するには: haconiwa space delete -c {session_name} --clean-dirs --force")
                
                # Use execvp to replace current process with tmux attach
                os.execvp('tmux', ['tmux', 'attach-session', '-t', session_name])
                
            except FileNotFoundError:
                typer.echo("❌ tmuxがインストールされていないかPATHに見つかりません", err=True)
                raise typer.Exit(1)
            except Exception as e:
                typer.echo(f"❌ 会社への入室に失敗しました: {e}", err=True)
                raise typer.Exit(1)
        
        elif should_attach and not created_sessions:
            typer.echo("⚠️ 会社が設立されませんでした。入室できません")
        elif not should_attach and created_sessions:
            if len(created_sessions) == 1:
                typer.echo(f"\n💡 会社を設立しました: {created_sessions[0]}")
                typer.echo(f"   入室するには: haconiwa space attach -c {created_sessions[0]} -r {room}")
                typer.echo(f"   削除するには: haconiwa space delete -c {created_sessions[0]} --clean-dirs --force")
            else:
                typer.echo(f"\n💡 {len(created_sessions)}社の会社を設立しました:")
                for i, company_name in enumerate(created_sessions, 1):
                    typer.echo(f"   {i}. {company_name}")
                typer.echo(f"\n   入室例: haconiwa space attach -c {created_sessions[0]} -r {room}")
                typer.echo(f"   削除例: haconiwa space delete -c {created_sessions[0]} --clean-dirs --force")
    
    except CRDValidationError as e:
        typer.echo(f"❌ バリデーションエラー: {e}", err=True)
        raise typer.Exit(1)
    except Exception as e:
        typer.echo(f"❌ エラー: {e}", err=True)
        raise typer.Exit(1)

# =====================================================================
# Space コマンド（company のリネーム・拡張）
# =====================================================================

space_app = typer.Typer(name="space", help="World/Company/Room/Desk 管理")

@space_app.command("ls")
def space_list():
    """Space一覧を表示"""
    space_manager = SpaceManager()
    spaces = space_manager.list_spaces()
    
    if not spaces:
        typer.echo("運営中の会社がありません")
        return
    
    typer.echo("📋 運営中の会社:")
    for space in spaces:
        typer.echo(f"  🏢 {space['name']} - {space['status']} ({space['panes']} デスク, {space['rooms']} ルーム)")

@space_app.command("list")
def space_list_alias():
    """Space一覧を表示 (lsのalias)"""
    space_list()

@space_app.command("start")
def space_start(
    company: str = typer.Option(..., "-c", "--company", help="Company name")
):
    """Company セッションを開始"""
    space_manager = SpaceManager()
    success = space_manager.start_company(company)
    
    if success:
        typer.echo(f"✅ 会社を開業しました: {company}")
    else:
        typer.echo(f"❌ 会社の開業に失敗しました: {company}", err=True)
        raise typer.Exit(1)

@space_app.command("stop")
def space_stop(
    company: str = typer.Option(..., "-c", "--company", help="Company name")
):
    """Company セッションを停止"""
    space_manager = SpaceManager()
    success = space_manager.cleanup_session(company)
    
    if success:
        typer.echo(f"✅ 会社を休業しました: {company}")
    else:
        typer.echo(f"❌ 会社の休業に失敗しました: {company}", err=True)
        raise typer.Exit(1)

@space_app.command("attach")
def space_attach(
    company: str = typer.Option(..., "-c", "--company", help="Company name"),
    room: str = typer.Option("room-01", "-r", "--room", help="Room ID")
):
    """特定のRoom に接続"""
    space_manager = SpaceManager()
    success = space_manager.attach_to_room(company, room)
    
    if success:
        typer.echo(f"✅ {company}/{room} に入室しました")
    else:
        typer.echo(f"❌ {company}/{room} への入室に失敗しました", err=True)
        raise typer.Exit(1)

@space_app.command("clone")
def space_clone(
    company: str = typer.Option(..., "-c", "--company", help="Company name")
):
    """Git リポジトリをclone"""
    space_manager = SpaceManager()
    success = space_manager.clone_repository(company)
    
    if success:
        typer.echo(f"✅ リポジトリをクローンしました: {company}")
    else:
        typer.echo(f"❌ リポジトリのクローンに失敗しました: {company}", err=True)
        raise typer.Exit(1)

@space_app.command("run")
def space_run(
    company: str = typer.Option(..., "-c", "--company", help="Company name"),
    command: str = typer.Option(None, "--cmd", help="Command to run in all panes"),
    claude_code: bool = typer.Option(False, "--claude-code", help="Run 'claude' command in all panes"),
    room: str = typer.Option(None, "-r", "--room", help="Target specific room (default: all rooms)"),
    dry_run: bool = typer.Option(False, "--dry-run", help="Show what would be executed without running"),
    confirm: bool = typer.Option(True, "--confirm/--no-confirm", help="Ask for confirmation before execution")
):
    """全ペインまたは指定ルームでコマンドを実行"""
    
    # Determine command to run
    if claude_code:
        actual_command = "claude"
    elif command:
        actual_command = command
    else:
        typer.echo("❌ --cmd または --claude-code のいずれかを指定してください", err=True)
        raise typer.Exit(1)
    
    # Import subprocess for tmux interaction
    import subprocess
    
    # Check if session exists
    try:
        result = subprocess.run(['tmux', 'has-session', '-t', company], 
                               capture_output=True, text=True)
        if result.returncode != 0:
            typer.echo(f"❌ 会社 '{company}' が見つかりません", err=True)
            raise typer.Exit(1)
    except FileNotFoundError:
        typer.echo("❌ tmuxがインストールされていないかPATHに見つかりません", err=True)
        raise typer.Exit(1)
    
    # Get list of panes
    try:
        if room:
            # Get panes for specific room (window)
            space_manager = SpaceManager()
            window_id = space_manager._get_window_id_for_room(room)
            result = subprocess.run(['tmux', 'list-panes', '-t', f'{company}:{window_id}', '-F', 
                                   '#{window_index}:#{pane_index}'], 
                                   capture_output=True, text=True)
            target_desc = f"ルーム {room} (ウィンドウ {window_id})"
        else:
            # Get all panes in session
            result = subprocess.run(['tmux', 'list-panes', '-t', company, '-F', 
                                   '#{window_index}:#{pane_index}', '-a'], 
                                   capture_output=True, text=True)
            target_desc = "全ルーム"
        
        if result.returncode != 0:
            typer.echo(f"❌ 作業デスクの取得に失敗しました: {result.stderr}", err=True)
            raise typer.Exit(1)
        
        panes = [line.strip() for line in result.stdout.strip().split('\n') if line.strip()]
        
        if not panes:
            typer.echo(f"❌ {target_desc} に作業デスクが見つかりません", err=True)
            raise typer.Exit(1)
        
        typer.echo(f"🎯 ターゲット: {company} ({target_desc})")
        typer.echo(f"📊 {len(panes)} 個の作業デスクを発見しました")
        typer.echo(f"🚀 コマンド: {actual_command}")
        
        if dry_run:
            typer.echo("\n🔍 ドライラン - 実行されるコマンド:")
            for i, pane in enumerate(panes[:5]):  # Show first 5
                typer.echo(f"  デスク {pane}: tmux send-keys -t {company}:{pane} '{actual_command}' Enter")
            if len(panes) > 5:
                typer.echo(f"  ... 他 {len(panes) - 5} 個のデスク")
            return
        
        # Confirmation
        if confirm:
            confirm_msg = f"{company} の {len(panes)} 個の作業デスクで '{actual_command}' を実行しますか？"
            if not typer.confirm(confirm_msg):
                typer.echo("❌ 操作がキャンセルされました")
                raise typer.Exit(0)
        
        # Execute command in all panes
        typer.echo(f"\n🚀 {len(panes)} 個の作業デスクで '{actual_command}' を実行中...")
        
        failed_panes = []
        for i, pane in enumerate(panes):
            try:
                # Send command to pane
                cmd = ['tmux', 'send-keys', '-t', f'{company}:{pane}', actual_command, 'Enter']
                result = subprocess.run(cmd, capture_output=True, text=True, timeout=5)
                
                if result.returncode == 0:
                    typer.echo(f"  ✅ デスク {pane}: コマンド送信完了")
                else:
                    typer.echo(f"  ❌ デスク {pane}: 失敗 - {result.stderr}")
                    failed_panes.append(pane)
                    
            except subprocess.TimeoutExpired:
                typer.echo(f"  ⏱️ デスク {pane}: タイムアウト")
                failed_panes.append(pane)
            except Exception as e:
                typer.echo(f"  ❌ デスク {pane}: エラー - {e}")
                failed_panes.append(pane)
        
        # Summary
        success_count = len(panes) - len(failed_panes)
        typer.echo(f"\n📊 実行完了: {success_count}/{len(panes)} 個のデスクが成功")
        
        if failed_panes:
            typer.echo(f"❌ 失敗したデスク: {', '.join(failed_panes)}")
            raise typer.Exit(1)
        else:
            typer.echo("✅ 全デスクの実行が成功しました")
            
    except Exception as e:
        typer.echo(f"❌ Error executing command: {e}", err=True)
        raise typer.Exit(1)

@space_app.command("delete")
def space_delete(
    company: str = typer.Option(..., "-c", "--company", help="Company name"),
    clean_dirs: bool = typer.Option(False, "--clean-dirs", help="Remove related directories"),
    force: bool = typer.Option(False, "--force", help="Force delete without confirmation")
):
    """Company セッションとリソースを削除"""
    
    # Import subprocess for tmux interaction
    import subprocess
    import shutil
    from pathlib import Path
    
    from haconiwa.space.manager import SpaceManager
    
    # Check if session exists
    try:
        result = subprocess.run(['tmux', 'has-session', '-t', company], 
                               capture_output=True, text=True)
        session_exists = result.returncode == 0
    except FileNotFoundError:
        typer.echo("❌ tmuxがインストールされていないかPATHに見つかりません", err=True)
        raise typer.Exit(1)
    
    if not session_exists:
        typer.echo(f"⚠️ 会社 '{company}' が登録されていません")
        if not clean_dirs:
            typer.echo("💡 オフィスを片付けるには --clean-dirs を使用してください")
            return
    
    # Confirmation
    if not force:
        operations = []
        if session_exists:
            operations.append(f"会社の運営を終了: {company}")
        if clean_dirs:
            operations.append(f"会社のオフィスを解体: ./{company}")
        
        if operations:
            typer.echo("以下を実行します:")
            for op in operations:
                typer.echo(f"  - {op}")
            
            if not typer.confirm("続行しますか？"):
                typer.echo("❌ 操作がキャンセルされました")
                raise typer.Exit(0)
    
    try:
        # Kill tmux session
        if session_exists:
            result = subprocess.run(['tmux', 'kill-session', '-t', company], 
                                   capture_output=True, text=True)
            if result.returncode == 0:
                typer.echo(f"✅ 会社の運営を終了しました: {company}")
            else:
                typer.echo(f"❌ 会社の運営終了に失敗しました: {result.stderr}", err=True)
        
        # Clean directories if requested
        if clean_dirs:
            import glob
            import os
            # Standard directory patterns
            dirs_to_clean = [
                f"./{company}",
                f"./{company}-desks",
                f"./test-{company}",
                f"./test-{company}-desks"
            ]
            
            # Additional flexible patterns for multiroom/space directories
            additional_patterns = [
                f"./test-*-desks",      # test-multiroom-desks, test-xxx-desks
                f"./*-{company}*",      # multiroom-company variants
                f"./test-*{company}*",  # test-multiroom-company variants  
                f"./{company}*",        # company variations
            ]
            
            # Add matched directories from glob patterns
            for pattern in additional_patterns:
                matched_dirs = glob.glob(pattern)
                for matched_dir in matched_dirs:
                    if matched_dir not in dirs_to_clean:
                        dirs_to_clean.append(matched_dir)
        
        # Clean up git worktrees first (before removing directories)
        if dirs_to_clean:
            cleaned_worktrees = []
            for dir_path in dirs_to_clean:
                if Path(dir_path).exists():
                    # Check if it's a git repository with worktrees
                    git_dir = Path(dir_path) / ".git"
                    if git_dir.exists():
                        try:
                            # List and remove worktrees
                            result = subprocess.run(['git', '-C', dir_path, 'worktree', 'list', '--porcelain'], 
                                                   capture_output=True, text=True)
                            if result.returncode == 0:
                                worktrees = []
                                current_worktree = {}
                                for line in result.stdout.strip().split('\n'):
                                    if line.startswith('worktree '):
                                        if current_worktree and current_worktree.get('worktree'):
                                            worktrees.append(current_worktree)
                                        current_worktree = {'worktree': line.split(' ', 1)[1]}
                                    elif line.startswith('branch '):
                                        current_worktree['branch'] = line.split(' ', 1)[1]
                                    elif line == 'bare':
                                        current_worktree['bare'] = True
                                    elif line == 'detached':
                                        current_worktree['detached'] = True
                                
                                # Add the last worktree
                                if current_worktree and current_worktree.get('worktree'):
                                    worktrees.append(current_worktree)
                                
                                # Remove non-main worktrees
                                for worktree in worktrees:
                                    wt_path = worktree['worktree']
                                    if wt_path != dir_path and Path(wt_path).exists():
                                        try:
                                            subprocess.run(['git', '-C', dir_path, 'worktree', 'remove', wt_path, '--force'], 
                                                         capture_output=True, text=True, check=True)
                                            cleaned_worktrees.append(wt_path)
                                            typer.echo(f"✅ 作業スペースを片付けました: {wt_path}")
                                        except subprocess.CalledProcessError as e:
                                            typer.echo(f"⚠️ 作業スペースの片付けに失敗しました {wt_path}: {e}")
                        except Exception as e:
                            typer.echo(f"⚠️ {dir_path} の作業スペースチェックエラー: {e}")
            
            # Remove directories
            cleaned_dirs = []
            for dir_path in dirs_to_clean:
                path_obj = Path(dir_path)
                if path_obj.exists():
                    # Skip if it's not a directory (e.g., YAML files)
                    if not path_obj.is_dir():
                        continue
                    try:
                        shutil.rmtree(dir_path)
                        cleaned_dirs.append(dir_path)
                        typer.echo(f"✅ オフィスを解体しました: {dir_path}")
                    except Exception as e:
                        typer.echo(f"❌ {dir_path} の解体に失敗しました: {e}", err=True)
            
            # Summary
            if cleaned_dirs or cleaned_worktrees:
                typer.echo(f"🗑️ {len(cleaned_dirs)} 個のオフィスと {len(cleaned_worktrees)} 個の作業スペースを片付けました")
        
        # Remove from SpaceManager tracking
        space_manager = SpaceManager()
        if hasattr(space_manager, 'active_sessions') and company in space_manager.active_sessions:
            del space_manager.active_sessions[company]
            typer.echo(f"✅ 会社台帳から除名しました: {company}")
        
        typer.echo(f"✅ 会社を正常に解散しました: {company}")
        
    except Exception as e:
        typer.echo(f"❌ 解散中にエラーが発生しました: {e}", err=True)
        raise typer.Exit(1)

# =====================================================================
# Tool コマンド（resource のリネーム・拡張）
# =====================================================================

tool_app = typer.Typer(name="tool", help="開発ツール連携機能")

@tool_app.command()
def list():
    """利用可能なツール一覧を表示"""
    typer.echo("🛠️ 利用可能なツール:")
    typer.echo("  📦 claude-code - Claude Code SDK連携")
    typer.echo("  📊 file-scanner - ファイルパススキャン")
    typer.echo("  🗄️ db-scanner - データベーススキャン")
    typer.echo("\n💡 ツールをインストールするには 'haconiwa tool install <tool>' を使用してください")

@tool_app.command()
def install(
    tool_name: str = typer.Argument(..., help="Tool name to install")
):
    """ツールをインストール"""
    supported_tools = ["claude-code", "file-scanner", "db-scanner"]
    
    if tool_name not in supported_tools:
        typer.echo(f"❌ 不明なツール: {tool_name}", err=True)
        typer.echo(f"サポートされているツール: {', '.join(supported_tools)}", err=True)
        raise typer.Exit(1)
    
    typer.echo(f"📦 {tool_name} をインストール中...")
    
    if tool_name == "claude-code":
        typer.echo("  → claude-code-sdk パッケージ")
        typer.echo("  → 実行: pip install claude-code-sdk")
    
    typer.echo(f"✅ ツール '{tool_name}' のインストール手順を提供しました")

@tool_app.command()
def configure(
    tool_name: str = typer.Argument(..., help="Tool name to configure")
):
    """ツールの設定"""
    if tool_name == "claude-code":
        typer.echo("🔧 claude-codeを設定中...")
        typer.echo("  環境変数を設定: ANTHROPIC_API_KEY=your-api-key")
        typer.echo("  またはコマンド実行時に --api-key フラグを渡してください")
    else:
        typer.echo(f"❌ {tool_name} の設定は利用できません", err=True)

# Import parallel-dev subcommands (use simplified version)
from haconiwa.tool.parallel_dev_simple import parallel_dev_app

# Add parallel-dev as a subcommand
tool_app.add_typer(parallel_dev_app, name="parallel-dev")

@tool_app.command()
def scan_filepath(
    pathscan: str = typer.Option(..., "--scan-filepath", help="PathScan CRD名"),
    yaml_output: bool = typer.Option(False, "--yaml", help="YAML形式で出力"),
    json_output: bool = typer.Option(False, "--json", help="JSON形式で出力")
):
    """ファイルパススキャンを実行"""
    # Mock implementation - would integrate with actual PathScanner
    typer.echo(f"🔍 PathScanでファイルをスキャン中: {pathscan}")
    
    # Simulate file scan results
    files = ["src/main.py", "src/utils.py", "src/config.py"]
    
    if yaml_output:
        typer.echo("files:")
        for file in files:
            typer.echo(f"  - {file}")
    elif json_output:
        import json
        typer.echo(json.dumps({"files": files}, indent=2))
    else:
        typer.echo("📁 発見されたファイル:")
        for file in files:
            typer.echo(f"  📄 {file}")

@tool_app.command()
def scan_db(
    database: str = typer.Option(..., "--scan-db", help="Database CRD名"),
    yaml_output: bool = typer.Option(False, "--yaml", help="YAML形式で出力"),
    json_output: bool = typer.Option(False, "--json", help="JSON形式で出力")
):
    """データベーススキャンを実行"""
    # Mock implementation - would integrate with actual DatabaseScanner
    typer.echo(f"🔍 データベースをスキャン中: {database}")
    
    # Simulate database scan results
    tables = ["users", "posts", "comments"]
    
    if yaml_output:
        typer.echo("tables:")
        for table in tables:
            typer.echo(f"  - {table}")
    elif json_output:
        import json
        typer.echo(json.dumps({"tables": tables}, indent=2))
    else:
        typer.echo("🗄️ 発見されたテーブル:")
        for table in tables:
            typer.echo(f"  📋 {table}")

# =====================================================================
# Policy コマンド（新規）
# =====================================================================

policy_app = typer.Typer(name="policy", help="CommandPolicy 管理")

@policy_app.command("ls")
def policy_list():
    """Policy一覧を表示"""
    policy_engine = PolicyEngine()
    policies = policy_engine.list_policies()
    
    if not policies:
        typer.echo("ポリシーが見つかりません")
        return
    
    typer.echo("🛡️ 利用可能なポリシー:")
    for policy in policies:
        active_mark = "🟢" if policy.get("active", False) else "⚪"
        typer.echo(f"  {active_mark} {policy['name']} ({policy['type']})")

@policy_app.command("test")
def policy_test(
    target: str = typer.Argument(..., help="Test target (agent)"),
    agent_id: str = typer.Argument(..., help="Agent ID"),
    cmd: str = typer.Option(..., "--cmd", help="Command to test")
):
    """コマンドがpolicyで許可されるかテスト"""
    if target != "agent":
        typer.echo("❌ 'agent' ターゲットのみサポートされています", err=True)
        raise typer.Exit(1)
    
    policy_engine = PolicyEngine()
    allowed = policy_engine.test_command(agent_id, cmd)
    
    if allowed:
        typer.echo(f"✅ エージェント {agent_id} のコマンドが許可されました: {cmd}")
    else:
        typer.echo(f"❌ エージェント {agent_id} のコマンドが拒否されました: {cmd}")

@policy_app.command("delete")
def policy_delete(
    name: str = typer.Argument(..., help="Policy name to delete")
):
    """Policy を削除"""
    policy_engine = PolicyEngine()
    success = policy_engine.delete_policy(name)
    
    if success:
        typer.echo(f"✅ ポリシーを削除しました: {name}")
    else:
        typer.echo(f"❌ ポリシーが見つかりません: {name}", err=True)
        raise typer.Exit(1)

# =====================================================================
# Monitor コマンド（新規）
# =====================================================================

monitor_app = typer.Typer(name="monitor", help="tmux multi-agent environment monitoring")

@monitor_app.callback(invoke_without_command=True)
def monitor_main(
    ctx: typer.Context,
    company: str = typer.Option(..., "-c", "--company", help="Company name (tmux session name)"),
    window: Optional[str] = typer.Option(None, "-w", "--window", help="Specific window number or name (default: all)"),
    columns: Optional[List[str]] = typer.Option(None, "--columns", help="Columns to display"),
    refresh: float = typer.Option(2.0, "-r", "--refresh", help="Refresh interval in seconds"),
    japanese: bool = typer.Option(False, "-j", "--japanese", help="Display in Japanese"),
):
    """
    Monitor tmux multi-agent development environment in real-time.
    
    Display real-time information about AI agents, CPU usage, and task status
    for each pane in the tmux session. Supports multiple windows with
    separate tables for each room.
    
    Examples:
      haconiwa monitor -c my-company
      haconiwa monitor -c my-company -w frontend --japanese  
      haconiwa monitor -c my-company --columns pane agent cpu status
    """
    
    # If a subcommand was invoked, let it handle the execution
    if ctx.invoked_subcommand is not None:
        return
    
    # Default columns if not specified
    if columns is None:
        columns = ["room", "pane", "title", "task", "claude", "agent", "cpu", "status"]
    
    # Validate columns
    valid_columns = ["room", "window", "pane", "title", "task", "parent", "claude", "agent", "cpu", "memory", "uptime", "status"]
    for col in columns:
        if col not in valid_columns:
            typer.echo(f"❌ Invalid column: {col}", err=True)
            typer.echo(f"Valid columns: {', '.join(valid_columns)}", err=True)
            raise typer.Exit(1)
    
    # Parse window parameter (could be number or name)
    window_param = None
    if window is not None:
        if window.isdigit():
            window_param = int(window)
        else:
            window_param = window
    
    # Check if tmux session exists
    import subprocess
    try:
        result = subprocess.run(['tmux', 'has-session', '-t', company], 
                               capture_output=True, text=True)
        if result.returncode != 0:
            typer.echo(f"❌ 会社 '{company}' が見つかりません", err=True)
            typer.echo("💡 利用可能なセッションを確認するには 'haconiwa space list' を使用してください", err=True)
            raise typer.Exit(1)
    except FileNotFoundError:
        typer.echo("❌ tmuxがインストールされていないかPATHに見つかりません", err=True)
        raise typer.Exit(1)
    
    # Check dependencies
    try:
        import rich
        import psutil
    except ImportError as e:
        missing_pkg = str(e).split("'")[1] if "'" in str(e) else str(e)
        typer.echo(f"❌ 必要なパッケージが見つかりません: {missing_pkg}", err=True)
        typer.echo("インストールするには: pip install rich psutil", err=True)
        raise typer.Exit(1)
    
    # Start monitoring
    try:
        monitor = TmuxMonitor(
            session_name=company,
            japanese=japanese,
            columns=columns,
            window=window_param
        )
        
        # Display startup message
        lang_info = " (日本語)" if japanese else ""
        window_info = f" (ウィンドウ: {window})" if window else " (全ウィンドウ)"
        typer.echo(f"🚀 {company}{window_info}{lang_info} の監視を開始します")
        typer.echo("停止するにはCtrl+Cを押してください")
        
        # Run monitoring
        monitor.run_monitor(refresh_rate=refresh)
        
    except KeyboardInterrupt:
        typer.echo("\n✅ 監視を停止しました")
    except Exception as e:
        typer.echo(f"\n❌ エラー: {e}", err=True)
        raise typer.Exit(1)

@monitor_app.command("help")
def monitor_help():
    """Show detailed help for monitor command"""
    help_text = """
🔍 Haconiwa Monitor - Real-time tmux multi-agent monitoring

USAGE:
  haconiwa monitor -c <company> [OPTIONS]
  haconiwa mon -c <company> [OPTIONS]     # Short alias

BASIC EXAMPLES:
  haconiwa monitor -c my-company                    # Monitor all windows
  haconiwa monitor -c my-company --japanese         # Japanese UI
  haconiwa monitor -c my-company -w 0               # Monitor window 0 only
  haconiwa monitor -c my-company -w frontend        # Monitor "frontend" window

COLUMN CUSTOMIZATION:
  haconiwa monitor -c my-company --columns pane title claude agent cpu status
  haconiwa monitor -c my-company --columns pane agent status  # Minimal view

PERFORMANCE TUNING:  
  haconiwa monitor -c my-company -r 0.5             # High-frequency updates
  haconiwa monitor -c my-company -r 5               # Low-frequency updates

AVAILABLE COLUMNS:
  room     - Room/Window name
  window   - Window number
  pane     - Pane number  
  title    - Task title
  parent   - Parent process ID
  claude   - Provider AI status (✓/✗)
  agent    - Custom agent ID
  cpu      - CPU usage with visual bar
  memory   - Memory usage
  uptime   - Process uptime
  status   - Agent status (仕事待ち/作業中/多忙)

TIPS:
  • Use --columns to customize display
  • Use -w to focus on specific room/window
  • Use --japanese for Japanese interface
  • Adjust --refresh for performance vs update frequency
  """
    typer.echo(help_text)

# =====================================================================
# アプリケーション登録
# =====================================================================

# v1.0 新コマンド
app.add_typer(space_app, name="space")
app.add_typer(tool_app, name="tool")
app.add_typer(policy_app, name="policy")
app.add_typer(monitor_app, name="monitor")
app.add_typer(monitor_app, name="mon")  # Short alias for monitor
app.add_typer(scan_app, name="scan")  # Universal AI model search

# 既存コマンド（一部deprecated）
app.add_typer(core_app, name="core")
app.add_typer(world_app, name="world")
app.add_typer(agent_app, name="agent")
app.add_typer(task_app, name="task")
app.add_typer(watch_app, name="watch")

# 後方互換性のため残す（deprecation warning付き）
app.add_typer(original_company_app, name="company", deprecated=True)
app.add_typer(original_resource_app, name="resource", deprecated=True)

if __name__ == "__main__":
    app()