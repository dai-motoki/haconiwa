# Haconiwa (箱庭) 🚧 **Under Development**

[![PyPI version](https://badge.fury.io/py/haconiwa.svg)](https://badge.fury.io/py/haconiwa)
[![Python](https://img.shields.io/badge/python-3.8+-blue.svg)](https://www.python.org/downloads/)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)
[![Development Status](https://img.shields.io/badge/status-alpha--development-red)](https://github.com/dai-motoki/haconiwa)

**Haconiwa (箱庭)** is an AI collaborative development support Python CLI tool. This next-generation tool integrates tmux company management, git-worktree integration, task management, and AI agent coordination to provide an efficient development environment.

[🇯🇵 日本語版 README](README_JA.md)

## ⚠️ Disclaimer

This project is in early alpha development and in a **demonstration phase**. Current CLI commands are primarily placeholders showing the intended interface design. Most functionality is actively under development and not yet implemented.

**Currently Working:**
- CLI installation and command structure
- Help system and documentation
- Basic command routing

**To be Implemented:**
- Complete implementation of all advertised features
- AI agent collaboration functionality
- Development tool integrations
- Actual task and company management

Production use is not recommended at this time. This is a development preview showing the intended user experience.

> ⚠️ **Note**: This project is currently under active development. Features and APIs may change frequently.

## 📋 Version Management

This project follows [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

- **📄 Changelog**: [CHANGELOG.md](CHANGELOG.md) - All version change history
- **🏷️ Latest Version**: 0.4.0
- **📦 PyPI**: [haconiwa](https://pypi.org/project/haconiwa/)
- **🔖 GitHub Releases**: [Releases](https://github.com/dai-motoki/haconiwa/releases)

## 🚀 Ready-to-Use Features

### 🔧 Recent Updates (2025-06-13)

**Task Branch Fix**: Fixed an issue where task branches were being created from the `main` branch instead of the YAML-specified `defaultBranch`. Now, when you specify `defaultBranch: "dev"` in your YAML configuration, all task worktrees will be correctly created from the `dev` branch.

- ✅ Task CRDs now properly inherit `defaultBranch` from their associated Space CRD
- ✅ Existing incorrect branches are automatically detected and recreated from the correct branch
- ✅ All hardcoded references to `main` branch have been replaced with configurable defaults

## 🛠️ Prerequisites

**Environment Setup**

```bash
# 1. Install tmux
# macOS
brew install tmux

# Ubuntu/Debian
sudo apt-get install tmux

# 2. Python environment setup (3.8+)
python --version  # Check version

# 3. Upgrade pip
pip install --upgrade pip

# 4. Claude Code setup
# See detailed instructions: https://docs.anthropic.com/en/docs/claude-code/getting-started
# Set environment variable (if needed)
export ANTHROPIC_API_KEY="your-api-key"

# 5. Install Haconiwa
pip install haconiwa --upgrade
```

### 📚 Basic Workflow

**1. Get YAML and Launch Project**

```bash
# Download YAML file from GitHub
wget https://raw.githubusercontent.com/dai-motoki/haconiwa/main/haconiwa-dev-company.yaml

# Or download with curl
curl -O https://raw.githubusercontent.com/dai-motoki/haconiwa/main/haconiwa-dev-company.yaml

# Apply YAML (automatically attaches to tmux session by default)
haconiwa apply -f haconiwa-dev-company.yaml
# Detach from tmux session: Ctrl+b, d

# Or, apply without attaching
haconiwa apply -f haconiwa-dev-company.yaml --no-attach

# If not attached, explicitly attach
haconiwa space attach -c haconiwa-dev-company
```

**2. Project Operations**

```bash
# Detach from tmux session: Ctrl+b, d

# Real-time monitoring in another terminal
haconiwa monitor -c haconiwa-dev-company --japanese

# List all projects
haconiwa space list

# Re-attach to project
haconiwa space attach -c haconiwa-dev-company
```

**3. Delete Projects**

```bash
# Completely delete space and directories
haconiwa space delete -c haconiwa-dev-company --clean-dirs --force
```

## 📝 YAML Grammar Detailed Explanation

Haconiwa's declarative YAML configuration uses multiple CRDs (Custom Resource Definitions) in multi-document format.

### 1. Organization CRD (Organization Definition)

```yaml
apiVersion: haconiwa.dev/v1
kind: Organization
metadata:
  name: haconiwa-dev-company-org  # Unique organization identifier
spec:
  companyName: "Haconiwa Development Company"  # Company name
  industry: "AI Development Tools & Infrastructure"  # Industry
  basePath: "./haconiwa-dev-company"  # Organization base path
  hierarchy:
    departments:  # Department definitions
    - id: "executive"  # Department ID (used for room assignment)
      name: "Executive Team"
      description: "Company leadership and strategic decision making"
      roles:  # Role definitions
      - roleType: "management"  # Management role
        title: "Chief Executive Officer"
        agentId: "ceo-motoki"  # Agent ID
        responsibilities:
          - "Strategic vision and direction"
          - "Company-wide decision making"
      - roleType: "engineering"  # Engineering role
        title: "Senior AI Engineer"
        agentId: "ai-lead-nakamura"
        responsibilities:
          - "AI/ML model development"
          - "Algorithm optimization"
```

**Organization CRD Key Elements:**
- `metadata.name`: Unique organization identifier (referenced from Space CRD)
- `spec.hierarchy.departments`: Department definitions (each department maps to a tmux room)
- `spec.hierarchy.departments[].roles`: Role definitions per department (4 roles form 16 panes)

### 2. Space CRD (Space Definition)

```yaml
apiVersion: haconiwa.dev/v1
kind: Space
metadata:
  name: haconiwa-dev-world  # Unique space identifier
spec:
  nations:  # Nation level (top hierarchy)
  - id: jp
    name: Japan
    cities:  # City level
    - id: tokyo
      name: Tokyo
      villages:  # Village level
      - id: haconiwa-village
        name: "Haconiwa Village"
        companies:  # Company level (tmux session)
        - name: haconiwa-dev-company  # Session name
          grid: "8x4"  # Grid size (8 columns × 4 rows = 32 panes)
          basePath: "./haconiwa-dev-world"
          organizationRef: "haconiwa-dev-company-org"  # Organization reference
          gitRepo:  # Git repository settings
            url: "https://github.com/dai-motoki/haconiwa"
            defaultBranch: "dev"  # Base branch for task branches
            auth: "https"
          agentDefaults:  # Agent default settings (planned)
            type: "claude-code"
            permissions:  # Permission settings (planned feature)
              allow:
                - "Bash(python -m pytest)"
                - "Bash(python -m ruff)"
                - "Bash(python -m mypy)"
                - "Read(src/**/*.py)"
                - "Write(src/**/*.py)"
              deny:
                - "Bash(rm -rf /)"
          buildings:  # Building level
          - id: "hq-tower"
            name: "Haconiwa HQ Tower"
            floors:  # Floor level
            - id: "executive-floor"
              name: "Executive Floor"
              rooms:  # Room level (tmux windows)
              - id: room-executive  # Executive window
                name: "Executive Room"
                description: "C-level executives and senior leadership"
              - id: room-standby   # Standby window
                name: "Standby Room"
                description: "Ready-to-deploy talent pool"
```

**Space CRD Hierarchy Structure:**
- `nations` > `cities` > `villages` > `companies` > `buildings` > `floors` > `rooms`
- Legal framework (law/) can be placed at each hierarchy level
- `companies` map to tmux sessions
- `rooms` map to tmux windows

**gitRepo Configuration Detailed Explanation:**
- `url`: URL of the Git repository to clone
- `defaultBranch`: Base branch from which task branches are created
  - Example: When `defaultBranch: "dev"`, all task branches are created from the `dev` branch
  - This allows protecting the `main` branch while deriving feature branches from the development branch
- `auth`: Authentication method ("https" or "ssh")

**Important**: With the `defaultBranch` setting, tasks with `worktree: true` in Task CRD will create new branches and worktrees from this branch. By using Git worktree, each task is isolated in its own directory, providing the following benefits:
- Each task has its own working directory, enabling parallel development
- Multiple tasks can progress simultaneously without branch switching
- Each agent can develop without affecting other tasks' work
- Example: `task_ai_strategy_01` is created as an isolated working environment in `./haconiwa-dev-world/tasks/task_ai_strategy_01/`

**agentDefaults.permissions (Planned Feature):**
- Feature to restrict commands and operations that agents can execute
- `allow`: Permitted command patterns
- `deny`: Prohibited command patterns
- Currently can be written as configuration values, but actual permission control is not yet implemented

### 3. Task CRD (Task Definition)

```yaml
apiVersion: haconiwa.dev/v1
kind: Task
metadata:
  name: task_ai_strategy_01  # Unique task identifier
spec:
  taskId: task_ai_strategy_01  # Task ID
  title: "AI Strategy Development"  # Task title
  description: |  # Detailed description in markdown format
    ## AI Strategy Development
    
    Develop comprehensive AI strategy for Haconiwa platform.
    
    ### Requirements:
    - Market analysis
    - Technology roadmap
    - Competitive analysis
    - Investment planning
  assignee: "ceo-motoki"  # Assigned agent ID
  spaceRef: "haconiwa-dev-company"  # Belonging space
  priority: "high"  # Priority (high/medium/low)
  worktree: true  # Whether to create Git worktree
  branch: "strategy/ai-roadmap"  # Branch name
```

**Task CRD Key Elements:**
- `assignee`: Specify agent ID defined in Organization CRD
- `spaceRef`: Specify the belonging company name
- `worktree`: If true, creates branch from defaultBranch
- `branch`: Branch name to create

### 4. Multi-Document Configuration

```yaml
# Organization definition
---
apiVersion: haconiwa.dev/v1
kind: Organization
metadata:
  name: my-org
spec:
  # ...

---
# Space definition
apiVersion: haconiwa.dev/v1
kind: Space
metadata:
  name: my-space
spec:
  # ...

---
# Task definitions (multiple allowed)
apiVersion: haconiwa.dev/v1
kind: Task
metadata:
  name: task-1
spec:
  # ...
```

**YAML File Configuration Best Practices:**
1. Place organization definition first
2. Place space definition next
3. Place task definitions last (recommend grouping by room)
4. Separate each document with `---`

### 5. Runtime Processing Flow

1. **YAML Parsing**: Decompose multi-document into individual CRD objects
2. **Organization Creation**: Build department/role structure from Organization CRD
3. **Space Creation**: Build tmux session/window structure from Space CRD
4. **Task Creation**: Create Git worktrees and task assignments from Task CRD
   - Create each task branch from `defaultBranch`
   - Place agents in task directories
5. **Claude Execution**: Auto-execute `cd {path} && claude` in each pane

### 6. Law CRD (Legal Framework Definition) - Planned Development

```yaml
apiVersion: haconiwa.dev/v1
kind: Law
metadata:
  name: haconiwa-legal-framework
spec:
  globalRules:  # Global rules
    - name: "security-policy"
      description: "Security policy for all agents"
      content: |
        ## Security Policy
        - Confidential information handling
        - Access control management
        - Data protection policies
    - name: "code-standards"
      description: "Coding standards"
      content: |
        ## Coding Standards
        - PEP 8 compliance (Python)
        - ESLint configuration (JavaScript)
        - Type safety enforcement
  
  hierarchicalRules:  # Hierarchical rules
    nation:
      enabled: true
      rules:
        - "National legal requirements"
        - "Data sovereignty regulations"
    city:
      enabled: true
      rules:
        - "Regional compliance requirements"
        - "Industry standard adherence"
    company:
      enabled: true
      rules:
        - "Organizational governance policies"
        - "Internal control regulations"
  
  permissions:  # Permission management
    defaultPolicy: "deny"  # Default deny
    rules:
      - resource: "production-database"
        actions: ["read"]
        subjects: ["senior-engineers", "cto"]
      - resource: "source-code"
        actions: ["read", "write"]
        subjects: ["all-engineers"]
      - resource: "financial-data"
        actions: ["read", "write"]
        subjects: ["cfo", "finance-team"]
  
  systemPrompts:  # Agent system prompts
    base: |
      You are an AI agent of Haconiwa Development Company.
      Please follow these rules and policies in your actions.
    roleSpecific:
      ceo: "Focus on strategic decision-making and company-wide direction."
      engineer: "Prioritize code quality and best practices."
      security: "Put security and compliance first."
```

**Law CRD Key Elements (Planned):**
- `globalRules`: Global rules applied to all hierarchies
- `hierarchicalRules`: Rules definition by hierarchy (nation/city/company etc.)
- `permissions`: Resource access control management
- `systemPrompts`: Role-specific agent behavior guidelines

**Planned Integration Features:**
- Automatic reference from Organization/Space CRDs
- Hierarchical rule inheritance mechanism
- Runtime permission checking
- Automatic prompt injection to agents

### apply yaml Pattern (v1.0 New Feature)

Declarative YAML file-based multiroom multi-agent environment management is available **right now**:

```bash
# 1. Installation
pip install haconiwa --upgrade

# 2. Download YAML file (directly from GitHub)
wget https://raw.githubusercontent.com/dai-motoki/haconiwa/main/test-multiroom-with-tasks.yaml

# Or download with curl
curl -O https://raw.githubusercontent.com/dai-motoki/haconiwa/main/test-multiroom-with-tasks.yaml

# Check file contents
cat test-multiroom-with-tasks.yaml

# 3. Apply YAML to create multiroom environment (auto-attach by default)
haconiwa apply -f test-multiroom-with-tasks.yaml

# 3b. Apply without auto-attach
haconiwa apply -f test-multiroom-with-tasks.yaml --no-attach

# 4. List spaces
haconiwa space list

# 5. List spaces (short form)
haconiwa space ls

# 6. Attach to specific room (if not auto-attached)
haconiwa space attach -c test-company-multiroom-tasks -r room-frontend

# 7. Execute claude command on all panes
haconiwa space run -c test-company-multiroom-tasks --claude-code

# 8. Execute custom command on specific room
haconiwa space run -c test-company-multiroom-tasks --cmd "echo hello" -r room-backend

# 9. Dry-run to check commands
haconiwa space run -c test-company-multiroom-tasks --claude-code --dry-run

# 10. Stop session
haconiwa space stop -c test-company-multiroom-tasks

# 11. Complete deletion (delete directories too)
haconiwa space delete -c test-company-multiroom-tasks --clean-dirs --force

# 12. Complete deletion (keep directories)
haconiwa space delete -c test-company-multiroom-tasks --force
```

**📁 Auto-created Multiroom Structure (Hierarchical Legal Framework):**
```
./test-multiroom-desks/
├── jp/                                  # Nation Level (国レベル)
│   ├── law/                            # National Law Directory
│   │   ├── global-rules.md            # グローバル規則
│   │   ├── system-prompts/            # システムプロンプト
│   │   │   └── nation-agent-prompt.md
│   │   └── permissions/               # 権限管理
│   │       ├── code-permissions.yaml
│   │       └── file-permissions.yaml
│   └── tokyo/                         # City Level (市レベル)
│       ├── law/                       # City Law Directory
│       │   ├── regional-rules.md     # 地域規則
│       │   ├── system-prompts/       # システムプロンプト
│       │   │   └── city-agent-prompt.md
│       │   └── permissions/          # 権限管理
│       │       ├── code-permissions.yaml
│       │       └── file-permissions.yaml
│       └── test-village/              # Village Level (村レベル)
│           ├── law/                   # Village Law Directory
│           │   ├── local-rules.md    # ローカル規則
│           │   ├── system-prompts/   # システムプロンプト
│           │   │   └── village-agent-prompt.md
│           │   └── permissions/      # 権限管理
│           │       ├── code-permissions.yaml
│           │       └── file-permissions.yaml
│           └── test-multiroom-company/    # Company Level (会社レベル)
│               ├── law/               # Company Law Directory
│               │   ├── project-rules.md  # プロジェクト規則
│               │   ├── system-prompts/   # システムプロンプト
│               │   │   └── company-agent-prompt.md
│               │   └── permissions/      # 権限管理
│               │       ├── code-permissions.yaml
│               │       └── file-permissions.yaml
│               └── headquarters/      # Building Level (建物レベル)
│                   ├── law/           # Building Law Directory
│                   │   ├── building-rules.md # 建物規則
│                   │   ├── system-prompts/   # システムプロンプト
│                   │   │   └── building-agent-prompt.md
│                   │   └── permissions/      # 権限管理
│                   │       ├── code-permissions.yaml
│                   │       └── file-permissions.yaml
│                   └── floor-1/       # Floor Level (階層レベル)
│                       ├── law/       # Floor Law Directory
│                       │   ├── floor-rules.md    # 階層規則
│                       │   ├── system-prompts/   # システムプロンプト
│                       │   │   └── floor-agent-prompt.md
│                       │   └── permissions/      # 権限管理
│                       │       ├── code-permissions.yaml
│                       │       └── file-permissions.yaml
│                       ├── room-01/   # Room Level (部屋レベル)
│                       │   ├── law/   # Room Law Directory
│                       │   │   ├── team-rules.md     # チーム規則
│                       │   │   ├── system-prompts/   # システムプロンプト
│                       │   │   │   └── room-agent-prompt.md
│                       │   │   └── permissions/      # 権限管理
│                       │   │       ├── code-permissions.yaml
│                       │   │       └── file-permissions.yaml
│                       │   └── desks/         # Desk Level (デスクレベル)
│                       │       ├── law/       # Desk Law Directory
│                       │       │   ├── agent-rules.md    # エージェント規則
│                       │       │   ├── system-prompts/   # システムプロンプト
│                       │       │   │   └── desk-agent-prompt.md
│                       │       │   └── permissions/      # 権限管理
│                       │       │       ├── code-permissions.yaml
│                       │       │       └── file-permissions.yaml
│                       │       ├── org-01-pm/
│                       │       ├── org-01-worker-a/
│                       │       ├── org-01-worker-b/
│                       │       ├── org-01-worker-c/
│                       │       ├── org-02-pm/
│                       │       ├── org-02-worker-a/
│                       │       ├── org-02-worker-b/
│                       │       ├── org-02-worker-c/
│                       │       ├── org-03-pm/
│                       │       ├── org-03-worker-a/
│                       │       ├── org-03-worker-b/
│                       │       ├── org-03-worker-c/
│                       │       ├── org-04-pm/
│                       │       ├── org-04-worker-a/
│                       │       ├── org-04-worker-b/
│                       │       └── org-04-worker-c/
│                       └── room-02/   # Room Level (部屋レベル)
│                           ├── law/   # Room Law Directory (同様の構成)
│                           └── desks/ # Desk Level (同様の構成)
├── standby/                # Standby agents (26 agents)
│   └── README.md          # Auto-generated explanation file
└── tasks/                  # Task-assigned agents (6 agents)
    ├── main/              # Main Git repository
    ├── 20250609061748_frontend-ui-design_01/     # Task 1
    ├── 20250609061749_backend-api-development_02/ # Task 2
    ├── 20250609061750_database-schema-design_03/  # Task 3
    ├── 20250609061751_devops-ci-cd-pipeline_04/   # Task 4
    ├── 20250609061752_user-authentication_05/     # Task 5
    └── 20250609061753_performance-optimization_06/ # Task 6
```

**🏢 tmux Structure (Multiroom):**
```
test-multiroom-company (Session)
├── Window 0: Alpha Room (16 panes)
│   ├── org-01 (4 panes): pm, worker-a, worker-b, worker-c
│   ├── org-02 (4 panes): pm, worker-a, worker-b, worker-c  
│   ├── org-03 (4 panes): pm, worker-a, worker-b, worker-c
│   └── org-04 (4 panes): pm, worker-a, worker-b, worker-c
└── Window 1: Beta Room (16 panes)
    ├── org-01 (4 panes): pm, worker-a, worker-b, worker-c
    ├── org-02 (4 panes): pm, worker-a, worker-b, worker-c
    ├── org-03 (4 panes): pm, worker-a, worker-b, worker-c
    └── org-04 (4 panes): pm, worker-a, worker-b, worker-c
```

**✅ YAML Apply Pattern Actual Features:**
- 🏢 **Declarative Management**: Environment definition via YAML files
- 🤖 **Multiroom Support**: Window separation by room units (Frontend/Backend)
- 🔄 **Auto Room Distribution**: Pane arrangement per room windows
- 🚀 **Bulk Command Execution**: All panes or room-specific execution
- 🎯 **Flexible Targeting**: Room-specific command execution
- 🏛️ **Hierarchical Management**: Nation > City > Village > Company
- 📄 **External Configuration**: Complete management via YAML configuration files
- 🗑️ **Flexible Cleanup**: Choice of directory retention or deletion
- 📊 **32 Pane Management**: 2 rooms × 16 panes configuration
- 🔧 **Dry-run Support**: Command verification before execution
- 🎯 **Task Assignment System**: Automatic agent directory movement
- 📋 **Log File Management**: Assignment records via agent_assignment.json
- 🔗 **Auto-attach Feature**: Automatically attach to session after apply (disable with --no-attach)
- 🤖 **Claude Auto-execution**: Claude command executed in all panes after creation
- 🏠 **Relative Path Support**: Clean path display using ~ prefix for home directories

### tmux Multi-Agent Environment (Traditional Method)

Create and manage a 4x4 grid multi-agent development environment **right now**:

```bash
# 1. Installation
pip install haconiwa

# 2. Create multi-agent environment (4 organizations × 4 roles = 16 panes)
haconiwa company build --name my-company \
  --base-path /path/to/desks \
  --org01-name "Frontend Development" --task01 "UI Design" \
  --org02-name "Backend Development" --task02 "API Development" \
  --org03-name "Database Team" --task03 "Schema Design" \
  --org04-name "DevOps Team" --task04 "Infrastructure"

# 3. List companies
haconiwa company list

# 4. Attach to existing company
haconiwa company attach my-company

# 5. Update company settings (organization name changes)
haconiwa company build --name my-company \
  --org01-name "New Frontend Team" --task01 "React Development"

# 6. Force rebuild existing company
haconiwa company build --name my-company \
  --base-path /path/to/desks \
  --org01-name "Renewed Development Team" \
  --rebuild

# 7. Terminate company (with directory cleanup)
haconiwa company kill my-company --clean-dirs --base-path /path/to/desks --force

# 8. Terminate company (keep directories)
haconiwa company kill my-company --force
```

**📁 Auto-created Directory Structure:**
```
/path/to/desks/
├── org-01/
│   ├── 01boss/          # PM desk
│   ├── 01worker-a/      # Worker-A desk
│   ├── 01worker-b/      # Worker-B desk
│   └── 01worker-c/      # Worker-C desk
├── org-02/
│   ├── 02boss/
│   ├── 02worker-a/
│   ├── 02worker-b/
│   └── 02worker-c/
├── org-03/ (same structure)
└── org-04/ (same structure)
```

**✅ Actually Working Features:**
- 🏢 **Integrated Build Command**: Create, update, and rebuild with a single command
- 🤖 **Automatic Existence Check**: Auto-detect company existence and choose appropriate action
- 🔄 **Seamless Updates**: Safely modify existing company configurations
- 🔨 **Force Rebuild**: Complete recreation with --rebuild option
- 🏗️ **Auto Directory Structure**: Automatic desk creation by organization/role
- 🏷️ **Custom Organization & Task Names**: Dynamic title configuration
- 🗑️ **Flexible Cleanup**: Choose to keep or delete directories
- 🏛️ **Company Management**: Complete support for create/list/attach/delete
- 📄 **Auto README Generation**: Automatic README.md creation in each desk
- 📊 **4x4 Multi-Agent**: Organizational tmux layout (16 panes)

## 📚 Build Command Detailed Guide

### Basic Usage

#### 1. Create New Company (Minimal Configuration)
```bash
# Simple company creation (default settings)
haconiwa company build --name my-company

# Custom base path specification
haconiwa company build --name my-company --base-path ./workspace
```

#### 2. Complete Custom Company Creation
```bash
haconiwa company build --name my-company \
  --base-path ./workspace \
  --org01-name "Frontend Team" --task01 "UI/UX Development" \
  --org02-name "Backend Team" --task02 "API Design" \
  --org03-name "Infrastructure Team" --task03 "DevOps" \
  --org04-name "QA Team" --task04 "Quality Assurance" \
  --no-attach  # Don't auto-attach after creation
```

#### 3. Update Existing Company
```bash
# Change organization name only (auto-detect update mode)
haconiwa company build --name my-company \
  --org01-name "New Frontend Team"

# Update multiple settings simultaneously
haconiwa company build --name my-company \
  --org01-name "React Development Team" --task01 "SPA Application Development" \
  --org02-name "Node.js Development Team" --task02 "RESTful API"
```

#### 4. Force Rebuild
```bash
# Completely recreate existing company
haconiwa company build --name my-company \
  --base-path ./workspace \
  --org01-name "Renewed Development Team" \
  --rebuild
```

### Advanced Usage

#### Desk Customization
```bash
# Specify workspace (desk) for each organization
haconiwa company build --name my-company \
  --desk01 "react-frontend-desk" \
  --desk02 "nodejs-backend-desk" \
  --desk03 "docker-infra-desk" \
  --desk04 "testing-qa-desk"
```

#### Cleanup Options
```bash
# Terminate company (delete tmux session only, keep directories)
haconiwa company kill my-company --force

# Complete deletion (delete directories too)
haconiwa company kill my-company \
  --clean-dirs \
  --base-path ./workspace \
  --force
```

### Automatic Mode Detection

The build command automatically detects company existence status and chooses the appropriate action:

| Situation | Action | Example Message |
|-----------|--------|----------------|
| Company doesn't exist | **New Creation** | 🏗️ Building new company: 'my-company' |
| Company exists + configuration changes | **Update** | 🔄 Updating existing company: 'my-company' |
| Company exists + no configuration changes | **Information Display** | ℹ️ No changes specified for company 'my-company' |
| --rebuild option specified | **Force Rebuild** | 🔄 Rebuilding company: 'my-company' |

### Troubleshooting

#### Common Issues and Solutions

**Issue**: Company not responding
```bash
# 1. Check company status
haconiwa company list

# 2. Force terminate
haconiwa company kill my-company --force

# 3. Recreate
haconiwa company build --name my-company --rebuild
```

**Issue**: Directory permission errors
```bash
# Check and fix base path permissions
chmod 755 ./workspace
haconiwa company build --name my-company --base-path ./workspace
```

**Issue**: tmux session remains
```bash
# Manually check tmux sessions
tmux list-sessions

# Manual deletion
tmux kill-session -t my-company
```

## ✨ Key Features (In Development)

- 🤖 **AI Agent Management**: Create and monitor Boss/Worker agents
- 📦 **World Management**: Build and manage development environments
- 🖥️ **tmux Company Integration**: Efficient development space management
- 📋 **Task Management**: Task management system integrated with git-worktree
- 📊 **Resource Management**: Efficient scanning of databases and file paths
- 👁️ **Real-time Monitoring**: Progress monitoring of agents and tasks

## 🏗️ Architecture Concepts

### CRD-Based Architecture

Haconiwa is built around four main CRDs (Custom Resource Definitions):

```
Haconiwa CRD Architecture
├── Organization CRD (Organization Definition)
│   ├── Department Structure (departments)
│   ├── Role Definitions (roles)
│   └── Responsibilities (responsibilities)
├── Space CRD (Space Definition)
│   ├── Hierarchy (nations > cities > villages > companies > buildings > floors > rooms)
│   ├── Git Repository Settings (gitRepo)
│   └── tmux Session/Window Mapping
├── Task CRD (Task Definition)
│   ├── Task Details (title, description)
│   ├── Agent Assignment (assignee)
│   └── Git Worktree Settings (branch, worktree)
└── Law CRD (Legal Framework) - Planned
    ├── Global Rules (globalRules)
    ├── Hierarchical Rules (hierarchicalRules)
    └── Permission Management (permissions)
```

### CRD Relationships and Processing Flow

```
1. Organization CRD
   ↓ Defines
   Agent Structure (Departments & Roles)
   ↓
2. Space CRD
   ↓ References (organizationRef)
   Physical Layout (tmux Sessions & Windows)
   ↓
3. Task CRD
   ↓ References (spaceRef, assignee)
   Work Assignment & Git Worktree Creation
   ↓
4. Law CRD (Planned)
   ↓ Integrates
   Rules & Permissions Applied to All CRDs
```

### tmux ↔ Haconiwa CRD Mapping

| Haconiwa CRD | tmux Concept | Main Role |
|-------------|--------------|-----------|
| **Organization** | - | Define agent organizational structure |
| **Space (Company)** | **Session** | Top-level container for development environment |
| **Space (Room)** | **Window** | Functional work groups |
| **Task + Agent** | **Pane** | Individual agent work environment |

### Key Features

**1. Declarative Environment Management**
- Define all configuration in YAML files
- Build reproducible development environments

**2. Task Isolation with Git Worktree**
- Each task works in an independent directory
- Automatic branch creation from `defaultBranch`
- Enable parallel development

**3. Hierarchical Structure**
- Space CRD hierarchy (Nation → City → Village → Company → Building → Floor → Room)
- Future hierarchical rule inheritance via Law CRD

**4. Automated Agent Placement**
- Automatic placement of agents defined in Organization CRD
- Work assignment via Task CRD
- Automatic mapping to tmux panes

## 🚀 Installation

```bash
pip install haconiwa
```

> 📝 **Development Note**: The package is available on PyPI, but many features are still under development.

## ⚡ Quick Start

> 🎭 **Important**: The commands shown below are **for demonstration purposes**. Currently, these commands display help information and basic structure, but the actual functionality is under development. We are actively working toward complete feature implementation.

### 1. Check available commands
```bash
haconiwa --help
```

### 2. Initialize project
```bash
haconiwa core init
```

### 3. Create development world
```bash
haconiwa world create local-dev
```

### 4. Launch AI agents
```bash
# Create boss agent
haconiwa agent spawn boss

# Create worker agent
haconiwa agent spawn worker-a
```

### 5. Task management
```bash
# Create new task
haconiwa task new feature-login

# Assign task to agent
haconiwa task assign feature-login worker-a

# Monitor progress
haconiwa watch tail worker-a
```

## 📖 Command Reference

> 🔧 **Development Note**: The commands listed below are currently **for demonstration and testing purposes**. The CLI structure is functional, but most commands display help information or placeholder responses. We are actively developing the core functionality behind each command group.

The CLI tool provides 7 main command groups:

### `agent` - Agent Management Commands
Manage AI agents (Boss/Worker) for collaborative development
- `haconiwa agent spawn <type>` - Create agent
- `haconiwa agent ps` - List agents
- `haconiwa agent kill <name>` - Stop agent

### `core` - Core Management Commands
System core management and configuration
- `haconiwa core init` - Initialize project
- `haconiwa core status` - Check system status
- `haconiwa core upgrade` - Upgrade system

### `resource` - Resource Management
Scan and manage project resources (databases, files, etc.)
- `haconiwa resource scan` - Resource scanning
- `haconiwa resource list` - List resources

### `company` - tmux Company and Enterprise Management
Efficient development enterprise environment management using tmux
- `haconiwa company build <name>` - Create, update, and rebuild tmux companies
- `haconiwa company list` - List companies
- `haconiwa company attach <name>` - Attach to company
- `haconiwa company kill <name>` - Terminate/delete company
- `haconiwa company resize <name>` - Adjust company layout

### `task` - Task Management Commands
Task management integrated with git-worktree
- `haconiwa task new <name>` - Create new task
- `haconiwa task assign <task> <agent>` - Assign task
- `haconiwa task status` - Check task status

### `watch` - Monitoring Commands
Real-time monitoring of agents and tasks
- `haconiwa watch tail <target>` - Real-time monitoring
- `haconiwa watch logs` - Display logs

### `world` - World Management
Development environment and world management
- `haconiwa world create <name>` - Create new development world
- `haconiwa world list` - List worlds
- `haconiwa world switch <name>` - Switch world

## 🛠️ Development Status

> 🎬 **Current Phase**: **Demonstration & Prototyping**  
> Most CLI commands are currently demonstration placeholders showing the intended structure and help information. We are actively developing the core functionality behind each command.

### ✅ Completed Features
- Basic CLI structure with 7 command groups
- PyPI package distribution and installation
- Core project initialization framework
- **tmux Company Management System (company build command)**
- **Multi-Agent 4x4 Layout Auto-Construction**
- **Organization, Task, and Desk Customization Features**
- **Automatic Company Existence Check and Update Functionality**
- **Flexible Cleanup System**
- Help system and command documentation
- Command group organization and routing

### 🚧 Features in Development
- AI agent generation and management (placeholder → implementation)
- git-worktree task management integration (placeholder → implementation)
- Resource scanning functionality (placeholder → implementation)
- Real-time monitoring system (placeholder → implementation)
- World/environment management (placeholder → implementation)

### 📋 Planned Features
- Advanced AI agent collaboration
- Integration with popular development tools
- Plugin system for extensibility
- Web-based monitoring dashboard

## 🛠️ Development Environment Setup

```bash
git clone https://github.com/dai-motoki/haconiwa.git
cd haconiwa
python -m venv venv
source venv/bin/activate  # Windows: venv\Scripts\activate
pip install -e .[dev]
```

### Running Tests

```bash
pytest tests/
```

## 📝 License

MIT License - See [LICENSE](LICENSE) file for details.

## 🤝 Contributing

We welcome contributions to the project! As this is an active development project, we recommend:

1. Check existing issues and discussions
2. Fork this repository
3. Create a feature branch (`git checkout -b feature/amazing-feature`)
4. Commit your changes (`git commit -m 'Add amazing feature'`)
5. Push to the branch (`git push origin feature/amazing-feature`)
6. Create a Pull Request

## 📞 Support

- GitHub Issues: [Issues](https://github.com/dai-motoki/haconiwa/issues)
- Email: kanri@kandaquantum.co.jp


---

**Haconiwa (箱庭)** - The Future of AI Collaborative Development 🚧