"""
CRD Applier for Haconiwa v1.0
"""

from typing import Union, List, Dict
from pathlib import Path
import logging
import sys

from .crd.models import (
    SpaceCRD, AgentCRD, TaskCRD, PathScanCRD, DatabaseCRD, CommandPolicyCRD, OrganizationCRD
)

logger = logging.getLogger(__name__)


class CRDApplierError(Exception):
    """CRD applier error"""
    pass


class CRDApplier:
    """CRD Applier - applies CRD objects to the system"""
    
    def __init__(self):
        self.applied_resources = {}
        self.force_clone = False  # Default to False
    
    def apply(self, crd: Union[SpaceCRD, AgentCRD, TaskCRD, PathScanCRD, DatabaseCRD, CommandPolicyCRD, OrganizationCRD]) -> bool:
        """Apply CRD to the system"""
        try:
            if isinstance(crd, SpaceCRD):
                return self._apply_space_crd(crd)
            elif isinstance(crd, AgentCRD):
                return self._apply_agent_crd(crd)
            elif isinstance(crd, TaskCRD):
                return self._apply_task_crd(crd)
            elif isinstance(crd, PathScanCRD):
                return self._apply_pathscan_crd(crd)
            elif isinstance(crd, DatabaseCRD):
                return self._apply_database_crd(crd)
            elif isinstance(crd, CommandPolicyCRD):
                return self._apply_commandpolicy_crd(crd)
            elif isinstance(crd, OrganizationCRD):
                return self._apply_organization_crd(crd)
            else:
                raise CRDApplierError(f"Unknown CRD type: {type(crd)}")
        except Exception as e:
            logger.error(f"Failed to apply CRD {crd.metadata.name}: {e}")
            raise CRDApplierError(f"Failed to apply CRD {crd.metadata.name}: {e}")
    
    def apply_multiple(self, crds: List[Union[SpaceCRD, AgentCRD, TaskCRD, PathScanCRD, DatabaseCRD, CommandPolicyCRD, OrganizationCRD]]) -> List[bool]:
        """Apply multiple CRDs to the system"""
        from rich.console import Console
        from rich.progress import Progress, SpinnerColumn, TextColumn, BarColumn, TimeElapsedColumn
        from rich.panel import Panel
        from rich.text import Text
        from rich.table import Table
        import time
        import logging
        
        # Store current applier instance for SpaceManager access (workaround)
        sys.modules['__main__']._current_applier = self
        
        console = Console()
        results = []
        space_sessions = []  # Track space sessions for post-processing
        
        # Temporarily adjust log levels to reduce noise during Rich display
        original_log_levels = {}
        loggers_to_quiet = [
            'haconiwa.task.manager', 
            'haconiwa.space.manager', 
            'haconiwa.core.applier',
            'haconiwa.agent.claude_integration',
            'haconiwa.legal.framework'
        ]
        for logger_name in loggers_to_quiet:
            log = logging.getLogger(logger_name)
            original_log_levels[logger_name] = log.level
            log.setLevel(logging.WARNING)  # Only show warnings and errors
        
        try:
            # Display header
            console.print("\n")
            console.print(Panel.fit(
                "[bold cyan]🚀 Haconiwa CRD Applier[/bold cyan]\n"
                f"[dim]Applying {len(crds)} resources...[/dim]",
                style="cyan"
            ))
            console.print()
            
            # Categorize CRDs for better display
            crd_categories = {
                "Space": [],
                "Task": [], 
                "Agent": [],
                "Database": [],
                "PathScan": [],
                "CommandPolicy": [],
                "Organization": []
            }
            
            for crd in crds:
                crd_type = type(crd).__name__.replace("CRD", "")
                if crd_type in crd_categories:
                    crd_categories[crd_type].append(crd)
            
            # Display resource summary
            summary_table = Table(title="📋 Resource Summary", show_header=True, header_style="bold magenta")
            summary_table.add_column("Resource Type", style="cyan")
            summary_table.add_column("Count", justify="right", style="green")
            summary_table.add_column("Names", style="dim")
            
            for category, items in crd_categories.items():
                if items:
                    names = ", ".join([item.metadata.name for item in items[:3]])
                    if len(items) > 3:
                        names += f" +{len(items)-3} more"
                    summary_table.add_row(category, str(len(items)), names)
            
            console.print(summary_table)
            console.print()
            
            # Apply CRDs with progress tracking
            with Progress(
                SpinnerColumn(),
                TextColumn("[progress.description]{task.description}"),
                BarColumn(),
                "[progress.percentage]{task.percentage:>3.0f}%",
                TimeElapsedColumn(),
                console=console
            ) as progress:
                
                main_task = progress.add_task("[cyan]Applying resources...", total=len(crds))
                
                for i, crd in enumerate(crds):
                    crd_type = type(crd).__name__.replace("CRD", "")
                    task_desc = f"[{crd_type}] {crd.metadata.name}"
                    
                    current_task = progress.add_task(f"Applying {task_desc}", total=1)
                    
                    try:
                        start_time = time.time()
                        result = self.apply(crd)
                        end_time = time.time()
                        
                        results.append(result)
                        
                        # Track Space CRDs for later pane updates
                        if isinstance(crd, SpaceCRD) and result:
                            company = crd.spec.nations[0].cities[0].villages[0].companies[0]
                            space_sessions.append({
                                "session_name": company.name,
                                "space_ref": company.name
                            })
                        
                        # Update progress
                        progress.update(current_task, completed=1)
                        progress.update(main_task, advance=1)
                        
                        # Display result
                        status_icon = "✅" if result else "❌"
                        elapsed = f"{end_time - start_time:.1f}s"
                        console.print(f"  {status_icon} {task_desc} [dim]({elapsed})[/dim]")
                        
                    except Exception as e:
                        logger.error(f"Failed to apply CRD {crd.metadata.name}: {e}")
                        results.append(False)
                        progress.update(current_task, completed=1)
                        progress.update(main_task, advance=1)
                        console.print(f"  ❌ {task_desc} [red]FAILED: {str(e)[:50]}...[/red]")
                    
                    progress.remove_task(current_task)
            
            # Post-processing phase
            if space_sessions:
                console.print()
                console.print(Panel.fit(
                    "[bold yellow]🔄 Post-Processing Phase[/bold yellow]\n"
                    "[dim]Updating task assignments and agent panes...[/dim]",
                    style="yellow"
                ))
                
                with Progress(
                    SpinnerColumn(),
                    TextColumn("[progress.description]{task.description}"),
                    console=console
                ) as progress:
                    
                    # Task assignment updates
                    task1 = progress.add_task("[yellow]Re-updating task assignments...")
                    self._update_all_space_task_assignments(space_sessions)
                    progress.update(task1, completed=1)
                    console.print("  ✅ Task assignments updated")
                    
                    # Agent pane updates  
                    task2 = progress.add_task("[yellow]Updating agent pane directories...")
                    updated_panes = self._update_all_agent_pane_directories(space_sessions)
                    progress.update(task2, completed=1)
                    console.print(f"  ✅ Updated {updated_panes} agent panes")
            
            # Final summary
            console.print()
            success_count = sum(results)
            total_count = len(results)
            
            if success_count == total_count:
                summary_style = "green"
                summary_icon = "🎉"
                summary_text = "All resources applied successfully!"
            else:
                summary_style = "red"
                summary_icon = "⚠️"
                summary_text = f"{success_count}/{total_count} resources applied successfully"
            
            console.print(Panel.fit(
                f"[bold {summary_style}]{summary_icon} {summary_text}[/bold {summary_style}]",
                style=summary_style
            ))
            
        finally:
            # Restore original log levels
            for logger_name, original_level in original_log_levels.items():
                logging.getLogger(logger_name).setLevel(original_level)
        
        return results
    
    def _update_all_agent_pane_directories(self, space_sessions: List[Dict[str, str]]):
        """Update agent pane directories for all space sessions"""
        if not space_sessions:
            return 0
        
        try:
            logger.info("🎯 Using new log-file based agent assignment (TaskManager pattern matching disabled)")
            
            # Import SpaceManager to call the new log-based update method
            from ..space.manager import SpaceManager
            space_manager = SpaceManager()
            
            total_updated = 0
            
            for space_info in space_sessions:
                session_name = space_info["session_name"]
                space_ref = space_info["space_ref"]
                
                logger.info(f"🔄 Running log-based pane update for space: {space_ref}")
                
                # First try the new direct assignment method
                base_path = Path(f"./{space_ref.replace('-company', '-world')}")
                if not base_path.exists():
                    base_path = Path(f"./{space_ref}")
                
                if base_path.exists():
                    updated_count = space_manager.update_panes_for_task_assignments(session_name, base_path)
                    if updated_count > 0:
                        total_updated += updated_count
                        logger.info(f"✅ Updated {updated_count} agent panes directly for space: {space_ref}")
                        continue
                
                # Fall back to log-based update method
                updated_count = space_manager.update_all_panes_from_task_logs(session_name, space_ref)
                total_updated += updated_count
                
                if updated_count > 0:
                    logger.info(f"✅ Updated {updated_count} agent panes for space: {space_ref}")
                else:
                    logger.info(f"ℹ️ No task assignments found for space: {space_ref}")
                
            logger.info(f"🎉 Total agent panes updated across all spaces: {total_updated}")
            return total_updated
                
        except Exception as e:
            logger.error(f"Failed to coordinate agent pane directories: {e}")
            return 0
    
    def _update_all_space_task_assignments(self, space_sessions: List[Dict[str, str]]):
        """Re-update task assignments for all space sessions after all CRDs are applied"""
        try:
            from ..task.manager import TaskManager
            from ..space.manager import SpaceManager
            
            task_manager = TaskManager()
            
            for space_info in space_sessions:
                session_name = space_info["session_name"]
                space_ref = space_info["space_ref"]
                
                # Get all task assignments for this space
                task_assignments = {}
                for task_name, task_data in task_manager.tasks.items():
                    assignee = task_data["config"].get("assignee")
                    task_space_ref = task_data["config"].get("space_ref")
                    if assignee and task_space_ref == space_ref:
                        task_assignments[assignee] = {
                            "name": task_name,
                            "worktree_path": f"tasks/{task_name}",
                            "config": task_data["config"]
                        }
                
                logger.info(f"Re-updating task assignments for space {space_ref}: {len(task_assignments)} tasks")
                for assignee, task_info in task_assignments.items():
                    logger.info(f"  {assignee} → {task_info['name']}")
                
                # Find and update the SpaceManager instance for this session
                # We need to get the SpaceManager instance that created this session
                # For now, we'll create a new one and set the task assignments
                space_manager = SpaceManager()
                space_manager.set_task_assignments(task_assignments)
                
                # Store the updated task assignments in active_sessions if available
                if session_name in space_manager.active_sessions:
                    space_manager.active_sessions[session_name]["task_assignments"] = task_assignments
                    
        except Exception as e:
            logger.error(f"Failed to re-update task assignments: {e}")
    
    def _apply_space_crd(self, crd: SpaceCRD) -> bool:
        """Apply Space CRD"""
        logger.info(f"Applying Space CRD: {crd.metadata.name}")
        
        try:
            # Store CRD for later reference
            self.applied_resources[f"Space/{crd.metadata.name}"] = crd
            
            # Import space manager here to avoid circular import
            from ..space.manager import SpaceManager
            space_manager = SpaceManager()
            
            # Convert CRD to internal configuration
            config = space_manager.convert_crd_to_config(crd)
            logger.info(f"Converted CRD to config: {config['name']} with {len(config.get('organizations', []))} organizations")
            
            # Handle Git repository if specified
            if config.get("git_repo"):
                git_config = config["git_repo"]
                logger.info(f"Git repository specified: {git_config['url']} (will be handled by SpaceManager)")
            
            # Apply Hierarchical Legal Framework if enabled
            logger.info("📋 About to check Hierarchical Legal Framework...")
            self._apply_hierarchical_legal_framework(crd, config)
            
            # IMPORTANT: Get TaskManager tasks and pass to SpaceManager for agent assignment
            from ..task.manager import TaskManager
            task_manager = TaskManager()
            
            # Set default branch from Space configuration
            if config.get("git_repo") and config["git_repo"].get("defaultBranch"):
                default_branch = config["git_repo"]["defaultBranch"]
                task_manager.set_default_branch(default_branch)
                logger.info(f"Set TaskManager default branch to: {default_branch}")
            
            # Pass task assignments to SpaceManager
            task_assignments = {}
            for task_name, task_data in task_manager.tasks.items():
                assignee = task_data["config"].get("assignee")
                space_ref = task_data["config"].get("space_ref")
                if assignee and space_ref == config['name']:
                    task_assignments[assignee] = {
                        "name": task_name,
                        "worktree_path": f"tasks/{task_name}",
                        "config": task_data["config"]
                    }
            
            # Display task assignments if any exist
            if task_assignments:
                from rich.console import Console
                from rich.table import Table
                
                console = Console()
                console.print("    [bold green]🎯 Agent Task Assignments[/bold green]")
                
                assign_table = Table(show_header=True, header_style="bold cyan")
                assign_table.add_column("Agent ID", style="yellow")
                assign_table.add_column("Task", style="green")
                assign_table.add_column("Description", style="dim")
                
                for assignee, task_info in task_assignments.items():
                    description = task_info["config"].get("description", "")[:50]
                    if len(description) > 47:
                        description = description[:47] + "..."
                    assign_table.add_row(assignee, task_info["name"], description)
                
                console.print(assign_table)
                logger.info(f"Passing {len(task_assignments)} task assignments to SpaceManager")
            else:
                logger.info("No existing task assignments found for this space")
            
            # Set task assignments in SpaceManager
            space_manager.set_task_assignments(task_assignments)
            
            # Create space infrastructure (32-pane tmux session with task-centric structure)
            logger.info("Creating 32-pane tmux session with tasks/ directory structure...")
            
            # Pass force_clone flag to SpaceManager
            space_manager._force_clone = self.force_clone
            
            result = space_manager.create_multiroom_session(config)
            
            if result:
                # Simple success message - details are shown by SpaceManager's Rich display
                logger.info(f"✅ Space CRD {crd.metadata.name} applied successfully")
            else:
                logger.error(f"❌ Failed to apply Space CRD {crd.metadata.name}")
            
            return result
            
        except Exception as e:
            logger.error(f"Exception while applying Space CRD {crd.metadata.name}: {e}")
            return False
    
    def _apply_hierarchical_legal_framework(self, crd: SpaceCRD, config: dict) -> bool:
        """Apply Hierarchical Legal Framework from Space CRD"""
        try:
            from rich.console import Console
            from rich.progress import Progress, SpinnerColumn, TextColumn
            
            console = Console()
            
            logger.info("🔍 Checking for Hierarchical Legal Framework in CRD...")
            
            # Check if any nation has legal framework enabled
            legal_framework_enabled = False
            for nation in crd.spec.nations:
                logger.info(f"🔍 Checking nation: {nation.id}")
                logger.info(f"🔍 Has legalFramework attr: {hasattr(nation, 'legalFramework')}")
                if hasattr(nation, 'legalFramework'):
                    logger.info(f"🔍 Legal framework object: {nation.legalFramework}")
                    logger.info(f"🔍 Legal framework enabled: {getattr(nation.legalFramework, 'enabled', False)}")
                
                if hasattr(nation, 'legalFramework') and getattr(nation.legalFramework, 'enabled', False):
                    legal_framework_enabled = True
                    logger.info(f"✅ Legal framework enabled for nation: {nation.id}")
                    break
            
            if not legal_framework_enabled:
                logger.info("❌ Hierarchical Legal Framework not enabled, skipping")
                return True
            
            # Display legal framework creation progress
            console.print("    [bold blue]📋 Creating Hierarchical Legal Framework...[/bold blue]")
            
            with Progress(
                SpinnerColumn(),
                TextColumn("[progress.description]{task.description}"),
                console=console
            ) as progress:
                task = progress.add_task("[blue]Setting up legal framework...", total=None)
                
                # Import legal framework
                from ..legal.framework import HierarchicalLegalFramework
                
                # Get base path from config
                base_path = Path(config['base_path'])
                
                # Create framework
                framework = HierarchicalLegalFramework(base_path)
                
                # Convert SpaceCRD to dict for framework processing
                crd_dict = self._convert_space_crd_to_dict(crd)
                
                # Debug: Log the converted dictionary
                logger.info(f"🔍 Converted CRD to dict for legal framework:")
                logger.info(f"🔍 Nations count: {len(crd_dict.get('spec', {}).get('nations', []))}")
                
                for i, nation in enumerate(crd_dict.get('spec', {}).get('nations', [])):
                    logger.info(f"🔍 Nation {i}: {nation.get('id')} - Legal framework enabled: {nation.get('legalFramework', {}).get('enabled', False)}")
                    cities = nation.get('cities', [])
                    logger.info(f"🔍   Cities count: {len(cities)}")
                    for j, city in enumerate(cities):
                        logger.info(f"🔍   City {j}: {city.get('id')} - Legal framework enabled: {city.get('legalFramework', {}).get('enabled', False)}")
                
                # Apply framework
                progress.update(task, description="[blue]Creating law directories...")
                success = framework.create_framework_from_yaml(crd_dict)
                
                progress.update(task, completed=1)
            
            if success:
                console.print(f"    ✅ Legal framework created: {len(framework.created_directories)} directories")
                logger.info(f"✅ Hierarchical Legal Framework created successfully")
                logger.info(f"   📁 Law directories: {len(framework.created_directories)}")
                logger.info(f"   🏛️ Framework base: {base_path}")
            else:
                console.print("    ❌ Legal framework creation failed")
                logger.warning("⚠️ Hierarchical Legal Framework creation failed")
                
            return success
            
        except Exception as e:
            logger.error(f"Failed to apply Hierarchical Legal Framework: {e}")
            return False

    def _convert_space_crd_to_dict(self, crd: SpaceCRD) -> dict:
        """Convert SpaceCRD to dictionary for legal framework processing"""
        return {
            'apiVersion': crd.apiVersion,
            'kind': crd.kind,
            'metadata': {
                'name': crd.metadata.name
            },
            'spec': {
                'nations': [self._convert_nation_to_dict(nation) for nation in crd.spec.nations]
            }
        }

    def _convert_nation_to_dict(self, nation) -> dict:
        """Convert Nation object to dictionary"""
        nation_dict = {
            'id': nation.id,
            'name': nation.name
        }
        
        # Add legal framework if present
        if hasattr(nation, 'legalFramework') and nation.legalFramework:
            nation_dict['legalFramework'] = {
                'enabled': getattr(nation.legalFramework, 'enabled', False),
                'lawDirectory': getattr(nation.legalFramework, 'lawDirectory', 'law'),
                'globalRules': getattr(nation.legalFramework, 'globalRules', 'global-rules.md'),
                'systemPrompts': getattr(nation.legalFramework, 'systemPrompts', 'system-prompts'),
                'permissions': getattr(nation.legalFramework, 'permissions', 'permissions')
            }
        
        # Add cities
        if hasattr(nation, 'cities') and nation.cities:
            nation_dict['cities'] = [self._convert_city_to_dict(city) for city in nation.cities]
        
        return nation_dict

    def _convert_city_to_dict(self, city) -> dict:
        """Convert City object to dictionary"""
        city_dict = {
            'id': city.id,
            'name': city.name
        }
        
        # Add legal framework if present
        if hasattr(city, 'legalFramework') and city.legalFramework:
            city_dict['legalFramework'] = {
                'enabled': getattr(city.legalFramework, 'enabled', False),
                'lawDirectory': getattr(city.legalFramework, 'lawDirectory', 'law'),
                'regionalRules': getattr(city.legalFramework, 'regionalRules', 'regional-rules.md'),
                'systemPrompts': getattr(city.legalFramework, 'systemPrompts', 'system-prompts'),
                'permissions': getattr(city.legalFramework, 'permissions', 'permissions')
            }
        
        # Add villages
        if hasattr(city, 'villages') and city.villages:
            city_dict['villages'] = [self._convert_village_to_dict(village) for village in city.villages]
        
        return city_dict

    def _convert_village_to_dict(self, village) -> dict:
        """Convert Village object to dictionary"""
        village_dict = {
            'id': village.id,
            'name': village.name
        }
        
        # Add legal framework if present
        if hasattr(village, 'legalFramework') and village.legalFramework:
            village_dict['legalFramework'] = {
                'enabled': getattr(village.legalFramework, 'enabled', False),
                'lawDirectory': getattr(village.legalFramework, 'lawDirectory', 'law'),
                'localRules': getattr(village.legalFramework, 'localRules', 'local-rules.md'),
                'systemPrompts': getattr(village.legalFramework, 'systemPrompts', 'system-prompts'),
                'permissions': getattr(village.legalFramework, 'permissions', 'permissions')
            }
        
        # Add companies
        if hasattr(village, 'companies') and village.companies:
            village_dict['companies'] = [self._convert_company_to_dict(company) for company in village.companies]
        
        return village_dict

    def _convert_company_to_dict(self, company) -> dict:
        """Convert Company object to dictionary"""
        company_dict = {
            'name': company.name,
            'grid': company.grid,
            'basePath': company.basePath
        }
        
        # Add legal framework if present
        if hasattr(company, 'legalFramework') and company.legalFramework:
            company_dict['legalFramework'] = {
                'enabled': getattr(company.legalFramework, 'enabled', False),
                'lawDirectory': getattr(company.legalFramework, 'lawDirectory', 'law'),
                'projectRules': getattr(company.legalFramework, 'projectRules', 'project-rules.md'),
                'systemPrompts': getattr(company.legalFramework, 'systemPrompts', 'system-prompts'),
                'permissions': getattr(company.legalFramework, 'permissions', 'permissions')
            }
        
        # Add organizations
        if hasattr(company, 'organizations') and company.organizations:
            company_dict['organizations'] = [
                {
                    'id': org.id,
                    'name': org.name,
                    'tasks': org.tasks if hasattr(org, 'tasks') else []
                } for org in company.organizations
            ]
        
        # Add git repo if present
        if hasattr(company, 'gitRepo') and company.gitRepo:
            company_dict['gitRepo'] = {
                'url': company.gitRepo.url,
                'defaultBranch': company.gitRepo.defaultBranch,
                'auth': company.gitRepo.auth
            }
        
        # Add buildings
        if hasattr(company, 'buildings') and company.buildings:
            company_dict['buildings'] = [self._convert_building_to_dict(building) for building in company.buildings]
        
        return company_dict

    def _convert_building_to_dict(self, building) -> dict:
        """Convert Building object to dictionary"""
        building_dict = {
            'id': building.id,
            'name': building.name
        }
        
        # Add legal framework if present
        if hasattr(building, 'legalFramework') and building.legalFramework:
            building_dict['legalFramework'] = {
                'enabled': getattr(building.legalFramework, 'enabled', False),
                'lawDirectory': getattr(building.legalFramework, 'lawDirectory', 'law'),
                'buildingRules': getattr(building.legalFramework, 'buildingRules', 'building-rules.md'),
                'systemPrompts': getattr(building.legalFramework, 'systemPrompts', 'system-prompts'),
                'permissions': getattr(building.legalFramework, 'permissions', 'permissions')
            }
        
        # Add floors
        if hasattr(building, 'floors') and building.floors:
            building_dict['floors'] = [self._convert_floor_to_dict(floor) for floor in building.floors]
        
        return building_dict

    def _convert_floor_to_dict(self, floor) -> dict:
        """Convert Floor object to dictionary"""
        floor_dict = {
            'id': floor.id,
            'name': floor.name
        }
        
        # Add legal framework if present
        if hasattr(floor, 'legalFramework') and floor.legalFramework:
            floor_dict['legalFramework'] = {
                'enabled': getattr(floor.legalFramework, 'enabled', False),
                'lawDirectory': getattr(floor.legalFramework, 'lawDirectory', 'law'),
                'floorRules': getattr(floor.legalFramework, 'floorRules', 'floor-rules.md'),
                'systemPrompts': getattr(floor.legalFramework, 'systemPrompts', 'system-prompts'),
                'permissions': getattr(floor.legalFramework, 'permissions', 'permissions')
            }
        
        # Add rooms
        if hasattr(floor, 'rooms') and floor.rooms:
            floor_dict['rooms'] = [self._convert_room_to_dict(room) for room in floor.rooms]
        
        return floor_dict

    def _convert_room_to_dict(self, room) -> dict:
        """Convert Room object to dictionary"""
        room_dict = {
            'id': room.id,
            'name': room.name
        }
        
        if hasattr(room, 'description') and room.description:
            room_dict['description'] = room.description
        
        # Add legal framework if present
        if hasattr(room, 'legalFramework') and room.legalFramework:
            room_dict['legalFramework'] = {
                'enabled': getattr(room.legalFramework, 'enabled', False),
                'lawDirectory': getattr(room.legalFramework, 'lawDirectory', 'law'),
                'teamRules': getattr(room.legalFramework, 'teamRules', 'team-rules.md'),
                'systemPrompts': getattr(room.legalFramework, 'systemPrompts', 'system-prompts'),
                'permissions': getattr(room.legalFramework, 'permissions', 'permissions')
            }
            
            # Add desks law if present
            if hasattr(room.legalFramework, 'desksLaw') and room.legalFramework.desksLaw:
                room_dict['legalFramework']['desksLaw'] = {
                    'enabled': getattr(room.legalFramework.desksLaw, 'enabled', False),
                    'lawDirectory': getattr(room.legalFramework.desksLaw, 'lawDirectory', 'law'),
                    'agentRules': getattr(room.legalFramework.desksLaw, 'agentRules', 'agent-rules.md'),
                    'systemPrompts': getattr(room.legalFramework.desksLaw, 'systemPrompts', 'system-prompts'),
                    'permissions': getattr(room.legalFramework.desksLaw, 'permissions', 'permissions')
                }
        
        return room_dict
    
    def _apply_agent_crd(self, crd: AgentCRD) -> bool:
        """Apply Agent CRD"""
        logger.info(f"Applying Agent CRD: {crd.metadata.name}")
        
        # Store CRD for later reference
        self.applied_resources[f"Agent/{crd.metadata.name}"] = crd
        
        # Import agent manager here to avoid circular import
        from ..agent.manager import AgentManager
        agent_manager = AgentManager()
        
        # Create agent configuration
        agent_config = {
            "name": crd.metadata.name,
            "role": crd.spec.role,
            "model": crd.spec.model,
            "space_ref": crd.spec.spaceRef,
            "system_prompt_path": crd.spec.systemPromptPath,
            "env": crd.spec.env or {}
        }
        
        # Apply agent configuration
        result = agent_manager.create_agent(agent_config)
        
        logger.info(f"Agent CRD {crd.metadata.name} applied successfully: {result}")
        return result
    
    def _apply_task_crd(self, crd: TaskCRD) -> bool:
        """Apply Task CRD"""
        logger.info(f"Applying Task CRD: {crd.metadata.name}")
        
        # Store CRD for later reference
        self.applied_resources[f"Task/{crd.metadata.name}"] = crd
        
        # Import task manager here to avoid circular import
        from ..task.manager import TaskManager
        task_manager = TaskManager()  # This will get the singleton instance
        
        # Get company agent defaults and git config from applied Space CRD
        company_agent_defaults = self._get_company_agent_defaults(crd.spec.spaceRef)
        git_config = self._get_company_git_config(crd.spec.spaceRef)
        
        # Set default branch if found in git config
        if git_config and git_config.get("defaultBranch"):
            default_branch = git_config["defaultBranch"]
            task_manager.set_default_branch(default_branch)
            logger.info(f"Set TaskManager default branch to: {default_branch} (from Space config)")
        
        # Create task configuration
        task_config = {
            "name": crd.metadata.name,
            "branch": crd.spec.branch,
            "worktree": crd.spec.worktree,
            "assignee": crd.spec.assignee,
            "space_ref": crd.spec.spaceRef,
            "description": crd.spec.description,
            "agent_config": self._convert_agent_config_to_dict(crd.spec.agentConfig) if crd.spec.agentConfig else None,
            "company_agent_defaults": company_agent_defaults
        }
        
        # Apply task configuration
        result = task_manager.create_task(task_config)
        
        logger.info(f"Task CRD {crd.metadata.name} applied successfully: {result}")
        return result
    
    def _get_company_agent_defaults(self, space_ref: str) -> dict:
        """Get company agent defaults from applied Space CRD"""
        try:
            # Find the Space CRD for this space_ref
            for resource_key, resource in self.applied_resources.items():
                if resource_key.startswith("Space/") and hasattr(resource, 'metadata'):
                    space_crd = resource
                    # Find the company in the Space CRD
                    for nation in space_crd.spec.nations:
                        for city in nation.cities:
                            for village in city.villages:
                                for company in village.companies:
                                    if company.name == space_ref:
                                        # Convert agentDefaults to dict
                                        if hasattr(company, 'agentDefaults') and company.agentDefaults:
                                            return self._convert_agent_defaults_to_dict(company.agentDefaults)
            
            logger.debug(f"No agent defaults found for space: {space_ref}")
            return {}
            
        except Exception as e:
            logger.error(f"Failed to get company agent defaults: {e}")
            return {}
    
    def _get_company_git_config(self, space_ref: str) -> dict:
        """Get company git config from applied Space CRD"""
        try:
            # Find the Space CRD for this space_ref
            for resource_key, resource in self.applied_resources.items():
                if resource_key.startswith("Space/") and hasattr(resource, 'metadata'):
                    space_crd = resource
                    # Find the company in the Space CRD
                    for nation in space_crd.spec.nations:
                        for city in nation.cities:
                            for village in city.villages:
                                for company in village.companies:
                                    if company.name == space_ref:
                                        # Return gitRepo config if exists
                                        if hasattr(company, 'gitRepo') and company.gitRepo:
                                            return {
                                                'url': company.gitRepo.url,
                                                'defaultBranch': getattr(company.gitRepo, 'defaultBranch', 'main'),
                                                'auth': getattr(company.gitRepo, 'auth', 'ssh')
                                            }
            
            logger.debug(f"No git config found for space: {space_ref}")
            return {}
            
        except Exception as e:
            logger.error(f"Error getting company git config: {e}")
            return {}
    
    def _convert_agent_config_to_dict(self, agent_config) -> dict:
        """Convert AgentConfig object to dictionary"""
        if not agent_config:
            return {}
        
        config_dict = {
            'type': getattr(agent_config, 'type', 'human-agent')
        }
        
        # Additional permissions
        if hasattr(agent_config, 'additionalPermissions') and agent_config.additionalPermissions:
            permissions = agent_config.additionalPermissions
            config_dict['additionalPermissions'] = {
                'allow': getattr(permissions, 'allow', []),
                'deny': getattr(permissions, 'deny', [])
            }
        
        # Environment variables
        if hasattr(agent_config, 'env') and agent_config.env:
            config_dict['env'] = agent_config.env
        
        # Tools
        if hasattr(agent_config, 'tools') and agent_config.tools:
            config_dict['tools'] = agent_config.tools
        
        return config_dict
    
    def _convert_agent_defaults_to_dict(self, agent_defaults) -> dict:
        """Convert AgentDefaultsConfig object to dictionary"""
        if not agent_defaults:
            return {}
        
        defaults_dict = {
            'type': getattr(agent_defaults, 'type', 'human-agent')
        }
        
        # Permissions
        if hasattr(agent_defaults, 'permissions') and agent_defaults.permissions:
            permissions = agent_defaults.permissions
            defaults_dict['permissions'] = {
                'allow': getattr(permissions, 'allow', []),
                'deny': getattr(permissions, 'deny', [])
            }
        
        # Environment variables
        if hasattr(agent_defaults, 'env') and agent_defaults.env:
            defaults_dict['env'] = agent_defaults.env
        
        return defaults_dict
    
    def _apply_pathscan_crd(self, crd: PathScanCRD) -> bool:
        """Apply PathScan CRD"""
        logger.info(f"Applying PathScan CRD: {crd.metadata.name}")
        
        # Store CRD for later reference
        self.applied_resources[f"PathScan/{crd.metadata.name}"] = crd
        
        # Import path scanner here to avoid circular import
        from ..resource.path_scanner import PathScanner
        
        # Create scanner configuration
        scanner_config = {
            "name": crd.metadata.name,
            "include": crd.spec.include,
            "exclude": crd.spec.exclude
        }
        
        # Register scanner configuration
        PathScanner.register_config(crd.metadata.name, scanner_config)
        
        logger.info(f"PathScan CRD {crd.metadata.name} applied successfully")
        return True
    
    def _apply_database_crd(self, crd: DatabaseCRD) -> bool:
        """Apply Database CRD"""
        logger.info(f"Applying Database CRD: {crd.metadata.name}")
        
        # Store CRD for later reference
        self.applied_resources[f"Database/{crd.metadata.name}"] = crd
        
        # Import database manager here to avoid circular import
        from ..resource.db_fetcher import DatabaseManager
        
        # Create database configuration
        db_config = {
            "name": crd.metadata.name,
            "dsn": crd.spec.dsn,
            "use_ssl": crd.spec.useSSL
        }
        
        # Register database configuration
        DatabaseManager.register_config(crd.metadata.name, db_config)
        
        logger.info(f"Database CRD {crd.metadata.name} applied successfully")
        return True
    
    def _apply_commandpolicy_crd(self, crd: CommandPolicyCRD) -> bool:
        """Apply CommandPolicy CRD"""
        logger.info(f"Applying CommandPolicy CRD: {crd.metadata.name}")
        
        # Store CRD for later reference
        self.applied_resources[f"CommandPolicy/{crd.metadata.name}"] = crd
        
        # Import policy engine here to avoid circular import
        from .policy.engine import PolicyEngine
        policy_engine = PolicyEngine()
        
        # Load policy from CRD
        policy = policy_engine.load_policy(crd)
        
        # Set as active policy if it's the default
        if crd.metadata.name == "default-command-whitelist":
            policy_engine.set_active_policy(policy)
        
        logger.info(f"CommandPolicy CRD {crd.metadata.name} applied successfully")
        return True
    
    def _apply_organization_crd(self, crd: OrganizationCRD) -> bool:
        """Apply Organization CRD"""
        logger.info(f"Applying Organization CRD: {crd.metadata.name}")
        
        # Store CRD for later reference
        self.applied_resources[f"Organization/{crd.metadata.name}"] = crd
        
        # Import organization manager here to avoid circular import
        from ..organization.manager import OrganizationManager
        organization_manager = OrganizationManager()
        
        # Convert CRD to organization configuration
        organization_config = {
            "name": crd.metadata.name,
            "company_name": crd.spec.companyName,
            "industry": crd.spec.industry,
            "base_path": crd.spec.basePath or f"./{crd.metadata.name}",
            "hierarchy": self._convert_organization_hierarchy_to_dict(crd.spec.hierarchy),
            "legal_framework": self._convert_legal_framework_to_dict(crd.spec.legalFramework) if hasattr(crd.spec, 'legalFramework') and crd.spec.legalFramework else None
        }
        
        # Apply organization configuration
        result = organization_manager.create_organization(organization_config)
        
        logger.info(f"Organization CRD {crd.metadata.name} applied successfully: {result}")
        return result
    
    def _convert_organization_hierarchy_to_dict(self, hierarchy) -> dict:
        """Convert OrganizationHierarchy to dictionary"""
        if not hierarchy:
            return {}
        
        return {
            "departments": [self._convert_department_to_dict(dept) for dept in hierarchy.departments],
            "legal_framework": self._convert_legal_framework_to_dict(hierarchy.legalFramework) if hasattr(hierarchy, 'legalFramework') and hierarchy.legalFramework else None
        }
    
    def _convert_department_to_dict(self, department) -> dict:
        """Convert DepartmentConfig to dictionary"""
        dept_dict = {
            "id": department.id,
            "name": department.name,
            "description": getattr(department, 'description', ''),
            "roles": [self._convert_role_to_dict(role) for role in department.roles],
            "parent_department": getattr(department, 'parentDepartment', None),
            "legal_framework": self._convert_legal_framework_to_dict(department.legalFramework) if hasattr(department, 'legalFramework') and department.legalFramework else None
        }
        return dept_dict
    
    def _convert_role_to_dict(self, role) -> dict:
        """Convert RoleConfig to dictionary"""
        return {
            "role_type": role.roleType,
            "title": role.title,
            "responsibilities": role.responsibilities,
            "reports_to": getattr(role, 'reportsTo', None)
        }
    
    def _convert_legal_framework_to_dict(self, legal_framework) -> dict:
        """Convert LegalFrameworkConfig to dictionary"""
        if not legal_framework:
            return {}
        
        framework_dict = {
            "enabled": getattr(legal_framework, 'enabled', False),
            "law_directory": getattr(legal_framework, 'lawDirectory', 'law'),
            "system_prompts": getattr(legal_framework, 'systemPrompts', 'system-prompts'),
            "permissions": getattr(legal_framework, 'permissions', 'permissions')
        }
        
        # Add specific rule files based on context
        for attr, key in [
            ('globalRules', 'global_rules'),
            ('regionalRules', 'regional_rules'), 
            ('localRules', 'local_rules'),
            ('projectRules', 'project_rules'),
            ('buildingRules', 'building_rules'),
            ('floorRules', 'floor_rules'),
            ('teamRules', 'team_rules'),
            ('agentRules', 'agent_rules'),
            ('organizationRules', 'organization_rules'),
            ('departmentRules', 'department_rules')
        ]:
            if hasattr(legal_framework, attr):
                framework_dict[key] = getattr(legal_framework, attr)
        
        return framework_dict
    
    def get_applied_resources(self) -> dict:
        """Get list of applied resources"""
        return self.applied_resources.copy()
    
    def remove_resource(self, resource_type: str, name: str) -> bool:
        """Remove applied resource"""
        resource_key = f"{resource_type}/{name}"
        if resource_key in self.applied_resources:
            del self.applied_resources[resource_key]
            logger.info(f"Removed resource: {resource_key}")
            return True
        return False 