# apply コマンド - 環境変数管理

## 概要

`haconiwa apply` コマンドに追加された `--env` フラグにより、Git worktreeを使用する各タスクに環境変数ファイル（.env）を自動配布する機能が実装されました。

## 機能詳細

### 基本的な使用方法

```bash
# .envファイルを指定してapply
haconiwa apply -f haconiwa-dev-company.yaml --env .env

# 複数の.envファイルを指定（マージされる）
haconiwa apply -f haconiwa-dev-company.yaml --env .env.base --env .env.local

# 環境別の.envファイル
haconiwa apply -f haconiwa-dev-company.yaml --env .env.production
```

### 環境変数ファイルの例

#### .env.base - 基本設定
```bash
COMPANY_NAME="Haconiwa Development Company"
API_ENDPOINT="https://api.haconiwa.dev"
LOG_LEVEL="INFO"
TIMEZONE="Asia/Tokyo"
LOCALE="ja_JP.UTF-8"
```

#### .env.local - ローカル開発用（.gitignoreに追加推奨）
```bash
ANTHROPIC_API_KEY="sk-ant-api03-..."
CLAUDE_MODEL="claude-3-opus-20240229"
DEBUG_MODE="true"
DATABASE_URL="postgresql://user:pass@localhost:5432/haconiwa_dev"
REDIS_URL="redis://localhost:6379"
```

## 実装詳細

### 自動コピーの動作フロー

```
1. haconiwa apply実行時に--envフラグを確認
    ↓
2. 指定された.envファイルを読み込み
    ↓
3. 複数ファイルの場合はマージ（後のファイルが優先）
    ↓
4. git worktree作成時に各タスクディレクトリに.envをコピー
    ↓
5. 各エージェントは自分のディレクトリの.envを使用
```

### ファイル配置の結果

```
./haconiwa-dev-world/
└── tasks/
    ├── task_backend_optimization_06/
    │   ├── .env               # 自動コピーされた環境変数ファイル
    │   ├── src/
    │   └── ...
    ├── task_ai_strategy_01/
    │   ├── .env               # 同じ内容がコピーされる
    │   ├── docs/
    │   └── ...
    └── task_frontend_ui_02/
        ├── .env               # 同じ内容がコピーされる
        ├── components/
        └── ...
```

## Space CRDでの環境変数ファイル指定（オプション）

YAMLファイル内でも環境変数ファイルを指定可能：

```yaml
apiVersion: haconiwa.dev/v1
kind: Space
metadata:
  name: haconiwa-dev-world
spec:
  nations:
    - id: jp
      cities:
        - id: tokyo
          villages:
            - id: haconiwa-village
              companies:
                - name: haconiwa-dev-company
                  # 環境変数ファイルの指定（オプション）
                  envFiles:
                    - path: ".env.base"        # 基本設定
                    - path: ".env.production"  # 本番環境設定
                    - path: ".env.secrets"     # シークレット（gitignore推奨）
                  gitRepo:
                    url: "https://github.com/dai-motoki/haconiwa"
                    defaultBranch: "main"
```

## セキュリティ考慮事項

### .gitignoreの推奨設定
```gitignore
# 環境変数ファイル
.env
.env.local
.env.*.local
.env.secrets

# 本番環境の設定は特に注意
.env.production
.env.staging
```

### 環境変数ファイルの管理指針
- `.env.base`: リポジトリにコミット可能（機密情報を含まない）
- `.env.local`: ローカル開発用（.gitignoreに追加）
- `.env.secrets`: API キーなど（絶対にコミットしない）

## CLI実装詳細

### 新しいフラグ

- `--env PATH`: 環境変数ファイルのパスを指定（複数回指定可能）

### 内部処理

1. **ファイル読み込み**: 指定された.envファイルを順次読み込み
2. **マージ処理**: 複数ファイルの環境変数をマージ（後勝ち）
3. **配布処理**: git worktree作成時に各タスクディレクトリに配布
4. **自動.gitignore更新**: タスクディレクトリに.gitignoreも自動生成

### エラーハンドリング

- 指定された.envファイルが存在しない場合は警告表示
- 読み込みエラーが発生した場合は詳細なエラーメッセージ
- 部分的な失敗でも他のタスクは継続処理

## 使用例とベストプラクティス

### 開発環境の設定例

```bash
# 開発用（デバッグ情報を含む）
haconiwa apply -f dev-company.yaml --env .env.base --env .env.dev

# ステージング環境
haconiwa apply -f staging-company.yaml --env .env.base --env .env.staging

# 本番環境（最小限の設定）
haconiwa apply -f prod-company.yaml --env .env.base --env .env.production
```

### 環境変数の読み込み確認

```bash
# 各ペインでclaudeコマンド実行前に.envを読み込み
cd /path/to/task && source .env && claude

# またはdotenvツールを使用
cd /path/to/task && dotenv claude
```

## メリット

1. **シンプル**: 複雑な継承メカニズムが不要
2. **標準的**: .envファイルは多くの開発者が慣れ親しんだ形式
3. **柔軟**: 環境別に異なる.envファイルを簡単に切り替え可能
4. **独立性**: 各タスクが独自の環境変数セットを持つ
5. **互換性**: 既存のツールやライブラリと相性が良い

## 将来の拡張予定

- **テンプレート機能**: 動的な環境変数生成
- **暗号化サポート**: 機密情報の安全な管理
- **環境別プロファイル**: より高度な環境管理機能

---

# 追加開発項目: AICodeConfig CRD サポート

## 概要

AI開発支援ツール用の設定を管理する汎用的なCRD `AICodeConfig` を新規追加し、各タスクのworktreeに自動的にAIツール用の設定ファイルを配布する機能を実装予定です。現在はClaude Codeをサポートし、将来的にGitHub Copilot、Cursor、Codeium等にも対応予定です。

## 新機能の設計

### 1. 新しいCRD: AICodeConfig

```yaml
apiVersion: haconiwa.dev/v1
kind: AICodeConfig
metadata:
  name: ai-config-claude-default
spec:
  # AIプロバイダーの指定（必須）
  provider: "claude"  # "claude", "copilot", "cursor", "codeium" など
  
  # プロバイダー固有の設定（ファイルパス指定）
  claude:
    # settings.local.jsonファイルのパス
    settingsFile: "./claude-settings/settings.local.json"
    
    # CLAUDE.mdファイルのパス
    guidelinesFile: "./claude-settings/CLAUDE.md"
  
  # 適用対象の指定（現在はカンパニー全体のみ）
  targetCompany: "haconiwa-dev-company"
```

### 2. 将来の拡張例（他のAIプロバイダー）

```yaml
# GitHub Copilot設定の例
---
apiVersion: haconiwa.dev/v1
kind: AICodeConfig
metadata:
  name: ai-config-copilot-default
spec:
  provider: "copilot"
  copilot:
    configFile: "./copilot-settings/config.json"

---
# Cursor設定の例
apiVersion: haconiwa.dev/v1
kind: AICodeConfig
metadata:
  name: ai-config-cursor-default
spec:
  provider: "cursor"
  cursor:
    settingsFile: "./cursor-settings/settings.json"
    rulesFile: "./cursor-settings/rules.md"
```

### 3. ファイル配置（provider別に自動生成）

```
./haconiwa-dev-world/
└── tasks/
    ├── task_backend_optimization_06/
    │   ├── .env
    │   ├── .claude/                    # Claude用（provider: "claude"の場合）
    │   │   └── settings.local.json
    │   ├── CLAUDE.md
    │   ├── .github/                    # Copilot用（provider: "copilot"の場合）
    │   │   └── copilot-config.yml
    │   └── .cursor/                    # Cursor用（provider: "cursor"の場合）
    │       └── settings.json
    └── task_ai_strategy_01/
        ├── .env
        ├── .claude/
        │   └── settings.local.json
        └── CLAUDE.md
```

### 4. 複数のAICodeConfig適用例

```yaml
# Claude デフォルト設定
---
apiVersion: haconiwa.dev/v1
kind: AICodeConfig
metadata:
  name: ai-config-claude-default
spec:
  provider: "claude"
  claude:
    settingsFile: "./claude-settings/default/settings.local.json"
    guidelinesFile: "./claude-settings/default/CLAUDE.md"

---
# フロントエンドチーム専用Claude設定
apiVersion: haconiwa.dev/v1
kind: AICodeConfig
metadata:
  name: ai-config-claude-frontend
spec:
  provider: "claude"
  claude:
    settingsFile: "./claude-settings/frontend/settings.local.json"
    guidelinesFile: "./claude-settings/frontend/CLAUDE.md"
  targetCompany: "haconiwa-dev-company"

---
# バックエンドチーム専用Claude設定
apiVersion: haconiwa.dev/v1
kind: AICodeConfig
metadata:
  name: ai-config-claude-backend
spec:
  provider: "claude"
  claude:
    settingsFile: "./claude-settings/backend/settings.local.json"
    guidelinesFile: "./claude-settings/backend/CLAUDE.md"
  targetCompany: "haconiwa-dev-company"

---
# Copilot設定（将来実装）
apiVersion: haconiwa.dev/v1
kind: AICodeConfig
metadata:
  name: ai-config-copilot-all
spec:
  provider: "copilot"
  copilot:
    settings:
      enable: true
```

## 適用ルール（現在の実装）

### 現在の適用範囲

**カンパニー単位での一括適用のみ**：
- `targetCompany`で指定されたカンパニー内の全タスクに同じ設定を適用
- 1つのカンパニーに対して1つのAICodeConfig設定のみ有効

### 適用例

```bash
# AICodeConfigを含むYAMLを適用
haconiwa apply -f ai-configs.yaml

# Space、Task、AICodeConfigを一緒に適用
haconiwa apply -f all-resources.yaml
```

## 実装計画

### Phase 1: AICodeConfig CRD の実装
- [ ] AICodeConfig モデルの定義
- [ ] provider フィールドによる識別
- [ ] CRDパーサーへの追加
- [ ] バリデーション処理

### Phase 2: Claude プロバイダーの実装
- [ ] claude設定からsettings.local.jsonを生成
- [ ] guidelinesからCLAUDE.mdを生成
- [ ] worktree作成時の自動配置
- [ ] `.claude/` ディレクトリの自動作成

### Phase 3: カンパニー単位の適用
- [ ] targetCompanyによる適用対象の指定
- [ ] カンパニー内全タスクへの一括適用

### Phase 4: 他のAIプロバイダー対応
- [ ] GitHub Copilot サポート
- [ ] Cursor サポート
- [ ] Codeium サポート
- [ ] プロバイダー別のファイル生成ロジック

### Phase 5: 将来の機能拡張（将来実装！）

#### 階層構造での適用（将来実装！）
- [ ] **Room単位での設定**: 特定のルームのみに適用
  ```yaml
  # 将来実装例
  targetSelector:
    matchRooms: ["room-frontend", "room-ui"]
  ```
- [ ] **役職単位での設定**: 特定の役職のエージェントのみに適用
  ```yaml
  # 将来実装例
  targetSelector:
    matchRoles: ["senior-engineer", "architect"]
  ```
- [ ] **タスク単位での設定**: パターンマッチングによる細かい制御
  ```yaml
  # 将来実装例
  targetSelector:
    matchTasks:
      - pattern: "task_frontend_*"
      - pattern: "task_ui_*"
  ```
- [ ] **Building/Floor単位での設定**: 組織階層に基づく適用
- [ ] **優先順位ルール**: より具体的な設定が優先される仕組み

#### その他の将来機能（将来実装！）
- [ ] YAML内での設定内容の直接記述サポート
- [ ] テンプレート変数の展開機能
- [ ] 環境変数の参照機能
- [ ] 設定の継承とマージ機能
- [ ] 複数AICodeConfigの組み合わせ適用

## メリット

1. **シンプルな開始**: カンパニー単位での一括適用で導入が簡単
2. **汎用的な設計**: 複数のAI開発支援ツールに対応可能
3. **宣言的管理**: YAMLで各種AI設定を宣言的に管理
4. **バージョン管理**: 設定の変更履歴をGitで追跡
5. **自動配布**: worktree作成時に自動的に適切な設定を配置
6. **将来の拡張性**: 階層構造での細かい制御に対応予定

## セキュリティ考慮事項

- AICodeConfig に API キーなどの機密情報を含めない
- guidelines/rules に機密情報やパスワードを記載しない
- 本番環境用の設定は別管理を推奨

## 参照ファイルの準備

### ディレクトリ構造例

```
./claude-settings/
├── default/
│   ├── settings.local.json
│   └── CLAUDE.md
├── frontend/
│   ├── settings.local.json
│   └── CLAUDE.md
└── backend/
    ├── settings.local.json
    └── CLAUDE.md
```

### settings.local.jsonの形式

Claude Codeは、ツールの実行権限をホワイトリスト形式で管理します：

```json
{
  "permissions": {
    "allow": [
      "Bash(コマンド:引数パターン)",
      "Edit(*)",
      "Read(*)",
      "Write(*)"
    ],
    "deny": [
      "Bash(危険なコマンド)"
    ]
  }
}
```

### パーミッションパターンの例

- `"Bash(git:*)"` - gitコマンドの全ての操作を許可
- `"Bash(npm install)"` - npm installコマンドのみ許可
- `"Bash(rm:*)"` - rmコマンドの全ての操作を許可（注意が必要）
- `"Edit(*)"` - 全てのファイル編集を許可
- `"Read(*)"` - 全てのファイル読み取りを許可
- `"Write(*)"` - 全てのファイル書き込みを許可

### セキュリティのベストプラクティス

1. **最小権限の原則**: 必要最小限の権限のみを付与
2. **deny リストの活用**: 危険なコマンドは明示的に拒否
3. **チーム別設定**: チームの役割に応じた権限設定
4. **定期的な見直し**: 権限設定の定期的な監査

## 他のCRDとの連携

AICodeConfigは他のCRDと独立して動作し、以下のような使い方が可能：

```yaml
# 1つのYAMLファイルに全てのリソースを定義
---
apiVersion: haconiwa.dev/v1
kind: Organization
metadata:
  name: my-org
spec:
  # ...

---
apiVersion: haconiwa.dev/v1
kind: Space
metadata:
  name: my-space
spec:
  # ...

---
apiVersion: haconiwa.dev/v1
kind: Task
metadata:
  name: my-task
spec:
  # ...

---
apiVersion: haconiwa.dev/v1
kind: AICodeConfig
metadata:
  name: my-ai-config
spec:
  provider: "claude"
  claude:
    # ...
``` 