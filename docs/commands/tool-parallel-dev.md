# tool parallel-dev コマンド - Claude Code SDK 並列実行

## 概要

`haconiwa tool parallel-dev` コマンドは、Claude Code SDKを使用した高速並列ファイル編集機能を提供します。最大10ファイルの同時編集により、大規模なコードベースの効率的な開発を支援します。

## サブコマンド構造

```bash
haconiwa tool parallel-dev claude    # Claude Code SDKでの並列実行
haconiwa tool parallel-dev status    # 実行状況確認
haconiwa tool parallel-dev cancel    # タスクキャンセル
haconiwa tool parallel-dev history   # 実行履歴表示
```

## 詳細機能

### 1. Claude 並列実行 (`tool parallel-dev claude`)

#### 基本的な使用方法

```bash
# 基本的な並列編集（3ファイル）
haconiwa tool parallel-dev claude \
  -f src/main.py,src/utils.py,src/api.py \
  -p "Add type hints to all functions","Refactor helper functions","Add comprehensive error handling"

# ファイルリストとプロンプトファイルを使用
haconiwa tool parallel-dev claude \
  --file-list files.txt \
  --prompt-file prompts.txt \
  -m 5 \
  -t 120

# YAML設定ファイルから実行
haconiwa tool parallel-dev claude --from-yaml parallel-dev.yaml
```

#### 必須フラグ

**ファイル指定（いずれか1つ）:**
- `-f, --files`: カンマ区切りのファイルパスリスト
- `--file-list`: ファイルパスを含むテキストファイル
- `--from-yaml`: YAML設定ファイル

**プロンプト指定（--filesの場合は必須）:**
- `-p, --prompts`: カンマ区切りのプロンプトリスト
- `--prompt-file`: プロンプトを含むテキストファイル（1行1プロンプト）

#### オプションフラグ

- `-m, --max-concurrent`: 同時実行数（デフォルト: 3、最大: 10）
- `-t, --timeout`: タイムアウト時間（秒）（デフォルト: 60）
- `--dry-run`: 実行前の確認表示
- `--api-key`: Anthropic APIキー（環境変数からも取得可能）
- `-o, --output-dir`: 結果出力ディレクトリ（デフォルト: ./parallel-dev-results）
- `--permission-mode`: 権限モード（acceptEdits, confirmEach など）
- `--allowed-tools`: 許可するツールのリスト（デフォルト: Read,Write,Edit）

### 2. 実行状況確認 (`tool parallel-dev status`)

```bash
# 全タスクの状況確認
haconiwa tool parallel-dev status

# 特定タスクの詳細
haconiwa tool parallel-dev status --task-id task-123

# JSON形式での出力
haconiwa tool parallel-dev status --format json
```

### 3. タスクキャンセル (`tool parallel-dev cancel`)

```bash
# 特定タスクのキャンセル
haconiwa tool parallel-dev cancel task-123

# 全タスクのキャンセル
haconiwa tool parallel-dev cancel --all

# 強制終了
haconiwa tool parallel-dev cancel task-123 --force
```

### 4. 実行履歴表示 (`tool parallel-dev history`)

```bash
# 実行履歴表示
haconiwa tool parallel-dev history

# 最新10件のみ表示
haconiwa tool parallel-dev history --limit 10

# 詳細履歴
haconiwa tool parallel-dev history --verbose
```

## 高度な使用例

### 1. 10ファイル一斉修正

```bash
haconiwa tool parallel-dev claude \
  -f src/models/user.py,src/models/product.py,src/models/order.py,src/services/auth.py,src/services/payment.py,src/api/routes/users.py,src/api/routes/products.py,src/utils/validators.py,src/utils/formatters.py,src/config/settings.py \
  -p "Add validation and type hints","Implement inventory tracking","Add status management","Implement JWT auth","Add payment gateway","Add CRUD endpoints","Implement search","Create validation functions","Add formatting utilities","Update configuration" \
  -m 5 \
  -t 120
```

### 2. ファイルリスト方式

**files.txt の内容:**
```
src/models/user.py
src/models/product.py
src/models/order.py
src/services/auth.py
src/services/payment.py
```

**prompts.txt の内容:**
```
Add validation methods and type hints
Implement inventory tracking
Add status management
Implement JWT authentication
Add payment gateway integration
```

**実行:**
```bash
haconiwa tool parallel-dev claude \
  --file-list files.txt \
  --prompt-file prompts.txt \
  -m 3 \
  --output-dir ./results
```

### 3. YAML設定ファイル方式

**parallel-dev.yaml の内容:**
```yaml
provider: claude
metadata:
  project: "My AI Project"
  version: "1.0.0"
tasks:
  - file: src/models/user.py
    prompt: Add validation methods and type hints
  - file: src/models/product.py  
    prompt: Implement inventory tracking
  - file: src/models/order.py
    prompt: Add status management
  - file: src/services/auth.py
    prompt: Implement JWT authentication
  - file: src/services/payment.py
    prompt: Add payment gateway integration
options:
  max_concurrent: 3
  timeout: 90
  allowed_tools: [Read, Write, Edit, MultiEdit]
  permission_mode: acceptEdits
  output_dir: ./parallel-dev-results
  api_key_env: ANTHROPIC_API_KEY
```

**実行:**
```bash
haconiwa tool parallel-dev claude --from-yaml parallel-dev.yaml
```

## 出力形式とログ

### コンソール出力

```
🚀 Starting parallel Claude Code SDK execution...

📋 Task Summary:
- Total files: 10
- Max concurrent: 5
- Timeout per task: 120s

Progress: [##########----------] 50% (5/10)

✅ Completed: src/models/user.py (45s)
✅ Completed: src/models/product.py (38s)
⏳ Processing: src/models/order.py (30s elapsed)
⏳ Processing: src/services/auth.py (25s elapsed)
⏳ Processing: src/services/payment.py (15s elapsed)
🔄 Queued: src/api/routes/users.py
🔄 Queued: src/api/routes/products.py
🔄 Queued: src/utils/validators.py
🔄 Queued: src/utils/formatters.py
🔄 Queued: src/config/settings.py

Final Summary:
✅ Success: 8/10 files (4m 23s total)
❌ Failed: 2/10 files
⚠️  Warnings: 1 file

📁 Results saved to: ./parallel-dev-results/2024-01-15_14-30-45/
```

### 結果ファイル構造

```
parallel-dev-results/
├── 2024-01-15_14-30-45/           # タイムスタンプ付きセッション
│   ├── summary.json               # 実行サマリー
│   ├── config.yaml               # 使用された設定
│   ├── logs/                     # 個別ファイルのログ
│   │   ├── src_models_user.py.log
│   │   ├── src_models_product.py.log
│   │   └── ...
│   ├── errors/                   # エラーファイル
│   │   └── src_services_payment.py.error
│   └── metrics/                  # パフォーマンス指標
│       ├── timing.json
│       └── resource_usage.json
└── latest -> 2024-01-15_14-30-45/  # 最新実行へのシンボリックリンク
```

### summary.json の例

```json
{
  "session_id": "session_2024-01-15_14-30-45",
  "start_time": "2024-01-15T14:30:45Z",
  "end_time": "2024-01-15T14:35:08Z",
  "total_duration": "4m 23s",
  "tasks": {
    "total": 10,
    "success": 8,
    "failed": 2,
    "warnings": 1
  },
  "files": [
    {
      "file": "src/models/user.py",
      "status": "success",
      "duration": "45s",
      "lines_changed": 32,
      "size_change": "+1.2KB"
    },
    {
      "file": "src/services/payment.py",
      "status": "failed",
      "duration": "60s",
      "error": "API timeout"
    }
  ],
  "performance": {
    "avg_duration": "38.2s",
    "max_concurrent_reached": 5,
    "api_calls_total": 156,
    "tokens_used": 45230
  }
}
```

## 内部実装詳細

### アーキテクチャ概要

```python
# コア実装構造
src/haconiwa/tool/parallel_dev/
├── __init__.py
├── executor.py         # メイン実行エンジン
├── task_manager.py     # タスク管理
├── session_manager.py  # セッション管理
├── claude_client.py    # Claude Code SDK ラッパー
├── progress_monitor.py # 進捗監視
└── result_processor.py # 結果処理
```

### 主要クラス

#### ParallelExecutor
```python
class ParallelExecutor:
    """並列実行のメインエンジン"""
    
    async def execute_parallel(
        self, 
        tasks: List[Task], 
        options: ExecutionOptions
    ) -> ExecutionResult:
        """
        並列実行の制御
        - セマフォによる同時実行数制限
        - タイムアウト制御
        - エラーハンドリング
        """
```

#### TaskManager
```python
class TaskManager:
    """タスクのライフサイクル管理"""
    
    def create_task(self, file_path: str, prompt: str) -> Task:
        """タスクオブジェクトの作成"""
    
    async def execute_task(self, task: Task) -> TaskResult:
        """個別タスクの実行"""
    
    def cancel_task(self, task_id: str) -> bool:
        """タスクのキャンセル"""
```

#### ClaudeClient
```python
class ClaudeClient:
    """Claude Code SDK のラッパー"""
    
    async def process_file(
        self, 
        file_path: str, 
        prompt: str, 
        options: ClaudeOptions
    ) -> ProcessingResult:
        """
        Claude Code SDK による単一ファイル処理
        - API呼び出し管理
        - 結果解析
        - エラー処理
        """
```

### 並列処理の実装

#### セマフォ制御
```python
async def controlled_parallel_processing(
    self, 
    files_and_prompts: List[Tuple[str, str]], 
    max_concurrent: int = 3
) -> List[ProcessingResult]:
    """同時実行数を制限した並列処理"""
    
    # セマフォで同時実行数を制限
    semaphore = asyncio.Semaphore(max_concurrent)
    
    async def process_with_semaphore(file_path: str, prompt: str):
        async with semaphore:
            return await self.claude_client.process_file(file_path, prompt)
    
    # 全タスクを作成
    tasks = [
        asyncio.create_task(process_with_semaphore(file_path, prompt))
        for file_path, prompt in files_and_prompts
    ]
    
    # 並列実行
    return await asyncio.gather(*tasks, return_exceptions=True)
```

#### エラーハンドリング
```python
async def robust_parallel_processor(
    self, 
    files_and_prompts: List[Tuple[str, str]]
) -> List[ProcessingResult]:
    """エラーハンドリングを含む堅牢な並列処理"""
    
    async def safe_process_file(file_path: str, edit_prompt: str):
        try:
            result = await self.claude_client.process_file(file_path, edit_prompt)
            return ProcessingResult(
                file=file_path, 
                status="success", 
                result=result
            )
        except Exception as e:
            logger.error(f"Failed to process {file_path}: {str(e)}")
            return ProcessingResult(
                file=file_path, 
                status="error", 
                error=str(e)
            )
    
    # タイムアウト付きで実行
    try:
        results = await asyncio.wait_for(
            asyncio.gather(*[
                safe_process_file(file_path, prompt)
                for file_path, prompt in files_and_prompts
            ]),
            timeout=self.options.timeout
        )
        return results
    except asyncio.TimeoutError:
        logger.error("Operation timed out")
        return [ProcessingResult(status="timeout")]
```

### 進捗監視システム

#### リアルタイム進捗表示
```python
class ProgressMonitor:
    """リアルタイム進捗監視"""
    
    def __init__(self, total_tasks: int):
        self.total_tasks = total_tasks
        self.completed_tasks = 0
        self.failed_tasks = 0
        self.active_tasks = {}
    
    async def monitor_progress(self):
        """進捗の継続監視とコンソール出力更新"""
        while self.completed_tasks + self.failed_tasks < self.total_tasks:
            self.update_console_display()
            await asyncio.sleep(1.0)
    
    def update_console_display(self):
        """コンソール表示の更新"""
        progress_percentage = (self.completed_tasks / self.total_tasks) * 100
        progress_bar = self.create_progress_bar(progress_percentage)
        
        print(f"\rProgress: {progress_bar} {progress_percentage:.1f}% ({self.completed_tasks}/{self.total_tasks})", end="")
```

### パフォーマンス最適化

#### メモリ管理
- **ストリーミング処理**: 大きなファイルでもメモリ使用量を抑制
- **結果キャッシュ**: 重複処理の防止
- **ガベージコレクション**: 定期的なメモリ解放

#### API効率化
- **接続プーリング**: HTTP接続の再利用
- **レート制限制御**: Anthropic APIの制限に適応
- **リトライ機構**: 一時的な障害への対応

#### 並列度調整
```python
def calculate_optimal_concurrency() -> int:
    """最適な並列度の計算"""
    cpu_count = os.cpu_count()
    memory_gb = psutil.virtual_memory().total / (1024**3)
    
    # CPUとメモリに基づく並列度調整
    if memory_gb < 8:
        return min(3, cpu_count)
    elif memory_gb < 16:
        return min(5, cpu_count)
    else:
        return min(10, cpu_count * 2)
```

## セキュリティ考慮事項

### API キー管理
- **環境変数**: `ANTHROPIC_API_KEY` による安全な管理
- **設定ファイル**: プレーンテキストでの保存を避ける
- **権限制限**: 最小権限の原則

### ファイルアクセス制御
- **パス検証**: ディレクトリトラバーサル攻撃の防止
- **読み書き権限**: ファイルアクセス権限の確認
- **サンドボックス**: 処理範囲の制限

### プロンプトインジェクション対策
- **入力検証**: プロンプトの安全性確認
- **実行制限**: 危険なコマンドの実行防止
- **ログ監視**: 異常な動作の検出

## トラブルシューティング

### 一般的な問題と解決方法

#### 1. API キー関連エラー
```bash
Error: API key not found or invalid

解決方法:
export ANTHROPIC_API_KEY="your-api-key-here"
# または
haconiwa tool parallel-dev claude --api-key "your-api-key-here" ...
```

#### 2. 並列度調整
```bash
# 並列度を下げて実行
haconiwa tool parallel-dev claude ... -m 2

# タイムアウトを延長
haconiwa tool parallel-dev claude ... -t 180
```

#### 3. ファイル権限エラー
```bash
Error: Permission denied for file: src/locked_file.py

解決方法:
chmod +w src/locked_file.py
```

#### 4. メモリ不足
```bash
# 並列度を1に制限
haconiwa tool parallel-dev claude ... -m 1

# 大きなファイルを除外
haconiwa tool parallel-dev claude ... --max-file-size 1MB
```

### ログ分析

#### エラーログの確認
```bash
# 最新の実行ログを確認
cat parallel-dev-results/latest/logs/error.log

# 特定ファイルのエラー詳細
cat parallel-dev-results/latest/errors/src_models_user.py.error
```

#### パフォーマンス分析
```bash
# 実行時間分析
cat parallel-dev-results/latest/metrics/timing.json

# リソース使用量確認
cat parallel-dev-results/latest/metrics/resource_usage.json
```

## 将来の拡張予定

### 他のAIプロバイダー対応
```bash
# GitHub Copilot統合
haconiwa tool parallel-dev github-copilot ...

# ChatGPT API統合
haconiwa tool parallel-dev chatgpt ...

# Google Gemini統合
haconiwa tool parallel-dev gemini ...
```

### 高度な機能
- **バッチ処理**: スケジュール実行機能
- **テンプレート機能**: よく使うパターンの保存
- **プロジェクト全体処理**: 自動ファイル発見と一括処理
- **チーム連携**: 結果の共有とレビュー機能
- **継続的監視**: ファイル変更の自動検知と処理

### 統合機能
- **IDE統合**: VS Code、JetBrains等への統合
- **CI/CD統合**: GitHub Actions、GitLab CI等との連携
- **監視ダッシュボード**: Web UIによる可視化 