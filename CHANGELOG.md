# Changelog

## [0.6.3] - 2025-06-20

### リリース版

- バージョン 0.6.3 をリリース

## [0.6.4] - 2025-06-20

### リリース版

- バージョン 0.6.4 をリリース

## [0.6.4-dev] - 2025-06-20

### 開発版

- バージョン 0.6.4-dev をリリース

All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [Unreleased]

## [0.6.0] - 2025-06-13

### 🔧 機能追加（feat）

#### **Git worktree 用の自動 `.env` ファイルコピー機能を追加**
- 📋 **apply コマンドの --env フラグ** - [詳細ガイド](docs/commands/apply.md)
- 🔄 **自動環境変数配布** - 各タスクブランチのgit worktreeディレクトリに.envファイルを自動コピー
- 🏗️ **環境別設定対応** - 複数の.envファイルマージ機能

#### **AIモデル検索と並列設定生成を含む `scan` コマンドを追加**
- 🔍 **scan コマンド完全実装** - [詳細ガイド](docs/commands/scan.md)
- 📊 **AIモデル検索・分析・比較・ガイド生成機能**
- 📝 **並列設定YAML自動生成** - `scan generate-parallel-config`
- 🎯 **プロジェクト内モデル管理** - プレフィックス自動削除、カテゴリ分類

#### **Claude Code SDK の並列実行機能を追加**
- ⚡ **tool parallel-dev コマンド** - [詳細ガイド](docs/commands/tool-parallel-dev.md)
- 🚀 **最大10ファイル並列編集** - asyncio.gatherによる高速並列処理
- 🎯 **セマフォ制御** - 同時実行数制限でAPI負荷管理
- 📊 **リアルタイム進捗表示** - 処理状況の可視化

### 🛠️ 修正（fix）

#### **`.haconiwa` ディレクトリ構造を改善し、マージコンフリクトを防止**
- 🗂️ **統一ディレクトリ構造** - agent_assignment.jsonのパス統一
- 🔧 **room-window動的マッピング** - ハードコーディング除去による柔軟性向上
- 🧹 **コンフリクト回避** - 複数ブランチ間での構造一貫性確保

#### **Git worktree が `origin/branch` から作成されるように修正**
- 🌿 **ブランチ作成改善** - defaultBranchからの正しいブランチ作成
- 🔗 **リモート追跡強化** - origin参照による一貫性確保
- ⚡ **ワークフロー最適化** - タスクブランチ間の独立性向上

## [0.5.0] - 2025-06-13

### Added
- 🤖 **Claude AI統合機能** - AgentへのClaude API統合とAI協調開発支援機能
- 📊 **tmuxモニタリングシステム** - セッション状態の監視とリアルタイム状態取得
- ⚖️ **法的フレームワーク** - プロジェクト管理とコンプライアンス機能
- 🏢 **組織管理システム** - 複数組織の階層管理とロール割り当て機能
- 🏗️ **スペース管理大幅拡充** - グリッドレイアウトと32ペイン対応、マルチルーム機能
- 📋 **YAML設定システム** - 複数の事前定義済み設定ファイルセット
- 🧪 **包括的テストスイート** - 統合テスト、ユニットテスト、シナリオテストの大幅拡充
- 🔄 **GitHub Actions CI/CD** - 継続的統合とシナリオテスト自動化
- 📜 **検証スクリプト群** - tmuxセッション、ペインボーダー、Claude実行検証
- 🤖 **Claude AI Integration** - Claude API integration for agents and AI-assisted collaborative development
- 📊 **tmux Monitoring System** - Session state monitoring and real-time status retrieval
- ⚖️ **Legal Framework** - Project management and compliance functionality
- 🏢 **Organization Management System** - Hierarchical management of multiple organizations and role assignments
- 🏗️ **Enhanced Space Management** - Grid layout with 32-pane support and multi-room functionality
- 📋 **YAML Configuration System** - Multiple pre-defined configuration file sets
- 🧪 **Comprehensive Test Suite** - Extensive integration, unit, and scenario test coverage
- 🔄 **GitHub Actions CI/CD** - Continuous integration and automated scenario testing
- 📜 **Verification Script Collection** - tmux session, pane border, and Claude execution verification
- 📖 **Enhanced Documentation** - Comprehensive README updates in both Japanese and English

### Changed
- 🔧 **CLI機能大幅拡張** - apply, init, policy, space, tool コマンドの機能強化
- 📁 **プロジェクト構造再編** - モジュラー設計とコンポーネント分離
- 🏷️ **設定ファイル体系化** - 用途別YAML設定ファイルの整理と標準化
- 🔧 **Extensive CLI Enhancement** - Enhanced functionality for apply, init, policy, space, tool commands
- 📁 **Project Structure Reorganization** - Modular design and component separation
- 🏷️ **Configuration File Systematization** - Organization and standardization of purpose-specific YAML files

### Fixed
- 🔗 **タスクブランチ管理** - デフォルトブランチからの正しいブランチ作成
- 🎯 **エージェント属性マッピング** - 自動ID割り当てとエージェント管理の修正
- 🧹 **不要ファイル削除** - fix_pane_titles.pyなど古いスクリプトの削除
- 🔗 **Task Branch Management** - Proper branch creation from default branches
- 🎯 **Agent Attribute Mapping** - Fixed automatic ID assignment and agent management
- 🧹 **Legacy File Cleanup** - Removal of outdated scripts like fix_pane_titles.py

### Technical
- 🎯 **54ファイル変更** - 14,432行追加、592行削除の大規模リファクタリング
- 🏗️ **Core Applier機能拡張** - YAML適用とCRD処理の大幅改善
- 📋 **CRDモデル拡充** - 6種類のCRD対応とパーサー機能強化
- 🔧 **Task Manager改良** - ワークツリー管理とブランチ戦略の最適化
- 🎯 **Massive Codebase Update** - 54 files changed, 14,432 additions, 592 deletions
- 🏗️ **Core Applier Enhancement** - Significant improvements to YAML application and CRD processing
- 📋 **Extended CRD Models** - Support for 6 CRD types and enhanced parser functionality
- 🔧 **Improved Task Manager** - Optimized worktree management and branching strategy

## [0.4.0] - 2025-06-12

### Added
- 🚀 **`--no-attach` option** for apply command - allows YAML application without auto-attaching to session
- 🧪 **Complete task assignment lifecycle tests** - comprehensive testing from YAML application to cleanup
- 📋 **Task assignment lifecycle test suite** covering create-to-delete workflow patterns
- 🔧 **Enhanced CLI testing** with improved mock object structure and error handling

### Changed
- 🧹 **Unit test improvements** - fixed CLI v1 and CommandPolicy test compatibility issues
- 🔧 **Mock object enhancements** - added proper spec attributes for CRD objects in tests
- 📊 **Test coverage expansion** - comprehensive validation of CLI apply command workflows

### Fixed
- ✅ **Unit test greenification** - resolved CLI v1 test failures related to --no-attach option addition
- 🔧 **Mock CRD object structure** - added missing metadata and spec attributes for proper test execution
- 📋 **PolicyEngine test compatibility** - aligned test expectations with actual implementation behavior

### Technical
- 🏗️ **Enhanced CLI argument parsing** for apply command with attach/no-attach logic handling
- 🧪 **Improved test infrastructure** for lifecycle testing patterns
- 📝 **Better error messaging** and validation in apply command workflows

## [0.2.1] - 2025-06-11

### Fixed
- 🐛 **ConfigFileHandler AttributeError**: Fixed missing `config_path` attribute in watchdog file handler
- 🔧 **Hot reload functionality**: Corrected scope access for config file monitoring

## [0.2.0] - 2025-06-10

### Added
- 🗑️ **Directory cleanup functionality** for `haconiwa company kill` command
- 📋 **`--clean-dirs` option** to automatically remove company directories
- 🛡️ **Safety confirmation prompt** when using directory cleanup
- 📄 **Metadata tracking system** for intelligent directory management
- 🔄 **Fallback cleanup logic** when metadata files are missing
- 🧪 **Comprehensive test suite** for directory cleanup functionality

### Changed
- 💀 **Enhanced kill command** with optional directory cleanup
- 🔒 **Safety-first design**: Directory deletion requires explicit `--clean-dirs` flag
- 📊 **Improved confirmation prompts** showing deletion scope

### Technical
- 📝 **JSON metadata files** for tracking created directories per company
- 🧹 **Automatic cleanup** of empty base directories
- 🧪 **Integration tests** covering full cleanup workflow
- 🛡️ **Error handling** for permission issues and missing paths

## [0.1.4] - 2025-06-09

### Added
- 📖 **Ready-to-Use Features section** in README (both Japanese and English)
- 📁 **Directory structure documentation** with `--base-path` option explanation
- 🏗️ **Architecture Concepts section** explaining tmux ↔ Haconiwa concept mapping
- 📄 **Auto README generation** in each workspace directory
- 🏷️ **Terminology unification**: session → company throughout documentation

### Changed
- 🔄 **Concept terminology**: Unified "session" to "company" across all documentation
- 📋 **tmux Session** → **Haconiwa Company** concept mapping clarification
- 🏢 **Building/Floor logical hierarchy** management explanation

### Fixed
- 📝 Missing `--base-path` parameter in usage examples
- 🏷️ Inconsistent terminology between session and company

## [0.1.3] - 2025-06-08

### Added
- 🚀 **Complete tmux multiagent environment** (4x4 grid layout)
- 🏢 **Custom organization names** via `--org01-name`, `--org02-name`, etc.
- 🏷️ **Custom task names** via `--task01`, `--task02`, etc.
- 📁 **Automatic directory structure creation** with organized workspaces
- 🔄 **Session update functionality** - safe updates without disrupting existing work
- 🏷️ **Intuitive title ordering**: Organization-Role-Task format
- 📋 **Reliable attach/list commands** using direct tmux subprocess calls
- 📄 **README.md auto-generation** in each workspace directory

### Changed
- 🏷️ **Title order optimization**: From "ORG-01-BOSS-TaskName" to "OrganizationName-BOSS-TaskName"
- 🔧 **Session detection logic**: Automatic detection of existing sessions for update mode
- 🛡️ **Safety improvements**: Prevents overwriting existing directories and files

### Fixed
- 🔗 **Attach command reliability**: Replaced libtmux with direct tmux subprocess calls
- 📋 **List command accuracy**: Improved session status detection
- 🔄 **Update mode safety**: Preserves running processes during title updates

## [0.1.2] - 2025-06-07

### Added
- 🏗️ **Basic tmux session integration** foundation
- 📋 **CLI command structure** with 7 main command groups
- 🎯 **Core project initialization** framework
- 📖 **Comprehensive help system** and command documentation

### Fixed
- 🔧 **Package installation** issues
- 📦 **PyPI distribution** configuration

## [0.1.1] - 2025-06-06

### Added
- 🚀 **Initial PyPI release**
- 📋 **Complete CLI structure** with all command groups
- 📖 **Documentation** (Japanese and English README)
- 🏗️ **Project foundation** and basic architecture

### Technical
- 🐍 **Python 3.8+** support
- 📦 **PyPI package** distribution setup
- 🔧 **Development tools** configuration (pytest, black, flake8, etc.)

## [0.1.0] - 2025-06-05

### Added
- 🎯 **Initial project setup**
- 📋 **CLI framework** with typer
- 🏗️ **Basic project structure**
- 📄 **License and documentation** foundation

[Unreleased]: https://github.com/dai-motoki/haconiwa/compare/v0.6.0...HEAD
[0.6.0]: https://github.com/dai-motoki/haconiwa/compare/v0.5.0...v0.6.0
[0.5.0]: https://github.com/dai-motoki/haconiwa/compare/v0.4.0...v0.5.0
[0.4.0]: https://github.com/dai-motoki/haconiwa/compare/v0.2.1...v0.4.0
[0.2.1]: https://github.com/dai-motoki/haconiwa/compare/v0.2.0...v0.2.1
[0.2.0]: https://github.com/dai-motoki/haconiwa/compare/v0.1.4...v0.2.0
[0.1.4]: https://github.com/dai-motoki/haconiwa/compare/v0.1.3...v0.1.4
[0.1.3]: https://github.com/dai-motoki/haconiwa/compare/v0.1.2...v0.1.3
[0.1.2]: https://github.com/dai-motoki/haconiwa/compare/v0.1.1...v0.1.2
[0.1.1]: https://github.com/dai-motoki/haconiwa/compare/v0.1.0...v0.1.1
[0.1.0]: https://github.com/dai-motoki/haconiwa/releases/tag/v0.1.0 