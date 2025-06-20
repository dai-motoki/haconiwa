"""
Space Manager for Haconiwa v1.0 - 32 Pane Support
"""

import subprocess
from pathlib import Path
from typing import Dict, List, Any, Optional
import logging
import json
import glob

from ..core.crd.models import SpaceCRD, OrganizationCRD

logger = logging.getLogger(__name__)


class SpaceManagerError(Exception):
    """Space manager error"""
    pass


class SpaceManager:
    """Space manager with 32-pane and multi-room support - Singleton pattern"""
    
    _instance = None
    _initialized = False
    
    def __new__(cls):
        if cls._instance is None:
            cls._instance = super(SpaceManager, cls).__new__(cls)
        return cls._instance
    
    def __init__(self):
        if not self._initialized:
            self.active_sessions = {}
            self.task_assignments = {}  # Direct task assignment storage: {assignee: task_info}
            SpaceManager._initialized = True
    
    def set_task_assignments(self, task_assignments: Dict[str, Dict[str, Any]]):
        """Set task assignments for agent-to-task mapping"""
        self.task_assignments = task_assignments
        logger.info(f"SpaceManagerに {len(task_assignments)} 個のタスクブランチ割り当てを設定しました")
    
    def get_task_by_assignee(self, assignee: str) -> Dict[str, Any]:
        """Get task assigned to specific agent"""
        return self.task_assignments.get(assignee)
    
    def create_multiroom_session(self, config: Dict[str, Any]) -> bool:
        """Create multiroom tmux session with proper Room → Window mapping and task-centric directory structure"""
        try:
            session_name = config["name"]
            grid = config.get("grid", "8x4")
            base_path = Path(config.get("base_path", f"./{session_name}"))
            rooms = config.get("rooms", [])
            organizations = config.get("organizations", [])
            organization_crd = config.get("organization_crd")
            
            logger.info(f"会社を作成中: {session_name} ({len(rooms)} ルーム)")
            
            # Check and remove existing tmux session if it exists
            self._cleanup_existing_session(session_name)
            
            # Create base directory structure
            base_path.mkdir(parents=True, exist_ok=True)
            
            # Create tasks directory for Git repository and worktrees
            tasks_path = base_path / "tasks"
            tasks_path.mkdir(exist_ok=True)
            main_repo_path = tasks_path / "main"
            
            # Handle Git repository setup in tasks/main/
            if config.get("git_repo"):
                git_config = config["git_repo"].copy()  # Make a copy to add space_ref
                git_config["space_ref"] = config["name"]  # Add space reference
                logger.info(f"tasks/main/ に Git リポジトリをセットアップ中: {git_config['url']}")
                
                # Clone to tasks/main/ 
                force_clone = getattr(self, '_force_clone', False)
                success = self._clone_repository_to_tasks(git_config, main_repo_path, force_clone)
                if not success:
                    logger.warning("tasks/main/ での Git リポジトリセットアップに失敗、Git なしで継続します")
            
            # Generate desk mappings with organization info and room configuration
            desk_mappings = self.generate_desk_mappings(organizations, rooms, grid, base_path, organization_crd=organization_crd)
            
            # Create tmux session (initial window 0) with base_path as working directory
            self._create_tmux_session(session_name, base_path)
            
            # Configure pane borders and titles (same as company build)
            self._configure_pane_borders(session_name)
            
            # Create windows for each room
            if not self._create_windows_for_rooms(session_name, rooms, base_path):
                logger.error("ルーム用部屋の作成に失敗しました")
                return False
            
            # Distribute desks to windows
            desk_distribution = self._distribute_desks_to_windows(desk_mappings)
            
            # Debug: Log distribution details
            logger.info("Desk distribution summary:")
            for room_id, desks in desk_distribution.items():
                logger.info(f"  {room_id}: {len(desks)} mappings")
                for i, desk in enumerate(desks):
                    logger.info(f"    {i}: {desk['desk_id']} ({desk['role']}) -> {desk['title']}")
            
            # Calculate panes per window
            layout_info = self._calculate_panes_per_window(grid, len(rooms))
            panes_per_window = layout_info["panes_per_window"]
            
            # Create panes in each window and set up desks
            # Only process rooms that actually have windows created
            valid_room_ids = [room["id"] for room in rooms]
            
            for room_id, desks_in_room in desk_distribution.items():
                # Skip room if it doesn't have a window
                if room_id not in valid_room_ids:
                    logger.warning(f"ルーム {room_id} をスキップ - 部屋が作成されていません")
                    continue
                    
                window_id = self._get_window_id_for_room(room_id)
                
                # Validate window_id is within valid range
                if window_id.isdigit() and int(window_id) >= len(rooms):
                    logger.error(f"ルーム {room_id} の room_id {window_id} が無効 - {len(rooms)} 個の部屋しか存在しません")
                    continue
                
                # Get pane count for this specific room
                if isinstance(panes_per_window, dict):
                    room_pane_count = panes_per_window.get(room_id, 16)
                else:
                    room_pane_count = panes_per_window
                
                logger.info(f"{room_id} をセットアップ中: {room_pane_count} デスク, {len(desks_in_room)} 割り当て")
                
                # Create panes in this window
                if not self._create_panes_in_window(session_name, window_id, room_pane_count):
                    logger.warning(f"部屋 {window_id} でデスクの作成に失敗しました")
                    continue
                
                # Ensure we have enough mappings for the panes
                if len(desks_in_room) < room_pane_count:
                    logger.warning(f"{room_id} の割り当てが不足: {room_pane_count} デスクに対して {len(desks_in_room)} 割り当て")
                    continue
                elif len(desks_in_room) > room_pane_count:
                    logger.info(f"{room_id} の余分な割り当て、最初の {room_pane_count} 割り当てを使用")
                    desks_in_room = desks_in_room[:room_pane_count]
                
                # Set up each desk in the window
                for pane_index, desk_mapping in enumerate(desks_in_room):
                    if pane_index >= room_pane_count:
                        logger.warning(f"{room_id} の余分な割り当て {pane_index} をスキップ")
                        break
                    
                    # Debug: Log the desk mapping being used
                    logger.debug(f"Setting up pane {window_id}.{pane_index} with agent_id: {desk_mapping.get('agent_id', 'MISSING')}")
                    
                    desk_dir = self._create_desk_directory(base_path, desk_mapping)
                    self._update_pane_in_window(session_name, window_id, pane_index, desk_mapping, desk_dir)
            
            # Store session configuration
            self.active_sessions[session_name] = {
                "config": config,
                "base_path": str(base_path),
                "desk_mappings": desk_mappings,
                "desk_distribution": desk_distribution,
                "session_name": session_name,
                "rooms": rooms  # Store rooms list for accurate window mapping
            }
            
            # Calculate actual pane count
            cols, rows = map(int, grid.split('x'))
            total_panes = cols * rows
            panes_per_room = total_panes // len(rooms) if len(rooms) > 1 else total_panes
            
            # Display created directory structure
            self._display_created_structure(base_path, organizations, total_panes, len(rooms))
            
            # Claude command will be sent after directory change in _update_pane_in_window
            # self._send_claude_command_to_all_panes(session_name, rooms, desk_distribution)
            
            logger.info(f"✅ 会社 '{session_name}' の作成が成功しました")
            logger.info(f"   📁 基準ディレクトリ: {base_path}")
            logger.info(f"   🏢 組織: {len(organizations)}")
            logger.info(f"   🚪 ルーム: {len(rooms)}")
            logger.info(f"   🖥️ デスク: 合計 {total_panes} ({panes_per_room} 個/ルーム)" if len(rooms) > 1 else f"   🖥️ デスク: {total_panes}")
            
            return True
            
        except Exception as e:
            logger.error(f"会社 {config.get('name', 'unknown')} の作成に失敗: {e}")
            return False
    
    def generate_desk_mappings(self, organizations: List[Dict[str, Any]] = None, rooms: List[Dict[str, Any]] = None, grid: str = "8x4", base_path: Path = None, organization_crd: OrganizationCRD = None) -> List[Dict[str, Any]]:
        """Generate desk mappings based on actual room configuration and grid size"""
        if not organizations:
            # Fallback to default organization names
            organizations = [{"id": "01", "name": "Default Organization", "department_id": "dev"}]
        
        if not rooms:
            # Fallback to default room if none provided
            rooms = [{"id": "room-01", "name": "Main Room"}]
        
        mappings = []
        
        # Calculate desks needed per room based on grid
        try:
            cols, rows = map(int, grid.split('x'))
            total_panes = cols * rows
            panes_per_room = total_panes // len(rooms) if len(rooms) > 0 else total_panes
        except:
            total_panes = 32
            panes_per_room = 16
        
        desk_counter = 0
        
        # organization_crd is now passed as an argument
        dept_roles_cache = {}
        
        # Generate desk mappings for each room
        for room_idx, room in enumerate(rooms):
            room_id = room["id"]
            room_name = room.get("name", room_id)
            
            # Calculate room number for agent ID format
            room_num = room_idx + 1  # r1, r2, etc.
            
            # Determine which department should be in this room
            if room_idx == 0:
                # First room - Executive Team
                target_dept_id = "executive"
                dept_name = "Executive Team"
                org_id = "01"
            else:
                # Second room - Standby Team  
                target_dept_id = "standby"
                dept_name = "Standby Team"
                org_id = "02"
            
            # Get department roles from Organization CRD
            dept_roles = None
            if organization_crd and target_dept_id:
                if target_dept_id not in dept_roles_cache:
                    dept_roles_cache[target_dept_id] = self._get_department_roles(organization_crd, target_dept_id)
                dept_roles = dept_roles_cache[target_dept_id]
            
            # Generate enough desks to fill all panes in this room
            for desk_idx in range(panes_per_room):
                # Get agent ID directly from Organization CRD roles
                agent_id = None
                role_name = f"agent-{desk_idx+1}"  # fallback
                title = f"Agent {desk_idx+1}"  # fallback
                
                if dept_roles:
                    # Use all_roles directly from the new structure
                    all_roles = dept_roles.get('all_roles', [])
                    
                    # If all_roles is not available, fall back to legacy structure
                    if not all_roles:
                        all_roles = []
                        if dept_roles.get('lead_role'):
                            all_roles.append(dept_roles['lead_role'])
                        if dept_roles.get('worker_roles'):
                            all_roles.extend(dept_roles['worker_roles'])
                    
                    # Debug logging for agentId reading order
                    logger.debug(f"Department {target_dept_id} - Total roles: {len(all_roles)}")
                    for idx, role in enumerate(all_roles):
                        role_agent_id = getattr(role, 'agentId', 'None')
                        role_title = getattr(role, 'title', 'Unknown')
                        logger.debug(f"  Role[{idx}]: title='{role_title}', agentId='{role_agent_id}'")
                    
                    # Map desk index to role
                    if desk_idx < len(all_roles):
                        role_obj = all_roles[desk_idx]
                        agent_id = getattr(role_obj, 'agentId', None)
                        title = getattr(role_obj, 'title', f"Agent {desk_idx+1}")
                        logger.debug(f"Desk {desk_idx} -> Role: title='{title}', agentId='{agent_id}'")
                        
                        # Determine role name for directory structure
                        if desk_idx == 0:
                            role_name = "pm"
                        else:
                            role_name = f"wk-{chr(ord('a') + desk_idx - 1)}" if desk_idx <= 26 else f"wk-{desk_idx}"
                
                # Fall back to default agent ID if not found in CRD
                if not agent_id:
                    # Generate dynamic agent ID based on department and desk position
                    if target_dept_id == "executive":
                        # Generate executive agent ID dynamically
                        agent_id = f"exec-{desk_idx+1:02d}"
                        title = f"Executive {desk_idx+1}"
                        
                    elif target_dept_id == "standby":
                        # Generate standby agent ID dynamically
                        agent_id = f"standby-dev-{desk_idx+1:02d}"
                        title = f"Standby Developer {desk_idx+1:02d}"
                    
                    # Determine role name
                    if desk_idx == 0:
                        role_name = "pm"
                    else:
                        role_name = f"wk-{chr(ord('a') + desk_idx - 1)}" if desk_idx <= 26 else f"wk-{desk_idx}"
                
                desk_id = f"desk-{room_id}-{desk_idx:02d}"
                dir_name = f"{target_dept_id[:4]}-{desk_idx+1:02d}"  # exec-01, exec-02, ..., stan-01, stan-02, ...
                pane_title = f"{dept_name} - {title} - {room_name}"
                
                mappings.append({
                    "desk_id": desk_id,
                    "agent_id": agent_id,
                    "org_id": f"org-{org_id}",
                    "role": role_name,
                    "room_id": room_id,
                    "directory_name": dir_name,
                    "title": pane_title
                })
                desk_counter += 1
        
        logger.info(f"Generated {len(mappings)} desk mappings for {len(rooms)} rooms")
        
        # Store the mappings for later use
        self._current_desk_mappings = mappings
        
        # Save desk mappings to file for later retrieval
        if base_path:
            try:
                haconiwa_dir = base_path / ".haconiwa"
                haconiwa_dir.mkdir(exist_ok=True)
                desk_mappings_file = haconiwa_dir / "desk_mappings.json"
                with open(desk_mappings_file, 'w') as f:
                    json.dump(mappings, f, indent=2)
                logger.debug(f"Saved desk mappings to {desk_mappings_file}")
            except Exception as e:
                logger.warning(f"Could not save desk mappings: {e}")
        
        return mappings
    
    def convert_crd_to_configs(self, crd: SpaceCRD) -> List[Dict[str, Any]]:
        """Convert Space CRD to internal configurations for multiple companies"""
        # Store the current Space CRD for reference
        self._current_space_crd = crd
        
        configs = []
        companies = crd.spec.nations[0].cities[0].villages[0].companies
        
        for company in companies:
            config = self._convert_single_company_to_config(crd, company)
            
            # Fetch and attach the full Organization CRD object to the config
            organization_ref = getattr(company, 'organizationRef', None)
            if organization_ref:
                config['organization_crd'] = self._get_organization_crd_by_ref(organization_ref)
            
            configs.append(config)
        
        return configs
    
    def convert_crd_to_config(self, crd: SpaceCRD) -> Dict[str, Any]:
        """Convert Space CRD to internal configuration (single company - for backward compatibility)"""
        configs = self.convert_crd_to_configs(crd)
        return configs[0] if configs else {}
    
    def _convert_single_company_to_config(self, crd: SpaceCRD, company) -> Dict[str, Any]:
        """Convert single company configuration from CRD"""
        
        # Use world name as base path if basePath is not specified
        base_path = company.basePath
        if base_path is None:
            base_path = f"./{crd.metadata.name}"
        
        # Extract rooms from CRD structure
        rooms = []
        if company.buildings and len(company.buildings) > 0:
            building = company.buildings[0]
            if building.floors:
                for floor in building.floors:
                    if floor.rooms:
                        for room in floor.rooms:
                            rooms.append({
                                "id": room.id,
                                "name": room.name,
                                "description": getattr(room, 'description', '')
                            })
        
        # If no rooms defined in CRD, create default based on grid
        if not rooms:
            grid_parts = company.grid.split('x')
            if len(grid_parts) == 2:
                cols, rows = int(grid_parts[0]), int(grid_parts[1])
                total_panes = cols * rows
                
                if total_panes <= 4:
                    # Single room for small grids
                    rooms = [{"id": "room-01", "name": "Main Room"}]
                elif total_panes <= 16:
                    # Two rooms for medium grids
                    rooms = [
                        {"id": "room-01", "name": "Alpha Room"},
                        {"id": "room-02", "name": "Beta Room"}
                    ]
                else:
                    # Three rooms for large grids
                    rooms = [
                        {"id": "room-01", "name": "Alpha Room"},
                        {"id": "room-02", "name": "Beta Room"},
                        {"id": "room-executive", "name": "Executive Room"}
                    ]
        
        config = {
            "name": company.name,
            "grid": company.grid,
            "base_path": base_path,
            "git_repo": None,
            "organizations": [],
            "rooms": rooms
        }
        
        # Add git repository config if specified
        if company.gitRepo:
            config["git_repo"] = {
                "url": company.gitRepo.url,
                "default_branch": company.gitRepo.defaultBranch,
                "auth": company.gitRepo.auth
            }
        
        # Store config file path for later processing
        config_file = getattr(company, 'configFile', None)
        if config_file:
            config["config_file"] = config_file
            logger.info(f"Config file specified for {company.name}: {config_file}")
        
        # Get organization reference and fetch organization data
        organization_ref = getattr(company, 'organizationRef', None)
        if organization_ref:
            # Fetch organization data from applied Organization CRDs
            organizations = self._get_organization_data(organization_ref)
            config["organizations"] = organizations
        else:
            # Fallback to simple organization if no organizationRef
            logger.warning("No organizationRef found, using simple organization")
            config["organizations"] = [
                {"id": "01", "name": company.name or "default-org", "department_id": "default"}
            ]
        
        return config
    
    def _get_organization_data(self, organization_ref: str) -> List[Dict[str, Any]]:
        """Get organization data from applied Organization CRDs"""
        try:
            logger.info(f"Fetching organization data for ref: {organization_ref}")
            
            # Try to get the actual Organization CRD from applied resources
            
            # Get singleton instance of CRDApplier - this needs to be improved in real implementation
            # For now, we'll use a workaround to access applied resources
            
            # Search for applied Organization CRD
            organization_crd = None
            applied_resources = {}
            
            # Try to access via module-level variable (workaround)
            try:
                import sys
                if hasattr(sys.modules.get('__main__'), '_current_applier'):
                    applier = getattr(sys.modules['__main__'], '_current_applier')
                    applied_resources = applier.get_applied_resources()
            except:
                pass
            
            # Look for Organization CRD in applied resources
            logger.info(f"Looking for Organization CRD: {organization_ref}")
            logger.info(f"Available resources: {list(applied_resources.keys())}")
            
            organization_crd = self._get_organization_crd_by_ref(organization_ref)

            if organization_crd:
                # Map Organization CRD departments to 32-pane structure
                departments = organization_crd.spec.hierarchy.departments
                logger.info(f"Found {len(departments)} departments in Organization CRD")
                
                # Create organization mapping based on actual departments
                organizations = []
                
                # If we have actual departments, use them
                if departments:
                    for i, dept in enumerate(departments[:5]):  # Up to 5 departments for our layout
                        org_id = f"{i+1:02d}"
                        organizations.append({
                            "id": org_id,
                            "name": dept.name,
                            "department_id": dept.id
                        })
                        logger.info(f"Added department {dept.id} → {dept.name}")
                    
                else:
                    # No departments defined, create a simple organization
                    logger.warning("No departments found in Organization CRD, creating simple organization")
                    organizations.append({
                        "id": "01",
                        "name": organization_ref,
                        "department_id": "default"
                    })
                
                # If we have executive department, map it to all organizations (leadership structure)
                executive_dept = None
                for dept in departments:
                    if dept.id == "executive":
                        executive_dept = dept
                        break
                
                if executive_dept:
                    logger.info(f"Found executive department: {executive_dept.name}")
                    # Executive roles will be distributed across organizations
                
                logger.info(f"Created {len(organizations)} organization mappings from Organization CRD")
                for org in organizations:
                    logger.info(f"  {org['id']}: {org['name']} (dept: {org['department_id']})")
                
                return organizations
                
            else:
                logger.warning(f"Organization CRD {organization_ref} not found in applied resources")
                # Fallback to simple organization
                logger.info("Using simple organization mapping")
                return [
                    {"id": "01", "name": organization_ref or "default-org", "department_id": "default"}
                ]
            
        except Exception as e:
            logger.error(f"Failed to get organization data for {organization_ref}: {e}")
            # Fallback to simple organization
            return [
                {"id": "01", "name": organization_ref or "default-org", "department_id": "default"}
            ]
    
    def _load_external_config_file(self, config_file_path: str, company_name: str):
        """Load and apply external configuration file"""
        try:
            from pathlib import Path
            import sys
            from ..core.crd.parser import CRDParser
            
            logger.info(f"Loading external config file: {config_file_path} for company: {company_name}")
            
            # Resolve file path
            file_path = Path(config_file_path)
            if not file_path.is_absolute():
                # Make relative to current working directory
                file_path = Path.cwd() / file_path
            
            if not file_path.exists():
                logger.warning(f"Config file not found: {file_path}")
                return
            
            # Parse multi-document YAML
            parser = CRDParser()
            with open(file_path, 'r', encoding='utf-8') as f:
                content = f.read()
            
            crds = parser.parse_multi_yaml(content)
            logger.info(f"Loaded {len(crds)} CRDs from {config_file_path}")
            
            # Apply the CRDs using the current applier instance
            # Get applier from the global state (set during apply command)
            if hasattr(sys.modules.get('__main__'), '_current_applier'):
                applier = getattr(sys.modules['__main__'], '_current_applier')
                for crd in crds:
                    applier.apply(crd)
                    name = crd.metadata.name if crd.metadata else crd.spec.taskBranchName if hasattr(crd.spec, 'taskBranchName') else 'unknown'
                    logger.info(f"Applied {crd.kind}/{name} from config file {config_file_path}")
            else:
                logger.warning("No current applier found, cannot apply CRDs from config file")
        
        except Exception as e:
            logger.error(f"Failed to load config file {config_file_path}: {e}")
            import traceback
            logger.debug(f"Stack trace: {traceback.format_exc()}")
    
    def _create_tmux_session(self, session_name: str, base_path: Path = None):
        """Create tmux session with optional working directory"""
        cmd = ["tmux", "new-session", "-d", "-s", session_name]
        if base_path:
            # Create session with specific working directory
            abs_path = str(base_path.absolute())
            cmd.extend(["-c", abs_path])
            logger.info(f"Creating tmux session with working directory: {abs_path}")
        result = subprocess.run(cmd, capture_output=True, text=True)
        if result.returncode != 0:
            raise SpaceManagerError(f"Failed to create tmux session: {result.stderr}")
        
        # Also set default-path for the session to ensure new windows inherit it
        if base_path:
            set_cmd = ["tmux", "set-option", "-t", session_name, "default-path", str(base_path.absolute())]
            subprocess.run(set_cmd, capture_output=True, text=True)
    
    def _create_windows_for_rooms(self, session_name: str, rooms: List[Dict[str, Any]], base_path: Path) -> bool:
        """Create tmux windows for each room"""
        try:
            # Create room-window mapping
            room_window_mapping = {}
            
            for i, room in enumerate(rooms):
                room_name = room.get("name", f"Room {i+1}")
                window_name = room_name.replace(" Room", "")  # "Alpha Room" → "Alpha"
                
                # Store room-window mapping
                room_id = room.get("id", room_name.lower().replace(" ", "-"))
                room_window_mapping[room_id] = i
                
                if i == 0:
                    # Rename the initial window (window 0)
                    cmd = ["tmux", "rename-window", "-t", f"{session_name}:0", window_name]
                else:
                    # Create new window
                    cmd = ["tmux", "new-window", "-t", session_name, "-n", window_name]
                
                result = subprocess.run(cmd, capture_output=True, text=True)
                if result.returncode != 0:
                    logger.error(f"Failed to create window {i} ({window_name}): {result.stderr}")
                    return False
                
                # Apply pane border settings to the new window
                subprocess.run(
                    ["tmux", "set-option", "-t", f"{session_name}:{i}", 
                     "pane-border-status", "top"],
                    capture_output=True, text=True
                )
                subprocess.run(
                    ["tmux", "set-option", "-t", f"{session_name}:{i}", 
                     "pane-border-format", "#{pane_title}"],
                    capture_output=True, text=True
                )
                
                logger.info(f"Created window {i}: {window_name}")
            
            # Save room-window mapping to file
            self._save_room_window_mapping(session_name, room_window_mapping, base_path)
            
            return True
            
        except Exception as e:
            logger.error(f"Error creating windows for rooms: {e}")
            return False
    
    def _save_room_window_mapping(self, session_name: str, mapping: Dict[str, int], base_path: Path) -> None:
        """Save room-window mapping to JSON file"""
        try:
            
            haconiwa_dir = base_path / ".haconiwa"
            haconiwa_dir.mkdir(exist_ok=True)
            
            mapping_file = haconiwa_dir / "room_window_mapping.json"
            
            # Load existing mappings if file exists
            existing_mappings = {}
            if mapping_file.exists():
                with open(mapping_file, 'r') as f:
                    existing_mappings = json.load(f)
            
            # Update with new mapping
            existing_mappings[session_name] = mapping
            
            # Save updated mappings
            with open(mapping_file, 'w') as f:
                json.dump(existing_mappings, f, indent=2)
            
            logger.debug(f"Saved room-window mapping for session {session_name}")
            
        except Exception as e:
            logger.warning(f"Could not save room-window mapping: {e}")
    
    def _load_room_window_mapping(self, session_name: str) -> Optional[Dict[str, int]]:
        """Load room-window mapping from JSON file"""
        try:
            # Get base path from active_sessions or use default
            base_path = Path.cwd()
            if hasattr(self, 'active_sessions') and session_name in self.active_sessions:
                session_data = self.active_sessions[session_name]
                if 'base_path' in session_data:
                    base_path = Path(session_data['base_path'])
            
            mapping_file = base_path / ".haconiwa" / "room_window_mapping.json"
            
            if mapping_file.exists():
                with open(mapping_file, 'r') as f:
                    all_mappings = json.load(f)
                    return all_mappings.get(session_name, None)
            
            return None
            
        except Exception as e:
            logger.warning(f"Could not load room-window mapping: {e}")
            return None
    
    def _create_panes_in_window(self, session_name: str, window_id: str, pane_count: int) -> bool:
        """Create panes in specific tmux window - supports different layouts"""
        try:
            if pane_count == 1:
                # Single pane, already exists
                logger.info(f"Window {window_id} already has 1 pane")
                return True
            
            elif pane_count == 2:
                # Split horizontally once
                cmd = ["tmux", "split-window", "-h", "-t", f"{session_name}:{window_id}.0"]
                result = subprocess.run(cmd, capture_output=True, text=True)
                if result.returncode != 0:
                    logger.warning(f"Failed to create horizontal split in window {window_id}: {result.stderr}")
                logger.info(f"Created {pane_count} panes in window {window_id} (2x1 layout)")
                return True
                
            elif pane_count == 3:
                # 1x3 layout: Split horizontally twice
                cmd = ["tmux", "split-window", "-h", "-t", f"{session_name}:{window_id}.0"]
                result = subprocess.run(cmd, capture_output=True, text=True)
                if result.returncode != 0:
                    logger.warning(f"Failed to create horizontal split 1 in window {window_id}: {result.stderr}")
                
                cmd = ["tmux", "split-window", "-h", "-t", f"{session_name}:{window_id}.1"]
                result = subprocess.run(cmd, capture_output=True, text=True)
                if result.returncode != 0:
                    logger.warning(f"Failed to create horizontal split 2 in window {window_id}: {result.stderr}")
                
                logger.info(f"Created {pane_count} panes in window {window_id} (1x3 layout)")
                return True
                
            elif pane_count == 4:
                # 2x2 layout or 1x4 layout
                # Split horizontally once, then split each vertically
                cmd = ["tmux", "split-window", "-h", "-t", f"{session_name}:{window_id}.0"]
                result = subprocess.run(cmd, capture_output=True, text=True)
                if result.returncode != 0:
                    logger.warning(f"Failed to create horizontal split 1 in window {window_id}: {result.stderr}")
                
                cmd = ["tmux", "split-window", "-v", "-t", f"{session_name}:{window_id}.0"]
                result = subprocess.run(cmd, capture_output=True, text=True)
                if result.returncode != 0:
                    logger.warning(f"Failed to create vertical split 1 in window {window_id}: {result.stderr}")
                
                cmd = ["tmux", "split-window", "-v", "-t", f"{session_name}:{window_id}.2"]
                result = subprocess.run(cmd, capture_output=True, text=True)
                if result.returncode != 0:
                    logger.warning(f"Failed to create vertical split 2 in window {window_id}: {result.stderr}")
                
                logger.info(f"Created {pane_count} panes in window {window_id} (2x2 layout)")
                return True
                
            elif pane_count == 8:
                # Alpha/Beta Room layout: 2x4 (8 panes)
                # Split vertically once to create 2 rows
                cmd = ["tmux", "split-window", "-v", "-t", f"{session_name}:{window_id}.0"]
                result = subprocess.run(cmd, capture_output=True, text=True)
                if result.returncode != 0:
                    logger.warning(f"Failed to create vertical split in window {window_id}: {result.stderr}")
                
                # Split each row horizontally 3 times to create 4 columns
                # Top row (panes 0-3)
                for i in range(3):
                    target_pane = 0 if i == 0 else 1
                    cmd = ["tmux", "split-window", "-h", "-t", f"{session_name}:{window_id}.{target_pane}"]
                    result = subprocess.run(cmd, capture_output=True, text=True)
                    if result.returncode != 0:
                        logger.warning(f"Failed to create horizontal split top-{i+1} in window {window_id}: {result.stderr}")
                
                # Bottom row (panes 4-7)
                for i in range(3):
                    target_pane = 4 if i == 0 else 5
                    cmd = ["tmux", "split-window", "-h", "-t", f"{session_name}:{window_id}.{target_pane}"]
                    result = subprocess.run(cmd, capture_output=True, text=True)
                    if result.returncode != 0:
                        logger.warning(f"Failed to create horizontal split bottom-{i+1} in window {window_id}: {result.stderr}")
                
                # Apply tiled layout for even distribution
                cmd = ["tmux", "select-layout", "-t", f"{session_name}:{window_id}", "tiled"]
                result = subprocess.run(cmd, capture_output=True, text=True)
                if result.returncode != 0:
                    logger.warning(f"Failed to apply tiled layout to window {window_id}: {result.stderr}")
                
                logger.info(f"Created {pane_count} panes in window {window_id} (2x4 layout)")
                return True
                
            elif pane_count == 16:
                # Default 4x4 layout (16 panes) - existing logic
                # Split vertically 3 times to create 4 rows
                cmd = ["tmux", "split-window", "-v", "-t", f"{session_name}:{window_id}.0"]
                result = subprocess.run(cmd, capture_output=True, text=True)
                if result.returncode != 0:
                    logger.warning(f"Failed to create vertical split 1 in window {window_id}: {result.stderr}")
                
                cmd = ["tmux", "split-window", "-v", "-t", f"{session_name}:{window_id}.0"]
                result = subprocess.run(cmd, capture_output=True, text=True)
                if result.returncode != 0:
                    logger.warning(f"Failed to create vertical split 2 in window {window_id}: {result.stderr}")
                
                cmd = ["tmux", "split-window", "-v", "-t", f"{session_name}:{window_id}.1"]
                result = subprocess.run(cmd, capture_output=True, text=True)
                if result.returncode != 0:
                    logger.warning(f"Failed to create vertical split 3 in window {window_id}: {result.stderr}")
                
                # Split each row horizontally 3 times to create 4 columns
                # Row 1 (panes 0-3)
                cmd = ["tmux", "split-window", "-h", "-t", f"{session_name}:{window_id}.0"]
                result = subprocess.run(cmd, capture_output=True, text=True)
                if result.returncode != 0:
                    logger.warning(f"Failed to create horizontal split row1-1 in window {window_id}: {result.stderr}")
                
                cmd = ["tmux", "split-window", "-h", "-t", f"{session_name}:{window_id}.0"]
                result = subprocess.run(cmd, capture_output=True, text=True)
                if result.returncode != 0:
                    logger.warning(f"Failed to create horizontal split row1-2 in window {window_id}: {result.stderr}")
                
                cmd = ["tmux", "split-window", "-h", "-t", f"{session_name}:{window_id}.1"]
                result = subprocess.run(cmd, capture_output=True, text=True)
                if result.returncode != 0:
                    logger.warning(f"Failed to create horizontal split row1-3 in window {window_id}: {result.stderr}")
                
                # Row 2 (panes 4-7)
                cmd = ["tmux", "split-window", "-h", "-t", f"{session_name}:{window_id}.4"]
                result = subprocess.run(cmd, capture_output=True, text=True)
                if result.returncode != 0:
                    logger.warning(f"Failed to create horizontal split row2-1 in window {window_id}: {result.stderr}")
                
                cmd = ["tmux", "split-window", "-h", "-t", f"{session_name}:{window_id}.4"]
                result = subprocess.run(cmd, capture_output=True, text=True)
                if result.returncode != 0:
                    logger.warning(f"Failed to create horizontal split row2-2 in window {window_id}: {result.stderr}")
                
                cmd = ["tmux", "split-window", "-h", "-t", f"{session_name}:{window_id}.5"]
                result = subprocess.run(cmd, capture_output=True, text=True)
                if result.returncode != 0:
                    logger.warning(f"Failed to create horizontal split row2-3 in window {window_id}: {result.stderr}")
                
                # Row 3 (panes 8-11)
                cmd = ["tmux", "split-window", "-h", "-t", f"{session_name}:{window_id}.8"]
                result = subprocess.run(cmd, capture_output=True, text=True)
                if result.returncode != 0:
                    logger.warning(f"Failed to create horizontal split row3-1 in window {window_id}: {result.stderr}")
                
                cmd = ["tmux", "split-window", "-h", "-t", f"{session_name}:{window_id}.8"]
                result = subprocess.run(cmd, capture_output=True, text=True)
                if result.returncode != 0:
                    logger.warning(f"Failed to create horizontal split row3-2 in window {window_id}: {result.stderr}")
                
                cmd = ["tmux", "split-window", "-h", "-t", f"{session_name}:{window_id}.9"]
                result = subprocess.run(cmd, capture_output=True, text=True)
                if result.returncode != 0:
                    logger.warning(f"Failed to create horizontal split row3-3 in window {window_id}: {result.stderr}")
                
                # Row 4 (panes 12-15)
                cmd = ["tmux", "split-window", "-h", "-t", f"{session_name}:{window_id}.12"]
                result = subprocess.run(cmd, capture_output=True, text=True)
                if result.returncode != 0:
                    logger.warning(f"Failed to create horizontal split row4-1 in window {window_id}: {result.stderr}")
                
                cmd = ["tmux", "split-window", "-h", "-t", f"{session_name}:{window_id}.12"]
                result = subprocess.run(cmd, capture_output=True, text=True)
                if result.returncode != 0:
                    logger.warning(f"Failed to create horizontal split row4-2 in window {window_id}: {result.stderr}")
                
                cmd = ["tmux", "split-window", "-h", "-t", f"{session_name}:{window_id}.13"]
                result = subprocess.run(cmd, capture_output=True, text=True)
                if result.returncode != 0:
                    logger.warning(f"Failed to create horizontal split row4-3 in window {window_id}: {result.stderr}")
                
                # Apply tiled layout for even distribution
                cmd = ["tmux", "select-layout", "-t", f"{session_name}:{window_id}", "tiled"]
                result = subprocess.run(cmd, capture_output=True, text=True)
                if result.returncode != 0:
                    logger.warning(f"Failed to apply tiled layout to window {window_id}: {result.stderr}")
                
                logger.info(f"Created {pane_count} panes in window {window_id} (4x4 layout)")
                return True
                
            elif pane_count == 32:
                # 8x4 layout (32 panes)
                # Create 8x4 grid using a more efficient approach
                # Use tiled layout after creating all panes
                
                # Create 31 additional panes (we already have 1)
                for i in range(31):
                    cmd = ["tmux", "split-window", "-t", f"{session_name}:{window_id}"]
                    result = subprocess.run(cmd, capture_output=True, text=True)
                    if result.returncode != 0:
                        logger.warning(f"Failed to create pane {i+2} in window {window_id}: {result.stderr}")
                
                # Apply tiled layout to arrange them in a grid
                cmd = ["tmux", "select-layout", "-t", f"{session_name}:{window_id}", "tiled"]
                result = subprocess.run(cmd, capture_output=True, text=True)
                if result.returncode != 0:
                    logger.warning(f"Failed to apply tiled layout to window {window_id}: {result.stderr}")
                
                logger.info(f"Created {pane_count} panes in window {window_id} (8x4 layout)")
                return True
            
            else:
                # Generic case: create required number of panes and use tiled layout
                # For large pane counts, apply tiled layout periodically to make room
                for i in range(pane_count - 1):
                    cmd = ["tmux", "split-window", "-t", f"{session_name}:{window_id}"]
                    result = subprocess.run(cmd, capture_output=True, text=True)
                    if result.returncode != 0:
                        logger.warning(f"Failed to create pane {i+2} in window {window_id}: {result.stderr}")
                    
                    # Apply tiled layout every 4 panes to ensure we have space
                    if (i + 2) % 4 == 0:
                        cmd = ["tmux", "select-layout", "-t", f"{session_name}:{window_id}", "tiled"]
                        subprocess.run(cmd, capture_output=True, text=True)
                
                # Final tiled layout
                cmd = ["tmux", "select-layout", "-t", f"{session_name}:{window_id}", "tiled"]
                result = subprocess.run(cmd, capture_output=True, text=True)
                if result.returncode != 0:
                    logger.warning(f"Failed to apply tiled layout to window {window_id}: {result.stderr}")
                
                layout_str = self._calculate_layout_for_panes(pane_count)
                logger.info(f"Created {pane_count} panes in window {window_id} ({layout_str} layout)")
                return True
            
        except Exception as e:
            logger.error(f"Failed to create panes in window {window_id}: {e}")
            return False
    
    def _distribute_desks_to_windows(self, desk_mappings: List[Dict[str, Any]]) -> Dict[str, List[Dict[str, Any]]]:
        """Distribute desk mappings to windows based on room_id"""
        distribution = {}
        
        for mapping in desk_mappings:
            room_id = mapping["room_id"]
            if room_id not in distribution:
                distribution[room_id] = []
            
            # Add window_id to mapping
            window_id = self._get_window_id_for_room(room_id)
            mapping_with_window = mapping.copy()
            mapping_with_window["window_id"] = window_id
            
            distribution[room_id].append(mapping_with_window)
        
        return distribution
    
    def _create_desk_directory(self, base_path: Path, mapping: Dict[str, Any]) -> Path:
        """Return base path without creating organization directories (agents will go to tasks or standby)"""
        # No longer create organization directories - agents go directly to tasks/ or standby/
        return base_path
    
    def _get_agent_id_from_pane_mapping(self, mapping: Dict[str, Any]) -> str:
        """Generate agent ID from pane mapping for task assignment lookup"""
        # Check if agent_id is directly provided in mapping
        if "agent_id" in mapping and mapping["agent_id"]:
            logger.debug(f"Using agent_id from mapping: {mapping['agent_id']}")
            return mapping["agent_id"]
        
        # Log warning if agent_id is missing
        logger.debug(f"No agent_id in mapping, falling back to generation. Mapping: {mapping}")
        
        # Check if desk_id already contains a well-formed agent ID
        desk_id = mapping.get("desk_id", "")
        
        # If desk_id looks like a proper agent ID (e.g., dev01-dev-r1-d1), use it directly
        if desk_id and desk_id.startswith("dev") and "-" in desk_id and len(desk_id.split("-")) >= 3:
            return desk_id
        
        # Otherwise, generate agent ID from org/role/room
        org_id = mapping["org_id"]  # "org-01"
        role = mapping["role"]      # "pm", "worker-a", "worker-b", "worker-c", "ceo", "cto", "coo", "assistant"
        room_id = mapping["room_id"]  # "room-01", "room-02", "room-executive"
        
        # Extract organization number
        org_num = org_id.split("-")[1] if "-" in org_id else "01"
        
        # Convert role to agent format
        if role == "pm":
            role_part = "pm"
        elif role in ["ceo", "cto", "coo", "assistant"]:
            # Executive roles keep their original names
            role_part = role
        elif role == "developer":
            # Simple developer role - default to wk-a
            role_part = "wk-a"
        elif "-" in role:
            # "worker-a" → "wk-a"
            worker_suffix = role.split("-")[1]  # "a", "b", "c"
            role_part = f"wk-{worker_suffix}"
        else:
            # Default fallback
            role_part = "wk-a"
        
        # Convert room to agent format dynamically based on room order
        # Get the window/room index from the actual room configuration
        if hasattr(self, '_current_space_crd') and self._current_space_crd:
            # Find room index from CRD
            room_index = 0
            company = self._current_space_crd.spec.nations[0].cities[0].villages[0].companies[0]
            for building in company.buildings:
                for floor in building.floors:
                    for idx, room in enumerate(floor.rooms):
                        if room.id == room_id:
                            room_index = idx
                            break
            # Convert index to room part: 0->r1, 1->r2, etc.
            room_part = f"r{room_index + 1}"
        else:
            # Fallback: try to load from saved room-window mapping
            for session_name in (self.active_sessions.keys() if hasattr(self, 'active_sessions') and self.active_sessions else []):
                mapping = self._load_room_window_mapping(session_name)
                if mapping and room_id in mapping:
                    room_index = mapping[room_id]
                    room_part = f"r{room_index + 1}"
                    break
            else:
                # If no mapping found, default to r1
                logger.warning(f"No room mapping found for {room_id}, defaulting to r1")
                room_part = "r1"
        
        # Generate agent ID: org01-pm-r1, org01-wk-a-r2, org05-ceo-re, etc.
        agent_id = f"org{org_num}-{role_part}-{room_part}"
        return agent_id
    
    def _get_task_directory_for_agent(self, agent_id: str, base_path: Path) -> Optional[Path]:
        """Get task worktree directory for assigned agent"""
        # Get task assignment for this agent
        task_info = self.get_task_by_assignee(agent_id)
        
        if task_info:
            # Return path to task worktree directory
            worktree_path = base_path / task_info["worktree_path"]
            if worktree_path.exists():
                logger.debug(f"Agent {agent_id} assigned to task {task_info['name']} → {worktree_path}")
                return worktree_path
            else:
                logger.warning(f"Task worktree directory not found: {worktree_path}")
        
        return None
    
    def _update_pane_in_window(self, session_name: str, window_id: str, pane_index: int, 
                              mapping: Dict[str, Any], desk_dir: Path) -> bool:
        """Update pane directory and title in specific window with task assignment or standby location"""
        try:
            # Check for task assignment first using log files
            agent_id = self._get_agent_id_from_pane_mapping(mapping)
            base_path = desk_dir  # desk_dir is now the base_path directly
            
            # Try to update from task logs (for agents with task assignments)
            task_updated = self._update_pane_from_task_logs(session_name, window_id, pane_index, mapping, base_path)
            
            if task_updated:
                # Agent was moved to task directory via task logs
                logger.debug(f"Agent {agent_id} moved to task directory via task logs")
                return True
            
            # No task assignment - move to standby location
            standby_dir = base_path / "standby"
            standby_dir.mkdir(exist_ok=True)
            
            # Create standby README if it doesn't exist
            readme_file = standby_dir / "README.md"
            if not readme_file.exists():
                with open(readme_file, 'w', encoding='utf-8') as f:
                    f.write("# 待機中エージェント\n\n")
                    f.write("このディレクトリには、現在タスクブランチが割り当てられていないエージェントが配置されています。\n\n")
                    f.write("## エージェント状況\n")
                    f.write("- タスクブランチ割り当てありエージェント → `../tasks/` ディレクトリ\n")
                    f.write("- タスクブランチ待機中エージェント → このディレクトリ\n\n")
                    f.write("新しいタスクブランチが作成されると、自動的にタスクブランチディレクトリに移動します。\n")
            
            # Always use absolute path but make it cleaner with ~ if possible
            absolute_path = str(standby_dir.absolute())
            home_path = str(Path.home())
            
            # Try to use ~ prefix for paths under home directory
            if absolute_path.startswith(home_path):
                standby_path = "~" + absolute_path[len(home_path):]
            else:
                standby_path = absolute_path
            
            # Just change directory, don't start claude automatically
            cmd = ["tmux", "send-keys", "-t", f"{session_name}:{window_id}.{pane_index}", 
                   f"cd {standby_path}", "Enter"]
            result1 = subprocess.run(cmd, capture_output=True, text=True)
            
            # Set standby pane title with agent ID and standby directory
            standby_title = f"{agent_id} - standby"
            cmd = ["tmux", "select-pane", "-t", f"{session_name}:{window_id}.{pane_index}", "-T", standby_title]
            result2 = subprocess.run(cmd, capture_output=True, text=True)
            
            if result1.returncode == 0 and result2.returncode == 0:
                logger.info(f"📍 Agent {agent_id} placed in standby location: {standby_path}")
                return True
            else:
                logger.error(f"Failed to place agent {agent_id} in standby location")
                return False
            
        except Exception as e:
            logger.error(f"Failed to update pane {pane_index} in window {window_id}: {e}")
            return False
    
    def _update_pane_from_task_logs(self, session_name: str, window_id: str, pane_index: int,
                                   mapping: Dict[str, Any], base_path: Path) -> bool:
        """Update pane directory based on task assignment logs"""
        try:
            import json
            
            # Generate agent ID from pane mapping
            agent_id = self._get_agent_id_from_pane_mapping(mapping)
            logger.debug(f"Checking task logs for agent {agent_id} (pane {window_id}.{pane_index})")
            
            # Look for task assignment logs in tasks directory
            tasks_path = base_path / "tasks"
            if not tasks_path.exists():
                logger.debug(f"No tasks directory found: {tasks_path}")
                return False
            
            # Search through all task directories for agent assignment logs
            assigned_task_dir = None
            task_info = None
            
            # Get all task directories - support both flat and nested structures
            task_dirs = []
            if tasks_path.exists():
                # First level: tasks/task_name or tasks/main
                for item in tasks_path.iterdir():
                    if item.is_dir() and item.name != "main":
                        task_dirs.append(item)
                
                # Second level: tasks/category/task_name (for feature/, bugfix/, etc.)
                for category_dir in tasks_path.iterdir():
                    if category_dir.is_dir() and category_dir.name != "main":
                        for task_dir in category_dir.iterdir():
                            if task_dir.is_dir():
                                task_dirs.append(task_dir)
            
            # Search through all collected task directories
            for task_dir in task_dirs:
                log_file = task_dir / ".haconiwa" / "agent_assignment.json"
                if log_file.exists():
                    try:
                        with open(log_file, 'r', encoding='utf-8') as f:
                            assignments = json.load(f)
                            if not isinstance(assignments, list):
                                assignments = [assignments]
                            
                            # Check if this agent is assigned to this task
                            for assignment in assignments:
                                if (assignment.get("agent_id") == agent_id and 
                                    assignment.get("space_session") == session_name and
                                    assignment.get("status") == "active"):
                                    
                                    assigned_task_dir = task_dir
                                    task_info = assignment
                                    logger.info(f"Found task assignment: {agent_id} → {task_dir.name}")
                                    break
                            
                            if assigned_task_dir:
                                break
                                    
                    except Exception as e:
                        logger.warning(f"Could not read assignment log {log_file}: {e}")
            
            # If agent has task assignment, move to task directory
            if assigned_task_dir and task_info:
                return self._move_pane_to_task_directory(session_name, window_id, pane_index, 
                                                       assigned_task_dir, task_info, mapping)
            else:
                logger.debug(f"No active task assignment found for agent {agent_id}")
                return False  # No task assigned - proceed to standby placement
                
        except Exception as e:
            logger.error(f"Error updating pane from task logs: {e}")
            return False
    
    def _move_pane_to_task_directory(self, session_name: str, window_id: str, pane_index: int,
                                   task_dir: Path, task_info: Dict[str, Any], mapping: Dict[str, Any]) -> bool:
        """Move pane to assigned task directory"""
        try:
            agent_id = task_info["agent_id"]
            task_name = task_info["task_name"]
            
            # Use tilde path without quotes 
            absolute_path = str(task_dir.absolute())
            home_path = str(Path.home())
            
            # Use ~ prefix for paths under home directory
            if absolute_path.startswith(home_path):
                task_path = "~" + absolute_path[len(home_path):]
            else:
                task_path = absolute_path
            
            # Update pane working directory to task directory
            # Check if claude is already running by checking the pane's current command
            check_cmd = ["tmux", "display-message", "-t", f"{session_name}:{window_id}.{pane_index}", "-p", "#{pane_current_command}"]
            check_result = subprocess.run(check_cmd, capture_output=True, text=True)
            
            if check_result.returncode == 0 and check_result.stdout.strip() == "node":
                # Claude is already running, use /cwd command
                cmd = ["tmux", "send-keys", "-t", f"{session_name}:{window_id}.{pane_index}", 
                       f"/cwd {task_path}", "Enter"]
            else:
                # Claude is not running, cd then start
                cmd = ["tmux", "send-keys", "-t", f"{session_name}:{window_id}.{pane_index}", 
                       f"cd {task_path} && claude", "Enter"]
            
            result1 = subprocess.run(cmd, capture_output=True, text=True)
            
            # Update pane title with agent ID and task directory
            new_title = f"{agent_id} - {task_name}"
            cmd = ["tmux", "select-pane", "-t", f"{session_name}:{window_id}.{pane_index}", "-T", new_title]
            result2 = subprocess.run(cmd, capture_output=True, text=True)
            
            if result1.returncode == 0 and result2.returncode == 0:
                logger.info(f"✅ Moved agent {agent_id} to task directory: {task_path}")
                logger.info(f"   📍 Pane: {window_id}.{pane_index}")
                logger.info(f"   📝 Task: {task_name}")
                
                # Update agent assignment log with actual pane information
                self._update_agent_assignment_log_with_pane_info(task_dir, agent_id, session_name, window_id, pane_index)
                
                return True
            else:
                logger.error(f"Failed to move pane {window_id}.{pane_index} to task directory")
                logger.error(f"   send-keys result: {result1.returncode}, select-pane result: {result2.returncode}")
                return False
                
        except Exception as e:
            logger.error(f"Error moving pane to task directory: {e}")
            return False
    
    def _update_agent_assignment_log_with_pane_info(self, task_dir: Path, agent_id: str, session_name: str, window_id: str, pane_index: int) -> bool:
        """Update agent assignment log with actual pane information"""
        try:
            import json
            
            # Path to agent assignment log file
            log_file = task_dir / ".haconiwa" / "agent_assignment.json"
            
            if not log_file.exists():
                logger.warning(f"Agent assignment log file not found: {log_file}")
                return False
            
            # Read current log file
            with open(log_file, 'r', encoding='utf-8') as f:
                data = json.load(f)
            
            # Ensure data is a list
            if not isinstance(data, list):
                data = [data]
            
            # Find and update the agent assignment
            updated = False
            for assignment in data:
                if (assignment.get("agent_id") == agent_id and 
                    assignment.get("space_session") == session_name and
                    assignment.get("status") == "active"):
                    
                    # Update with actual pane information
                    assignment["tmux_window"] = window_id
                    assignment["tmux_pane"] = int(pane_index)
                    updated = True
                    logger.info(f"📝 Updated log: {agent_id} → window {window_id}, pane {pane_index}")
                    break
            
            if updated:
                # Save updated log
                with open(log_file, 'w', encoding='utf-8') as f:
                    json.dump(data, f, indent=2, ensure_ascii=False)
                logger.info(f"✅ Updated agent assignment log with pane info: {log_file}")
                return True
            else:
                logger.warning(f"Could not find agent assignment for {agent_id} in log file")
                return False
                
        except Exception as e:
            logger.error(f"Error updating agent assignment log with pane info: {e}")
            return False
    
    def _get_room_window_mapping(self, rooms: List[Dict[str, Any]]) -> Dict[str, Dict[str, str]]:
        """Get room to window ID mapping"""
        mapping = {}
        for i, room in enumerate(rooms):
            room_id = room["id"]
            room_name = room["name"]
            mapping[room_id] = {
                "window_id": str(i),
                "name": room_name
            }
        return mapping
    
    def _get_window_id_for_room(self, room_id: str) -> str:
        """Get window ID for specific room"""
        # Map room IDs to window IDs based on their order in the active session
        if hasattr(self, 'active_sessions') and self.active_sessions:
            # Get the first active session
            session_data = next(iter(self.active_sessions.values()), {})
            
            # First check if we have stored rooms list (preferred method)
            rooms = session_data.get('rooms', [])
            if rooms:
                for idx, room in enumerate(rooms):
                    if room.get('id') == room_id:
                        return str(idx)
            
            # Fallback to desk_distribution if rooms not stored
            desk_distribution = session_data.get('desk_distribution', {})
            room_ids = list(desk_distribution.keys())
            
            # Find the index of this room_id
            if room_id in room_ids:
                idx = room_ids.index(room_id)
                # Validate against actual room count
                if rooms and idx >= len(rooms):
                    logger.warning(f"Room index {idx} exceeds actual room count {len(rooms)} for {room_id}")
                    return "0"
                return str(idx)
        
        # Try to load from saved room-window mapping
        # First try all active sessions
        for session_name in (self.active_sessions.keys() if hasattr(self, 'active_sessions') and self.active_sessions else []):
            mapping = self._load_room_window_mapping(session_name)
            if mapping and room_id in mapping:
                logger.debug(f"Found room {room_id} in saved mapping for session {session_name}: window {mapping[room_id]}")
                return str(mapping[room_id])
        
        # If not found, try to find mapping file in current directory structure
        # This handles cases where active_sessions is not yet populated
        import glob
        mapping_files = glob.glob("*/.haconiwa/room_window_mapping.json")
        for mapping_file in mapping_files:
            try:
                with open(mapping_file, 'r') as f:
                    all_mappings = json.load(f)
                    for session_name, session_mapping in all_mappings.items():
                        if room_id in session_mapping:
                            logger.debug(f"Found room {room_id} in mapping file {mapping_file}: window {session_mapping[room_id]}")
                            return str(session_mapping[room_id])
            except Exception as e:
                logger.debug(f"Could not read mapping file {mapping_file}: {e}")
        
        # Final fallback: default to window 0
        logger.warning(f"Could not determine window for room {room_id}, defaulting to window 0")
        return "0"
    
    def _calculate_panes_per_window(self, grid: str, room_count: int) -> Dict[str, Any]:
        """Calculate panes per window based on grid and room count"""
        # Parse grid to get total panes
        try:
            cols, rows = map(int, grid.split('x'))
            total_panes = cols * rows
        except:
            total_panes = 16  # Default fallback
            cols, rows = 4, 4
        
        # For single room, all panes go to that room
        if room_count == 1:
            return {
                "total_panes": total_panes,
                "panes_per_window": total_panes,
                "layout_per_window": f"{cols}x{rows}"
            }
        
        # For multiple rooms, distribute panes evenly
        panes_per_room = total_panes // room_count
        remainder = total_panes % room_count
        
        # Special handling for known configurations
        if grid == "8x4" and room_count == 3:
            # Special case: 32 panes, 3 rooms -> 8, 8, 4 for executive
            return {
                "total_panes": 20,  # Reduced total for executive room
                "panes_per_window": {"room-01": 8, "room-02": 8, "room-executive": 4},
                "layout_per_window": {"room-01": "2x4", "room-02": "2x4", "room-executive": "1x4"}
            }
        
        # Generic distribution
        return {
            "total_panes": total_panes,
            "panes_per_window": panes_per_room,
            "layout_per_window": self._calculate_layout_for_panes(panes_per_room)
        }
    
    def _calculate_layout_for_panes(self, pane_count: int) -> str:
        """Calculate optimal layout string for given pane count"""
        if pane_count == 1:
            return "1x1"
        elif pane_count == 2:
            return "2x1"
        elif pane_count == 3:
            return "3x1"
        elif pane_count == 4:
            return "2x2"
        elif pane_count <= 6:
            return "3x2"
        elif pane_count <= 8:
            return "4x2"
        elif pane_count <= 9:
            return "3x3"
        elif pane_count <= 12:
            return "4x3"
        elif pane_count <= 16:
            return "4x4"
        elif pane_count <= 20:
            return "5x4"
        elif pane_count <= 25:
            return "5x5"
        else:
            # For larger counts, try to keep it roughly square
            import math
            cols = int(math.ceil(math.sqrt(pane_count)))
            rows = int(math.ceil(pane_count / cols))
            return f"{cols}x{rows}"
    
    def create_room_layout(self, session_name: str, room_config: Dict[str, Any]) -> bool:
        """Create layout for specific room"""
        try:
            room_id = room_config["id"]
            desks = room_config.get("desks", [])
            
            logger.info(f"Creating room layout: {room_id} with {len(desks)} desks")
            
            # This is a simplified implementation
            # In a full implementation, this would handle room-specific layouts
            return True
            
        except Exception as e:
            logger.error(f"Failed to create room layout: {e}")
            return False
    
    def extract_agent_config(self, desk_config: Dict[str, Any]) -> Dict[str, Any]:
        """Extract agent configuration from desk config"""
        agent = desk_config.get("agent", {})
        return {
            "name": agent.get("name", ""),
            "role": agent.get("role", "worker"),
            "model": agent.get("model", "gpt-4o"),
            "env": agent.get("env", {}),
            "desk_id": desk_config["id"]
        }
    
    def update_pane_title(self, session_name: str, pane_index: int, config: Dict[str, Any]) -> bool:
        """Update tmux pane title"""
        title = config.get("title", f"Pane {pane_index}")
        cmd = ["tmux", "select-pane", "-t", f"{session_name}:0.{pane_index}", "-T", title]
        result = subprocess.run(cmd, capture_output=True, text=True)
        return result.returncode == 0
    
    def create_task_worktree(self, task_config: Dict[str, Any]) -> bool:
        """Create Git worktree for task"""
        try:
            branch = task_config["branch"]
            base_path = task_config["base_path"]
            
            # Create worktree directory
            worktree_path = Path(base_path) / "worktrees" / branch
            
            cmd = ["git", "worktree", "add", str(worktree_path), branch]
            result = subprocess.run(cmd, capture_output=True, text=True, cwd=base_path)
            
            if result.returncode == 0:
                logger.info(f"Created worktree for branch {branch}")
                return True
            else:
                logger.error(f"Failed to create worktree: {result.stderr}")
                return False
                
        except Exception as e:
            logger.error(f"Failed to create task worktree: {e}")
            return False
    
    def switch_to_room(self, session_name: str, room_id: str) -> bool:
        """Switch to specific room (tmux window)"""
        try:
            window_id = self._get_window_id_for_room(room_id)
            cmd = ["tmux", "select-window", "-t", f"{session_name}:{window_id}"]
            result = subprocess.run(cmd, capture_output=True, text=True)
            
            if result.returncode == 0:
                logger.info(f"Switched to {room_id} (window {window_id})")
                return True
            else:
                logger.error(f"Failed to switch to {room_id}: {result.stderr}")
                return False
            
        except Exception as e:
            logger.error(f"Failed to switch to room {room_id}: {e}")
            return False
    
    def calculate_layout(self, grid: str) -> Dict[str, Any]:
        """Calculate layout parameters"""
        if grid == "8x4":
            return {
                "columns": 8,
                "rows": 4,
                "total_panes": 32,
                "panes_per_room": 16
            }
        else:
            # Default fallback
            return {
                "columns": 4,
                "rows": 4,
                "total_panes": 16,
                "panes_per_room": 16
            }
    
    def distribute_organizations(self, organizations: List[Dict[str, Any]], room_count: int) -> List[Dict[str, Any]]:
        """Distribute organizations across rooms"""
        rooms = []
        for i in range(room_count):
            room_id = f"room-{i+1:02d}"
            room_name = ["Alpha Room", "Beta Room"][i] if i < 2 else f"Room {i+1}"
            
            rooms.append({
                "id": room_id,
                "name": room_name,
                "organizations": organizations.copy()  # All orgs in each room
            })
        
        return rooms
    
    def cleanup_session(self, session_name: str, purge_data: bool = False) -> bool:
        """Clean up tmux session and optionally data"""
        try:
            # Kill tmux session
            cmd = ["tmux", "kill-session", "-t", session_name]
            result = subprocess.run(cmd, capture_output=True, text=True)
            
            # Remove from active sessions
            if session_name in self.active_sessions:
                del self.active_sessions[session_name]
            
            logger.info(f"Cleaned up session: {session_name}")
            return result.returncode == 0
            
        except Exception as e:
            logger.error(f"Failed to cleanup session {session_name}: {e}")
            return False
    
    def attach_to_room(self, session_name: str, room_id: str) -> bool:
        """Attach to specific room in session"""
        try:
            # Switch to room first
            self.switch_to_room(session_name, room_id)
            
            # Attach to session
            cmd = ["tmux", "attach-session", "-t", session_name]
            result = subprocess.run(cmd, capture_output=True, text=True)
            
            return result.returncode == 0
            
        except Exception as e:
            logger.error(f"Failed to attach to room {room_id}: {e}")
            return False
    
    def list_spaces(self) -> List[Dict[str, Any]]:
        """List all running Haconiwa spaces (tmux sessions)"""
        spaces = []
        
        try:
            # Get actual tmux sessions
            result = subprocess.run(['tmux', 'list-sessions', '-F', '#{session_name}:#{session_windows}'], 
                                   capture_output=True, text=True)
            
            if result.returncode != 0:
                logger.warning("No tmux sessions found or tmux not available")
                return spaces
            
            for line in result.stdout.strip().split('\n'):
                if not line:
                    continue
                
                try:
                    session_name, window_count = line.split(':')
                    
                    # Check if this looks like a haconiwa session
                    if self._is_haconiwa_session(session_name):
                        # Get pane count for this specific session only
                        pane_result = subprocess.run(['tmux', 'list-panes', '-t', session_name, '-a', '-F', '#{session_name}:#{window_index}.#{pane_index}'], 
                                                   capture_output=True, text=True)
                        
                        if pane_result.returncode == 0:
                            # Count panes that belong to this session only
                            panes_for_session = [line for line in pane_result.stdout.strip().split('\n') 
                                               if line.startswith(f"{session_name}:")]
                            pane_count = len(panes_for_session)
                        else:
                            pane_count = 0
                        
                        spaces.append({
                            "name": session_name,
                            "status": "active",
                            "rooms": int(window_count),
                            "panes": pane_count
                        })
                        
                except ValueError:
                    continue
            
            return spaces
            
        except Exception as e:
            logger.error(f"Failed to list spaces: {e}")
            return spaces
    
    def _is_haconiwa_session(self, session_name: str) -> bool:
        """Check if a tmux session is a Haconiwa session"""
        # Simple heuristic: sessions ending with "-company" or having specific patterns
        return (session_name.endswith('-company') or 
                session_name in self.active_sessions or
                any(keyword in session_name.lower() for keyword in ['test', 'multiroom', 'enterprise']))
    
    def _send_claude_command_to_all_panes(self, session_name: str, rooms: List[Dict[str, Any]], desk_distribution: Dict[str, List[Dict[str, Any]]]) -> None:
        """Send 'claude' command to all panes after setup"""
        try:
            logger.info("🤖 Sending claude command to all panes...")
            
            # Send command to each room's panes
            for room_idx, room in enumerate(rooms):
                room_id = room["id"]
                window_id = str(room_idx)
                
                # Get desks for this room
                desks_in_room = desk_distribution.get(room_id, [])
                
                for pane_index, desk_mapping in enumerate(desks_in_room):
                    # Send claude command to this pane
                    cmd = ["tmux", "send-keys", "-t", f"{session_name}:{window_id}.{pane_index}", 
                           "claude", "Enter"]
                    result = subprocess.run(cmd, capture_output=True, text=True)
                    
                    if result.returncode == 0:
                        logger.debug(f"✅ Sent claude command to pane {window_id}.{pane_index}")
                    else:
                        logger.warning(f"Failed to send claude command to pane {window_id}.{pane_index}: {result.stderr}")
            
            logger.info("✅ Claude command sent to all panes")
            
        except Exception as e:
            logger.error(f"Failed to send claude commands: {e}")
    
    def start_company(self, company_name: str) -> bool:
        """Not implemented"""
        return False
    def clone_repository(self, company_name: str) -> bool:
        """Not implemented"""
        return False
    
    def _configure_pane_borders(self, session_name: str):
        """Configure pane borders and titles for tmux session"""
        try:
            # Configure pane borders and titles at session level
            cmd1 = ["tmux", "set-option", "-t", session_name, "pane-border-status", "top"]
            result1 = subprocess.run(cmd1, capture_output=True, text=True)
            
            cmd2 = ["tmux", "set-option", "-t", session_name, "pane-border-format", "#{pane_title}"]
            result2 = subprocess.run(cmd2, capture_output=True, text=True)
            
            # Also set for each window to ensure it's applied
            windows_result = subprocess.run(
                ["tmux", "list-windows", "-t", session_name, "-F", "#{window_index}"],
                capture_output=True, text=True
            )
            
            if windows_result.returncode == 0:
                for window_id in windows_result.stdout.strip().split('\n'):
                    if window_id:
                        # Set pane border options for each window
                        subprocess.run(
                            ["tmux", "set-option", "-t", f"{session_name}:{window_id}", 
                             "pane-border-status", "top"],
                            capture_output=True, text=True
                        )
                        subprocess.run(
                            ["tmux", "set-option", "-t", f"{session_name}:{window_id}", 
                             "pane-border-format", "#{pane_title}"],
                            capture_output=True, text=True
                        )
            
            if result1.returncode == 0 and result2.returncode == 0:
                logger.info(f"Configured pane borders for session and all windows: {session_name}")
            else:
                logger.warning(f"Failed to configure pane borders: {result1.stderr} {result2.stderr}")
        
        except Exception as e:
            logger.error(f"Failed to configure pane borders: {e}")

    def _clone_repository_to_tasks(self, git_config: Dict[str, Any], main_repo_path: Path, force_clone: bool) -> bool:
        """Clone repository to tasks/main/ with improved error handling and user confirmation"""
        try:
            import subprocess
            import shutil
            
            # Create parent directory
            main_repo_path.parent.mkdir(parents=True, exist_ok=True)
            
            # Prepare clone command
            url = git_config["url"]
            auth = git_config.get("auth", "https")
            
            # Check if target directory already exists
            if main_repo_path.exists():
                # Check if it's already a git repository
                git_dir = main_repo_path / ".git"
                if git_dir.exists():
                    logger.info(f"Directory {main_repo_path} is already a git repository, skipping clone")
                    return True
                
                # Check if directory is empty
                if any(main_repo_path.iterdir()):
                    logger.warning(f"⚠️ Directory '{main_repo_path}' already exists and is not empty.")
                    
                    # Show existing contents (first few items)
                    items = list(main_repo_path.iterdir())
                    logger.info("📁 Existing contents:")
                    for i, item in enumerate(items[:5]):  # Show max 5 items
                        item_type = "📁" if item.is_dir() else "📄"
                        logger.info(f"   {item_type} {item.name}")
                    
                    if len(items) > 5:
                        logger.info(f"   ... and {len(items) - 5} more items")
                    
                    # Ask for confirmation unless force flag is set
                    if not force_clone:
                        logger.info("\n🤔 This will replace the existing directory with the Git repository.")
                        
                        # Import typer for confirmation prompt
                        try:
                            import typer
                            continue_anyway = typer.confirm("Do you want to continue and replace the directory?")
                            if not continue_anyway:
                                logger.info("❌ Git clone operation cancelled by user.")
                                logger.info("Continuing without Git repository setup")
                                return True  # Not critical failure, continue without Git
                        except ImportError:
                            # Fallback to input() if typer not available
                            response = input("Do you want to continue and replace the directory? (y/N): ")
                            if response.lower() not in ['y', 'yes']:
                                logger.info("❌ Git clone operation cancelled by user.")
                                logger.info("Continuing without Git repository setup")
                                return True
                    else:
                        logger.info("\n🔨 --force-clone flag is set, replacing directory...")
                    
                    # Remove existing directory
                    shutil.rmtree(main_repo_path)
                    logger.info(f"Removed existing directory: {main_repo_path}")
                else:
                    # Directory exists but is empty, remove it and clone
                    logger.info(f"Empty directory {main_repo_path} exists, removing and cloning")
                    main_repo_path.rmdir()
            
            cmd = ["git", "clone", url, str(main_repo_path)]
            
            # Execute clone
            result = subprocess.run(cmd, capture_output=True, text=True, timeout=300)
            
            if result.returncode == 0:
                logger.info(f"✅ Successfully cloned repository from {url}")
                
                # Checkout and pull the specified default branch
                default_branch = git_config.get("defaultBranch", "main")
                logger.info(f"Checking out and pulling branch: {default_branch}")
                
                # Fetch all branches first
                fetch_cmd = ["git", "-C", str(main_repo_path), "fetch", "origin"]
                fetch_result = subprocess.run(fetch_cmd, capture_output=True, text=True)
                if fetch_result.returncode != 0:
                    logger.warning(f"Failed to fetch branches: {fetch_result.stderr}")
                
                # Checkout the default branch
                checkout_cmd = ["git", "-C", str(main_repo_path), "checkout", default_branch]
                checkout_result = subprocess.run(checkout_cmd, capture_output=True, text=True)
                if checkout_result.returncode != 0:
                    logger.warning(f"Failed to checkout {default_branch}: {checkout_result.stderr}")
                
                # Pull latest changes
                pull_cmd = ["git", "-C", str(main_repo_path), "pull", "origin", default_branch]
                pull_result = subprocess.run(pull_cmd, capture_output=True, text=True)
                if pull_result.returncode != 0:
                    logger.warning(f"Failed to pull {default_branch}: {pull_result.stderr}")
                else:
                    logger.info(f"✅ Successfully checked out and pulled {default_branch} branch")
                
                # After repository is set up, set default branch for TaskManager
                space_ref = git_config.get("space_ref")
                if space_ref and default_branch:
                    logger.info(f"Setting TaskManager default branch to: {default_branch}")
                    from ..task.manager import TaskManager
                    task_manager = TaskManager()
                    task_manager.set_default_branch(default_branch)
                
                return True
            else:
                logger.error(f"❌ Failed to clone repository: {result.stderr}")
                return False
                
        except subprocess.TimeoutExpired:
            logger.error("❌ Git clone operation timed out")
            return False
        except Exception as e:
            logger.error(f"❌ Error during git clone: {e}")
            return False
    
    def update_all_panes_from_task_logs(self, session_name: str, space_ref: str) -> int:
        """Update pane directories from all .haconiwa/agent_assignment.json files"""
        try:
            updated_count = 0
            
            # Get base path from space_ref
            # Try to get organization base path first from current applier instance
            import sys
            org_base_path = None
            if hasattr(sys.modules['__main__'], '_current_applier'):
                applier = sys.modules['__main__']._current_applier
                org_base_path = applier._get_organization_base_path(space_ref)
            
            if org_base_path:
                base_path = Path(org_base_path)
            else:
                # Fallback to space_ref directory
                base_path = Path(f"./{space_ref}")
                if not base_path.exists():
                    base_path = Path("./test-world-multiroom-tasks")
                    if not base_path.exists():
                        logger.warning(f"Cannot find base path for space: {space_ref}")
                        return 0
            
            logger.info(f"🔄 Re-checking task logs for all panes in session: {session_name}")
            logger.info(f"📁 Using base path: {base_path}")
            
            # Get all windows in the session
            cmd = ["tmux", "list-windows", "-t", session_name, "-F", "#{window_index}:#{window_name}"]
            result = subprocess.run(cmd, capture_output=True, text=True)
            
            if result.returncode != 0:
                logger.error(f"Failed to list windows: {result.stderr}")
                return 0
            
            # Process each window
            for line in result.stdout.strip().split('\n'):
                if not line:
                    continue
                    
                window_id, window_name = line.split(':', 1)
                
                # Get all panes in this window
                cmd = ["tmux", "list-panes", "-t", f"{session_name}:{window_id}", "-F", "#{pane_index}"]
                pane_result = subprocess.run(cmd, capture_output=True, text=True)
                
                if pane_result.returncode == 0:
                    for pane_line in pane_result.stdout.strip().split('\n'):
                        if not pane_line:
                            continue
                            
                        pane_index = int(pane_line)
                        
                        # Create a minimal mapping for agent ID generation
                        # We'll reconstruct it from the window/pane position
                        mapping = self._reconstruct_mapping_from_position(window_id, pane_index)
                        
                        # Check for task assignment and update if found
                        success = self._update_pane_from_task_logs(session_name, window_id, pane_index, mapping, base_path)
                        if success:
                            # Check if agent was actually moved to task directory
                            if self._check_if_pane_moved_to_task(session_name, window_id, pane_index):
                                updated_count += 1
                                agent_id = self._get_agent_id_from_pane_mapping(mapping)
                                logger.debug(f"Agent {agent_id} successfully updated to task directory")
            
            logger.info(f"🎯 Updated {updated_count} agent panes based on task logs")
            return updated_count
            
        except Exception as e:
            logger.error(f"Failed to update panes from task logs: {e}")
            return 0
    
    def _reconstruct_mapping_from_position(self, window_id: str, pane_index: int) -> Dict[str, Any]:
        """Reconstruct desk mapping based on window and pane position"""
        # This is a fallback method and may not be fully accurate
        return {
            "org_id": f"org-{pane_index // 4 + 1:02d}",
            "role": ["pm", "worker-a", "worker-b", "worker-c"][pane_index % 4],
            "room_id": "room-frontend" if window_id == "0" else "room-backend",
            "desk_id": f"desk-{'room-frontend' if window_id == '0' else 'room-backend'}-{pane_index // 4 + 1:02d}-{pane_index % 4:02d}"
        }
    
    def _check_if_pane_moved_to_task(self, session_name: str, window_id: str, pane_index: int) -> bool:
        """Check if a pane is already in a task directory"""
        try:
            # Get current path of the pane
            cmd = ["tmux", "list-panes", "-t", f"{session_name}:{window_id}", 
                   "-F", "#{pane_index}:#{pane_current_path}"]
            result = subprocess.run(cmd, capture_output=True, text=True)
            
            if result.returncode == 0:
                for line in result.stdout.strip().split('\n'):
                    if line.startswith(f"{pane_index}:"):
                        current_path = line.split(':', 1)[1]
                        # Check if path contains 'tasks/' indicating it's in a task directory
                        return "/tasks/" in current_path
            
            return False
            
        except Exception as e:
            logger.error(f"Error checking pane path: {e}")
            return False
    
    def _cleanup_existing_session(self, session_name: str):
        """Cleanup existing tmux session and associated directories"""
        try:
            # Check if session exists first
            check_cmd = ["tmux", "has-session", "-t", session_name]
            check_result = subprocess.run(check_cmd, capture_output=True, text=True)
            
            if check_result.returncode == 0:
                # Session exists, kill it
                kill_cmd = ["tmux", "kill-session", "-t", session_name]
                kill_result = subprocess.run(kill_cmd, capture_output=True, text=True)
                
                if kill_result.returncode == 0:
                    logger.debug(f"Cleaned up existing session: {session_name}")
                else:
                    logger.warning(f"Failed to clean up existing session: {kill_result.stderr}")
            else:
                logger.debug(f"No existing session to clean up: {session_name}")
        
        except Exception as e:
            logger.warning(f"Error during session cleanup: {e}")
    
    def _display_created_structure(self, base_path: Path, organizations: List[Dict[str, Any]], total_panes: int = 32, room_count: int = 2) -> None:
        """Display visual representation of the created structure"""
        from rich.console import Console
        from rich.panel import Panel
        from rich.columns import Columns
        
        console = Console()
        
        # Get task assignments for display
        task_assignments = self._get_current_task_assignments()
        
        # Create main world hierarchy tree
        world_tree = self._create_world_hierarchy_tree(base_path, organizations, task_assignments)
        
        # Create directory structure tree
        directory_tree = self._create_directory_structure_tree(base_path, organizations, total_panes, room_count)
        
        # Create task assignment table
        task_table = self._create_task_assignment_table(task_assignments)
        
        # Display all components
        console.print()
        
        # World Hierarchy
        console.print(Panel.fit(
            world_tree,
            title="[bold blue]🌍 ワールド空間階層[/bold blue]",
            style="blue",
            subtitle="[dim]論理構造とエージェント割り当て[/dim]"
        ))
        
        # Directory Structure and Task Assignments side by side
        if task_assignments:
            columns = Columns([
                Panel.fit(directory_tree, title="[bold green]📁 ディレクトリ構造[/bold green]", style="green"),
                Panel.fit(task_table, title="[bold yellow]🎯 タスクブランチ割り当て[/bold yellow]", style="yellow")
            ], equal=True)
            console.print(columns)
        else:
            console.print(Panel.fit(
                directory_tree,
                title="[bold green]📁 ディレクトリ構造[/bold green]",
                style="green"
            ))
        
        console.print()
    
    def _create_world_hierarchy_tree(self, base_path: Path, organizations: List[Dict[str, Any]], task_assignments: Dict[str, Any]):
        """Create Rich tree for world hierarchy"""
        from rich.tree import Tree
        
        tree = Tree(f"🌍 [bold cyan]World: {base_path.name}[/bold cyan]")
        
        # Get actual space configuration from active session
        session_config = None
        company_name = "Unknown Company"
        for session_name, session_info in self.active_sessions.items():
            if Path(session_info.get("base_path", "")) == base_path:
                session_config = session_info.get("config", {})
                company_name = session_config.get("name", "Unknown Company")
                break
        
        # Get actual CRD data if available
        space_crd = None
        if hasattr(self, '_current_space_crd'):
            space_crd = self._current_space_crd
        
        # Build hierarchy from CRD or use minimal defaults
        if space_crd and hasattr(space_crd.spec, 'nations') and space_crd.spec.nations:
            nation = space_crd.spec.nations[0]
            nation_branch = tree.add(f"🏴 [blue]Nation: {nation.name}[/blue]")
            
            if nation.cities:
                city = nation.cities[0]
                city_branch = nation_branch.add(f"🏙️ [blue]City: {city.name}[/blue]")
                
                if city.villages:
                    village = city.villages[0]
                    village_branch = city_branch.add(f"🏘️ [blue]Village: {village.name}[/blue]")
                    
                    if village.companies:
                        company = village.companies[0]
                        company_branch = village_branch.add(f"🏢 [green]Company: {company.name}[/green]")
                        
                        if company.buildings:
                            building = company.buildings[0]
                            building_branch = company_branch.add(f"🏢 [yellow]Building: {building.name}[/yellow]")
                            
                            # Process floors and rooms from CRD
                            room_branches = {}
                            for floor in building.floors:
                                floor_branch = building_branch.add(f"🏠 [yellow]{floor.name}[/yellow]")
                                
                                for room in floor.rooms:
                                    room_branch = floor_branch.add(f"🚪 [cyan]{room.name} ({room.id})[/cyan]")
                                    room_branches[room.id] = room_branch
                        else:
                            # No buildings defined - minimal structure
                            room_branches = {
                                "room-01": company_branch.add("🚪 [cyan]Room 1[/cyan]")
                            }
                    else:
                        # No companies - minimal structure
                        room_branches = {
                            "room-01": village_branch.add("🚪 [cyan]Room 1[/cyan]")
                        }
                else:
                    # No villages - minimal structure
                    room_branches = {
                        "room-01": city_branch.add("🚪 [cyan]Room 1[/cyan]")
                    }
            else:
                # No cities - minimal structure
                room_branches = {
                    "room-01": nation_branch.add("🚪 [cyan]Room 1[/cyan]")
                }
        else:
            # No CRD data - use session configuration or minimal defaults
            nation_branch = tree.add("🏴 [blue]Nation: Default[/blue]")
            city_branch = nation_branch.add("🏙️ [blue]City: Default[/blue]")
            village_branch = city_branch.add("🏘️ [blue]Village: Default[/blue]")
            company_branch = village_branch.add(f"🏢 [green]Company: {company_name}[/green]")
            
            # Get rooms from session config
            rooms = session_config.get("rooms", [{"id": "room-01", "name": "Room 1"}]) if session_config else [{"id": "room-01", "name": "Room 1"}]
            room_branches = {}
            for room in rooms:
                room_id = room.get("id", "room-01")
                room_name = room.get("name", "Room")
                room_branch = company_branch.add(f"🚪 [cyan]{room_name} ({room_id})[/cyan]")
                room_branches[room_id] = room_branch
        
        # Get organization data from Organization CRD for detailed role mapping
        organization_crd_data = self._get_organization_crd_for_display()
        
        # Add organizations and desks to rooms based on actual structure
        # Get organization data from Organization CRD for detailed role mapping
        organization_crd_data = self._get_organization_crd_for_display()
        
        # Process organizations based on actual room structure
        for room_id, room_branch in room_branches.items():
            # Get desk mappings for this room from session info
            if hasattr(self, 'active_sessions'):
                for session_info in self.active_sessions.values():
                    desk_distribution = session_info.get("desk_distribution", {})
                    desks_in_room = desk_distribution.get(room_id, [])
                    
                    # Group desks by organization
                    org_groups = {}
                    for desk in desks_in_room:
                        org_id = desk.get("org_id", "org-01")
                        if org_id not in org_groups:
                            org_groups[org_id] = []
                        org_groups[org_id].append(desk)
                    
                    # Add organizations to room
                    for org_id, org_desks in org_groups.items():
                        # Find organization info
                        org_num = int(org_id.split("-")[1]) if "-" in org_id else 1
                        org_info = organizations[org_num - 1] if org_num <= len(organizations) else {}
                        org_name = org_info.get("name", f"Organization {org_num}")
                        department_id = org_info.get("department_id", "unknown")
                        
                        # Get department roles
                        dept_roles = self._get_department_roles(organization_crd_data, department_id)
                        
                        # Add organization branch
                        if "executive" in room_id:
                            org_branch = room_branch.add(f"📋 [gold1]{org_name}[/gold1]")
                        else:
                            org_branch = room_branch.add(f"📋 [magenta]{org_name}[/magenta]")
                        
                        # Add desks (agents) to organization
                        for desk in org_desks:
                            role = desk.get("role", "worker")
                            desk_id = desk.get("desk_id", "unknown")
                            
                            # Determine role title based on role type and department
                            if role in ["ceo", "cto", "coo", "assistant"]:
                                # Executive roles
                                role_title = role.upper() if role != "assistant" else "Executive Assistant"
                            elif role == "pm":
                                role_title = dept_roles.get("lead", "Team Lead") if dept_roles else "Project Manager"
                            else:
                                # Worker roles
                                worker_idx = ord(role.split("-")[1]) - ord('a') if "-" in role else 0
                                role_titles = dept_roles.get("workers", ["Senior Developer", "Developer", "Junior Developer"]) if dept_roles else ["Senior Developer", "Developer", "Junior Developer"]
                                role_title = role_titles[worker_idx] if worker_idx < len(role_titles) else f"Worker {chr(ord('A')+worker_idx)}"
                            
                            # Generate agent ID for task lookup
                            agent_id = self._get_agent_id_from_pane_mapping(desk)
                            task_info = task_assignments.get(agent_id, {})
                            task_display = f" → [green]{task_info['task_name']}[/green]" if task_info else " [dim](standby)[/dim]"
                            
                            org_branch.add(f"👤 [white]{role_title}[/white] ({agent_id}){task_display}")
                    
                    break  # Use first matching session
        
        return tree
    
    def _create_directory_structure_tree(self, base_path: Path, organizations: List[Dict[str, Any]], total_panes: int = 32, room_count: int = 2):
        """Create Rich tree for directory structure"""
        from rich.tree import Tree
        
        tree = Tree(f"📁 [bold cyan]{base_path.name}/[/bold cyan]")
        
        # Tasks directory
        tasks_branch = tree.add("📁 [yellow]tasks/[/yellow] (Git Repository & Worktrees)")
        tasks_branch.add("📁 [green]main/[/green] (Main Repository)")
        
        # Check for actual task directories and show them
        tasks_path = base_path / "tasks"
        task_count = 0
        if tasks_path.exists():
            task_dirs = [d for d in tasks_path.iterdir() if d.is_dir() and d.name != "main"]
            if task_dirs:
                for task_dir in sorted(task_dirs):
                    # Try to get task description from assignment log
                    task_display = task_dir.name
                    assignment_log = task_dir / ".haconiwa" / "agent_assignment.json"
                    if assignment_log.exists():
                        try:
                            import json
                            with open(assignment_log, 'r', encoding='utf-8') as f:
                                log_data = json.load(f)
                                if not isinstance(log_data, list):
                                    log_data = [log_data]
                                if log_data and log_data[0].get("agent_id"):
                                    agent_id = log_data[0]["agent_id"]
                                    task_display = f"{task_dir.name} → {agent_id}"
                        except:
                            pass
                    
                    tasks_branch.add(f"📁 [cyan]{task_display}[/cyan] (Task Worktree)")
                    task_count += 1
        
        # Show standby directory (created automatically)
        standby_branch = tree.add("📁 [dim]standby/[/dim] (Unassigned Agents)")
        
        # Add summary info
        panes_per_room = total_panes // room_count if room_count > 1 else total_panes
        pane_info = f"Tmux Panes: {total_panes} ({panes_per_room} per room)" if room_count > 1 else f"Tmux Panes: {total_panes}"
        if task_count > 0:
            tree.add(f"[dim]📊 Active Tasks: {task_count} | {pane_info}[/dim]")
        else:
            tree.add(f"[dim]📊 No active tasks | {pane_info}[/dim]")
        
        return tree
    
    def _create_task_assignment_table(self, task_assignments: Dict[str, Any]):
        """Create Rich table for task assignments"""
        from rich.table import Table
        
        table = Table(show_header=True, header_style="bold cyan")
        table.add_column("タスクブランチ", style="green", width=40)
        table.add_column("ルーム", style="blue", width=16)
        table.add_column("役職", style="magenta", width=20)
        table.add_column("エージェント", style="yellow", width=20)
        
        if not task_assignments:
            table.add_row("[dim]No task assignments[/dim]", "", "", "")
            return table
        
        # Get organization data from Organization CRD for role information
        organization_crd_data = self._get_organization_crd_for_display()
        
        # Get organization and room data from current session
        organization_ref = None
        rooms = []
        desk_mappings = []
        for session_info in self.active_sessions.values():
            config = session_info.get("config", {})
            organizations = config.get("organizations", [])
            rooms = config.get("rooms", [])
            desk_mappings = session_info.get("desk_mappings", [])
            if organizations:
                # Get organization reference from the first active session
                break
        
        if not organizations:
            # Fallback to default organizations
            organizations = self._get_organization_data(None)
        
        # If we have desk mappings, use them to display correct agent IDs
        if desk_mappings:
            for mapping in desk_mappings:
                # Get agent ID from desk mapping
                agent_id = self._get_agent_id_from_pane_mapping(mapping)
                room_name = mapping.get("title", "").split(" - ")[-1] if " - " in mapping.get("title", "") else "Unknown Room"
                role_name = mapping.get("title", "").split(" - ")[1] if len(mapping.get("title", "").split(" - ")) > 2 else "Developer"
                
                # Check for task assignment
                assigned_task = ""
                for task_agent_id, task_info in task_assignments.items():
                    if task_agent_id == agent_id:
                        assigned_task = task_info.get("task_name", "Unknown Task")
                        break
                
                if not assigned_task:
                    assigned_task = "[dim]standby[/dim]"
                
                table.add_row(assigned_task, room_name, role_name, agent_id)
            
            return table
        
        # Fallback to old logic if no desk mappings
        # Add assignments for first 4 organizations (Alpha and Beta rooms)
        for i, org in enumerate(organizations[:4]):
            org_id = i + 1
            org_name = org.get("name", f"Organization {org_id}")
            department_id = org.get("department_id", "unknown")
            
            # Get actual roles for this department from Organization CRD
            dept_roles = self._get_department_roles(organization_crd_data, department_id)
            
            # Room assignment based on organization ID and actual room configuration
            if rooms and i < len(rooms):
                room = rooms[i % len(rooms)]  # Cycle through available rooms
                room_id = room.get("id", f"room-{i+1:02d}")
                room_name = room.get("name", f"Room {i+1}")
            else:
                # Fallback if no room configuration
                room_name = "Alpha Room" if i < 2 else "Beta Room"
                room_id = "room-01" if i < 2 else "room-02"
            
            for j in range(4):  # 4 roles per organization
                if j == 0:
                    role_part = "pm"
                    role_title = dept_roles.get("lead", "Team Lead") if dept_roles else "Project Manager"
                else:
                    role_part = f"wk-{chr(ord('a')+j-1)}"
                    role_titles = dept_roles.get("workers", ["Senior Developer", "Developer", "Junior Developer"]) if dept_roles else ["Senior Developer", "Developer", "Junior Developer"]
                    role_title = role_titles[j-1] if j-1 < len(role_titles) else f"Worker {chr(ord('A')+j-1)}"
                
                agent_id = f"org{org_id:02d}-{role_part}-{'r1' if i < 2 else 'r2'}"
                
                # Check for task assignment using the exact agent_id
                assigned_task = ""
                for task_agent_id, task_info in task_assignments.items():
                    if task_agent_id == agent_id:
                        assigned_task = task_info.get("task_name", "Unknown Task")
                        break
                
                if not assigned_task:
                    assigned_task = "[dim]standby[/dim]"
                
                table.add_row(assigned_task, room_name, role_title, agent_id)
        
        # Add Executive Leadership assignments (Organization 5)
        if len(organizations) >= 5:
            exec_org = organizations[4]  # 5th organization
            exec_org_name = exec_org.get("name", "Executive Leadership")
            
            # Get executive roles from Organization CRD
            exec_dept_roles = self._get_department_roles(organization_crd_data, "executive")
            
            # Executive roles
            exec_roles = ["ceo", "cto", "coo", "assistant"]
            exec_titles = ["CEO", "CTO", "COO", "Executive Assistant"]
            
            # Use actual titles from Organization CRD if available
            if exec_dept_roles:
                actual_exec_titles = []
                exec_role_data = exec_dept_roles.get("workers", [])
                for role_name in exec_role_data:
                    if "ceo" in role_name.lower():
                        actual_exec_titles.append(role_name)
                    elif "cto" in role_name.lower():
                        actual_exec_titles.append(role_name)
                    elif "coo" in role_name.lower():
                        actual_exec_titles.append(role_name)
                
                # Fill in missing standard titles
                if len(actual_exec_titles) < 3:
                    standard_titles = ["CEO", "CTO", "COO"]
                    for title in standard_titles:
                        if not any(title.lower() in t.lower() for t in actual_exec_titles):
                            actual_exec_titles.append(title)
                            if len(actual_exec_titles) >= 3:
                                break
                                
                actual_exec_titles.append("Executive Assistant")
                exec_titles = actual_exec_titles[:4]
            
            for i, (role_name, role_title) in enumerate(zip(exec_roles, exec_titles)):
                agent_id = f"org05-{role_name}-re"
                
                # Check for task assignment using the exact agent_id
                assigned_task = ""
                for task_agent_id, task_info in task_assignments.items():
                    if task_agent_id == agent_id:
                        assigned_task = task_info.get("task_name", "Unknown Task")
                        break
                
                if not assigned_task:
                    assigned_task = "[dim]standby[/dim]"
                
                # Use actual room name if available
                exec_room_name = "Executive Room"
                if rooms and len(rooms) > 2:
                    exec_room = rooms[2]  # Third room for executives
                    exec_room_name = exec_room.get("name", "Executive Room")
                
                table.add_row(assigned_task, exec_room_name, role_title, agent_id)
        
        return table
    
    def _get_current_task_assignments(self) -> Dict[str, Dict[str, Any]]:
        """Get current task assignments for display by reading from task directories"""
        assignments = {}
        
        # First check stored task assignments
        if hasattr(self, 'task_assignments') and self.task_assignments:
            for agent_id, task_info in self.task_assignments.items():
                # Extract room from agent ID (org01-pm-r1 → r1)
                room = agent_id.split("-")[-1] if "-" in agent_id else "r1"
                assignments[agent_id] = {
                    "task_name": task_info.get("name", "Unknown Task"),
                    "room": room,
                    "status": "active"
                }
        
        # Also check task directories for additional assignment info
        for session_name, session_info in self.active_sessions.items():
            config = session_info.get("config", {})
            base_path = Path(config.get("base_path", "./"))
            tasks_path = base_path / "tasks"
            
            if tasks_path.exists():
                # Scan task directories for assignment logs
                for task_dir in tasks_path.iterdir():
                    if task_dir.is_dir() and task_dir.name != "main":
                        assignment_log = task_dir / ".haconiwa" / "agent_assignment.json"
                        if assignment_log.exists():
                            try:
                                import json
                                with open(assignment_log, 'r', encoding='utf-8') as f:
                                    log_data = json.load(f)
                                    
                                # Handle both single assignment and list format
                                if not isinstance(log_data, list):
                                    log_data = [log_data]
                                
                                for assignment in log_data:
                                    agent_id = assignment.get("agent_id")
                                    if agent_id and assignment.get("status") == "active":
                                        room = agent_id.split("-")[-1] if "-" in agent_id else "r1"
                                        assignments[agent_id] = {
                                            "task_name": assignment.get("task_name", task_dir.name),
                                            "room": room,
                                            "status": "active"
                                        }
                                        
                            except Exception as e:
                                logger.debug(f"Could not read assignment log {assignment_log}: {e}")
        
        return assignments
    
    def update_panes_for_task_assignments(self, session_name: str, base_path: Path) -> int:
        """Update panes immediately after task assignments"""
        updated_count = 0
        
        try:
            # Get all task assignments - support both flat and nested directory structures
            task_dirs = []
            tasks_base = base_path / "tasks"
            
            if tasks_base.exists():
                # First level: tasks/task_name or tasks/main
                for item in tasks_base.iterdir():
                    if item.is_dir() and item.name != "main":
                        task_dirs.append(item)
                
                # Second level: tasks/category/task_name (for feature/, bugfix/, etc.)
                for category_dir in tasks_base.iterdir():
                    if category_dir.is_dir() and category_dir.name != "main":
                        for task_dir in category_dir.iterdir():
                            if task_dir.is_dir():
                                task_dirs.append(task_dir)
            
            logger.info(f"Found {len(task_dirs)} potential task directories")
            
            for task_dir in task_dirs:
                
                # Check for assignment log
                assignment_log = task_dir / ".haconiwa" / "agent_assignment.json"
                if not assignment_log.exists():
                    logger.debug(f"No assignment log found in {task_dir}")
                    continue
                
                logger.info(f"Processing task directory: {task_dir} (assignment log found)")
                
                try:
                    with open(assignment_log, 'r') as f:
                        assignments = json.load(f)
                    
                    for assignment in assignments:
                        if assignment.get("status") != "active":
                            continue
                        
                        agent_id = assignment.get("agent_id")
                        if not agent_id:
                            continue
                        
                        # Find the pane with this agent ID
                        pane_found = False
                        
                        # Try to load desk mappings from state file if not in memory
                        desk_mappings = None
                        if hasattr(self, '_current_desk_mappings'):
                            desk_mappings = self._current_desk_mappings
                        else:
                            # Try to load from saved state
                            desk_mappings_file = base_path / ".haconiwa" / "desk_mappings.json"
                            if desk_mappings_file.exists():
                                try:
                                    with open(desk_mappings_file, 'r') as f:
                                        desk_mappings = json.load(f)
                                except Exception as e:
                                    logger.warning(f"Could not load desk mappings: {e}")
                        
                        if desk_mappings:
                            logger.debug(f"Checking desk mappings for agent {agent_id}")
                            for idx, mapping in enumerate(desk_mappings):
                                if mapping.get('agent_id') == agent_id:
                                    # Calculate window and pane from index
                                    # First 16 panes (0-15) -> window 0 (Executive)
                                    # Next 16 panes (16-31) -> window 1 (Standby)
                                    if idx < 16:
                                        window_id = "0"
                                        pane_index = idx
                                    else:
                                        window_id = "1"
                                        pane_index = idx - 16
                                    
                                    # Move to task directory and start claude
                                    task_path = task_dir.absolute()
                                    home_path = str(Path.home())
                                    
                                    if str(task_path).startswith(home_path):
                                        task_path_str = "~" + str(task_path)[len(home_path):]
                                    else:
                                        task_path_str = str(task_path)
                                    
                                    logger.info(f"Moving agent {agent_id} from pane {window_id}.{pane_index} to {task_path_str}")
                                    
                                    # Extract task branch name from task directory
                                    task_branch_name = assignment.get("task_name", task_dir.name)
                                    
                                    # Update pane title to agent-taskbranch format
                                    pane_title = f"{agent_id}-{task_branch_name}"
                                    title_cmd = ["tmux", "select-pane", "-t", f"{session_name}:{window_id}.{pane_index}", 
                                                "-T", pane_title]
                                    title_result = subprocess.run(title_cmd, capture_output=True, text=True)
                                    
                                    if title_result.returncode == 0:
                                        logger.info(f"✅ Updated pane title to: {pane_title}")
                                    else:
                                        logger.warning(f"⚠️ Failed to update pane title: {title_result.stderr}")
                                    
                                    cmd = ["tmux", "send-keys", "-t", f"{session_name}:{window_id}.{pane_index}", 
                                           f"cd {task_path_str} && claude", "Enter"]
                                    result = subprocess.run(cmd, capture_output=True, text=True)
                                    
                                    if result.returncode == 0:
                                        logger.info(f"✅ Successfully moved agent {agent_id} to task directory: {task_path_str}")
                                        updated_count += 1
                                        pane_found = True
                                        break
                                    else:
                                        logger.error(f"❌ Failed to move agent {agent_id}: tmux error: {result.stderr}")
                        else:
                            logger.warning(f"No desk mappings available for agent assignment")
                        
                        if not pane_found:
                            logger.warning(f"Could not find pane for agent {agent_id}")
                
                except Exception as e:
                    logger.error(f"Error processing assignment log {assignment_log}: {e}")
        
        except Exception as e:
            logger.error(f"Error updating panes for task assignments: {e}")
        
        return updated_count
    
    def _get_organization_crd_for_display(self) -> Optional[Dict[str, Any]]:
        """Get the first available Organization CRD for display purposes"""
        try:
            # Try to get Organization CRD from applied resources
            import sys
            if hasattr(sys.modules.get('__main__'), '_current_applier'):
                applier = getattr(sys.modules['__main__'], '_current_applier')
                applied_resources = applier.get_applied_resources()
                
                for resource_key, resource in applied_resources.items():
                    if resource_key.startswith("Organization/"):
                        return resource
            return None
        except:
            return None
    
    def _get_department_roles(self, organization_crd, department_id: str) -> Optional[Dict[str, Any]]:
        """Get roles for a specific department from Organization CRD"""
        try:
            if not organization_crd:
                return None
            
            # Find the department
            for dept in organization_crd.spec.hierarchy.departments:
                if dept.id == department_id:
                    # Return all roles for this department
                    return {
                        "lead_role": next((role for role in dept.roles if "lead" in role.title.lower() or "manager" in role.title.lower()), None),
                        "worker_roles": [role for role in dept.roles if "lead" not in role.title.lower() and "manager" not in role.title.lower()],
                        "all_roles": dept.roles
                    }
            
            return None
        except Exception as e:
            logger.warning(f"Could not get roles for department {department_id}: {e}")
            return None
    
    def _get_organization_crd_by_ref(self, organization_ref: str) -> Optional[Dict[str, Any]]:
        """Get organization CRD object from applied resources by reference name"""
        try:
            import sys
            if hasattr(sys.modules.get('__main__'), '_current_applier'):
                applier = getattr(sys.modules['__main__'], '_current_applier')
                applied_resources = applier.get_applied_resources()
                
                for resource_key, resource in applied_resources.items():
                    if resource_key.startswith("Organization/") and resource.metadata.name == organization_ref:
                        logger.info(f"Found Organization CRD by ref: {organization_ref}")
                        return resource
            return None
        except Exception as e:
            logger.warning(f"Could not get Organization CRD for ref {organization_ref}: {e}")
            return None
    
    def update_pane_titles_from_org(self, session_name: str, organization_crd: OrganizationCRD):
        """Update all pane titles in a session based on an Organization CRD."""
        try:
            logger.info(f"Updating pane titles for session '{session_name}' using Organization CRD '{organization_crd.metadata.name}'")

            session_config = self.active_sessions.get(session_name)
            if not session_config:
                logger.error(f"Session '{session_name}' not found in active sessions.")
                return

            config = session_config['config']
            base_path = Path(session_config['base_path'])
            
            # Re-generate desk mappings with the provided Organization CRD
            desk_mappings = self.generate_desk_mappings(
                organizations=config.get("organizations", []),
                rooms=config.get("rooms", []),
                grid=config.get("grid", "8x4"),
                base_path=base_path,
                organization_crd=organization_crd
            )

            desk_distribution = self._distribute_desks_to_windows(desk_mappings)

            for room_id, desks_in_room in desk_distribution.items():
                window_id = self._get_window_id_for_room(room_id)
                
                for pane_index, desk_mapping in enumerate(desks_in_room):
                    agent_id = desk_mapping.get("agent_id")
                    if not agent_id:
                        logger.warning(f"Could not determine agent_id for pane {pane_index} in room {room_id}. Skipping title update.")
                        continue

                    new_title = f"{agent_id} - standby"
                    
                    cmd = ["tmux", "select-pane", "-t", f"{session_name}:{window_id}.{pane_index}", "-T", new_title]
                    result = subprocess.run(cmd, capture_output=True, text=True)
                    if result.returncode == 0:
                        logger.debug(f"Updated title for pane {window_id}.{pane_index} to '{new_title}'")
                    else:
                        logger.warning(f"Failed to update title for pane {window_id}.{pane_index}: {result.stderr}")
            logger.info(f"Successfully updated pane titles for session '{session_name}'.")
        except Exception as e:
            logger.error(f"Error updating pane titles: {e}")
            import traceback
            logger.debug(f"Stack trace: {traceback.format_exc()}")
 