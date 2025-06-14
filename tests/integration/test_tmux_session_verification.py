#!/usr/bin/env python3
"""
Tmux Session Verification Tests

包括的なtmuxセッション検証テストスイート
tmuxコマンドを使用して、作成されたセッションの状態を詳細に検証
"""

import subprocess
import json
import pytest
from pathlib import Path
from typing import Dict, List, Tuple, Optional
from rich.console import Console
from rich.table import Table
from rich.panel import Panel
from rich import print as rprint


class TmuxSessionVerifier:
    """Tmux session verification utility"""
    
    def __init__(self, session_name: str):
        self.session_name = session_name
        self.console = Console()
        
    def run_tmux_command(self, args: List[str]) -> Tuple[int, str, str]:
        """Run tmux command and return result"""
        cmd = ["tmux"] + args
        result = subprocess.run(cmd, capture_output=True, text=True)
        return result.returncode, result.stdout, result.stderr
    
    def session_exists(self) -> bool:
        """Check if session exists"""
        rc, stdout, _ = self.run_tmux_command(["has-session", "-t", self.session_name])
        return rc == 0
    
    def get_windows(self) -> List[Dict[str, str]]:
        """Get all windows in session"""
        rc, stdout, _ = self.run_tmux_command([
            "list-windows", "-t", self.session_name,
            "-F", "#{window_index}:#{window_name}:#{window_panes}"
        ])
        
        if rc != 0:
            return []
        
        windows = []
        for line in stdout.strip().split('\n'):
            if line:
                parts = line.split(':')
                windows.append({
                    "index": parts[0],
                    "name": parts[1],
                    "pane_count": parts[2]
                })
        return windows
    
    def get_panes(self, window_id: str = None) -> List[Dict[str, str]]:
        """Get all panes in session or specific window"""
        target = self.session_name
        if window_id is not None:
            target = f"{self.session_name}:{window_id}"
        
        rc, stdout, _ = self.run_tmux_command([
            "list-panes", "-t", target,
            "-F", "#{window_index}.#{pane_index}|#{pane_title}|#{pane_current_path}|#{pane_width}x#{pane_height}"
        ])
        
        if rc != 0:
            return []
        
        panes = []
        for line in stdout.strip().split('\n'):
            if line:
                parts = line.split('|', 3)
                panes.append({
                    "id": parts[0],
                    "title": parts[1] if len(parts) > 1 else "",
                    "path": parts[2] if len(parts) > 2 else "",
                    "size": parts[3] if len(parts) > 3 else ""
                })
        return panes
    
    def verify_pane_titles(self) -> Dict[str, List[str]]:
        """Verify all panes have titles"""
        issues = []
        panes = self.get_panes()
        
        for pane in panes:
            if not pane["title"] or pane["title"] == "":
                issues.append(f"Pane {pane['id']} has no title")
        
        return {"pane_titles": issues}
    
    def verify_pane_paths(self) -> Dict[str, List[str]]:
        """Verify all panes are in correct directories"""
        issues = []
        panes = self.get_panes()
        
        for pane in panes:
            path = pane["path"]
            if path.endswith("/haconiwa"):
                issues.append(f"Pane {pane['id']} is in haconiwa root directory")
            elif not (path.endswith("/standby") or "/tasks/" in path):
                issues.append(f"Pane {pane['id']} is in unexpected directory: {path}")
        
        return {"pane_paths": issues}
    
    def verify_window_structure(self, expected_windows: List[Dict[str, any]]) -> Dict[str, List[str]]:
        """Verify window structure matches expectations"""
        issues = []
        windows = self.get_windows()
        
        if len(windows) != len(expected_windows):
            issues.append(f"Expected {len(expected_windows)} windows, found {len(windows)}")
        
        for i, (actual, expected) in enumerate(zip(windows, expected_windows)):
            if actual["name"] != expected.get("name", ""):
                issues.append(f"Window {i}: expected name '{expected.get('name')}', got '{actual['name']}'")
            
            expected_panes = expected.get("pane_count", 0)
            if int(actual["pane_count"]) != expected_panes:
                issues.append(f"Window {i}: expected {expected_panes} panes, got {actual['pane_count']}")
        
        return {"window_structure": issues}
    
    def verify_grid_layout(self, grid: str, room_count: int) -> Dict[str, List[str]]:
        """Verify grid layout is correctly implemented"""
        issues = []
        
        try:
            cols, rows = map(int, grid.split('x'))
            total_expected_panes = cols * rows
            panes_per_room = total_expected_panes // room_count if room_count > 0 else total_expected_panes
        except:
            issues.append(f"Invalid grid specification: {grid}")
            return {"grid_layout": issues}
        
        windows = self.get_windows()
        total_actual_panes = sum(int(w["pane_count"]) for w in windows)
        
        if total_actual_panes != total_expected_panes:
            issues.append(f"Expected {total_expected_panes} total panes ({grid}), found {total_actual_panes}")
        
        # Check pane distribution across windows
        for i, window in enumerate(windows):
            if int(window["pane_count"]) != panes_per_room:
                issues.append(f"Window {i}: expected {panes_per_room} panes, got {window['pane_count']}")
        
        return {"grid_layout": issues}
    
    def capture_pane_content(self, pane_id: str, lines: int = 10) -> str:
        """Capture content from a specific pane"""
        rc, stdout, _ = self.run_tmux_command([
            "capture-pane", "-t", f"{self.session_name}:{pane_id}",
            "-p", "-S", f"-{lines}"
        ])
        return stdout if rc == 0 else ""
    
    def verify_claude_command(self) -> Dict[str, List[str]]:
        """Verify claude command was executed in all panes"""
        issues = []
        panes = self.get_panes()
        
        for pane in panes[:5]:  # Check first 5 panes as sample
            content = self.capture_pane_content(pane["id"], lines=20)
            if "claude" not in content:
                issues.append(f"Pane {pane['id']}: claude command not found in recent output")
        
        return {"claude_command": issues}
    
    def generate_report(self, verifications: Dict[str, Dict[str, List[str]]]) -> None:
        """Generate comprehensive verification report"""
        self.console.print(Panel.fit(
            f"[bold blue]Tmux Session Verification Report[/bold blue]\n"
            f"Session: {self.session_name}",
            style="blue"
        ))
        
        # Summary table
        table = Table(title="Verification Summary")
        table.add_column("Check", style="cyan")
        table.add_column("Status", style="green")
        table.add_column("Issues", style="red")
        
        total_issues = 0
        for check_name, issues_dict in verifications.items():
            for category, issues in issues_dict.items():
                status = "✅ PASS" if len(issues) == 0 else "❌ FAIL"
                table.add_row(category, status, str(len(issues)))
                total_issues += len(issues)
        
        self.console.print(table)
        
        # Detailed issues
        if total_issues > 0:
            self.console.print("\n[bold red]Detailed Issues:[/bold red]")
            for check_name, issues_dict in verifications.items():
                for category, issues in issues_dict.items():
                    if issues:
                        self.console.print(f"\n[yellow]{category}:[/yellow]")
                        for issue in issues:
                            self.console.print(f"  • {issue}")
        
        # Session structure
        self.console.print("\n[bold cyan]Session Structure:[/bold cyan]")
        windows = self.get_windows()
        for window in windows:
            self.console.print(f"\nWindow {window['index']}: {window['name']} ({window['pane_count']} panes)")
            
            # Show first few panes of each window
            panes = self.get_panes(window['index'])
            for pane in panes[:3]:
                path_short = pane['path'].split('/')[-2:] if '/' in pane['path'] else [pane['path']]
                path_display = '/'.join(path_short)
                self.console.print(f"  Pane {pane['id']}: {pane['title'][:50]}... → {path_display}")
            
            if len(panes) > 3:
                self.console.print(f"  ... and {len(panes) - 3} more panes")


def test_multiroom_session():
    """Test multiroom session with comprehensive checks"""
    session_name = "test-company-multiroom-tasks"
    verifier = TmuxSessionVerifier(session_name)
    
    # Check if session exists
    assert verifier.session_exists(), f"Session {session_name} does not exist"
    
    # Expected structure for 8x4 grid with 2 rooms
    expected_windows = [
        {"name": "Frontend", "pane_count": 16},
        {"name": "Backend", "pane_count": 16}
    ]
    
    # Run all verifications
    verifications = {
        "structure": verifier.verify_window_structure(expected_windows),
        "grid": verifier.verify_grid_layout("8x4", 2),
        "titles": verifier.verify_pane_titles(),
        "paths": verifier.verify_pane_paths(),
        "claude": verifier.verify_claude_command()
    }
    
    # Generate report
    verifier.generate_report(verifications)
    
    # Assert no issues
    total_issues = sum(len(issues) for check in verifications.values() for issues in check.values())
    assert total_issues == 0, f"Found {total_issues} issues in session verification"


def test_simple_dev_session():
    """Test simple dev session (1x3 grid)"""
    session_name = "simple-dev-company"
    verifier = TmuxSessionVerifier(session_name)
    
    if not verifier.session_exists():
        pytest.skip(f"Session {session_name} does not exist")
    
    expected_windows = [
        {"name": "simple-dev-company", "pane_count": 3}
    ]
    
    verifications = {
        "structure": verifier.verify_window_structure(expected_windows),
        "grid": verifier.verify_grid_layout("1x3", 1),
        "titles": verifier.verify_pane_titles(),
        "paths": verifier.verify_pane_paths(),
        "claude": verifier.verify_claude_command()
    }
    
    verifier.generate_report(verifications)
    
    total_issues = sum(len(issues) for check in verifications.values() for issues in check.values())
    assert total_issues == 0, f"Found {total_issues} issues in session verification"


def test_8x4_single_room_session():
    """Test 8x4 grid single room session"""
    session_name = "test-company-8x4-tasks"
    verifier = TmuxSessionVerifier(session_name)
    
    if not verifier.session_exists():
        pytest.skip(f"Session {session_name} does not exist")
    
    expected_windows = [
        {"name": "test-company-8x4-tasks", "pane_count": 32}
    ]
    
    verifications = {
        "structure": verifier.verify_window_structure(expected_windows),
        "grid": verifier.verify_grid_layout("8x4", 1),
        "titles": verifier.verify_pane_titles(),
        "paths": verifier.verify_pane_paths(),
        "claude": verifier.verify_claude_command()
    }
    
    verifier.generate_report(verifications)
    
    total_issues = sum(len(issues) for check in verifications.values() for issues in check.values())
    assert total_issues == 0, f"Found {total_issues} issues in session verification"


if __name__ == "__main__":
    # Run verification for specific session
    import sys
    
    if len(sys.argv) > 1:
        session_name = sys.argv[1]
        verifier = TmuxSessionVerifier(session_name)
        
        if not verifier.session_exists():
            print(f"Session '{session_name}' does not exist")
            sys.exit(1)
        
        # Detect grid and room count from actual structure
        windows = verifier.get_windows()
        total_panes = sum(int(w["pane_count"]) for w in windows)
        room_count = len(windows)
        
        # Estimate grid from total panes
        if total_panes == 3:
            grid = "1x3"
        elif total_panes == 16:
            grid = "4x4"
        elif total_panes == 32:
            grid = "8x4"
        else:
            grid = f"?x? ({total_panes} panes)"
        
        verifications = {
            "structure": {"windows": []},  # Skip expected structure check
            "grid": verifier.verify_grid_layout(grid, room_count),
            "titles": verifier.verify_pane_titles(),
            "paths": verifier.verify_pane_paths(),
            "claude": verifier.verify_claude_command()
        }
        
        verifier.generate_report(verifications)
    else:
        # Run all tests
        test_multiroom_session()
        test_simple_dev_session()
        test_8x4_single_room_session()