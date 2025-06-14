"""
Task Submitter for dynamic task creation and assignment
"""

import subprocess
import json
import logging
from pathlib import Path
from typing import Dict, Any, Optional, List
from datetime import datetime

from ..space.manager import SpaceManager
from ..task.manager import TaskManager
from ..core.logging import get_logger

logger = get_logger(__name__)


class TaskSubmitError(Exception):
    """Task submission error"""
    pass


class TaskSubmitter:
    """Submit tasks to existing companies with automatic worktree creation"""
    
    def __init__(self, space_manager: SpaceManager = None, task_manager: TaskManager = None):
        self.space_manager = space_manager or SpaceManager()
        self.task_manager = task_manager or TaskManager()
    
    def submit_task(
        self,
        company: str,
        assignee: str,
        title: str,
        branch: str,
        description: str = "",
        description_file: Optional[str] = None,
        base_branch: Optional[str] = None,
        priority: str = "medium",
        room: Optional[str] = None,
        worktree_path: Optional[str] = None,
        dry_run: bool = False
    ) -> Dict[str, Any]:
        """Submit a task to an existing company"""
        try:
            # 1. Validate and prepare description
            task_description = self._prepare_description(description, description_file)
            
            # 2. Validate company exists
            if not self._validate_company(company):
                raise TaskSubmitError(f"Company '{company}' not found. Use 'haconiwa space list' to see available companies.")
            
            # 3. Validate agent exists in company
            available_agents = self._get_available_agents(company, room)
            if assignee not in available_agents:
                raise TaskSubmitError(
                    f"Agent '{assignee}' not found in company '{company}'. "
                    f"Available agents: {', '.join(available_agents)}"
                )
            
            # 4. Determine base branch
            if not base_branch:
                base_branch = self._get_current_branch()
                logger.info(f"Using current branch as base: {base_branch}")
            
            # 5. Determine worktree path
            if not worktree_path:
                worktree_path = f"./tasks/{branch}"
            worktree_path = Path(worktree_path)
            
            # 6. Validate branch name
            if not self._validate_branch_name(branch):
                raise TaskSubmitError(f"Invalid branch name: {branch}")
            
            # Check if branch already exists
            if self._branch_exists(branch):
                raise TaskSubmitError(f"Branch '{branch}' already exists. Use a different branch name.")
            
            # Check if worktree directory already exists
            if worktree_path.exists():
                raise TaskSubmitError(f"Directory '{worktree_path}' already exists. Remove it or use --worktree-path.")
            
            if dry_run:
                self._show_dry_run_summary(
                    company, assignee, title, branch, task_description,
                    base_branch, priority, room, worktree_path
                )
                return {"dry_run": True, "status": "preview"}
            
            # 7. Create Git worktree
            logger.info(f"Creating worktree at {worktree_path} for branch {branch}")
            self._create_worktree(branch, str(worktree_path), base_branch)
            
            # 8. Find agent pane
            pane_info = self._find_agent_pane(company, assignee, room)
            if not pane_info:
                raise TaskSubmitError(f"Could not find pane for agent {assignee}")
            
            # 9. Move agent to worktree
            self._move_agent_to_worktree(company, pane_info, str(worktree_path))
            
            # 10. Create task record
            task = self._create_task_record(
                title=title,
                branch=branch,
                assignee=assignee,
                description=task_description,
                priority=priority,
                worktree_path=str(worktree_path),
                company=company
            )
            
            # 11. Create agent assignment log
            self._create_agent_assignment_log(
                worktree_path=worktree_path,
                assignee=assignee,
                task_name=title,
                company=company,
                description=task_description
            )
            
            logger.info(f"✅ Successfully submitted task: {title}")
            logger.info(f"📁 Worktree created at: {worktree_path}")
            logger.info(f"👤 Assigned to: {assignee}")
            
            return task
            
        except TaskSubmitError:
            raise
        except Exception as e:
            logger.error(f"Unexpected error during task submission: {e}")
            raise TaskSubmitError(f"Failed to submit task: {str(e)}")
    
    def _prepare_description(self, description: str, description_file: Optional[str]) -> str:
        """Prepare task description from inline text or file"""
        if description_file and description:
            raise TaskSubmitError("Cannot specify both --description and --description-file. Use one or the other.")
        
        if description_file:
            return self._read_description_file(description_file)
        
        return description
    
    def _read_description_file(self, file_path: str) -> str:
        """Read description from markdown file"""
        file_path = Path(file_path)
        if not file_path.exists():
            raise FileNotFoundError(f"Description file '{file_path}' not found")
        
        with open(file_path, 'r', encoding='utf-8') as f:
            return f.read()
    
    def _validate_company(self, company: str) -> bool:
        """Check if company exists in active sessions"""
        # Check tmux sessions
        result = subprocess.run(
            ["tmux", "list-sessions", "-F", "#{session_name}"],
            capture_output=True,
            text=True
        )
        
        if result.returncode != 0:
            logger.debug("No tmux sessions found")
            return False
        
        sessions = result.stdout.strip().split('\n')
        return company in sessions
    
    def _get_available_agents(self, company: str, room: Optional[str] = None) -> List[str]:
        """Get list of available agents in company"""
        agents = []
        
        try:
            # First try to get agents from existing assignment logs
            available_in_standby = self._get_agents_from_standby(company)
            if available_in_standby:
                return available_in_standby
            
            # Fallback to parsing pane paths
            cmd = ["tmux", "list-panes", "-a", "-t", company, 
                   "-F", "#{session_name}:#{window_index}:#{pane_index}:#{pane_current_path}"]
            result = subprocess.run(cmd, capture_output=True, text=True)
            
            if result.returncode != 0:
                logger.error(f"Failed to list panes: {result.stderr}")
                return agents
            
            # Parse pane information to extract agent IDs
            for line in result.stdout.strip().split('\n'):
                if not line:
                    continue
                
                parts = line.split(':')
                if len(parts) >= 4:
                    window_idx = parts[1]
                    pane_path = parts[3]
                    
                    # If room is specified, filter by window
                    if room:
                        if room == "room-alpha" and window_idx != "0":
                            continue
                        elif room == "room-beta" and window_idx != "1":
                            continue
                    
                    # Extract agent ID from path
                    agent_id = self._extract_agent_id_from_path(pane_path, window_idx)
                    if agent_id:
                        agents.append(agent_id)
            
            return sorted(set(agents))  # Remove duplicates and sort
            
        except Exception as e:
            logger.error(f"Error getting available agents: {e}")
            return agents
    
    def _get_agents_from_standby(self, company: str) -> List[str]:
        """Get available agents from standby directories"""
        agents = []
        
        try:
            # List panes that are in standby directories
            cmd = ["tmux", "list-panes", "-a", "-t", company,
                   "-F", "#{pane_index}:#{pane_current_path}"]
            result = subprocess.run(cmd, capture_output=True, text=True)
            
            if result.returncode != 0:
                return agents
            
            # Map pane positions to expected agent IDs for kamui-dev-company
            # Based on the YAML configuration order
            pane_to_agent_map = {
                0: "ceo-motoki",
                1: "cto-yamada", 
                2: "cfo-tanaka",
                3: "vpe-sato",
                4: "vpp-suzuki",
                5: "vpo-watanabe",
                6: "ai-lead-nakamura",
                7: "backend-lead-kobayashi",
                8: "frontend-lead-ishii",
                9: "devops-lead-matsui",
                10: "security-lead-inoue",
                11: "data-lead-kimura",
                12: "qa-manager-hayashi",
                13: "docs-lead-yamamoto",
                14: "community-ito",
                15: "platform-kato"
            }
            
            # Parse panes and find ones in standby
            for line in result.stdout.strip().split('\n'):
                if not line:
                    continue
                    
                parts = line.split(':', 1)
                if len(parts) >= 2:
                    pane_idx = int(parts[0])
                    pane_path = parts[1]
                    
                    # Check if pane is in standby
                    if '/standby' in pane_path and pane_idx in pane_to_agent_map:
                        agents.append(pane_to_agent_map[pane_idx])
            
            return agents
            
        except Exception as e:
            logger.debug(f"Could not get agents from standby: {e}")
            return []
    
    def _extract_agent_id_from_path(self, path: str, window_idx: str) -> Optional[str]:
        """Extract agent ID from pane path"""
        # Path examples:
        # /path/to/test-multiroom-desks/org-01/01pm → org01-pm-r1 (window 0)
        # /path/to/test-multiroom-desks/org-01/01a → org01-wk-a-r1 (window 0)
        # /path/to/test-multiroom-desks/org-01/11pm → org01-pm-r2 (window 1)
        
        path_parts = path.split('/')
        if len(path_parts) < 2:
            return None
        
        # Check if this is a kamui-dev-company style path (tasks or standby)
        if any(part in path for part in ['/tasks/task_', '/standby']):
            # For kamui-dev-company, we need to look up the agent from assignment logs
            # or use a placeholder ID based on pane position
            return f"kamui-agent-w{window_idx}-p{path_parts[-1]}"
        
        # Get last two parts (org-XX/XXY)
        org_dir = path_parts[-2]  # org-01
        desk_dir = path_parts[-1]  # 01pm, 01a, 11pm, etc.
        
        if not org_dir.startswith('org-'):
            return None
        
        org_num = org_dir.split('-')[1]  # 01, 02, etc.
        
        # Determine room from window index
        room = "r1" if window_idx == "0" else "r2"
        
        # Parse desk directory
        if desk_dir.endswith('pm'):
            return f"org{org_num}-pm-{room}"
        elif len(desk_dir) == 3 and desk_dir[-1] in 'abc':
            worker_type = desk_dir[-1]
            return f"org{org_num}-wk-{worker_type}-{room}"
        
        return None
    
    def _get_current_branch(self) -> str:
        """Get current Git branch"""
        result = subprocess.run(
            ["git", "rev-parse", "--abbrev-ref", "HEAD"],
            capture_output=True,
            text=True
        )
        
        if result.returncode != 0:
            logger.warning("Could not determine current branch, using 'main'")
            return "main"
        
        return result.stdout.strip()
    
    def _validate_branch_name(self, branch: str) -> bool:
        """Validate branch name format"""
        # Basic validation for branch names
        if not branch:
            return False
        
        # Check for invalid characters
        invalid_chars = [' ', '..', '~', '^', ':', '\\', '?', '*', '[']
        for char in invalid_chars:
            if char in branch:
                return False
        
        return True
    
    def _branch_exists(self, branch: str) -> bool:
        """Check if branch already exists"""
        result = subprocess.run(
            ["git", "rev-parse", "--verify", branch],
            capture_output=True,
            text=True
        )
        return result.returncode == 0
    
    def _create_worktree(self, branch: str, worktree_path: str, base_branch: str):
        """Create Git worktree with new branch"""
        # Create parent directory if needed
        Path(worktree_path).parent.mkdir(parents=True, exist_ok=True)
        
        # Create worktree with new branch
        cmd = ["git", "worktree", "add", "-b", branch, worktree_path, base_branch]
        result = subprocess.run(cmd, capture_output=True, text=True)
        
        if result.returncode != 0:
            error_msg = result.stderr.strip()
            if "already exists" in error_msg:
                raise TaskSubmitError(f"Branch '{branch}' already exists")
            elif "is not a git repository" in error_msg:
                raise TaskSubmitError("Failed to create worktree. Ensure you are in a git repository.")
            else:
                raise TaskSubmitError(f"Failed to create worktree: {error_msg}")
        
        logger.info(f"✅ Created worktree at {worktree_path} for branch {branch}")
    
    def _find_agent_pane(self, company: str, assignee: str, room: Optional[str] = None) -> Optional[Dict[str, Any]]:
        """Find tmux pane for specific agent"""
        try:
            # For kamui-dev-company style agents, use the pane mapping
            if company == "kamui-dev-company":
                return self._find_kamui_agent_pane(company, assignee, room)
            
            # Parse assignee to determine expected window
            parts = assignee.split("-")
            if len(parts) < 3:
                logger.error(f"Invalid assignee format: {assignee}")
                return None
            
            # Determine window from assignee
            room_part = parts[-1]  # r1 or r2
            window_id = "0" if room_part == "r1" else "1"
            
            # Override with explicit room if provided
            if room:
                if room == "room-alpha":
                    window_id = "0"
                elif room == "room-beta":
                    window_id = "1"
            
            # List panes in the specific window
            cmd = ["tmux", "list-panes", "-t", f"{company}:{window_id}",
                   "-F", "#{pane_index}:#{pane_current_path}:#{pane_title}"]
            result = subprocess.run(cmd, capture_output=True, text=True)
            
            if result.returncode != 0:
                logger.error(f"Failed to list panes: {result.stderr}")
                return None
            
            # Find pane by checking path patterns
            for line in result.stdout.strip().split('\n'):
                if not line:
                    continue
                
                parts = line.split(':', 2)
                if len(parts) >= 2:
                    pane_index = parts[0]
                    current_path = parts[1]
                    
                    # Check if this pane matches the agent
                    if self._path_matches_agent(current_path, assignee):
                        return {
                            "session": company,
                            "window_id": window_id,
                            "pane_index": pane_index,
                            "current_path": current_path
                        }
            
            logger.warning(f"Could not find pane for agent {assignee}")
            return None
            
        except Exception as e:
            logger.error(f"Error finding pane for agent {assignee}: {e}")
            return None
    
    def _find_kamui_agent_pane(self, company: str, assignee: str, room: Optional[str] = None) -> Optional[Dict[str, Any]]:
        """Find pane for kamui-dev-company agents"""
        # Map agent IDs to expected pane indices
        agent_to_pane_map = {
            "ceo-motoki": 0,
            "cto-yamada": 1,
            "cfo-tanaka": 2,
            "vpe-sato": 3,
            "vpp-suzuki": 4,
            "vpo-watanabe": 5,
            "ai-lead-nakamura": 6,
            "backend-lead-kobayashi": 7,
            "frontend-lead-ishii": 8,
            "devops-lead-matsui": 9,
            "security-lead-inoue": 10,
            "data-lead-kimura": 11,
            "qa-manager-hayashi": 12,
            "docs-lead-yamamoto": 13,
            "community-ito": 14,
            "platform-kato": 15
        }
        
        if assignee not in agent_to_pane_map:
            logger.error(f"Unknown agent: {assignee}")
            return None
        
        pane_idx = agent_to_pane_map[assignee]
        window_id = "0"  # Default to first window
        
        # Override with explicit room if provided
        if room:
            if room == "room-alpha":
                window_id = "0"
            elif room == "room-beta":
                window_id = "1"
        
        # Get pane info
        cmd = ["tmux", "list-panes", "-t", f"{company}:{window_id}.{pane_idx}",
               "-F", "#{pane_index}:#{pane_current_path}"]
        result = subprocess.run(cmd, capture_output=True, text=True)
        
        if result.returncode == 0 and result.stdout.strip():
            parts = result.stdout.strip().split(':', 1)
            if len(parts) >= 2:
                return {
                    "session": company,
                    "window_id": window_id,
                    "pane_index": str(pane_idx),
                    "current_path": parts[1]
                }
        
        return None
    
    def _path_matches_agent(self, path: str, assignee: str) -> bool:
        """Check if path matches expected pattern for agent"""
        # Extract org and role info from assignee
        parts = assignee.split("-")
        if len(parts) < 3:
            return False
        
        org_num = parts[0][3:]  # org01 → 01
        role = parts[1]  # pm or wk
        room = parts[-1]  # r1 or r2
        
        if role == "pm":
            # Check for PM patterns: 01pm (r1), 11pm (r2)
            if room == "r1":
                return path.endswith(f"/{org_num}pm")
            else:  # r2
                # For room 2, the pattern is 1X where X is the org number
                return path.endswith(f"/1{int(org_num) % 10}pm")
        elif role == "wk" and len(parts) >= 4:
            worker_type = parts[2]  # a, b, c
            # Check for worker patterns: 01a (r1), 11a (r2)
            if room == "r1":
                return path.endswith(f"/{org_num}{worker_type}")
            else:  # r2
                # For room 2, the pattern is 1X where X is the org number
                return path.endswith(f"/1{int(org_num) % 10}{worker_type}")
        
        return False
    
    def _move_agent_to_worktree(self, company: str, pane_info: Dict[str, Any], worktree_path: str):
        """Move agent's pane to worktree directory"""
        session = pane_info["session"]
        window_id = pane_info["window_id"]
        pane_index = pane_info["pane_index"]
        
        # Convert to absolute path
        abs_worktree_path = str(Path(worktree_path).absolute())
        
        # Send cd command to the pane
        cmd = ["tmux", "send-keys", "-t", f"{session}:{window_id}.{pane_index}",
               f"cd {abs_worktree_path}", "C-m"]
        result = subprocess.run(cmd, capture_output=True, text=True)
        
        if result.returncode != 0:
            raise TaskSubmitError(f"Failed to move agent to worktree: {result.stderr}")
        
        logger.info(f"✅ Moved agent to worktree directory: {abs_worktree_path}")
    
    def _create_task_record(self, **kwargs) -> Dict[str, Any]:
        """Create task record"""
        task = {
            "id": f"task-{kwargs['branch']}-{datetime.now().strftime('%Y%m%d%H%M%S')}",
            "title": kwargs["title"],
            "branch": kwargs["branch"],
            "assignee": kwargs["assignee"],
            "description": kwargs["description"],
            "priority": kwargs["priority"],
            "worktree_path": kwargs["worktree_path"],
            "company": kwargs["company"],
            "created_at": datetime.now().isoformat(),
            "status": "active"
        }
        
        # Store in TaskManager
        self.task_manager.tasks[task["id"]] = {
            "config": task,
            "status": "created",
            "worktree_created": True,
            "assignee": kwargs["assignee"],
            "description": kwargs["description"]
        }
        
        return task
    
    def _create_agent_assignment_log(self, worktree_path: Path, assignee: str, 
                                   task_name: str, company: str, description: str):
        """Create agent assignment log in worktree"""
        try:
            # Create .haconiwa directory
            haconiwa_dir = worktree_path / ".haconiwa"
            haconiwa_dir.mkdir(parents=True, exist_ok=True)
            
            # Create assignment info
            assignment_info = {
                "agent_id": assignee,
                "task_name": task_name,
                "space_session": company,
                "assigned_at": datetime.now().isoformat(),
                "assignment_type": "manual",
                "task_directory": str(worktree_path),
                "status": "active",
                "description": description
            }
            
            # Write to JSON file
            log_file = haconiwa_dir / "agent_assignment.json"
            with open(log_file, 'w', encoding='utf-8') as f:
                json.dump([assignment_info], f, indent=2, ensure_ascii=False)
            
            # Create README
            readme_file = haconiwa_dir / "README.md"
            readme_content = f"""# エージェント割り当て情報

## 基本情報
- **エージェントID**: `{assignee}`
- **タスク名**: `{task_name}`
- **割り当て日時**: {assignment_info['assigned_at']}
- **ステータス**: {assignment_info['status']}

## 環境情報
- **カンパニー**: `{company}`
- **タスクディレクトリ**: `{assignment_info['task_directory']}`

## タスク詳細
{description}

## このディレクトリについて
このディレクトリは、GitのWorktree機能を使用して作成された専用の作業ディレクトリです。
このエージェント専用のブランチで作業を行い、他のエージェントとは独立した開発環境を提供します。

---
*このファイルは Haconiwa Task Submit コマンドによって作成されました*
"""
            
            with open(readme_file, 'w', encoding='utf-8') as f:
                f.write(readme_content)
            
            logger.info(f"📝 Created agent assignment log in {haconiwa_dir}")
            
        except Exception as e:
            logger.error(f"Failed to create agent assignment log: {e}")
    
    def _show_dry_run_summary(self, company: str, assignee: str, title: str, branch: str,
                            description: str, base_branch: str, priority: str, 
                            room: Optional[str], worktree_path: Path):
        """Show what would be done in dry-run mode"""
        print("\n🔍 DRY RUN MODE - The following actions would be performed:\n")
        print(f"1. ✓ Validate company '{company}' exists")
        print(f"2. ✓ Validate agent '{assignee}' exists in company")
        print(f"3. ✓ Create new branch '{branch}' from '{base_branch}'")
        print(f"4. ✓ Create worktree at '{worktree_path}'")
        print(f"5. ✓ Move agent '{assignee}' to worktree directory")
        print(f"6. ✓ Create task record with:")
        print(f"   - Title: {title}")
        print(f"   - Priority: {priority}")
        if room:
            print(f"   - Room: {room}")
        if description:
            print(f"   - Description: {description[:100]}{'...' if len(description) > 100 else ''}")
        print(f"7. ✓ Create agent assignment log in worktree")
        print("\n✅ All validations passed. Run without --dry-run to execute.")