# Haconiwa (箱庭) 🚧 **Under Development**

[![PyPI version](https://badge.fury.io/py/haconiwa.svg)](https://badge.fury.io/py/haconiwa)
[![Python](https://img.shields.io/badge/python-3.8+-blue.svg)](https://www.python.org/downloads/)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)
[![Development Status](https://img.shields.io/badge/status-alpha--development-red)](https://github.com/dai-motoki/haconiwa)

**Haconiwa (箱庭)** is an AI collaborative development support Python CLI tool. This next-generation tool integrates tmux company management, git-worktree integration, task management, and AI agent coordination to provide an efficient development environment.

> ⚠️ **Note**: This project is currently under active development. Features and APIs may change frequently.

[🇯🇵 日本語版 README](README_JA.md)

## 📋 Version Management

This project follows [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

- **📄 Changelog**: [CHANGELOG.md](CHANGELOG.md) - All version change history
- **🏷️ Latest Version**: 0.4.0
- **📦 PyPI**: [haconiwa](https://pypi.org/project/haconiwa/)
- **🔖 GitHub Releases**: [Releases](https://github.com/dai-motoki/haconiwa/releases)

## 🚀 Ready-to-Use Features

### apply yaml Pattern (v1.0 New Feature)

Declarative YAML file-based multiroom multi-agent environment management is available **right now**:

```bash
# 1. Installation
pip install haconiwa --upgrade

# 2. Download YAML file (directly from GitHub)
wget https://raw.githubusercontent.com/dai-motoki/haconiwa/main/haconiwa-multiroom-test.yaml

# Or download with curl
curl -O https://raw.githubusercontent.com/dai-motoki/haconiwa/main/haconiwa-multiroom-test.yaml

# Check file contents
cat haconiwa-multiroom-test.yaml

# 3. Apply YAML to create multiroom environment
haconiwa apply -f haconiwa-multiroom-test.yaml

# 4. List spaces
haconiwa space list

# 5. List spaces (short form)
haconiwa space ls

# 6. Attach to specific room
haconiwa space attach -c test-multiroom-company -r room-01

# 7. Execute claude command on all panes
haconiwa space run -c test-multiroom-company --claude-code

# 8. Execute custom command on specific room
haconiwa space run -c test-multiroom-company --cmd "echo hello" -r room-01

# 9. Dry-run to check commands
haconiwa space run -c test-multiroom-company --claude-code --dry-run

# 10. Stop session
haconiwa space stop -c test-multiroom-company

# 11. Complete deletion (delete directories too)
haconiwa space delete -c test-multiroom-company --clean-dirs --force

# 12. Complete deletion (keep directories)
haconiwa space delete -c test-multiroom-company --force
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
- 🤖 **Multiroom Support**: Window separation by room units
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

### Space Rule Hierarchy (スペース規則階層)

Haconista incorporates a **space rule hierarchy** that manages agent governance through simple rule inheritance following the YAML space structure:

| Hierarchy Level | Rule Document | Tmux Mapping | Agent Governance | Directory Structure |
|----------------|---------------|--------------|------------------|-------------------|
| **Nation (国)** | **Global Rules (グローバル規則)** | - | Universal principles & core standards | `jp/law/global-rules.md` |
| **City (市)** | **Regional Rules (地域規則)** | - | Regional guidelines & compliance | `jp/tokyo/law/regional-rules.md` |
| **Village (村)** | **Local Rules (ローカル規則)** | - | Community practices & workflows | `jp/tokyo/test-village/law/local-rules.md` |
| **Company (会社)** | **Project Rules (プロジェクト規則)** | **Session** | Project policies & procedures | `jp/tokyo/test-village/test-multiroom-company/law/project-rules.md` |
| **Building (建物)** | **Building Rules (建物規則)** | - | Building-specific guidelines | `../headquarters/law/building-rules.md` |
| **Floor (階層)** | **Floor Rules (階層規則)** | - | Floor-level management | `../floor-1/law/floor-rules.md` |
| **Room (部屋)** | **Team Rules (チーム規則)** | **Window** | Team-specific guidelines | `../room-01/law/team-rules.md` |
| **Desk (デスク)** | **Agent Rules (エージェント規則)** | **Pane** | Individual agent behavior rules | `../desks/law/agent-rules.md` |

### Rule Document & Agent Management System

Each hierarchy level contains a `law/` directory with:

```
{level}/law/
├── {rule-document}.md      # 規則文書 (Rule Document)
├── system-prompts/         # システムプロンプト (System Prompts)
│   └── {level}-agent-prompt.md
└── permissions/            # 権限管理 (Permissions Management)
    ├── code-permissions.yaml    # コード権限 (Code Permissions)
    └── file-permissions.yaml   # ファイル権限 (File Permissions)
```

**📋 Space Rule Framework Features:**
- **🏛️ YAML-Aligned Hierarchy**: Perfect match with YAML space structure (Nations > Cities > Villages > Companies > Buildings > Floors > Rooms > Desks)
- **🤖 Universal Agents**: All agents follow the same structure with different rule sets
- **📜 Distributed Law Management**: Rule documents distributed across actual space hierarchy
- **🔐 Hierarchical Permissions**: Code and file access rights inherited through space levels
- **📋 Compliance Tracking**: Automatic rule compliance verification across all space levels
- **🔄 Rule Inheritance**: Agents inherit rules from all parent space levels in order

### tmux ↔ Haconiwa Concept Mapping

| tmux Concept | Haconiwa Concept | Rule Framework | Description |
|-------------|------------------|----------------|-------------|
| **Session** | **Company** | **Project Rules** | Top-level management unit with project governance |
| **Window** | **Room** | **Team Rules** | Functional work areas with team-specific rules |
| **Pane** | **Desk** | **Agent Rules** | Individual workspaces with personal agent rules |

### Hierarchical Rule Management

```
YAML-Aligned Space Rule Framework (YAML準拠スペース規則フレームワーク)
├── Nation (jp) (国)                    ← Global principles (グローバル原則)
│   └── City (tokyo) (市)              ← Regional guidelines (地域ガイドライン)
│       └── Village (test-village) (村) ← Local practices (ローカルプラクティス)
│           └── Company (test-multiroom-company) (会社) ← Project rules (プロジェクト規則) → tmux Session
│               └── Building (headquarters) (建物) ← Building rules (建物規則)
│                   └── Floor (floor-1) (階層) ← Floor rules (階層規則)
│                       └── Room (room-01/room-02) (部屋) ← Team rules (チーム規則) → tmux Window
│                           └── Desk (desks/*) (デスク) ← Agent rules (エージェント規則) → tmux Pane
```

**Space Governance Features:**
- **Nation**: Global principles, universal standards, core architecture guidelines
- **City**: Regional development standards, technical compliance requirements
- **Village**: Community guidelines, local workflow standards, team protocols
- **Company**: Project management policies, business logic constraints, resource rules
- **Building**: Building-specific procedures, physical space management
- **Floor**: Floor-level coordination, resource allocation, cross-room communication
- **Room**: Team-specific procedures, role-based responsibilities, task guidelines
- **Desk**: Individual agent behavior, personal productivity standards, task constraints

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

---

**Haconiwa (箱庭)** - The Future of AI Collaborative Development 🚧