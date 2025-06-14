"""
Organization Manager for Haconiwa v1.0
"""

import subprocess
from pathlib import Path
from typing import Dict, List, Any, Optional
import logging

logger = logging.getLogger(__name__)


class OrganizationManagerError(Exception):
    """Organization manager error"""
    pass


class OrganizationManager:
    """Organization manager for creating and managing organizational structures"""
    
    def __init__(self):
        self.created_organizations = {}
    
    def create_organization(self, config: Dict[str, Any]) -> bool:
        """Create organization structure with departments and roles"""
        try:
            org_name = config["name"]
            company_name = config["company_name"]
            industry = config["industry"]
            base_path = Path(config.get("base_path", f"./{org_name}"))
            hierarchy = config.get("hierarchy", {})
            legal_framework = config.get("legal_framework")
            
            logger.info(f"Creating organization: {company_name} ({industry})")
            logger.info(f"Base path: {base_path}")
            
            # Create base organization directory
            org_path = base_path / "organization"
            org_path.mkdir(parents=True, exist_ok=True)
            
            # Create company metadata file
            self._create_company_metadata(org_path, config)
            
            # Create organizational hierarchy
            departments_created = 0
            roles_created = 0
            
            if hierarchy and "departments" in hierarchy:
                for dept_config in hierarchy["departments"]:
                    dept_result = self._create_department(org_path, dept_config)
                    departments_created += 1
                    roles_created += len(dept_config.get("roles", []))
            
            # Apply organization-level legal framework
            if legal_framework:
                self._apply_organization_legal_framework(org_path, legal_framework)
            
            # Display organization structure
            self._display_organization_structure(org_path, config, departments_created, roles_created)
            
            # Store organization configuration
            self.created_organizations[org_name] = {
                "config": config,
                "path": str(org_path),
                "departments": departments_created,
                "roles": roles_created
            }
            
            logger.info(f"✅ Organization '{company_name}' created successfully")
            logger.info(f"   📁 Path: {org_path}")
            logger.info(f"   🏢 Departments: {departments_created}")
            logger.info(f"   👥 Roles: {roles_created}")
            
            return True
            
        except Exception as e:
            logger.error(f"Failed to create organization {config.get('name', 'unknown')}: {e}")
            return False
    
    def _create_company_metadata(self, org_path: Path, config: Dict[str, Any]) -> None:
        """Create company metadata file"""
        metadata_file = org_path / "company_info.md"
        
        content = f"""# {config['company_name']}

## Company Information
- **Industry**: {config['industry']}
- **Organization Type**: {config['name']}
- **Created**: {self._get_timestamp()}

## Description
This directory contains the organizational structure and role definitions for {config['company_name']}.

## Directory Structure
- `departments/` - Department-specific configurations and roles
- `roles/` - Global role definitions and templates
- `policies/` - Company-wide policies and procedures
- `law/` - Legal framework and compliance rules (if enabled)

## Navigation
Use the department directories to access specific team configurations and role assignments.
"""
        
        with open(metadata_file, 'w', encoding='utf-8') as f:
            f.write(content)
    
    def _create_department(self, org_path: Path, dept_config: Dict[str, Any]) -> bool:
        """Create department structure with roles"""
        try:
            dept_id = dept_config["id"]
            dept_name = dept_config["name"]
            dept_description = dept_config.get("description", "")
            roles = dept_config.get("roles", [])
            
            # Create department directory
            dept_path = org_path / "departments" / dept_id
            dept_path.mkdir(parents=True, exist_ok=True)
            
            # Create department README
            self._create_department_readme(dept_path, dept_config)
            
            # Create roles directory
            roles_path = dept_path / "roles"
            roles_path.mkdir(exist_ok=True)
            
            # Create each role
            for role_config in roles:
                self._create_role(roles_path, role_config, dept_name)
            
            # Apply department-level legal framework
            dept_legal_framework = dept_config.get("legal_framework")
            if dept_legal_framework:
                self._apply_department_legal_framework(dept_path, dept_legal_framework)
            
            logger.info(f"Created department: {dept_name} ({dept_id}) with {len(roles)} roles")
            return True
            
        except Exception as e:
            logger.error(f"Failed to create department {dept_config.get('id', 'unknown')}: {e}")
            return False
    
    def _create_role(self, roles_path: Path, role_config: Dict[str, Any], dept_name: str) -> None:
        """Create individual role configuration"""
        role_type = role_config["role_type"]
        title = role_config["title"]
        responsibilities = role_config.get("responsibilities", [])
        reports_to = role_config.get("reports_to")
        
        # Create role directory (sanitize title for directory name)
        role_dir_name = title.lower().replace(" ", "-").replace("/", "-")
        role_path = roles_path / role_dir_name
        role_path.mkdir(exist_ok=True)
        
        # Create role definition file
        role_file = role_path / "role_definition.md"
        
        content = f"""# {title}

## Role Information
- **Department**: {dept_name}
- **Role Type**: {role_type}
- **Reports To**: {reports_to or "Not specified"}

## Responsibilities
"""
        
        if responsibilities:
            for resp in responsibilities:
                content += f"- {resp}\n"
        else:
            content += "- *Responsibilities to be defined*\n"
        
        content += f"""
## Working Directory
This role's working directory and configurations are located in:
`{role_path}`

## Legal Framework
Role-specific legal framework and permissions are defined in the `law/` subdirectory (if applicable).

---
*Generated on: {self._get_timestamp()}*
"""
        
        with open(role_file, 'w', encoding='utf-8') as f:
            f.write(content)
    
    def _create_department_readme(self, dept_path: Path, dept_config: Dict[str, Any]) -> None:
        """Create department README file"""
        readme_file = dept_path / "README.md"
        
        content = f"""# {dept_config['name']}

## Department Information
- **ID**: {dept_config['id']}
- **Name**: {dept_config['name']}
- **Description**: {dept_config.get('description', 'No description provided')}

## Structure
This department contains the following roles:

"""
        
        roles = dept_config.get("roles", [])
        if roles:
            for role in roles:
                title = role["title"]
                role_type = role["role_type"]
                content += f"- **{title}** ({role_type})\n"
        else:
            content += "- *No roles defined*\n"
        
        content += f"""
## Directory Layout
- `roles/` - Individual role configurations
- `law/` - Department-specific legal framework (if enabled)
- `policies/` - Department policies and procedures

---
*Generated on: {self._get_timestamp()}*
"""
        
        with open(readme_file, 'w', encoding='utf-8') as f:
            f.write(content)
    
    def _apply_organization_legal_framework(self, org_path: Path, legal_framework: Dict[str, Any]) -> None:
        """Apply legal framework to organization level"""
        try:
            from ..legal.framework import HierarchicalLegalFramework
            
            # Create legal framework structure
            framework = HierarchicalLegalFramework(org_path)
            
            # Create organization-level legal framework
            law_path = org_path / "law"
            law_path.mkdir(exist_ok=True)
            
            # Create organization-level rules
            org_rules_file = law_path / "organization-rules.md"
            with open(org_rules_file, 'w', encoding='utf-8') as f:
                f.write(f"""# Organization Legal Framework

## Company-Wide Rules
This document defines the legal framework and compliance rules for the entire organization.

## Scope
These rules apply to all departments, roles, and activities within the organization.

## Rules
- All organizational activities must comply with industry regulations
- Department-specific rules supplement but do not override organization rules
- Role-specific permissions are granted within department boundaries

## Framework Structure
- **Organization Level**: Company-wide rules and policies
- **Department Level**: Team-specific regulations
- **Role Level**: Individual responsibilities and permissions

---
*Generated on: {self._get_timestamp()}*
""")
            
            logger.info(f"Applied organization-level legal framework: {law_path}")
            
        except Exception as e:
            logger.warning(f"Could not apply organization legal framework: {e}")
    
    def _apply_department_legal_framework(self, dept_path: Path, legal_framework: Dict[str, Any]) -> None:
        """Apply legal framework to department level"""
        try:
            # Create department-level legal framework
            law_path = dept_path / "law"
            law_path.mkdir(exist_ok=True)
            
            # Create department-level rules
            dept_rules_file = law_path / "department-rules.md"
            with open(dept_rules_file, 'w', encoding='utf-8') as f:
                f.write(f"""# Department Legal Framework

## Department-Specific Rules
This document defines the legal framework and compliance rules specific to this department.

## Scope
These rules apply to all roles and activities within this department.

## Inheritance
- Inherits from organization-level legal framework
- Adds department-specific regulations
- Can be further specialized at role level

---
*Generated on: {self._get_timestamp()}*
""")
            
            logger.debug(f"Applied department-level legal framework: {law_path}")
            
        except Exception as e:
            logger.warning(f"Could not apply department legal framework: {e}")
    
    def _display_organization_structure(self, org_path: Path, config: Dict[str, Any], 
                                      departments_created: int, roles_created: int) -> None:
        """Display organization structure using Rich"""
        from rich.console import Console
        from rich.tree import Tree
        from rich.panel import Panel
        
        console = Console()
        
        # Create organization tree
        company_name = config["company_name"]
        industry = config["industry"]
        
        tree = Tree(f"🏢 [bold cyan]{company_name}[/bold cyan] ({industry})")
        
        # Add departments
        hierarchy = config.get("hierarchy", {})
        if hierarchy and "departments" in hierarchy:
            for dept_config in hierarchy["departments"]:
                dept_name = dept_config["name"]
                dept_id = dept_config["id"]
                roles = dept_config.get("roles", [])
                
                dept_branch = tree.add(f"🏬 [yellow]{dept_name}[/yellow] ({dept_id})")
                
                # Add roles to department
                for role_config in roles:
                    title = role_config["title"]
                    role_type = role_config["role_type"]
                    reports_to = role_config.get("reports_to", "")
                    
                    role_display = f"👤 [white]{title}[/white] [{role_type}]"
                    if reports_to:
                        role_display += f" → {reports_to}"
                    
                    dept_branch.add(role_display)
        
        # Display in panel
        console.print()
        console.print(Panel.fit(
            tree,
            title="[bold green]🏢 Organization Structure[/bold green]",
            style="green",
            subtitle=f"[dim]{departments_created} departments, {roles_created} roles[/dim]"
        ))
        console.print()
    
    def _get_timestamp(self) -> str:
        """Get current timestamp"""
        from datetime import datetime
        return datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    
    def list_organizations(self) -> List[Dict[str, Any]]:
        """List all created organizations"""
        return list(self.created_organizations.values())
    
    def get_organization(self, name: str) -> Optional[Dict[str, Any]]:
        """Get specific organization configuration"""
        return self.created_organizations.get(name) 