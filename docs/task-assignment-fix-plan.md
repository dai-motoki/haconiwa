# タスク投入コマンド設計書

## 概要

既存のカンパニー（tmuxセッション）に対して動的にタスクを投入するための新しいCLIコマンドを追加します。このコマンドにより、YAMLファイルを作成することなく、コマンドラインから直接タスクを作成し、エージェントに割り当てることが可能になります。

### 主な特徴
- **Git worktreeの自動作成**: 現在のブランチから新規ブランチを作成し、専用のディレクトリ（worktree）を生成
- **エージェントの自動移動**: 割り当てられたエージェントを新規作成されたworktreeディレクトリに自動的に移動
- **ブランチ名とディレクトリ名の一致**: 指定したブランチ名がそのままworktreeのディレクトリ名として使用される

## コマンド構造

### 基本構文

```bash
haconiwa task submit [OPTIONS]
```

### オプション

| オプション | 短縮形 | 必須 | デフォルト | 説明 |
|-----------|-------|------|-----------|------|
| `--company` | `-c` | ✓ | - | タスクを投入するカンパニー名 |
| `--assignee` | `-a` | ✓ | - | タスクを割り当てるエージェントID |
| `--title` | `-t` | ✓ | - | タスクのタイトル |
| `--description` | `-d` | ✗ | "" | タスクの詳細説明（マークダウン対応） |
| `--description-file` | `-f` | ✗ | - | タスク詳細を記載したマークダウンファイル |
| `--branch` | `-b` | ✓ | - | 新規ブランチ名（ディレクトリ名にもなる） |
| `--base-branch` | - | ✗ | 現在のブランチ | worktreeのベースとなるブランチ |
| `--priority` | `-p` | ✗ | "medium" | タスクの優先度 (high/medium/low) |
| `--room` | `-r` | ✗ | 自動検出 | 特定のルーム（tmux window）を指定 |
| `--worktree-path` | - | ✗ | ./tasks/{branch} | worktreeを作成するパス |
| `--dry-run` | - | ✗ | False | 実行内容を表示するが実際には実行しない |

## 使用例

### 基本的な使用例

```bash
# 最小限の指定でタスク投入（現在のブランチから新規ブランチを作成）
haconiwa task submit \
  -c haconiwa-dev-company \
  -a "ai-engineer-01" \
  -t "APIエンドポイントの実装" \
  -b "feature/api-endpoints"

# 詳細な説明付きでタスク投入（インライン）
haconiwa task submit \
  -c haconiwa-dev-company \
  -a "frontend-lead" \
  -t "ダッシュボード画面の実装" \
  -b "feature/dashboard-ui" \
  -d "## 要件\n- React 18を使用\n- レスポンシブデザイン対応\n- ダークモード対応" \
  -p high

# マークダウンファイルから詳細を読み込み
haconiwa task submit \
  -c haconiwa-dev-company \
  -a "backend-lead" \
  -t "API設計と実装" \
  -b "feature/api-v2" \
  -f "./docs/api-specification.md"

# 特定のベースブランチから作成
haconiwa task submit \
  -c test-multiroom-company \
  -r room-backend \
  -a "backend-engineer-02" \
  -t "データベーススキーマの最適化" \
  -b "feature/db-optimization" \
  --base-branch "develop"

# カスタムworktreeパス指定
haconiwa task submit \
  -c my-company \
  -a "devops-lead" \
  -t "CI/CDパイプラインの構築" \
  -b "feature/ci-cd-pipeline" \
  --worktree-path "./infrastructure/ci-cd"

# ドライランで確認
haconiwa task submit \
  -c my-company \
  -a "qa-engineer" \
  -t "E2Eテストの実装" \
  -b "test/e2e-implementation" \
  --dry-run
```

### 高度な使用例

```bash
# 複数タスクの一括投入（スクリプト例）
#!/bin/bash
haconiwa task submit -c my-company -a "frontend-01" -t "Header component" -b "feature/header"
haconiwa task submit -c my-company -a "frontend-02" -t "Footer component" -b "feature/footer"
haconiwa task submit -c my-company -a "backend-01" -t "User API" -b "feature/user-api"

# developブランチから複数のフィーチャーブランチを作成
for feature in "auth" "profile" "settings"; do
  haconiwa task submit \
    -c my-company \
    -a "engineer-${feature}" \
    -t "${feature} implementation" \
    -b "feature/${feature}" \
    --base-branch "develop"
done

# マークダウンファイルを使った複数タスクの投入
for task in tasks/*.md; do
  task_name=$(basename "$task" .md)
  haconiwa task submit \
    -c my-company \
    -a "available-engineer" \
    -t "$task_name" \
    -b "feature/$task_name" \
    -f "$task"
done

# 実行例：タスク投入後の状態確認
haconiwa task submit \
  -c my-company \
  -a "ai-engineer-01" \
  -t "AI model optimization" \
  -b "feature/ai-optimization" && \
haconiwa monitor -c my-company --japanese
```

### Git worktreeの動作例

```bash
# 実行前のディレクトリ構造
./
├── src/
├── tests/
└── README.md

# コマンド実行
haconiwa task submit \
  -c my-company \
  -a "engineer-01" \
  -t "New feature" \
  -b "feature/awesome-feature"

# 実行後のディレクトリ構造
./
├── src/
├── tests/
├── README.md
└── tasks/
    └── feature/awesome-feature/  # 新規作成されたworktree
        ├── src/
        ├── tests/
        └── README.md

# エージェントは自動的に ./tasks/feature/awesome-feature/ に移動
```

### マークダウンファイルを使用した例

```bash
# task-spec.md ファイルの内容
cat > task-spec.md << 'EOF'
# ユーザー認証システムの実装

## 概要
新しいユーザー認証システムを実装し、既存の認証機能を置き換える。

## 要件
### 機能要件
- JWT トークンベースの認証
- OAuth 2.0 プロバイダー連携（Google, GitHub）
- 2要素認証（2FA）のサポート
- パスワードリセット機能

### 技術要件
- Node.js + Express
- PostgreSQLでのユーザー管理
- Redis でのセッション管理
- bcrypt によるパスワードハッシュ化

## 実装手順
1. データベーススキーマの設計
2. 認証ミドルウェアの実装
3. APIエンドポイントの作成
4. フロントエンド統合
5. テストの作成

## 参考資料
- [JWT Best Practices](https://example.com/jwt-best-practices)
- [OAuth 2.0 仕様書](https://example.com/oauth2-spec)
EOF

# マークダウンファイルを使ってタスク投入
haconiwa task submit \
  -c my-company \
  -a "senior-backend-dev" \
  -t "ユーザー認証システムの実装" \
  -b "feature/auth-system" \
  -f task-spec.md
```

## 実装詳細

### 処理フロー

1. **入力検証**
   - カンパニーの存在確認
   - エージェントIDの妥当性検証
   - 必須パラメータのチェック
   - ブランチ名の形式検証

2. **カンパニー情報取得**
   - `SpaceManager`を使用してtmuxセッション情報を取得
   - エージェントの現在位置（ペイン）を特定
   - 組織構造の確認

3. **Git worktree作成**
   - 現在のブランチ（または`--base-branch`）から新規ブランチを作成
   - worktreeディレクトリを作成（デフォルト: `./tasks/{branch-name}`）
   - 例: ブランチ`feature/api-endpoints` → ディレクトリ`./tasks/feature/api-endpoints`
   - worktree作成コマンド:
     ```bash
     git worktree add -b {branch} {worktree-path} {base-branch}
     ```

4. **エージェント割り当て**
   - 指定されたエージェントのペインを特定
   - エージェントを新規作成したworktreeディレクトリに移動
   - tmuxコマンドでペインのカレントディレクトリを変更:
     ```bash
     tmux send-keys -t {session}:{window}.{pane} "cd {worktree-path}" C-m
     ```
   - 割り当てログの作成（`.haconiwa/agent_assignment.json`）

5. **通知と確認**
   - タスク作成の成功メッセージ表示
   - 作成されたworktreeパスの表示
   - エージェントの移動完了確認

### エラーハンドリング

- **カンパニーが存在しない場合**
  ```
  Error: Company 'xxx' not found. Use 'haconiwa space list' to see available companies.
  ```

- **エージェントが見つからない場合**
  ```
  Error: Agent 'xxx' not found in company 'yyy'. Available agents: [list]
  ```

- **Git worktree作成失敗**
  ```
  Error: Failed to create worktree. Ensure you are in a git repository.
  ```

- **ブランチが既に存在する場合**
  ```
  Error: Branch 'feature/xxx' already exists. Use a different branch name.
  ```

- **worktreeディレクトリが既に存在する場合**
  ```
  Error: Directory './tasks/feature/xxx' already exists. Remove it or use --worktree-path.
  ```

- **説明ファイルが見つからない場合**
  ```
  Error: Description file 'xxx.md' not found.
  ```

- **説明ファイルとインライン説明の両方が指定された場合**
  ```
  Error: Cannot specify both --description and --description-file. Use one or the other.
  ```

## 内部実装

### 新規クラス/関数

```python
# src/haconiwa/task/submit.py
class TaskSubmitter:
    def __init__(self, space_manager: SpaceManager, task_manager: TaskManager):
        self.space_manager = space_manager
        self.task_manager = task_manager
    
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
        worktree_path: Optional[str] = None
    ) -> Task:
        """既存のカンパニーにタスクを投入"""
        # 1. 説明の処理
        if description_file and description:
            raise ValueError("Cannot specify both --description and --description-file")
        
        if description_file:
            description = self._read_description_file(description_file)
        
        # 2. ベースブランチの決定
        if not base_branch:
            base_branch = self._get_current_branch()
        
        # 3. worktreeパスの決定
        if not worktree_path:
            worktree_path = f"./tasks/{branch}"
        
        # 4. Git worktreeの作成
        self._create_worktree(branch, worktree_path, base_branch)
        
        # 5. エージェントのペインを特定
        pane_info = self._find_agent_pane(company, assignee, room)
        
        # 6. エージェントをworktreeディレクトリに移動
        self._move_agent_to_worktree(pane_info, worktree_path)
        
        # 7. タスクオブジェクトの作成と保存
        task = self._create_task(
            title=title,
            branch=branch,
            assignee=assignee,
            description=description,
            priority=priority,
            worktree_path=worktree_path
        )
        
        return task
    
    def _read_description_file(self, file_path: str) -> str:
        """マークダウンファイルから説明を読み込む"""
        if not Path(file_path).exists():
            raise FileNotFoundError(f"Description file '{file_path}' not found")
        
        with open(file_path, 'r', encoding='utf-8') as f:
            return f.read()
```

### CLI統合

```python
# src/haconiwa/task/cli.py に追加
@task_app.command("submit")
def submit_task(
    company: str = typer.Option(..., "--company", "-c", help="Company name"),
    assignee: str = typer.Option(..., "--assignee", "-a", help="Agent ID"),
    title: str = typer.Option(..., "--title", "-t", help="Task title"),
    branch: str = typer.Option(..., "--branch", "-b", help="Branch name (becomes directory name)"),
    description: str = typer.Option("", "--description", "-d", help="Task description"),
    description_file: Optional[str] = typer.Option(None, "--description-file", "-f", help="Markdown file with task description"),
    base_branch: Optional[str] = typer.Option(None, "--base-branch", help="Base branch for worktree"),
    priority: str = typer.Option("medium", "--priority", "-p", help="Task priority"),
    room: Optional[str] = typer.Option(None, "--room", "-r", help="Target room/window"),
    worktree_path: Optional[str] = typer.Option(None, "--worktree-path", help="Custom worktree path"),
    dry_run: bool = typer.Option(False, "--dry-run", help="Show what would be done")
):
    """Submit a task to an existing company with automatic worktree creation"""
    # 実装...
```

## 他機能との連携

### monitorコマンドとの連携
- タスク投入後、`haconiwa monitor`で即座に反映を確認可能
- エージェントのステータスが「仕事待ち」から「作業中」に変化

### YAMLファイルとの相互運用
- `task submit`で作成したタスクも`.haconiwa/tasks/`に記録
- 後からYAMLエクスポート可能

### ログとトレーサビリティ
- すべてのタスク投入は`.haconiwa/task_history.json`に記録
- エージェント割り当て履歴の追跡が可能

## 将来の拡張性

1. **バルク投入機能**
   - CSVやJSONファイルからの一括タスク投入
   - テンプレート機能

2. **インテリジェント割り当て**
   - エージェントの負荷を考慮した自動割り当て
   - スキルマッチングによる最適化

3. **ワークフロー統合**
   - 依存関係のあるタスクチェーンの定義
   - 承認フローの実装

4. **通知機能**
   - タスク完了時の通知
   - Slack/Discord統合

## テスト計画

### ユニットテスト
- 各オプションの検証ロジック
- エラーケースの網羅的テスト

### 統合テスト
- 実際のtmuxセッションでの動作確認
- Git worktree作成の検証
- エージェント割り当ての確認

### E2Eテスト
- 完全なワークフローのテスト
- 他コマンドとの連携確認

## まとめ

この`task submit`コマンドにより、Haconiwaの柔軟性が大幅に向上します。YAMLファイルによる静的な定義と、コマンドラインからの動的なタスク投入の両方をサポートすることで、さまざまな開発ワークフローに対応できるようになります。

### 主な利点
- **動的なタスク投入**: 実行中のカンパニーに柔軟にタスクを追加
- **マークダウンファイル対応**: 詳細な仕様書をファイルから読み込み可能
- **Git worktree統合**: 各タスクが独立した作業環境を持つ
- **自動エージェント移動**: タスク割り当て時にエージェントが自動的に適切なディレクトリに移動