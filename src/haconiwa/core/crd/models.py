"""
CRD Data Models for Haconiwa v1.0
"""

from typing import List, Dict, Any, Optional, Union
from pydantic import BaseModel, Field, field_validator, ConfigDict
import re


class Metadata(BaseModel):
    """CRD Metadata"""
    name: str = Field(..., description="Resource name")


class LegalFrameworkConfig(BaseModel):
    """Legal Framework configuration"""
    enabled: bool = Field(False, description="Enable legal framework")
    lawDirectory: str = Field("law", description="Law directory name")
    systemPrompts: str = Field("system-prompts", description="System prompts directory")
    permissions: str = Field("permissions", description="Permissions directory")


class AgentPermissions(BaseModel):
    """Agent permissions configuration"""
    allow: List[str] = Field(default=[], description="Allowed permissions")
    deny: List[str] = Field(default=[], description="Denied permissions")


class AgentDefaultsConfig(BaseModel):
    """Agent defaults configuration for company level"""
    type: str = Field("human-agent", description="Default agent type")
    permissions: Optional[AgentPermissions] = None
    env: Optional[Dict[str, str]] = Field(default={}, description="Environment variables")


class AgentConfig(BaseModel):
    """Agent configuration for task level"""
    type: str = Field("human-agent", description="Agent type")
    additionalPermissions: Optional[AgentPermissions] = None
    env: Optional[Dict[str, str]] = Field(default={}, description="Additional environment variables")
    tools: Optional[List[str]] = Field(default=[], description="Available tools")


class NationLegalFramework(LegalFrameworkConfig):
    """Nation-level legal framework"""
    globalRules: str = Field("global-rules.md", description="Global rules document")


class CityLegalFramework(LegalFrameworkConfig):
    """City-level legal framework"""
    regionalRules: str = Field("regional-rules.md", description="Regional rules document")


class VillageLegalFramework(LegalFrameworkConfig):
    """Village-level legal framework"""
    localRules: str = Field("local-rules.md", description="Local rules document")


class CompanyLegalFramework(LegalFrameworkConfig):
    """Company-level legal framework"""
    projectRules: str = Field("project-rules.md", description="Project rules document")


class BuildingLegalFramework(LegalFrameworkConfig):
    """Building-level legal framework"""
    buildingRules: str = Field("building-rules.md", description="Building rules document")


class FloorLegalFramework(LegalFrameworkConfig):
    """Floor-level legal framework"""
    floorRules: str = Field("floor-rules.md", description="Floor rules document")


class DeskLegalFramework(LegalFrameworkConfig):
    """Desk-level legal framework"""
    agentRules: str = Field("agent-rules.md", description="Agent rules document")


class RoomLegalFramework(LegalFrameworkConfig):
    """Room-level legal framework"""
    teamRules: str = Field("team-rules.md", description="Team rules document")
    desksLaw: Optional[DeskLegalFramework] = Field(None, description="Desk-level legal framework")


class DeskConfig(BaseModel):
    """Desk configuration"""
    id: str
    name: str
    legalFramework: Optional[DeskLegalFramework] = None


class RoomConfig(BaseModel):
    """Room configuration"""
    id: str
    name: str
    description: Optional[str] = None
    legalFramework: Optional[RoomLegalFramework] = None
    desks: List[DeskConfig] = []


class FloorConfig(BaseModel):
    """Floor configuration"""
    id: str
    name: str
    legalFramework: Optional[FloorLegalFramework] = None
    rooms: List[RoomConfig] = []


class BuildingConfig(BaseModel):
    """Building configuration"""
    id: str
    name: str
    legalFramework: Optional[BuildingLegalFramework] = None
    floors: List[FloorConfig] = []


class GitRepoConfig(BaseModel):
    """Git repository configuration"""
    url: str
    defaultBranch: str = "main"
    auth: str = Field(..., description="Authentication method: ssh, https, token")
    
    @field_validator('auth')
    @classmethod
    def validate_auth(cls, v):
        if v not in ['ssh', 'https', 'token']:
            raise ValueError('auth must be ssh, https, or token')
        return v


class OrganizationConfig(BaseModel):
    """Organization configuration"""
    id: str
    name: str
    tasks: List[str] = []


class CompanyConfig(BaseModel):
    """Company configuration"""
    name: str
    grid: str = "8x4"
    basePath: Optional[str] = None
    legalFramework: Optional[CompanyLegalFramework] = None
    gitRepo: Optional[GitRepoConfig] = None
    organizationRef: Optional[str] = Field(None, description="Reference to Organization CRD")
    organizations: List[OrganizationConfig] = []
    buildings: List[BuildingConfig] = []
    agentDefaults: Optional[AgentDefaultsConfig] = None


class VillageConfig(BaseModel):
    """Village configuration"""
    id: str
    name: str
    legalFramework: Optional[VillageLegalFramework] = None
    companies: List[CompanyConfig] = []


class CityConfig(BaseModel):
    """City configuration"""
    id: str
    name: str
    legalFramework: Optional[CityLegalFramework] = None
    villages: List[VillageConfig] = []


class NationConfig(BaseModel):
    """Nation configuration"""
    id: str
    name: str
    legalFramework: Optional[NationLegalFramework] = None
    cities: List[CityConfig] = []


class SpaceSpec(BaseModel):
    """Space CRD specification"""
    nations: List[NationConfig] = Field(..., description="List of nations")
    
    @field_validator('nations')
    @classmethod
    def validate_nations(cls, v):
        if not v:
            raise ValueError('nations cannot be empty')
        return v


class SpaceCRD(BaseModel):
    """Space CRD - World/Company/Room/Desk hierarchy"""
    apiVersion: str = Field("haconiwa.dev/v1", description="API version")
    kind: str = Field("Space", description="Resource kind")
    metadata: Metadata
    spec: SpaceSpec


class AgentSpec(BaseModel):
    """Agent CRD specification"""
    role: str = Field(..., description="Agent role: pm or worker")
    model: str = Field(..., description="AI model to use")
    spaceRef: Optional[str] = Field(None, description="Reference to Space")
    systemPromptPath: Optional[str] = Field(None, description="Path to system prompt file")
    env: Optional[Dict[str, str]] = Field(None, description="Environment variables")
    
    @field_validator('role')
    @classmethod
    def validate_role(cls, v):
        if v not in ['pm', 'worker']:
            raise ValueError("role must be 'pm' or 'worker'")
        return v


class AgentCRD(BaseModel):
    """Agent CRD - AI agent configuration"""
    apiVersion: str = Field("haconiwa.dev/v1", description="API version")
    kind: str = Field("Agent", description="Resource kind")
    metadata: Metadata
    spec: AgentSpec


class TaskSpec(BaseModel):
    """Task CRD specification"""
    branch: str = Field(..., description="Git branch name")
    worktree: bool = Field(True, description="Use git worktree")
    assignee: Optional[str] = Field(None, description="Assigned agent")
    spaceRef: Optional[str] = Field(None, description="Reference to Space")
    description: Optional[str] = Field(None, description="Task description")
    agentConfig: Optional[AgentConfig] = Field(None, description="Agent configuration for this task")
    
    @field_validator('branch')
    @classmethod
    def validate_branch(cls, v):
        # Git branch name validation
        if not re.match(r'^[a-zA-Z0-9._/-]+$', v):
            raise ValueError('branch name contains invalid characters')
        return v


class TaskCRD(BaseModel):
    """Task CRD - Git worktree task"""
    apiVersion: str = Field("haconiwa.dev/v1", description="API version")
    kind: str = Field("Task", description="Resource kind")
    metadata: Metadata
    spec: TaskSpec


class PathScanSpec(BaseModel):
    """PathScan CRD specification"""
    include: List[str] = Field(..., description="Include patterns")
    exclude: List[str] = Field(default_factory=list, description="Exclude patterns")


class PathScanCRD(BaseModel):
    """PathScan CRD - File path scanning configuration"""
    apiVersion: str = Field("haconiwa.dev/v1", description="API version")
    kind: str = Field("PathScan", description="Resource kind")
    metadata: Metadata
    spec: PathScanSpec


class DatabaseSpec(BaseModel):
    """Database CRD specification"""
    dsn: str = Field(..., description="Database connection string")
    useSSL: bool = Field(False, description="Use SSL connection")


class DatabaseCRD(BaseModel):
    """Database CRD - Database connection configuration"""
    apiVersion: str = Field("haconiwa.dev/v1", description="API version")
    kind: str = Field("Database", description="Resource kind")
    metadata: Metadata
    spec: DatabaseSpec


class RolePolicy(BaseModel):
    """Role-specific policy"""
    allow: Dict[str, List[str]] = Field(default_factory=dict, description="Allowed commands")
    deny: Dict[str, List[str]] = Field(default_factory=dict, description="Denied commands")


class CommandPolicySpec(BaseModel):
    """CommandPolicy CRD specification"""
    global_commands: Dict[str, List[str]] = Field(
        default_factory=dict, 
        description="Global command whitelist",
        alias="global"
    )
    roles: Dict[str, RolePolicy] = Field(
        default_factory=dict, 
        description="Role-specific policies"
    )


class CommandPolicyCRD(BaseModel):
    """CommandPolicy CRD - Command execution policy"""
    apiVersion: str = Field("haconiwa.dev/v1", description="API version")
    kind: str = Field("CommandPolicy", description="Resource kind")
    metadata: Metadata
    spec: CommandPolicySpec
    
    model_config = ConfigDict(populate_by_name=True)


# Organization CRD Models
class RoleConfig(BaseModel):
    """Role configuration within organization"""
    roleType: str = Field(..., description="Role type: executive, management, engineering, design")
    title: str = Field(..., description="Role title: CEO, CTO, PM, Senior Developer, etc.")
    responsibilities: List[str] = Field(default_factory=list, description="List of responsibilities")
    reportsTo: Optional[str] = Field(None, description="ID of parent role")
    agentId: Optional[str] = Field(None, description="Unique agent ID for this role")


class DepartmentConfig(BaseModel):
    """Department configuration within organization"""
    id: str = Field(..., description="Department ID")
    name: str = Field(..., description="Department name")
    description: Optional[str] = Field(None, description="Department description")
    roles: List[RoleConfig] = Field(default_factory=list, description="Department roles")
    parentDepartment: Optional[str] = Field(None, description="Parent department ID")
    legalFramework: Optional[LegalFrameworkConfig] = Field(None, description="Department legal framework")


class OrganizationHierarchy(BaseModel):
    """Organization hierarchy configuration"""
    departments: List[DepartmentConfig] = Field(default_factory=list, description="Organization departments")
    legalFramework: Optional[LegalFrameworkConfig] = Field(None, description="Hierarchy legal framework")


class OrganizationSpec(BaseModel):
    """Organization CRD specification"""
    companyName: str = Field(..., description="Company name")
    industry: str = Field(..., description="Industry type")
    hierarchy: OrganizationHierarchy = Field(..., description="Organization hierarchy")
    basePath: Optional[str] = Field(None, description="Base path for organization files")
    legalFramework: Optional[LegalFrameworkConfig] = Field(None, description="Organization legal framework")


class OrganizationCRD(BaseModel):
    """Organization Custom Resource Definition"""
    apiVersion: str = Field("haconiwa.dev/v1", description="API version")
    kind: str = Field("Organization", description="Resource kind")
    metadata: Metadata
    spec: OrganizationSpec
    
    model_config = ConfigDict(populate_by_name=True) 