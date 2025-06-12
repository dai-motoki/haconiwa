"""
Task Manager for Haconiwa v1.0
"""

import logging
import subprocess
from typing import Dict, Any, Optional
from pathlib import Path

logger = logging.getLogger(__name__)


class TaskManager:
    """Task manager for Git worktree tasks - Singleton pattern"""
    
    _instance = None
    _initialized = False
    
    def __new__(cls):
        if cls._instance is None:
            cls._instance = super(TaskManager, cls).__new__(cls)
            cls._instance.tasks = {}
            cls._instance.default_branch = "main"  # Default value
            cls._initialized = True
        return cls._instance
    
    def __init__(self):
        # Only initialize once
        pass
    
    def set_default_branch(self, branch: str):
        """Set the default branch to use for creating new branches"""
        self.default_branch = branch
        logger.info(f"TaskManager default branch set to: {branch}")
    
    def create_task(self, config: Dict[str, Any]) -> bool:
        """Create task from configuration with Git worktree"""
        try:
            name = config.get("name")
            branch = config.get("branch")
            worktree = config.get("worktree", True)
            assignee = config.get("assignee")
            space_ref = config.get("space_ref")
            description = config.get("description", "")
            agent_config = config.get("agent_config")  # エージェント設定
            company_agent_defaults = config.get("company_agent_defaults")  # 会社デフォルト設定
            
            logger.info(f"Creating task: {name} (branch: {branch}, assignee: {assignee})")
            
            # Create worktree if requested
            if worktree and space_ref:
                success = self._create_worktree(name, branch, space_ref)
                if not success:
                    logger.warning(f"Failed to create worktree for task {name}, but continuing")
            
            # Store task info
            self.tasks[name] = {
                "config": config,
                "status": "created",
                "worktree_created": worktree and space_ref,
                "assignee": assignee,
                "description": description,
                "agent_config": agent_config
            }
            
            # IMPORTANT: Create agent assignment log immediately after task creation
            if assignee and worktree and space_ref:
                self._create_immediate_agent_assignment_log(name, assignee, space_ref, description)
                
                # Claude Code統合: .claude/settings.local.json の作成
                if agent_config or company_agent_defaults:
                    logger.info(f"🔧 Setting up Claude Code integration for {assignee}...")
                    self._create_claude_code_settings(name, space_ref, company_agent_defaults, agent_config)
            
            logger.info(f"✅ Created task: {name}")
            if worktree and space_ref:
                logger.info(f"   📁 Worktree created for branch: {branch}")
            logger.info(f"   👤 Assigned to: {assignee}")
            logger.info(f"   📝 Description: {description}")
            
            return True
            
        except Exception as e:
            logger.error(f"Failed to create task: {e}")
            return False
    
    def _create_worktree(self, task_name: str, branch: str, space_ref: str) -> bool:
        """Create Git worktree in tasks directory"""
        try:
            # Find space base path (assuming task_name follows naming convention)
            # e.g., "2025-01-09-frontend-ui-design-agent001" -> space should be in "./test-multiroom-desks"
            # For now, we'll use a heuristic to find the space
            base_path = self._find_space_base_path(space_ref)
            if not base_path:
                logger.error(f"Could not find base path for space: {space_ref}")
                return False
            
            tasks_path = base_path / "tasks"
            main_repo_path = tasks_path / "main"
            worktree_path = tasks_path / task_name
            
            # Check if main repository exists
            if not main_repo_path.exists():
                logger.error(f"Main repository not found at: {main_repo_path}")
                return False
            
            # Check if worktree already exists
            if worktree_path.exists():
                logger.info(f"Worktree already exists: {worktree_path}")
                return True
            
            # Create new branch and worktree
            logger.info(f"Creating worktree: {worktree_path} for branch: {branch}")
            
            # First, ensure we're on the default branch and it's up to date
            logger.info(f"Fetching and checking out {self.default_branch} branch")
            
            # Fetch the latest from origin
            fetch_result = subprocess.run(['git', '-C', str(main_repo_path), 'fetch', 'origin', self.default_branch], 
                                        capture_output=True, text=True)
            if fetch_result.returncode != 0:
                logger.warning(f"Failed to fetch {self.default_branch}: {fetch_result.stderr}")
            
            # Checkout default branch
            checkout_result = subprocess.run(['git', '-C', str(main_repo_path), 'checkout', self.default_branch], 
                                           capture_output=True, text=True)
            if checkout_result.returncode != 0:
                logger.warning(f"Failed to checkout {self.default_branch}: {checkout_result.stderr}")
            
            # Pull latest changes
            pull_result = subprocess.run(['git', '-C', str(main_repo_path), 'pull', 'origin', self.default_branch], 
                                       capture_output=True, text=True)
            if pull_result.returncode != 0:
                logger.warning(f"Failed to pull {self.default_branch}: {pull_result.stderr}")
            
            # Check if branch already exists
            check_branch = subprocess.run(['git', '-C', str(main_repo_path), 'rev-parse', '--verify', branch], 
                                        capture_output=True, text=True)
            
            if check_branch.returncode == 0:
                # Branch exists, check if it's based on the correct branch
                merge_base = subprocess.run(['git', '-C', str(main_repo_path), 'merge-base', branch, f'origin/{self.default_branch}'], 
                                          capture_output=True, text=True)
                default_branch_commit = subprocess.run(['git', '-C', str(main_repo_path), 'rev-parse', f'origin/{self.default_branch}'], 
                                                     capture_output=True, text=True)
                
                if merge_base.stdout.strip() != default_branch_commit.stdout.strip():
                    # Branch exists but is based on wrong branch, delete and recreate
                    logger.info(f"Branch {branch} exists but is based on wrong branch, recreating from {self.default_branch}")
                    subprocess.run(['git', '-C', str(main_repo_path), 'branch', '-D', branch], 
                                 capture_output=True, text=True)
                    # Create new branch from the default branch
                    result1 = subprocess.run(['git', '-C', str(main_repo_path), 'checkout', '-b', branch, f'origin/{self.default_branch}'], 
                                           capture_output=True, text=True)
                else:
                    # Branch exists and is based on correct branch, just checkout
                    result1 = subprocess.run(['git', '-C', str(main_repo_path), 'checkout', branch], 
                                           capture_output=True, text=True)
            else:
                # Branch doesn't exist, create it from the default branch
                result1 = subprocess.run(['git', '-C', str(main_repo_path), 'checkout', '-b', branch, f'origin/{self.default_branch}'], 
                                       capture_output=True, text=True)
            
            if result1.returncode != 0:
                logger.warning(f"Failed to create/checkout branch {branch}: {result1.stderr}")
            
            # Switch back to default branch
            subprocess.run(['git', '-C', str(main_repo_path), 'checkout', self.default_branch], 
                         capture_output=True, text=True)
            
            # Create worktree (using absolute paths)
            result2 = subprocess.run(['git', '-C', str(main_repo_path), 'worktree', 'add', 
                                   str(worktree_path.absolute()), branch], 
                                   capture_output=True, text=True)
            
            if result2.returncode == 0:
                logger.info(f"✅ Successfully created worktree: {worktree_path}")
                return True
            else:
                logger.error(f"Failed to create worktree: {result2.stderr}")
                return False
            
        except Exception as e:
            logger.error(f"Error creating worktree: {e}")
            return False
    
    def _find_space_base_path(self, space_ref: str) -> Path:
        """Find base path for space reference"""
        # Strategy 1: Get from SpaceManager active sessions (most reliable)
        try:
            from ..space.manager import SpaceManager
            space_manager = SpaceManager()
            
            # Check active sessions for matching space
            for session_name, session_info in space_manager.active_sessions.items():
                config = session_info.get("config", {})
                # Check if this session matches our space_ref
                if (config.get("name") == space_ref or 
                    session_name == space_ref):
                    base_path = Path(config.get("base_path", f"./{session_name}"))
                    if base_path.exists() and (base_path / "tasks").exists():
                        logger.info(f"Found space base path from SpaceManager: {base_path}")
                        return base_path
        except Exception as e:
            logger.debug(f"Could not get base path from SpaceManager: {e}")
        
        # Strategy 2: Standard naming patterns (space_ref based)
        candidates = [
            Path(f"./{space_ref}"),
            Path(f"./{space_ref}-desks"),
            Path(f"./test-{space_ref}"),
            Path(f"./test-{space_ref}-desks"),
            # Additional patterns for company-style spaces
            Path(f"./{space_ref.replace('-company', '-desks')}"),
            Path(f"./test-{space_ref.replace('-company', '-desks')}"),
            Path(f"./{space_ref.replace('company', 'desks')}"),
        ]
        
        for candidate in candidates:
            if candidate.exists() and (candidate / "tasks").exists():
                logger.info(f"Found space base path via pattern matching: {candidate}")
                return candidate
        
        # Strategy 3: Scan all directories for tasks subdirectory (fallback)
        logger.debug(f"Scanning current directory for any directory with 'tasks' subdirectory...")
        current_dirs = [p for p in Path(".").iterdir() if p.is_dir()]
        for dir_path in current_dirs:
            if (dir_path / "tasks").exists():
                # Additional validation: check if it looks like a haconiwa workspace
                tasks_dir = dir_path / "tasks"
                if (tasks_dir / "main").exists() or any(tasks_dir.iterdir()):
                    logger.info(f"Found space base path via directory scan: {dir_path}")
                    return dir_path
        
        # Debug: list what actually exists
        logger.debug(f"Searching for space: {space_ref}")
        logger.debug(f"Checked candidates: {[str(c) for c in candidates]}")
        logger.debug(f"Available directories: {[p.name for p in current_dirs]}")
        
        logger.warning(f"Could not find base path for space: {space_ref}")
        return None
    
    def _get_session_name_from_space_ref(self, space_ref: str) -> str:
        """Get actual session name from space reference"""
        # For most cases, the space_ref is actually the company name, which is the session name
        # But we need to handle world-based naming where space_ref might be different
        # For now, return space_ref as it should be the company name
        return space_ref
    
    def list_tasks(self) -> Dict[str, Any]:
        """List all tasks"""
        return self.tasks.copy()
    
    def get_task(self, name: str) -> Dict[str, Any]:
        """Get specific task"""
        return self.tasks.get(name)
    
    def delete_task(self, name: str) -> bool:
        """Delete task and its worktree"""
        try:
            if name not in self.tasks:
                logger.warning(f"Task not found: {name}")
                return False
            
            task = self.tasks[name]
            
            # Remove worktree if it was created
            if task.get("worktree_created"):
                space_ref = task["config"].get("space_ref")
                if space_ref:
                    base_path = self._find_space_base_path(space_ref)
                    if base_path:
                        worktree_path = base_path / "tasks" / name
                        if worktree_path.exists():
                            # Remove worktree
                            main_repo_path = base_path / "tasks" / "main"
                            if main_repo_path.exists():
                                result = subprocess.run(['git', '-C', str(main_repo_path), 'worktree', 'remove', str(worktree_path)], 
                                                      capture_output=True, text=True)
                                if result.returncode == 0:
                                    logger.info(f"✅ Removed worktree: {worktree_path}")
                                else:
                                    logger.warning(f"Failed to remove worktree: {result.stderr}")
            
            # Remove from tasks
            del self.tasks[name]
            logger.info(f"✅ Deleted task: {name}")
            return True
            
        except Exception as e:
            logger.error(f"Failed to delete task {name}: {e}")
            return False
    
    def get_task_by_assignee(self, assignee: str) -> Dict[str, Any]:
        """Get task assigned to specific agent"""
        for task_name, task_data in self.tasks.items():
            if task_data["config"].get("assignee") == assignee:
                return {
                    "name": task_name,
                    "worktree_path": f"tasks/{task_name}",
                    "config": task_data["config"]
                }
        return None
    
    def get_agent_assignments(self, space_ref: str) -> Dict[str, str]:
        """Get mapping of agent IDs to task worktree paths"""
        assignments = {}
        for task_name, task_data in self.tasks.items():
            config = task_data["config"]
            if config.get("space_ref") == space_ref and config.get("assignee"):
                assignee = config["assignee"]
                assignments[assignee] = f"tasks/{task_name}"
        return assignments
    
    def update_agent_pane_directories(self, space_ref: str, session_name: str) -> bool:
        """Update pane directories for agents assigned to tasks"""
        try:
            updated_count = 0
            
            for task_name, task_data in self.tasks.items():
                config = task_data["config"]
                if config.get("space_ref") != space_ref or not config.get("assignee"):
                    continue
                
                assignee = config["assignee"]
                worktree_path = f"tasks/{task_name}"
                
                # Find the pane for this agent
                pane_info = self._find_pane_for_agent(assignee, session_name)
                if pane_info:
                    success = self._update_agent_pane_directory(
                        session_name, pane_info, assignee, task_name, worktree_path
                    )
                    if success:
                        updated_count += 1
                        logger.info(f"Updated agent {assignee} pane to task directory: {worktree_path}")
                    else:
                        logger.warning(f"Failed to update pane for agent {assignee}")
                else:
                    logger.warning(f"Could not find pane for agent {assignee}")
            
            logger.info(f"Updated {updated_count} agent pane directories")
            return updated_count > 0
            
        except Exception as e:
            logger.error(f"Failed to update agent pane directories: {e}")
            return False
    
    def _find_pane_for_agent(self, assignee: str, session_name: str) -> Optional[Dict[str, Any]]:
        """Find tmux pane for specific agent"""
        try:
            # Parse assignee: org01-pm-r1 or org01-wk-a-r1
            parts = assignee.split("-")
            
            if len(parts) == 3:
                # Format: org01-pm-r1
                org_part = parts[0]  # org01
                role_part = parts[1]  # pm
                room_part = parts[2]  # r1, r2
                worker_type = None
            elif len(parts) == 4:
                # Format: org01-wk-a-r1
                org_part = parts[0]  # org01
                role_part = parts[1]  # wk
                worker_type = parts[2]  # a, b, c
                room_part = parts[3]  # r1, r2
            else:
                logger.warning(f"Invalid assignee format: {assignee}")
                return None
            
            # Extract organization number
            org_num = org_part[3:]  # "01"
            
            # Map room to window
            if room_part == "r1":
                window_id = "0"
            elif room_part == "r2":
                window_id = "1"
            else:
                logger.warning(f"Unknown room part: {room_part}")
                return None
            
            # Calculate expected pane index based on desk mapping logic
            # Alpha Room (r1): org1=0-3, org2=4-7, org3=8-11, org4=12-15
            # Beta Room (r2): org1=0-3, org2=4-7, org3=8-11, org4=12-15
            org_index = int(org_num) - 1  # 01->0, 02->1, 03->2, 04->3
            
            if role_part == "pm":
                role_offset = 0
            elif role_part == "wk" and worker_type:
                # a=1, b=2, c=3
                role_offset = ord(worker_type) - ord('a') + 1
            else:
                logger.warning(f"Unknown role: {role_part}")
                return None
            
            # Calculate pane index: org_base + role_offset
            expected_pane_index = org_index * 4 + role_offset
            
            # Also generate directory patterns for verification
            if room_part == "r1":
                # Alpha Room patterns: 01pm, 01a, 01b, 01c, 02pm, etc.
                if role_part == "pm":
                    expected_patterns = [f"/org-{org_num}/{org_num}pm"]
                elif role_part == "wk" and worker_type:
                    expected_patterns = [f"/org-{org_num}/{org_num}{worker_type}"]
                else:
                    logger.warning(f"Unknown role: {role_part}")
                    return None
            else:
                # Beta Room patterns: 11pm, 11a, 11b, 11c, 12pm, etc.
                if role_part == "pm":
                    expected_patterns = [f"/org-{org_num}/1{int(org_num)}pm"]
                elif role_part == "wk" and worker_type:
                    expected_patterns = [f"/org-{org_num}/1{int(org_num)}{worker_type}"]
                else:
                    logger.warning(f"Unknown role: {role_part}")
                    return None
            
            logger.debug(f"Looking for pane {expected_pane_index} with patterns: {expected_patterns} in window {window_id}")
            logger.debug(f"Assignee: {assignee} → org_index: {org_index}, role_offset: {role_offset}, expected_pane: {expected_pane_index}")
            
            # Get all panes in the window
            cmd = ["tmux", "list-panes", "-t", f"{session_name}:{window_id}", 
                   "-F", "#{pane_index}:#{pane_current_path}:#{pane_title}"]
            result = subprocess.run(cmd, capture_output=True, text=True)
            
            if result.returncode != 0:
                logger.error(f"Failed to list panes: {result.stderr}")
                return None
            
            # Debug: show all panes in this window
            logger.debug(f"All panes in window {window_id}:")
            panes_info = {}
            for line in result.stdout.strip().split('\n'):
                if line:
                    parts = line.split(':', 2)
                    if len(parts) >= 2:
                        pane_idx = parts[0]
                        pane_path = parts[1]
                        panes_info[int(pane_idx)] = pane_path
                        logger.debug(f"  Pane {pane_idx}: {pane_path}")
            
            # Strategy 1: Try exact pane index match first
            if expected_pane_index in panes_info:
                pane_path = panes_info[expected_pane_index]
                # Check if it matches expected pattern OR is already a task directory
                for pattern in expected_patterns:
                    if pane_path.endswith(pattern) or "/tasks/" in pane_path:
                        logger.debug(f"Found target pane {expected_pane_index}: {pane_path}")
                        # Get full info for this pane
                        for line in result.stdout.strip().split('\n'):
                            if line.startswith(f"{expected_pane_index}:"):
                                parts = line.split(':', 2)
                                if len(parts) >= 3:
                                    return {
                                        "window_id": window_id,
                                        "pane_index": str(expected_pane_index),
                                        "current_path": parts[1],
                                        "title": parts[2]
                                    }
            
            # Strategy 2: Fallback to pattern matching if exact index doesn't work
            for line in result.stdout.strip().split('\n'):
                if not line:
                    continue
                parts = line.split(':', 2)
                if len(parts) >= 3:
                    pane_index = parts[0]
                    current_path = parts[1]
                    pane_title = parts[2]
                    
                    # Check if this pane matches any expected patterns
                    for pattern in expected_patterns:
                        if current_path.endswith(pattern):
                            logger.debug(f"Found matching pane {pane_index}: {current_path} (pattern: {pattern})")
                            return {
                                "window_id": window_id,
                                "pane_index": pane_index,
                                "current_path": current_path,
                                "title": pane_title
                            }
            
            logger.warning(f"Could not find pane {expected_pane_index} with patterns {expected_patterns} in window {window_id}")
            return None
            
        except Exception as e:
            logger.error(f"Error finding pane for agent {assignee}: {e}")
            return None
    
    def _update_agent_pane_directory(self, session_name: str, pane_info: Dict[str, Any], 
                                   assignee: str, task_name: str, worktree_path: str) -> bool:
        """Update specific pane to use task worktree directory"""
        try:
            window_id = pane_info["window_id"]
            pane_index = pane_info["pane_index"]
            
            # Find space base path from current path
            current_path = pane_info["current_path"]
            # Extract base path: /path/to/test-multiroom-desks/org-01/01pm → /path/to/test-multiroom-desks
            path_parts = current_path.split("/")
            base_path_parts = []
            for part in path_parts:
                base_path_parts.append(part)
                if part.endswith("-desks"):
                    break
            base_path = "/".join(base_path_parts)
            
            # Build task directory path
            task_dir = f"{base_path}/{worktree_path}"
            
            # Create agent assignment log in task directory
            self._create_agent_assignment_log(task_dir, assignee, task_name, session_name, window_id, pane_index)
            
            # Update pane working directory
            cmd = ["tmux", "send-keys", "-t", f"{session_name}:{window_id}.{pane_index}", 
                   f"cd {task_dir}", "Enter"]
            result1 = subprocess.run(cmd, capture_output=True, text=True)
            
            # Update pane title to include task info
            old_title = pane_info["title"]
            new_title = f"{old_title} [Task: {task_name}]"
            cmd = ["tmux", "select-pane", "-t", f"{session_name}:{window_id}.{pane_index}", 
                   "-T", new_title]
            result2 = subprocess.run(cmd, capture_output=True, text=True)
            
            if result1.returncode == 0 and result2.returncode == 0:
                logger.debug(f"Updated pane {window_id}.{pane_index}: {task_dir}")
                return True
            else:
                logger.error(f"Failed to update pane {window_id}.{pane_index}")
                return False
            
        except Exception as e:
            logger.error(f"Error updating pane directory: {e}")
            return False
    
    def _create_agent_assignment_log(self, task_dir: str, assignee: str, task_name: str, 
                                   session_name: str, window_id: str, pane_index: str) -> bool:
        """Create agent assignment log file in task directory"""
        try:
            from datetime import datetime
            import json
            
            task_path = Path(task_dir)
            if not task_path.exists():
                logger.warning(f"Task directory does not exist: {task_dir}")
                return False
            
            # Create .haconiwa directory for agent logs
            haconiwa_dir = task_path / ".haconiwa"
            haconiwa_dir.mkdir(exist_ok=True)
            
            # Agent assignment log file
            log_file = haconiwa_dir / "agent_assignment.json"
            
            # Prepare assignment information
            assignment_info = {
                "agent_id": assignee,
                "task_name": task_name,
                "space_session": session_name,
                "tmux_window": window_id,
                "tmux_pane": pane_index,
                "assigned_at": datetime.now().isoformat(),
                "assignment_type": "automatic",
                "task_directory": task_dir,
                "status": "active"
            }
            
            # Load existing assignments if file exists
            assignments = []
            if log_file.exists():
                try:
                    with open(log_file, 'r', encoding='utf-8') as f:
                        existing_data = json.load(f)
                        if isinstance(existing_data, list):
                            assignments = existing_data
                        elif isinstance(existing_data, dict):
                            assignments = [existing_data]  # Convert single assignment to list
                except Exception as e:
                    logger.warning(f"Could not read existing assignment log: {e}")
            
            # Add new assignment
            assignments.append(assignment_info)
            
            # Write updated assignments to file
            with open(log_file, 'w', encoding='utf-8') as f:
                json.dump(assignments, f, indent=2, ensure_ascii=False)
            
            # Also create a human-readable log
            readme_file = haconiwa_dir / "README.md"
            self._create_agent_readme(readme_file, assignee, task_name, assignment_info)
            
            logger.info(f"📝 Created agent assignment log: {log_file}")
            return True
            
        except Exception as e:
            logger.error(f"Failed to create agent assignment log: {e}")
            return False
    
    def _create_agent_readme(self, readme_file: Path, assignee: str, task_name: str, assignment_info: Dict[str, Any]) -> bool:
        """Create human-readable README for agent assignment"""
        try:
            readme_content = f"""# エージェント割り当て情報

## 基本情報
- **エージェントID**: `{assignee}`
- **タスク名**: `{task_name}`
- **割り当て日時**: {assignment_info['assigned_at']}
- **ステータス**: {assignment_info['status']}

## 環境情報
- **スペースセッション**: `{assignment_info['space_session']}`
- **tmuxウィンドウ**: {assignment_info['tmux_window']}
- **tmuxペイン**: {assignment_info['tmux_pane']}
- **タスクディレクトリ**: `{assignment_info['task_directory']}`

## エージェント役割
{self._get_agent_role_description(assignee)}

## このディレクトリについて
このディレクトリは、GitのWorktree機能を使用して作成された専用の作業ディレクトリです。
このエージェント専用のブランチで作業を行い、他のエージェントとは独立した開発環境を提供します。

## ログファイル
- `agent_assignment.json`: 割り当て履歴のJSON形式ログ
- `README.md`: この説明ファイル

---
*このファイルは Haconiwa v1.0 によって自動生成されました*
"""
            
            with open(readme_file, 'w', encoding='utf-8') as f:
                f.write(readme_content)
            
            logger.debug(f"Created agent README: {readme_file}")
            return True
            
        except Exception as e:
            logger.error(f"Failed to create agent README: {e}")
            return False
    
    def _get_agent_role_description(self, assignee: str) -> str:
        """Get role description for agent"""
        try:
            parts = assignee.split("-")
            if len(parts) >= 2:
                org_part = parts[0]  # org01
                role_part = parts[1]  # pm or wk
                
                org_num = org_part[3:]  # "01"
                
                if role_part == "pm":
                    return f"**役割**: プロジェクトマネージャー (組織{org_num})\n**責任範囲**: プロジェクト全体の管理、チームコーディネーション、進捗管理"
                elif role_part == "wk" and len(parts) >= 3:
                    worker_type = parts[2]  # a, b, c
                    worker_roles = {
                        "a": "**役割**: シニア開発者\n**責任範囲**: 技術設計、コードレビュー、アーキテクチャ決定",
                        "b": "**役割**: 中級開発者\n**責任範囲**: 機能実装、テスト作成、ドキュメント作成", 
                        "c": "**役割**: ジュニア開発者\n**責任範囲**: 基本実装、学習、サポート業務"
                    }
                    return worker_roles.get(worker_type, f"**役割**: 開発者-{worker_type.upper()}")
            
            return "**役割**: 未定義"
            
        except Exception:
            return "**役割**: 解析エラー"
    
    def _create_immediate_agent_assignment_log(self, task_name: str, assignee: str, space_ref: str, description: str) -> bool:
        """Create agent assignment log immediately when task is created"""
        try:
            from datetime import datetime
            import json
            
            # Find space base path
            base_path = self._find_space_base_path(space_ref)
            if not base_path:
                logger.warning(f"Could not find base path for space: {space_ref}")
                return False
            
            # Task directory path
            task_dir = base_path / "tasks" / task_name
            if not task_dir.exists():
                logger.warning(f"Task directory does not exist: {task_dir}")
                return False
            
            # Create .haconiwa directory for agent logs
            haconiwa_dir = task_dir / ".haconiwa"
            haconiwa_dir.mkdir(exist_ok=True)
            
            # Agent assignment log file
            log_file = haconiwa_dir / "agent_assignment.json"
            
            # Get the actual session name (company name) instead of using space_ref directly
            # For haconiwa-world, the session name is the company name
            session_name = self._get_session_name_from_space_ref(space_ref)
            
            # Prepare assignment information (without tmux pane info for now)
            assignment_info = {
                "agent_id": assignee,
                "task_name": task_name,
                "space_session": session_name,  # Use actual session name
                "tmux_window": None,  # Will be set when pane is found
                "tmux_pane": None,    # Will be set when pane is found
                "assigned_at": datetime.now().isoformat(),
                "assignment_type": "automatic",
                "task_directory": str(task_dir),
                "status": "active",
                "description": description
            }
            
            # Write assignment to file (always create new, don't append)
            with open(log_file, 'w', encoding='utf-8') as f:
                json.dump([assignment_info], f, indent=2, ensure_ascii=False)
            
            # Also create a human-readable log
            readme_file = haconiwa_dir / "README.md"
            self._create_agent_readme(readme_file, assignee, task_name, assignment_info)
            
            logger.info(f"📝 Created immediate agent assignment log: {log_file}")
            return True
            
        except Exception as e:
            logger.error(f"Failed to create immediate agent assignment log: {e}")
            return False
    
    def _create_claude_code_settings(self, task_name: str, space_ref: str, company_agent_defaults: Dict[str, Any], agent_config: Dict[str, Any]) -> bool:
        """Create Claude Code settings file"""
        try:
            # Find space base path
            base_path = self._find_space_base_path(space_ref)
            if not base_path:
                logger.warning(f"Could not find base path for space: {space_ref}")
                return False
            
            # Task directory path
            task_dir = base_path / "tasks" / task_name
            if not task_dir.exists():
                logger.warning(f"Task directory does not exist: {task_dir}")
                return False
            
            # Claude Code統合を使用して設定ファイルを作成
            from ..agent.claude_integration import ClaudeCodeIntegration
            claude_integration = ClaudeCodeIntegration()
            
            # 設定ファイル作成
            success = claude_integration.create_claude_settings(
                task_dir, 
                company_agent_defaults or {}, 
                agent_config
            )
            
            if success:
                logger.info(f"📁 Created Claude Code settings for task: {task_name}")
            else:
                logger.warning(f"Failed to create Claude Code settings for task: {task_name}")
            
            return success
            
        except Exception as e:
            logger.error(f"Failed to create Claude Code settings: {e}")
            return False 