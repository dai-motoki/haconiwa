# 箱庭 (Haconiwa) 🚧 **開発中**

[![PyPI version](https://badge.fury.io/py/haconiwa.svg)](https://badge.fury.io/py/haconiwa)
[![Python](https://img.shields.io/badge/python-3.8+-blue.svg)](https://www.python.org/downloads/)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)
[![Development Status](https://img.shields.io/badge/status-alpha--development-red)](https://github.com/dai-motoki/haconiwa)

**箱庭 (Haconiwa)** は、AI協調開発支援Python CLIツールです。tmux会社管理、git-worktree連携、タスク管理、AIエージェント調整機能を統合し、効率的な開発環境を提供する次世代ツールです。

[🇺🇸 English README](README.md)

## ⚠️ 免責事項

このプロジェクトは初期アルファ開発段階かつ**デモンストレーションフェーズ**にあります。現在のCLIコマンドは主に意図されたインターフェースデザインを示すプレースホルダーです。ほとんどの機能は活発に開発中でまだ実装されていません。

**現在動作するもの:**
- CLIのインストールとコマンド構造
- ヘルプシステムとドキュメント
- 基本的なコマンドルーティング

**今後実装予定:**
- 宣伝されている全機能の完全実装
- AIエージェント協調機能
- 開発ツールとの統合
- 実際のタスクと会社管理

現時点では本番環境での使用は推奨されません。これは意図されたユーザーエクスペリエンスを示す開発プレビューです。

> ⚠️ **注意**: このプロジェクトは現在活発に開発中です。機能やAPIは頻繁に変更される可能性があります。

## 📋 バージョン管理

このプロジェクトは[Semantic Versioning](https://semver.org/lang/ja/)に従っています。

- **📄 変更履歴**: [CHANGELOG.md](CHANGELOG.md) - 全てのバージョンの変更履歴
- **🏷️ 最新バージョン**: 0.4.0
- **📦 PyPI**: [haconiwa](https://pypi.org/project/haconiwa/)
- **🔖 GitHubリリース**: [Releases](https://github.com/dai-motoki/haconiwa/releases)

## 🔧 最近の更新 (2025-06-13)

**タスクブランチの修正**: YAMLで指定された`defaultBranch`ではなく`main`ブランチからタスクブランチが作成される問題を修正しました。YAML設定で`defaultBranch: "dev"`を指定すると、すべてのタスクワークツリーが正しく`dev`ブランチから作成されるようになりました。

- ✅ Task CRDが関連するSpace CRDから`defaultBranch`を適切に継承
- ✅ 既存の誤ったブランチを自動的に検出し、正しいブランチから再作成
- ✅ ハードコードされた`main`ブランチへのすべての参照を設定可能なデフォルトに置き換え

## 🛠️ 事前準備

**必要な環境のセットアップ**

```bash
# 1. tmuxのインストール
# macOS
brew install tmux

# Ubuntu/Debian
sudo apt-get install tmux

# 2. Python環境のセットアップ（3.8以上）
python --version  # バージョン確認

# 3. pipのアップグレード
pip install --upgrade pip

# 4. Claude Codeのセットアップ
# 詳細な手順はこちらを参照: https://docs.anthropic.com/en/docs/claude-code/getting-started
# 環境変数の設定（必要に応じて）
export ANTHROPIC_API_KEY="your-api-key"

# 5. Haconiwaのインストール
pip install haconiwa --upgrade
```

## 📚 基本的なワークフロー

**1. YAMLファイルの取得とプロジェクト立ち上げ**

```bash
# YAMLファイルダウンロード（GitHubから直接取得）
wget https://raw.githubusercontent.com/dai-motoki/haconiwa/main/haconiwa-dev-company.yaml

# または curlでダウンロード
curl -O https://raw.githubusercontent.com/dai-motoki/haconiwa/main/haconiwa-dev-company.yaml

# YAML適用（デフォルトで自動的にtmuxセッションにアタッチ）
haconiwa apply -f haconiwa-dev-company.yaml
# tmuxセッションから離脱: Ctrl+b, d

# または、アタッチしない場合
haconiwa apply -f haconiwa-dev-company.yaml --no-attach

# アタッチしなかった場合は、明示的にアタッチ
haconiwa space attach -c haconiwa-dev-company
```

**2. プロジェクトの操作**

```bash
# tmuxセッションから離脱: Ctrl+b, d

# 別のターミナルでリアルタイム監視
haconiwa monitor -c haconiwa-dev-company --japanese

# プロジェクト一覧を確認
haconiwa space list

# プロジェクトに再接続
haconiwa space attach -c haconiwa-dev-company
```

**3. プロジェクトの削除**

```bash
# スペースとディレクトリを完全削除
haconiwa space delete -c haconiwa-dev-company --clean-dirs --force
```

## 📝 YAML文法詳細解説

Haconiwaの宣言型YAML設定は、複数のCRD (Custom Resource Definition) をマルチドキュメント形式で記述します。

### 1. Organization CRD（組織定義）

```yaml
apiVersion: haconiwa.dev/v1
kind: Organization
metadata:
  name: haconiwa-dev-company-org  # 組織の一意識別子
spec:
  companyName: "Haconiwa Development Company"  # 会社名
  industry: "AI Development Tools & Infrastructure"  # 業界
  basePath: "./haconiwa-dev-company"  # 組織のベースパス
  hierarchy:
    departments:  # 部門定義
    - id: "executive"  # 部門ID（ルーム割り当てに使用）
      name: "Executive Team"
      description: "Company leadership and strategic decision making"
      roles:  # 役割定義
      - roleType: "management"  # 管理職
        title: "Chief Executive Officer"
        agentId: "ceo-motoki"  # エージェントID
        responsibilities:
          - "Strategic vision and direction"
          - "Company-wide decision making"
      - roleType: "engineering"  # エンジニア
        title: "Senior AI Engineer"
        agentId: "ai-lead-nakamura"
        responsibilities:
          - "AI/ML model development"
          - "Algorithm optimization"
```

**Organization CRDの主要要素:**
- `metadata.name`: 組織の一意識別子（Space CRDから参照される）
- `spec.hierarchy.departments`: 部門の定義（各部門がtmuxのルームに対応）
- `spec.hierarchy.departments[].roles`: 各部門の役割定義（4つの役割で16ペインを構成）

### 2. Space CRD（空間定義）

```yaml
apiVersion: haconiwa.dev/v1
kind: Space
metadata:
  name: haconiwa-dev-world  # スペースの一意識別子
spec:
  nations:  # 国レベル（最上位階層）
  - id: jp
    name: Japan
    cities:  # 市レベル
    - id: tokyo
      name: Tokyo
      villages:  # 村レベル
      - id: haconiwa-village
        name: "Haconiwa Village"
        companies:  # 会社レベル（tmuxセッション）
        - name: haconiwa-dev-company  # セッション名
          grid: "8x4"  # グリッドサイズ（8列×4行=32ペイン）
          basePath: "./haconiwa-dev-world"
          organizationRef: "haconiwa-dev-company-org"  # 組織参照
          gitRepo:  # Gitリポジトリ設定
            url: "https://github.com/dai-motoki/haconiwa"
            defaultBranch: "dev"  # タスクブランチの基となるブランチ
            auth: "https"
          agentDefaults:  # エージェントのデフォルト設定（開発予定）
            type: "claude-code"
            permissions:  # 権限設定（開発予定機能）
              allow:
                - "Bash(python -m pytest)"
                - "Bash(python -m ruff)"
                - "Bash(python -m mypy)"
                - "Read(src/**/*.py)"
                - "Write(src/**/*.py)"
              deny:
                - "Bash(rm -rf /)"
          buildings:  # 建物レベル
          - id: "hq-tower"
            name: "Haconiwa HQ Tower"
            floors:  # 階層レベル
            - id: "executive-floor"
              name: "Executive Floor"
              rooms:  # 部屋レベル（tmuxウィンドウ）
              - id: room-executive  # Executive用ウィンドウ
                name: "Executive Room"
                description: "C-level executives and senior leadership"
              - id: room-standby  # Standby用ウィンドウ
                name: "Standby Room"
                description: "Ready-to-deploy talent pool"
```

**Space CRDの階層構造:**
- `nations` > `cities` > `villages` > `companies` > `buildings` > `floors` > `rooms`
- 各階層に法的フレームワーク（law/）を配置可能
- `companies`がtmuxセッションに対応
- `rooms`がtmuxウィンドウに対応

**gitRepo設定の詳細解説:**
- `url`: クローンするGitリポジトリのURL
- `defaultBranch`: タスクブランチを作成する際の基準となるブランチ
  - 例: `defaultBranch: "dev"` の場合、すべてのタスクブランチは`dev`ブランチから作成される
  - これにより、`main`ブランチを保護しながら、開発ブランチからフィーチャーブランチを派生させることが可能
- `auth`: 認証方式（"https" または "ssh"）

**重要**: `defaultBranch`の設定により、Task CRDで`worktree: true`が指定されたタスクは、このブランチから新しいブランチとworktreeが作成されます。Git worktreeを使用することで、各タスクは独立したディレクトリに隔離され、以下のメリットがあります：
- 各タスクが専用のワーキングディレクトリを持つため、並行開発が可能
- ブランチの切り替えなしに複数のタスクを同時進行できる
- 各エージェントが他のタスクの作業に影響を与えることなく開発可能
- 例: `task_ai_strategy_01`は`./haconiwa-dev-world/tasks/task_ai_strategy_01/`に独立した作業環境として作成される

**agentDefaults.permissions（開発予定機能）:**
- エージェントが実行できるコマンドや操作を制限する機能
- `allow`: 許可されるコマンドパターン
- `deny`: 禁止されるコマンドパターン
- 現在は設定値として記述可能だが、実際の権限制御は未実装

### 3. Task CRD（タスク定義）

```yaml
apiVersion: haconiwa.dev/v1
kind: Task
metadata:
  name: task_ai_strategy_01  # タスクの一意識別子
spec:
  taskId: task_ai_strategy_01  # タスクID
  title: "AI Strategy Development"  # タスクタイトル
  description: |  # マークダウン形式の詳細説明
    ## AI Strategy Development
    
    Develop comprehensive AI strategy for Haconiwa platform.
    
    ### Requirements:
    - Market analysis
    - Technology roadmap
    - Competitive analysis
    - Investment planning
  assignee: "ceo-motoki"  # 割り当て先エージェントID
  spaceRef: "haconiwa-dev-company"  # 所属スペース
  priority: "high"  # 優先度（high/medium/low）
  worktree: true  # Git worktreeを作成するか
  branch: "strategy/ai-roadmap"  # ブランチ名
```

**Task CRDの主要要素:**
- `assignee`: Organization CRDで定義したエージェントIDを指定
- `spaceRef`: 所属するcompany名を指定
- `worktree`: trueの場合、defaultBranchからブランチを作成
- `branch`: 作成するブランチ名

### 4. マルチドキュメント構成

```yaml
# 組織定義
---
apiVersion: haconiwa.dev/v1
kind: Organization
metadata:
  name: my-org
spec:
  # ...

---
# スペース定義
apiVersion: haconiwa.dev/v1
kind: Space
metadata:
  name: my-space
spec:
  # ...

---
# タスク定義（複数可）
apiVersion: haconiwa.dev/v1
kind: Task
metadata:
  name: task-1
spec:
  # ...
```

**YAMLファイル構成のベストプラクティス:**
1. 組織定義を最初に配置
2. スペース定義を次に配置
3. タスク定義を最後に配置（ルームごとにグループ化推奨）
4. `---`で各ドキュメントを区切る

### 5. 実行時の処理フロー

1. **YAMLパース**: マルチドキュメントを個別のCRDオブジェクトに分解
2. **組織作成**: Organization CRDから部門・役割構造を構築
3. **スペース作成**: Space CRDからtmuxセッション・ウィンドウ構造を構築
4. **タスク作成**: Task CRDからGit worktreeとタスク割り当てを作成
   - `defaultBranch`から各タスクのブランチを作成
   - エージェントをタスクディレクトリに配置
5. **Claude実行**: 各ペインで`cd {path} && claude`を自動実行

### 6. Law CRD（法的フレームワーク定義）- 開発予定

```yaml
apiVersion: haconiwa.dev/v1
kind: Law
metadata:
  name: haconiwa-legal-framework
spec:
  globalRules:  # グローバル規則
    - name: "security-policy"
      description: "全エージェントのセキュリティポリシー"
      content: |
        ## セキュリティポリシー
        - 機密情報の取り扱い規定
        - アクセス権限の管理
        - データ保護方針
    - name: "code-standards"
      description: "コーディング規約"
      content: |
        ## コーディング標準
        - PEP 8準拠（Python）
        - ESLint設定（JavaScript）
        - 型安全性の確保
  
  hierarchicalRules:  # 階層別規則
    nation:
      enabled: true
      rules:
        - "国レベルの法的要件"
        - "データ主権に関する規定"
    city:
      enabled: true
      rules:
        - "地域のコンプライアンス要件"
        - "業界標準への準拠"
    company:
      enabled: true
      rules:
        - "組織のガバナンスポリシー"
        - "内部統制規定"
  
  permissions:  # 権限管理
    defaultPolicy: "deny"  # デフォルトは拒否
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
  
  systemPrompts:  # エージェント用システムプロンプト
    base: |
      あなたはHaconiwa開発会社のAIエージェントです。
      以下の規則とポリシーに従って行動してください。
    roleSpecific:
      ceo: "戦略的意思決定と会社全体の方向性に焦点を当ててください。"
      engineer: "コード品質とベストプラクティスを重視してください。"
      security: "セキュリティとコンプライアンスを最優先に考えてください。"
```

**Law CRDの主要要素（開発予定）:**
- `globalRules`: 全階層に適用されるグローバル規則
- `hierarchicalRules`: 階層別（nation/city/company等）の規則定義
- `permissions`: リソースへのアクセス権限管理
- `systemPrompts`: 役割別のエージェント行動指針

**統合予定の機能:**
- Organization/Space CRDからの自動参照
- 階層的な規則の継承メカニズム
- 実行時の権限チェック機能
- エージェントへの自動プロンプト注入

## 🚀 今すぐ使える機能

### apply yamlパターン（v1.0 新機能）

宣言型YAMLファイルでのマルチルーム・マルチエージェント環境管理が**今すぐ**利用できます：

```bash
# 1. インストール
pip install haconiwa --upgrade

# 2. YAMLファイルダウンロード（GitHubから直接取得）
wget https://raw.githubusercontent.com/dai-motoki/haconiwa/main/test-multiroom-with-tasks.yaml

# または curlでダウンロード
curl -O https://raw.githubusercontent.com/dai-motoki/haconiwa/main/test-multiroom-with-tasks.yaml

# ファイル内容確認
cat test-multiroom-with-tasks.yaml

# 3. YAML適用でマルチルーム環境作成（デフォルトで自動アタッチ）
haconiwa apply -f test-multiroom-with-tasks.yaml

# 3b. 自動アタッチなしで適用
haconiwa apply -f test-multiroom-with-tasks.yaml --no-attach

# 4. スペース一覧確認
haconiwa space list

# 5. スペース一覧確認（短縮形）
haconiwa space ls

# 6. 特定ルームに接続（自動アタッチしなかった場合）
haconiwa space attach -c test-company-multiroom-tasks -r room-frontend

# 7. 全ペインでclaudeコマンド実行
haconiwa space run -c test-company-multiroom-tasks --claude-code

# 8. 特定ルームでカスタムコマンド実行
haconiwa space run -c test-company-multiroom-tasks --cmd "echo hello" -r room-backend

# 9. ドライランでコマンド確認
haconiwa space run -c test-company-multiroom-tasks --claude-code --dry-run

# 10. セッション停止
haconiwa space stop -c test-company-multiroom-tasks

# 11. 完全削除（ディレクトリも削除）
haconiwa space delete -c test-company-multiroom-tasks --clean-dirs --force

# 12. 完全削除（ディレクトリは保持）
haconiwa space delete -c test-company-multiroom-tasks --force
```

**📁 自動作成されるマルチルーム構造（階層的法的フレームワーク）:**
```
./test-multiroom-desks/
├── jp/                                  # 国レベル (Nation Level)
│   ├── law/                            # 国家法ディレクトリ
│   │   ├── global-rules.md            # グローバル規則
│   │   ├── system-prompts/            # システムプロンプト
│   │   │   └── nation-agent-prompt.md
│   │   └── permissions/               # 権限管理
│   │       ├── code-permissions.yaml
│   │       └── file-permissions.yaml
│   └── tokyo/                         # 市レベル (City Level)
│       ├── law/                       # 市法ディレクトリ
│       │   ├── regional-rules.md     # 地域規則
│       │   ├── system-prompts/       # システムプロンプト
│       │   │   └── city-agent-prompt.md
│       │   └── permissions/          # 権限管理
│       │       ├── code-permissions.yaml
│       │       └── file-permissions.yaml
│       └── test-village/              # 村レベル (Village Level)
│           ├── law/                   # 村法ディレクトリ
│           │   ├── local-rules.md    # ローカル規則
│           │   ├── system-prompts/   # システムプロンプト
│           │   │   └── village-agent-prompt.md
│           │   └── permissions/      # 権限管理
│           │       ├── code-permissions.yaml
│           │       └── file-permissions.yaml
│           └── test-multiroom-company/    # 会社レベル (Company Level)
│               ├── law/               # 会社法ディレクトリ
│               │   ├── project-rules.md  # プロジェクト規則
│               │   ├── system-prompts/   # システムプロンプト
│               │   │   └── company-agent-prompt.md
│               │   └── permissions/      # 権限管理
│               │       ├── code-permissions.yaml
│               │       └── file-permissions.yaml
│               └── headquarters/      # 建物レベル (Building Level)
│                   ├── law/           # 建物法ディレクトリ
│                   │   ├── building-rules.md # 建物規則
│                   │   ├── system-prompts/   # システムプロンプト
│                   │   │   └── building-agent-prompt.md
│                   │   └── permissions/      # 権限管理
│                   │       ├── code-permissions.yaml
│                   │       └── file-permissions.yaml
│                   └── floor-1/       # 階層レベル (Floor Level)
│                       ├── law/       # 階層法ディレクトリ
│                       │   ├── floor-rules.md    # 階層規則
│                       │   ├── system-prompts/   # システムプロンプト
│                       │   │   └── floor-agent-prompt.md
│                       │   └── permissions/      # 権限管理
│                       │       ├── code-permissions.yaml
│                       │       └── file-permissions.yaml
│                       ├── room-01/   # 部屋レベル (Room Level)
│                       │   ├── law/   # 部屋法ディレクトリ
│                       │   │   ├── team-rules.md     # チーム規則
│                       │   │   ├── system-prompts/   # システムプロンプト
│                       │   │   │   └── room-agent-prompt.md
│                       │   │   └── permissions/      # 権限管理
│                       │   │       ├── code-permissions.yaml
│                       │   │       └── file-permissions.yaml
│                       │   └── desks/         # デスクレベル (Desk Level)
│                       │       ├── law/       # デスク法ディレクトリ
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
│                       └── room-02/   # 部屋レベル (Room Level)
│                           ├── law/   # 部屋法ディレクトリ (同様の構成)
│                           └── desks/ # デスクレベル (同様の構成)
├── standby/                # 待機中エージェント（26 agents）
│   └── README.md          # 自動生成説明ファイル
└── tasks/                  # タスク割り当て済みエージェント（6 agents）
    ├── main/              # メインGitリポジトリ
    ├── 20250609061748_frontend-ui-design_01/     # タスク1
    ├── 20250609061749_backend-api-development_02/ # タスク2
    ├── 20250609061750_database-schema-design_03/  # タスク3
    ├── 20250609061751_devops-ci-cd-pipeline_04/   # タスク4
    ├── 20250609061752_user-authentication_05/     # タスク5
    └── 20250609061753_performance-optimization_06/ # タスク6
```

**🏢 tmux構造（マルチルーム）:**
```
test-multiroom-company (Session)
├── Window 0: Alpha Room (16ペイン)
│   ├── org-01 (4ペイン): pm, worker-a, worker-b, worker-c
│   ├── org-02 (4ペイン): pm, worker-a, worker-b, worker-c  
│   ├── org-03 (4ペイン): pm, worker-a, worker-b, worker-c
│   └── org-04 (4ペイン): pm, worker-a, worker-b, worker-c
└── Window 1: Beta Room (16ペイン)
    ├── org-01 (4ペイン): pm, worker-a, worker-b, worker-c
    ├── org-02 (4ペイン): pm, worker-a, worker-b, worker-c
    ├── org-03 (4ペイン): pm, worker-a, worker-b, worker-c
    └── org-04 (4ペイン): pm, worker-a, worker-b, worker-c
```

**✅ YAML適用パターンの実際の機能:**
- 🏢 **宣言型管理**: YAMLファイルによる環境定義
- 🤖 **マルチルーム対応**: Room単位のWindow分離（Frontend/Backend）
- 🔄 **自動ルーム分散**: ルーム別Windowでのペイン配置
- 🚀 **一括コマンド実行**: 全ペインまたはルーム別実行
- 🎯 **柔軟なターゲティング**: ルーム指定コマンド実行
- 🏛️ **階層管理**: Nation > City > Village > Company
- 📄 **外部設定**: YAML設定ファイルでの完全管理
- 🗑️ **柔軟なクリーンアップ**: ディレクトリ保持・削除の選択
- 📊 **32ペイン管理**: 2ルーム × 16ペイン構成
- 🔧 **ドライラン対応**: 実行前のコマンド確認
- 🎯 **タスク割り当てシステム**: エージェント自動ディレクトリ移動
### tmux マルチエージェント環境（従来方式）

4x4グリッドのマルチエージェント開発環境を**今すぐ**作成・管理できます：

```bash
# 1. インストール
pip install haconiwa --upgrade


# 2-1. 直接Tmuxでアタッチする場合はこちらを実行してください（4組織 × 4役割 = 16ペイン）。
haconiwa company build --name my-company \
  --org01-name "フロントエンド開発部" --task01 "UI設計" \
  --org02-name "バックエンド開発部" --task02 "API開発" \
  --org03-name "データベース部門" --task03 "スキーマ設計" \
  --org04-name "DevOps部門" --task04 "インフラ構築"

# 2. マルチエージェント環境作成（4組織 × 4役割 = 16ペイン）
haconiwa company build --name my-company \
  --org01-name "フロントエンド開発部" --task01 "UI設計" \
  --org02-name "バックエンド開発部" --task02 "API開発" \
  --org03-name "データベース部門" --task03 "スキーマ設計" \
  --org04-name "DevOps部門" --task04 "インフラ構築" --no-attach

# 3. 会社一覧確認
haconiwa company list

# 4. 既存の会社に接続
haconiwa company attach my-company

# 5. 会社設定更新（既存会社の組織名変更）
haconiwa company build --name my-company \
  --org01-name "新フロントエンド部" --task01 "React開発"

# 6. 会社を完全に再構築（--rebuildオプション）
haconiwa company build --name my-company \
  --org01-name "リニューアル開発部" \
  --rebuild

# 7. 会社終了（ディレクトリも削除）
haconiwa company kill my-company --clean-dirs --force

# 8. 会社終了（ディレクトリは保持）
haconiwa company kill my-company --force
```

**📁 自動作成されるディレクトリ構造:**
```
/path/to/desks/
├── org-01/
│   ├── 01boss/          # PM用デスク
│   ├── 01worker-a/      # Worker-A用デスク
│   ├── 01worker-b/      # Worker-B用デスク
│   └── 01worker-c/      # Worker-C用デスク
├── org-02/
│   ├── 02boss/
│   ├── 02worker-a/
│   ├── 02worker-b/
│   └── 02worker-c/
├── org-03/ (同様の構造)
└── org-04/ (同様の構造)
```

**✅ 実際に動作する機能:**
- 🏢 **統合buildコマンド**: 新規作成・更新・再構築を一つのコマンドで実現
- 🤖 **自動存在チェック**: 会社の存在を自動判定し適切な動作を選択
- 🔄 **シームレス更新**: 既存会社の設定変更を安全に実行
- 🔨 **強制再構築**: --rebuildオプションで完全な再作成
- 🏗️ **自動ディレクトリ構成**: 組織・役割別デスク自動作成
- 🏷️ **カスタム組織名・タスク名**: 動的なタイトル設定
- 🗑️ **柔軟なクリーンアップ**: ディレクトリ保持・削除の選択可能
- 🏛️ **会社管理**: 作成・一覧・接続・削除の完全サポート
- 📄 **README自動生成**: 各デスクにREADME.md自動作成
- 📊 **4x4マルチエージェント**: 組織的tmuxレイアウト（16ペイン）

### 📊 リアルタイムモニタリング機能 ✅ **テスト済み**

作成したtmuxマルチエージェント環境を**リアルタイムで監視**できます：

```bash
# 1. 基本的なモニタリング（全window表示）
haconiwa monitor -c test-company-multiroom-tasks

# 2. 短縮形エイリアス
haconiwa mon -c my-company

# 3. 日本語UI表示
haconiwa monitor -c my-company --japanese

# 4. 特定のwindow（部屋）のみ監視
haconiwa monitor -c test-company-multiroom-tasks -w 0          # Frontend部屋のみ
haconiwa monitor -c test-company-multiroom-tasks -w Backend   # Backend部屋のみ

# 5. 表示列をカスタマイズ（推奨設定）
haconiwa monitor -c my-company --columns room pane title claude agent cpu status --japanese

# 6. 高頻度更新（パフォーマンス調整）
haconiwa monitor -c my-company -r 0.5 --japanese  # 0.5秒間隔更新

# 7. 低頻度更新（CPUリソース節約）
haconiwa monitor -c my-company -r 5 --japanese    # 5秒間隔更新

# 8. ミニマル表示（最小限の情報）
haconiwa monitor -c my-company --columns pane agent status --japanese
```

**🖥️ リアルタイム表示内容:**
```
💼  会社名: test-company-multiroom-tasks

        アクティブペイン: 22/32
        平均稼働率: 0.8%
        合計メモリ: 551.3MB
        最終更新: 11:15:42

🏢  部屋: Frontend
┏━━━━━━━━┳━━━━━━━━━━━━━━━━━┳━━━━━━━━━━━━━━━━━┳━━━━━━━━━━━━━━━━━━━━━┳━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━┳━━━━━━━━━━━━━┓
┃ ペイン ┃ タスク          ┃ プロバイダAI   ┃ エージェント名      ┃ 稼働率                                                               ┃ ステータス  ┃
┡━━━━━━━━╇━━━━━━━━━━━━━━━━━╇━━━━━━━━━━━━━━━━━╇━━━━━━━━━━━━━━━━━━━━━╇━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━╇━━━━━━━━━━━━━┩
│ 0      │ Greeting        │ ✓ Claude       │ lead-pm-01          │   0.1% ░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░                 │  仕事待ち   │
│ 1      │ Greeting Start  │ ✓ Claude       │ motoki              │   0.2% ░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░                 │  仕事待ち   │
│ 2      │ Greeting        │ ✓ Claude       │ ai-dev-7523         │   0.1% ░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░                 │  仕事待ち   │
└────────┴─────────────────┴─────────────────┴─────────────────────┴──────────────────────────────────────────────────────────────────────┴─────────────┘

🏢  部屋: Backend  
┏━━━━━━━━┳━━━━━━━━━━━━━━━━━┳━━━━━━━━━━━━━━━━━┳━━━━━━━━━━━━━━━━━━━━━┳━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━┳━━━━━━━━━━━━━┓
┃ ペイン ┃ タスク          ┃ プロバイダAI   ┃ エージェント名      ┃ 稼働率                                                               ┃ ステータス  ┃
┡━━━━━━━━╇━━━━━━━━━━━━━━━━━╇━━━━━━━━━━━━━━━━━╇━━━━━━━━━━━━━━━━━━━━━╇━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━╇━━━━━━━━━━━━━┩
│ 0      │ Backend Task    │ ✗ Claude無し   │ lead-pm-01          │ N/A                                                                  │ プロセス無し │
│ 1      │ API Development │ ✓ Claude       │ motoki              │   2.3% ██░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░                 │  作業中     │
└────────┴─────────────────┴─────────────────┴─────────────────────┴──────────────────────────────────────────────────────────────────────┴─────────────┘
```

**✅ 実装・テスト済み機能:**
- 🔍 **リアルタイム監視**: 2秒間隔でのライブ更新
- 🏢 **複数window対応**: Frontend/Backend等の部屋別表示
- 👥 **カスタムエージェントID表示**: 個人名やカスタムIDの完全サポート
- 🎨 **視覚的CPU稼働率バー**: カラフルなプログレスバー表示
- 🇯🇵 **完全日本語UI**: 列名・ステータス・メッセージの日本語化
- 📊 **柔軟な列選択**: 必要な情報のみ表示可能
- 🎯 **window指定監視**: 特定の部屋のみに絞り込み可能
- 🚀 **高性能監視**: psutil + Rich による高速リアルタイム更新
- 📈 **智能ステータス判定**: CPU使用率に基づく自動ステータス判定
- 💼 **会社概要サマリー**: アクティブペイン数・平均CPU・合計メモリ
- 🎮 **短縮形エイリアス**: `mon` でクイックアクセス
- ⚡ **依存関係チェック**: 必要パッケージの自動確認

**📊 利用可能な表示列:**
- `room` - 部屋/Window名（Frontend/Backend等）
- `window` - Window番号
- `pane` - ペイン番号
- `title` - タスクタイトル
- `parent` - 親プロセスID
- `claude` - プロバイダAI状態（✓/✗）
- `agent` - カスタムエージェントID
- `cpu` - CPU使用率（視覚的バー付き）
- `memory` - メモリ使用量
- `uptime` - プロセス稼働時間
- `status` - エージェントステータス（仕事待ち/作業中/多忙）

**🎯 状態判定ルール:**
- **仕事待ち** (≤2.0% CPU): 待機状態、新しいタスク受付可能
- **作業中** (2.0-20% CPU): アクティブに作業中
- **多忙** (>20% CPU): 高負荷作業中、割り込み注意

**💡 使用例・Tips:**
```bash
# 開発作業中の推奨監視設定
haconiwa monitor -c my-company --columns room pane agent cpu status --japanese -r 1

# 詳細デバッグ時
haconiwa monitor -c my-company --columns room pane title claude agent cpu memory status --japanese

# 軽量監視（リソース節約）
haconiwa monitor -c my-company --columns pane agent status --japanese -r 10

# Frontend部屋の集中監視
haconiwa monitor -c my-company -w 0 --japanese
```

**🔧 必要な依存関係:**
- `rich` - リッチなターミナルUI表示
- `psutil` - プロセス情報取得
- `tmux` - セッション管理

monitor機能は**実際にテスト済み**で、32ペインの大規模マルチエージェント環境でも安定動作を確認しています。

## 📚 buildコマンド詳細ガイド

### 基本的な使い方

#### 1. 新規会社作成（最小構成）
```bash
# シンプルな会社作成（デフォルト設定）
haconiwa company build --name my-company

# カスタムベースパス指定
haconiwa company build --name my-company --base-path ./workspace
```

#### 2. 完全カスタム会社作成
```bash
haconiwa company build --name my-company \
  --base-path ./workspace \
  --org01-name "フロントエンド部" --task01 "UI/UX開発" \
  --org02-name "バックエンド部" --task02 "API設計" \
  --org03-name "インフラ部" --task03 "DevOps" \
  --org04-name "QA部" --task04 "品質保証" \
  --no-attach  # 作成後に自動接続しない
```

#### 3. 既存会社の更新
```bash
# 組織名のみ変更（自動検出で更新モード）
haconiwa company build --name my-company \
  --org01-name "新フロントエンド部"

# 複数の設定を同時更新
haconiwa company build --name my-company \
  --org01-name "React開発チーム" --task01 "SPAアプリ開発" \
  --org02-name "Node.js開発チーム" --task02 "RESTful API"
```

#### 4. 強制再構築
```bash
# 既存会社を完全に再作成
haconiwa company build --name my-company \
  --base-path ./workspace \
  --org01-name "リニューアル開発部" \
  --rebuild
```

### 高度な使い方

#### デスクのカスタマイズ
```bash
# 各組織のワークスペース（デスク）を指定
haconiwa company build --name my-company \
  --desk01 "react-frontend-desk" \
  --desk02 "nodejs-backend-desk" \
  --desk03 "docker-infra-desk" \
  --desk04 "testing-qa-desk"
```

#### クリーンアップオプション
```bash
# 会社終了（tmuxセッションのみ削除、ディレクトリ保持）
haconiwa company kill my-company --force

# 完全削除（ディレクトリも削除）
haconiwa company kill my-company \
  --clean-dirs \
  --base-path ./workspace \
  --force
```

### 動作モード自動判定

buildコマンドは会社の存在状況を自動判定し、適切な動作を選択します：

| 状況 | 動作 | メッセージ例 |
|------|------|-------------|
| 会社が存在しない | **新規作成** | 🏗️ Building new company: 'my-company' |
| 会社が存在する + 設定変更あり | **更新** | 🔄 Updating existing company: 'my-company' |
| 会社が存在する + 設定変更なし | **情報表示** | ℹ️ No changes specified for company 'my-company' |
| --rebuildオプション指定 | **強制再構築** | 🔄 Rebuilding company: 'my-company' |

### トラブルシューティング

#### よくある問題と解決方法

**問題**: 会社が応答しない場合
```bash
# 1. 会社の状態確認
haconiwa company list

# 2. 強制終了
haconiwa company kill my-company --force

# 3. 再作成
haconiwa company build --name my-company --rebuild
```

**問題**: ディレクトリの権限エラー
```bash
# ベースパスの権限確認と修正
chmod 755 ./workspace
haconiwa company build --name my-company --base-path ./workspace
```

**問題**: tmuxセッションが残っている
```bash
# 手動でtmuxセッション確認
tmux list-sessions

# 手動削除
tmux kill-session -t my-company
```

## ✨ 主な機能 (開発中)

- 🤖 **AIエージェント管理**: Boss/Workerエージェントの作成・監視
- 📦 **ワールド管理**: 開発環境の構築・管理
- 🖥️ **tmux会社連携**: 開発スペースの効率的な管理
- 📋 **タスク管理**: git-worktreeと連携したタスク管理システム
- 📊 **リソース管理**: DBやファイルパスの効率的なスキャン
- 👁️ **リアルタイム監視**: エージェントやタスクの進捗監視
- 🛠️ **開発ツール連携**: Claude Code SDK等を使用した並列開発支援（開発中）

## 🏗️ アーキテクチャ概念

### CRDベースのアーキテクチャ

Haconiwaは4つの主要なCRD（Custom Resource Definition）を中心に構築されています：

```
Haconiwa CRDアーキテクチャ
├── Organization CRD（組織定義）
│   ├── 部門構造（departments）
│   ├── 役割定義（roles）
│   └── 責任範囲（responsibilities）
├── Space CRD（空間定義）
│   ├── 階層構造（nations > cities > villages > companies > buildings > floors > rooms）
│   ├── Gitリポジトリ設定（gitRepo）
│   └── tmuxセッション/ウィンドウマッピング
├── Task CRD（タスク定義）
│   ├── タスク詳細（title, description）
│   ├── エージェント割り当て（assignee）
│   └── Git worktree設定（branch, worktree）
└── Law CRD（法的フレームワーク）- 開発予定
    ├── グローバル規則（globalRules）
    ├── 階層別規則（hierarchicalRules）
    └── 権限管理（permissions）
```

### CRD間の関係と処理フロー

```
1. Organization CRD
   ↓ 定義
   エージェント構造（部門・役割）
   ↓
2. Space CRD
   ↓ 参照（organizationRef）
   物理的な配置（tmuxセッション・ウィンドウ）
   ↓
3. Task CRD
   ↓ 参照（spaceRef, assignee）
   作業割り当てとGit worktree作成
   ↓
4. Law CRD（開発予定）
   ↓ 統合
   全CRDに対する規則・権限適用
```

### tmux ↔ Haconiwa CRD マッピング

| Haconiwa CRD | tmux概念 | 主な役割 |
|-------------|----------|----------|
| **Organization** | - | エージェントの組織構造定義 |
| **Space (Company)** | **Session** | 開発環境のトップレベルコンテナ |
| **Space (Room)** | **Window** | 機能別の作業グループ |
| **Task + Agent** | **Pane** | 個別のエージェント作業環境 |

### 主要な特徴

**1. 宣言的な環境管理**
- YAMLファイルですべての構成を定義
- 再現可能な開発環境の構築

**2. Git worktreeによるタスク隔離**
- 各タスクが独立したディレクトリで作業
- `defaultBranch`からの自動ブランチ作成
- 並行開発の実現

**3. 階層的な構造**
- Space CRDの階層（国→市→村→会社→建物→階→部屋）
- 将来的にLaw CRDによる階層的な規則継承

**4. 自動化されたエージェント配置**
- Organization CRDで定義されたエージェントの自動配置
- Task CRDによる作業割り当て
- tmuxペインへの自動マッピング

## 🚀 インストール

```bash
pip install haconiwa
```

> 📝 **開発ノート**: パッケージはPyPIで利用可能ですが、多くの機能はまだ開発中です。

## ⚡ クイックスタート

> 🎭 **重要**: 以下に示すコマンドは**デモンストレーション用です**。現在、これらのコマンドはヘルプ情報と基本構造を表示するものですが、実際の機能は開発中です。完全な機能の実装に向けて積極的に取り組んでいます。

### 1. 利用可能なコマンドを確認
```bash
haconiwa --help
```

### 2. プロジェクト初期化
```bash
haconiwa core init
```

### 3. 開発ワールド作成
```bash
haconiwa world create local-dev
```

### 4. AIエージェント起動
```bash
# ボスエージェント作成
haconiwa agent spawn boss

# ワーカーエージェント作成
haconiwa agent spawn worker-a
```

### 5. タスク管理
```bash
# 新しいタスク作成
haconiwa task new feature-login

# エージェントにタスク割り当て
haconiwa task assign feature-login worker-a

# 進捗監視
haconiwa watch tail worker-a
```

## 📖 コマンドリファレンス

> 🔧 **開発ノート**: 以下にリストされているコマンドは現在**デモンストレーションとテスト用途**のものです。CLI構造は機能していますが、ほとんどのコマンドはヘルプ情報やプレースホルダーレスポンスを表示します。各コマンドグループの基盤機能を積極的に開発中です。

CLIツールは7つの主要コマンドグループを提供します：

### `agent` - エージェント管理コマンド
協調開発のためのAIエージェント（Boss/Worker）を管理
- `haconiwa agent spawn <type>` - エージェント作成
- `haconiwa agent ps` - エージェント一覧表示
- `haconiwa agent kill <name>` - エージェント停止

### `core` - コア管理コマンド
システムのコア管理と設定
- `haconiwa core init` - プロジェクトの初期化
- `haconiwa core status` - システム状態確認
- `haconiwa core upgrade` - システムアップグレード

### `resource` - リソース管理
プロジェクトリソース（データベース、ファイルなど）のスキャンと管理
- `haconiwa resource scan` - リソーススキャン
- `haconiwa resource list` - リソース一覧表示

### `tool` - 開発ツール管理
外部ツールやSDKとの統合機能
- `haconiwa tool list` - 利用可能なツール一覧
- `haconiwa tool install <tool>` - ツールのインストール
- `haconiwa tool configure <tool>` - ツールの設定
- `haconiwa tool parallel-dev` - AI並列開発機能（開発中）

### `company` - tmux会社と企業管理
tmuxを使った効率的な開発企業環境管理
- `haconiwa company build <name>` - tmux会社の作成・更新・再構築
- `haconiwa company list` - 会社一覧
- `haconiwa company attach <name>` - 会社接続
- `haconiwa company kill <name>` - 会社終了・削除
- `haconiwa company resize <name>` - 会社レイアウト調整

### `task` - タスク管理コマンド
git-worktreeと連携したタスク管理
- `haconiwa task new <name>` - 新しいタスク作成
- `haconiwa task assign <task> <agent>` - タスク割り当て
- `haconiwa task status` - タスク状態確認

### `watch` - 監視コマンド
エージェントとタスクのリアルタイム監視
- `haconiwa watch tail <target>` - リアルタイム監視
- `haconiwa watch logs` - ログ表示

### `world` - ワールド管理
開発環境とワールドの管理
- `haconiwa world create <n>` - 新しい開発ワールドを作成
- `haconiwa world list` - ワールド一覧表示
- `haconiwa world switch <n>` - ワールド切り替え

### `monitor` - リアルタイム監視コマンド ✅ **テスト済み**
tmuxマルチエージェント環境のリアルタイム監視と可視化
- `haconiwa monitor -c <company>` - 基本監視（全window表示）
- `haconiwa mon -c <company>` - 短縮形エイリアス  
- `haconiwa monitor -c <company> --japanese` - 日本語UI
- `haconiwa monitor -c <company> -w <window>` - 特定window監視
- `haconiwa monitor -c <company> --columns <cols>` - カスタム列表示
- `haconiwa monitor -c <company> -r <interval>` - 更新間隔調整
- `haconiwa monitor help` - 詳細ヘルプ表示

### `tool` - 開発ツール連携コマンド
外部ツールやSDKとの統合機能
- `haconiwa tool list` - 利用可能なツール一覧
- `haconiwa tool install <tool>` - ツールのインストール  
- `haconiwa tool configure <tool>` - ツールの設定
- **`haconiwa tool parallel-dev`** - AI並列開発機能 🚧 **開発中**

#### `tool parallel-dev` - Claude Code SDK並列実行機能
高速並列ファイル編集のためのAI開発支援機能
- `haconiwa tool parallel-dev claude` - Claude Code SDKでの並列編集実行
- `haconiwa tool parallel-dev status` - 実行中タスクの状態確認
- `haconiwa tool parallel-dev cancel <task-id>` - 実行中タスクのキャンセル
- `haconiwa tool parallel-dev history` - 実行履歴表示

**主な機能:**
- 🚀 **高速並列処理**: 最大10ファイルの同時編集
- 📝 **柔軟なプロンプト指定**: ファイルごとに個別のプロンプト
- 🎯 **セマフォ制御**: 同時実行数の制限でAPI負荷を管理
- 📊 **リアルタイム進捗表示**: 処理状況の可視化
- 🔧 **エラーハンドリング**: 個別失敗でも他タスクは継続

**使用例:**
```bash
# 基本的な並列編集（3ファイル）
haconiwa tool parallel-dev claude \
  -f src/main.py,src/utils.py,src/api.py \
  -p "Add type hints","Refactor functions","Add error handling"

# 10ファイルの一斉修正
haconiwa tool parallel-dev claude \
  --file-list files.txt \
  --prompt-file prompts.txt \
  -m 5 \
  -t 120

# YAML設定ファイルから実行
haconiwa tool parallel-dev claude --from-yaml parallel-dev.yaml

# 実行状態の確認
haconiwa tool parallel-dev status
```

## 🛠️ 開発状況

> 🎬 **現在のフェーズ**: **デモンストレーション・プロトタイピング**  
> ほとんどのCLIコマンドは現在、意図された構造とヘルプ情報を示すデモンストレーション用プレースホルダーです。各コマンドの背後にある核となる機能を積極的に開発中です。

### ✅ 完了済み機能
- 7つのコマンドグループを持つ基本CLI構造
- PyPIパッケージ配布とインストール
- コアプロジェクト初期化フレームワーク
- **tmux会社管理システム（company buildコマンド）**
- **マルチエージェント4x4レイアウト自動構築**
- **組織・タスク・デスクカスタマイズ機能**
- **会社の自動存在チェックと更新機能**
- **柔軟なクリーンアップシステム**
- **📊 リアルタイムモニタリングシステム（monitor/mon コマンド）**
- **🏢 複数window対応のマルチエージェント監視**
- **👥 カスタムエージェントID表示機能**
- **🇯🇵 完全日本語UI対応**
- **🎨 視覚的CPU稼働率表示**
- **📈 智能ステータス自動判定機能**
- ヘルプシステムとコマンドドキュメント
- コマンドグループの組織化とルーティング

### 🚧 開発中機能
- AIエージェントの生成と管理 (プレースホルダー → 実装)
- git-worktreeとのタスク管理 (プレースホルダー → 実装)
- リソーススキャン機能 (プレースホルダー → 実装)
- リアルタイム監視システム (プレースホルダー → 実装)
- ワールド/環境管理 (プレースホルダー → 実装)
- **開発ツール連携機能（tool parallel-dev）** (設計 → 実装中)
  - Claude Code SDK統合による並列ファイル編集（最大10ファイル同時）
  - asyncio.gatherによる高速非同期処理
  - 柔軟なプロンプト管理（ファイルごとに個別指定）
  - エラーハンドリングと進捗表示
  - 将来的に他のAIツール（GitHub Copilot、ChatGPT等）も統合予定

### 📋 計画中機能
- 高度なAIエージェント協調
- 人気の開発ツールとの統合
- 拡張性のためのプラグインシステム
- Webベース監視ダッシュボード

## 🛠️ 開発環境セットアップ

```bash
git clone https://github.com/dai-motoki/haconiwa.git
cd haconiwa
python -m venv venv
source venv/bin/activate  # Windows: venv\Scripts\activate
pip install -e .[dev]
```

### テスト実行

```bash
pytest tests/
```

## 📝 ライセンス

MIT License - 詳細は [LICENSE](LICENSE) ファイルをご覧ください。

## 🤝 コントリビューション

プロジェクトへの貢献を歓迎します！これは活発な開発プロジェクトのため、以下をお勧めします：

1. 既存のissueとディスカッションを確認
2. このリポジトリをフォーク
3. 機能ブランチを作成 (`git checkout -b feature/amazing-feature`)
4. 変更をコミット (`git commit -m 'Add amazing feature'`)
5. ブランチにプッシュ (`git push origin feature/amazing-feature`)
6. プルリクエストを作成

## 📞 サポート

- GitHub Issues: [Issues](https://github.com/dai-motoki/haconiwa/issues)
- メール: kanri@kandaquantum.co.jp


---

**箱庭 (Haconiwa)** - AI協調開発の未来 🚧 