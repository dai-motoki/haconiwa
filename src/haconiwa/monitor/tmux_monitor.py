"""
tmux multi-agent environment real-time monitoring tool
Uses rich library for colorful display
"""

import subprocess
import time
import psutil
import json
from pathlib import Path
from rich.console import Console
from rich.live import Live
from rich.table import Table
from rich.panel import Panel
from rich.layout import Layout
from rich.text import Text
from datetime import datetime
import re


class TmuxMonitor:
    """tmux multi-agent environment monitor"""
    
    def __init__(self, session_name, japanese=False, columns=None, window=None):
        self.session_name = session_name
        self.window = window
        self.console = Console()
        self.japanese = japanese
        self.columns = columns if columns else ["pane", "title", "task", "claude", "agent", "cpu", "memory", "status"]
        self.agent_mappings = self.load_agent_mappings()
        
        # 日本語テキスト
        self.texts = {
            'en': {
                'pane': 'Pane',
                'title': 'Title', 
                'task': 'Task',
                'parent': 'Parent',
                'claude': 'Provider AI',
                'agent': 'Agent Name',
                'room': 'Room',
                'cpu': 'CPU%',
                'memory': 'Memory',
                'uptime': 'Uptime',
                'status': 'Status',
                'window': 'Window',
                'no_claude': 'No Claude',
                'no_process': 'No process',
                'inactive': 'inactive',
                'summary': 'Summary',
                'active_panes': 'Active Panes',
                'average_cpu': 'Average CPU',
                'total_memory': 'Total Memory',
                'last_update': 'Last Update',
                'system_status': 'System Status',
                'monitoring_stopped': 'Monitoring stopped by user',
                'starting_monitor': 'Starting tmux monitor for session',
                'press_ctrl_c': 'Press Ctrl+C to stop',
                'waiting_for_work': 'Waiting',
                'working': 'Working',
                'busy': 'Busy',
                'no_task': '-'
            },
            'ja': {
                'pane': 'ペイン',
                'title': 'タイトル',
                'task': 'タスク',
                'parent': '親プロセス', 
                'claude': 'プロバイダAI',
                'agent': 'エージェント名',
                'room': '部屋',
                'cpu': '稼働率',
                'memory': 'メモリ',
                'uptime': '稼働時間',
                'status': 'ステータス',
                'window': 'ウィンドウ',
                'no_claude': 'Claude無し',
                'no_process': 'プロセス無し',
                'inactive': '非アクティブ',
                'summary': 'サマリー',
                'active_panes': 'アクティブペイン',
                'average_cpu': '平均稼働率',
                'total_memory': '合計メモリ',
                'last_update': '最終更新',
                'system_status': 'システム状態',
                'monitoring_stopped': 'ユーザーによりモニタリングが停止されました',
                'starting_monitor': 'tmuxモニターを開始します セッション',
                'press_ctrl_c': 'Ctrl+Cで停止',
                'waiting_for_work': '仕事待ち',
                'working': '作業中',
                'busy': '多忙',
                'no_task': '-'
            }
        }
        
        self.lang = 'ja' if japanese else 'en'
    
    def load_agent_mappings(self):
        """エージェントIDマッピングをdesk_mappings.jsonから読み込み"""
        try:
            # セッション名からワールドディレクトリ名を推測
            # haconiwa-dev-company -> haconiwa-dev-world
            world_dir = self.session_name.replace('-company', '-world')
            
            # 複数の可能なパスを試行
            possible_paths = [
                f"{world_dir}/.haconiwa/desk_mappings.json",
                f"{self.session_name}/.haconiwa/desk_mappings.json",
                f".haconiwa/desk_mappings.json"
            ]
            
            for path in possible_paths:
                if Path(path).exists():
                    with open(path, 'r', encoding='utf-8') as f:
                        mappings = json.load(f)
                        # ペインインデックス順にエージェントIDをマッピング
                        agent_map = {}
                        for i, mapping in enumerate(mappings):
                            agent_map[i] = mapping.get('agent_id', f'unknown-{i}')
                        return agent_map
            
            # マッピングファイルが見つからない場合のデフォルト
            return {}
            
        except Exception as e:
            print(f"Warning: Could not load agent mappings: {e}")
            return {}
    
    def get_agent_id_for_pane(self, window_index, pane_index):
        """ウィンドウとペインインデックスに対応するエージェントIDを取得"""
        # window:pane の形式でキーを作成するか、従来通りpane_indexのみを使用
        # とりあえず従来通りの形式を維持（将来的に拡張可能）
        agent_key = f"{window_index}:{pane_index}" if window_index is not None else pane_index
        return self.agent_mappings.get(agent_key, self.agent_mappings.get(pane_index, f"agent-{window_index}:{pane_index}"))
    
    def get_text(self, key):
        """言語に応じたテキストを取得"""
        return self.texts[self.lang].get(key, key)
    
    def get_status_by_cpu(self, cpu_percent):
        """CPU使用率に基づいてステータスを決定"""
        if cpu_percent <= 2.0:
            return self.get_text('waiting_for_work')
        elif cpu_percent <= 20.0:
            return self.get_text('working')
        else:
            return self.get_text('busy')
    
    def extract_task_name(self, pane_title):
        """ペインタイトルからタスク名を抽出"""
        # "[Task: task_name]" パターンを探す
        match = re.search(r'\[Task:\s*([^\]]+)\]', pane_title)
        if match:
            return match.group(1).strip()
        return None
    
    def extract_task_id_from_path(self, current_path):
        """現在のパスからタスクIDを抽出"""
        if not current_path:
            return None
        
        # パスからtask_で始まるディレクトリ名を探す
        path_parts = Path(current_path).parts
        for part in path_parts:
            if part.startswith('task_') and not part == 'tasks':
                return part
        
        return None
    
    def get_tmux_windows_info(self):
        """tmux window情報を取得"""
        try:
            result = subprocess.run([
                'tmux', 'list-windows', '-t', self.session_name, '-F', '#{window_index}:#{window_name}'
            ], capture_output=True, text=True, timeout=1)
            
            windows = {}
            if result.returncode == 0:
                for line in result.stdout.strip().split('\n'):
                    if ':' in line:
                        parts = line.split(':', 1)
                        if len(parts) >= 2:
                            windows[int(parts[0])] = parts[1]
            return windows
        except Exception:
            return {}
    
    def get_tmux_panes_info(self):
        """tmuxペイン情報を高速取得（複数window対応）"""
        try:
            panes = []
            
            if self.window is not None:
                # 特定のwindowのみ取得
                result = subprocess.run([
                    'tmux', 'list-panes', '-t', f'{self.session_name}:{self.window}', 
                    '-F', str(self.window) + ':#{pane_index}:#{pane_title}:#{pane_pid}:#{pane_current_path}'
                ], capture_output=True, text=True, timeout=1)
                
                if result.returncode == 0:
                    for line in result.stdout.strip().split('\n'):
                        if ':' in line:
                            parts = line.split(':', 4)
                            if len(parts) >= 5:
                                panes.append({
                                    'window': int(parts[0]),
                                    'index': int(parts[1]),
                                    'title': parts[2],
                                    'pid': int(parts[3]) if parts[3].isdigit() else 0,
                                    'current_path': parts[4]
                                })
            else:
                # 全windowのペイン情報を取得
                # まずwindowの一覧を取得
                windows_result = subprocess.run([
                    'tmux', 'list-windows', '-t', self.session_name, '-F', '#{window_index}'
                ], capture_output=True, text=True, timeout=1)
                
                if windows_result.returncode == 0:
                    for window_index in windows_result.stdout.strip().split('\n'):
                        if window_index.isdigit():
                            # 各windowのペイン情報を取得
                            result = subprocess.run([
                                'tmux', 'list-panes', '-t', f'{self.session_name}:{window_index}', 
                                '-F', window_index + ':#{pane_index}:#{pane_title}:#{pane_pid}:#{pane_current_path}'
                            ], capture_output=True, text=True, timeout=1)
                            
                            if result.returncode == 0:
                                for line in result.stdout.strip().split('\n'):
                                    if ':' in line and line.strip():
                                        parts = line.split(':', 4)
                                        if len(parts) >= 5:
                                            panes.append({
                                                'window': int(parts[0]),
                                                'index': int(parts[1]),
                                                'title': parts[2],
                                                'pid': int(parts[3]) if parts[3].isdigit() else 0,
                                                'current_path': parts[4]
                                            })
            
            return panes
        except Exception:
            return []

    def get_claude_processes(self):
        """Claudeプロセス情報を高速取得（psutil使用・CPU測定改良版）"""
        try:
            claude_processes = {}
            
            # 全プロセスを高速スキャン
            for proc in psutil.process_iter(['pid', 'name', 'cmdline']):
                try:
                    proc_info = proc.info
                    pid = proc_info['pid']
                    name = proc_info['name']
                    cmdline = proc_info['cmdline'] or []
                    cmdline_str = ' '.join(cmdline)
                    
                    # Claudeプロセスの判定
                    if self.is_claude_process_fast(name, cmdline_str):
                        # プロセス詳細情報を取得
                        process = psutil.Process(pid)
                        
                        # CPU使用率を取得（interval=Noneで前回からの差分を使用）
                        cpu_percent = process.cpu_percent()
                        
                        # 初回は0が返ってくるので、0の場合は瞬間的な測定
                        if cpu_percent == 0.0:
                            cpu_percent = process.cpu_percent(interval=0.1)
                        
                        claude_processes[pid] = {
                            'cpu_percent': cpu_percent,
                            'memory_percent': process.memory_percent(),
                            'memory_info': process.memory_info(),
                            'name': name,
                            'cmdline': cmdline
                        }
                        
                except (psutil.NoSuchProcess, psutil.AccessDenied, psutil.ZombieProcess):
                    continue
            
            return claude_processes
            
        except Exception:
            return {}

    def is_claude_process_fast(self, comm, args):
        """高速Claudeプロセス判定"""
        comm_lower = comm.lower()
        args_lower = args.lower()
        
        # 直接claudeコマンドで実行されている場合
        if 'claude' in comm_lower:
            return True
            
        # Node.jsでclaude関連が実行されている場合
        if 'node' in comm_lower:
            return any(keyword in args_lower for keyword in ['claude', 'anthropic'])
            
        return False
    
    def get_cpu_color(self, cpu_percent):
        """CPU使用率に応じた色を返す（暖色系）"""
        if cpu_percent >= 80:
            return "red"          # 高負荷: 赤
        elif cpu_percent >= 50:
            return "yellow"       # 中負荷: 黄色
        elif cpu_percent >= 20:
            return "bright_yellow"  # 軽負荷: 明るい黄色
        else:
            return "magenta"      # アイドル: マゼンタ
    
    def create_cpu_bar(self, cpu_percent, width=20):
        """文字ベースのCPUバーを作成（%数字を左配置、バー位置を揃える）"""
        filled = int((cpu_percent / 100) * width)
        bar = "█" * filled + "░" * (width - filled)
        color = self.get_cpu_color(cpu_percent)
        # %数字を固定幅（6文字）で左配置し、その後にバーを表示
        percentage_text = f"{cpu_percent:5.1f}%"
        return f"{percentage_text} [{color}]{bar}[/{color}]"
    
    def create_monitoring_table(self):
        """単一のモニタリングテーブルを作成（部屋名を列として表示）"""
        windows_info = self.get_tmux_windows_info()
        panes = self.get_tmux_panes_info()
        claude_processes = self.get_claude_processes()
        
        # 会社名をタイトルに含める
        title_text = f"💼  会社名: [bold green]{self.session_name}[/bold green]"
        table = Table(title=title_text, show_header=True, header_style="bold magenta", expand=True)
        
        # 列の定義（roomを追加）
        column_configs = {
            'room': {"header": self.get_text('room'), "style": "bright_cyan", "width": 12},
            'window': {"header": self.get_text('window'), "style": "bright_yellow", "width": 8},
            'pane': {"header": self.get_text('pane'), "style": "dim", "width": 6},
            'title': {"header": self.get_text('title'), "style": "cyan", "min_width": 20},
            'task': {"header": self.get_text('task'), "style": "bright_yellow", "min_width": 20},
            'parent': {"header": self.get_text('parent'), "style": "dim", "width": 12},
            'claude': {"header": self.get_text('claude'), "style": "bright_green", "width": 15},
            'agent': {"header": self.get_text('agent'), "style": "bright_cyan", "width": 20},
            'cpu': {"header": self.get_text('cpu'), "justify": "left", "width": 60},
            'memory': {"header": self.get_text('memory'), "justify": "right", "width": 10},
            'uptime': {"header": self.get_text('uptime'), "justify": "center", "width": 10},
            'status': {"header": self.get_text('status'), "justify": "center", "width": 10}
        }
        
        # 選択された列のみ追加
        for col_name in self.columns:
            if col_name in column_configs:
                config = column_configs[col_name]
                header = config.pop("header")
                table.add_column(header, **config)
        
        # 各ペインの行を追加（全windowの全ペイン）
        for pane in panes:
            window_index = pane['window']
            pane_index = pane['index']
            pane_title = pane['title']
            pane_pid = pane['pid']
            pane_current_path = pane.get('current_path', '')
            window_name = windows_info.get(window_index, f"Window-{window_index}")
            
            # そのペインのPIDに対応するClaudeプロセスを探す
            claude_process = None
            for pid, proc_info in claude_processes.items():
                # ペインのPIDまたは子プロセスをチェック
                if pid == pane_pid or self.is_child_of_pane(pid, pane_pid):
                    claude_process = proc_info
                    break
            
            row_data = []
            
            for col_name in self.columns:
                if col_name == 'room':
                    row_data.append(f"[bright_cyan]{window_name}[/bright_cyan]")
                elif col_name == 'window':
                    row_data.append(str(window_index))
                elif col_name == 'pane':
                    row_data.append(str(pane_index))
                elif col_name == 'title':
                    # エージェント名とカレントディレクトリを表示
                    agent_id = self.get_agent_id_for_pane(window_index, pane_index)
                    
                    # パスから最後のディレクトリ名を取得
                    if pane_current_path:
                        # ホームディレクトリを~に置換
                        home_path = str(Path.home())
                        display_path = pane_current_path.replace(home_path, '~')
                        # 最後のディレクトリ名のみを取得
                        dir_name = Path(pane_current_path).name
                    else:
                        dir_name = "unknown"
                    
                    # エージェント名 - ディレクトリ名の形式で表示
                    display_title = f"{agent_id} - {dir_name}"
                    row_data.append(display_title)
                elif col_name == 'task':
                    # まずペインタイトルからタスク名を抽出を試みる
                    task_name = self.extract_task_name(pane_title)
                    
                    # ペインタイトルにタスク名がない場合は、パスから抽出
                    if not task_name:
                        task_id = self.extract_task_id_from_path(pane_current_path)
                        task_name = task_id
                    
                    if task_name:
                        row_data.append(f"[bright_yellow]{task_name}[/bright_yellow]")
                    else:
                        row_data.append(f"[dim]{self.get_text('no_task')}[/dim]")
                elif col_name == 'parent':
                    row_data.append(str(pane_pid))
                elif col_name == 'claude':
                    if claude_process:
                        row_data.append("[green]✓[/green] Claude")
                    else:
                        row_data.append(f"[red]✗[/red] {self.get_text('no_claude')}")
                elif col_name == 'agent':
                    # カスタムエージェントIDを表示
                    agent_id = self.get_agent_id_for_pane(window_index, pane_index)
                    row_data.append(f"[bright_cyan]{agent_id}[/bright_cyan]")
                elif col_name == 'cpu':
                    if claude_process:
                        cpu_display = self.create_cpu_bar(claude_process['cpu_percent'], width=45)
                        row_data.append(cpu_display)
                    else:
                        row_data.append("N/A")
                elif col_name == 'memory':
                    if claude_process:
                        memory_mb = claude_process['memory_info'].rss / 1024 / 1024
                        row_data.append(f"{memory_mb:.1f}MB")
                    else:
                        row_data.append("N/A")
                elif col_name == 'uptime':
                    row_data.append("N/A")  # uptimeは簡略化
                elif col_name == 'status':
                    if claude_process:
                        status_text = self.get_status_by_cpu(claude_process['cpu_percent'])
                        if claude_process['cpu_percent'] <= 2.0:
                            status_color = "magenta"
                        elif claude_process['cpu_percent'] <= 20.0:
                            status_color = "yellow"
                        else:
                            status_color = "red"
                        row_data.append(f"[{status_color}]{status_text}[/{status_color}]")
                    else:
                        row_data.append(f"[dim]{self.get_text('no_process')}[/dim]")
            
            table.add_row(*row_data)
        
        return table

    def is_child_of_pane(self, process_pid, pane_pid):
        """プロセスがペインの子プロセスかチェック（psutil高速版）"""
        try:
            process = psutil.Process(process_pid)
            # 直接の親をチェック
            if process.ppid() == pane_pid:
                return True
            # 祖父プロセスもチェック（1レベル上）
            parent = psutil.Process(process.ppid())
            if parent.ppid() == pane_pid:
                return True
            return False
        except (psutil.NoSuchProcess, psutil.AccessDenied):
            return False
    
    def create_summary_panel(self):
        """サマリーパネルを作成"""
        panes = self.get_tmux_panes_info()
        claude_processes = self.get_claude_processes()
        
        active_count = 0
        total_cpu = 0
        total_memory = 0
        
        for pane in panes:
            pane_pid = pane['pid']
            # ペインに関連するClaudeプロセスを探す
            for pid, proc_info in claude_processes.items():
                if pid == pane_pid or self.is_child_of_pane(pid, pane_pid):
                    active_count += 1
                    total_cpu += proc_info['cpu_percent']
                    total_memory += proc_info['memory_info'].rss / 1024 / 1024
                    break
        
        avg_cpu = total_cpu / active_count if active_count > 0 else 0
        
        summary_text = f"""
        {self.get_text('active_panes')}: {active_count}/{len(panes)}
        {self.get_text('average_cpu')}: {avg_cpu:.1f}%
        {self.get_text('total_memory')}: {total_memory:.1f}MB
        {self.get_text('last_update')}: {datetime.now().strftime('%H:%M:%S')}
        """
        
        company_title = f"💼  会社名: [bold green]{self.session_name}[/bold green]"
        return Panel(summary_text, title=company_title, border_style="blue")
    
    def run_monitor(self, refresh_rate=2):
        """モニタリングを実行"""
        try:
            with Live(refresh_per_second=1/refresh_rate) as live:
                while True:
                    # レイアウト作成
                    layout = Layout()
                    
                    # 単一テーブルを取得
                    table = self.create_monitoring_table()
                    
                    if table is None:
                        # テーブルがない場合
                        layout.split_column(
                            Layout(self.create_summary_panel(), size=8),
                            Layout(Panel("No data available", title="Status"))
                        )
                    else:
                        # テーブルがある場合
                        layout.split_column(
                            Layout(self.create_summary_panel(), size=8),
                            Layout(table)
                        )
                    
                    live.update(layout)
                    time.sleep(refresh_rate)
                    
        except KeyboardInterrupt:
            self.console.print(f"\n[yellow]{self.get_text('monitoring_stopped')}[/yellow]")
        except Exception as e:
            self.console.print(f"[red]Error: {e}[/red]") 