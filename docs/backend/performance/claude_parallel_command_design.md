# Tool Parallel-Dev コマンド設計案

## 概要

既存の`tool`コマンドグループにClaude Code SDKを使用した並列開発機能を追加します。これにより、既存のコマンド体系との一貫性を保ちながら、将来的に他のAIツールも統合可能な拡張性を持たせます。

## コマンド構造

### メインコマンド
```bash
haconiwa tool parallel-dev
```

### サブコマンド構造
```bash
haconiwa tool parallel-dev claude    # Claude Code SDKでの並列実行
haconiwa tool parallel-dev status    # 実行状況確認
haconiwa tool parallel-dev cancel    # タスクキャンセル
haconiwa tool parallel-dev history   # 実行履歴表示
```

## `haconiwa tool parallel-dev claude` の詳細

### 必須フラグ

1. **ファイル指定**（いずれか1つ）
   - `-f, --files`: カンマ区切りのファイルパスリスト
   - `--file-list`: ファイルパスを含むテキストファイル
   - `--from-yaml`: YAML設定ファイル

2. **プロンプト指定**（--filesの場合は必須）
   - `-p, --prompts`: カンマ区切りのプロンプトリスト（ファイル数と一致する必要あり）
   - `--prompt-file`: プロンプトを含むテキストファイル（1行1プロンプト）

### オプションフラグ

- `-m, --max-concurrent`: 同時実行数（デフォルト: 3、最大: 10）
- `-t, --timeout`: タイムアウト時間（秒）（デフォルト: 60）
- `--dry-run`: 実行前の確認表示
- `--api-key`: Anthropic APIキー（環境変数 ANTHROPIC_API_KEY からも取得可能）
- `-o, --output-dir`: 結果出力ディレクトリ（デフォルト: ./parallel-dev-results）
- `--permission-mode`: 権限モード（acceptEdits, confirmEach など）
- `--allowed-tools`: 許可するツールのリスト（デフォルト: Read,Write,Edit）

## 使用例

### 例1: 基本的な使用方法
```bash
haconiwa tool parallel-dev claude \
  -f src/main.py,\
  src/utils.py,\
  src/api.py \
  -p "Add type hints to all functions",\
  "Refactor helper functions for better readability",\
  "Add comprehensive error handling"
```

### 例2: ファイルリストを使用
```bash
# files.txt の内容:
# src/models/user.py
# src/models/product.py
# src/models/order.py

# prompts.txt の内容:
# Add validation methods and type hints
# Implement inventory tracking
# Add status management

haconiwa tool parallel-dev claude \
  --file-list files.txt \
  --prompt-file prompts.txt \
  -m 2
```

### 例3: 10個のファイルを一斉修正
```bash
haconiwa tool parallel-dev claude \
  -f src/models/user.py,src/models/product.py,src/models/order.py,src/services/auth.py,src/services/payment.py,src/api/routes/users.py,src/api/routes/products.py,src/utils/validators.py,src/utils/formatters.py,src/config/settings.py \
  -p "Add validation and type hints","Implement inventory tracking","Add status management","Implement JWT auth","Add payment gateway","Add CRUD endpoints","Implement search","Create validation functions","Add formatting utilities","Update configuration" \
  -m 5 \
  -t 120
```

### 例4: YAMLファイルから設定を読み込み
```yaml
# parallel-dev.yaml の内容:
provider: claude
tasks:
  - file: src/models/user.py
    prompt: Add validation methods and type hints
  - file: src/models/product.py  
    prompt: Implement inventory tracking
  - file: src/models/order.py
    prompt: Add status management
options:
  max_concurrent: 3
  timeout: 90
  allowed_tools: [Read, Write, Edit, MultiEdit]
```

```bash
haconiwa tool parallel-dev claude --from-yaml parallel-dev.yaml
```

### 例5: ドライラン実行
```bash
haconiwa tool parallel-dev claude \
  -f src/main.py,src/test.py \
  -p "Add docstrings","Add unit tests" \
  --dry-run
```

### 例6: 実行状態の管理
```bash
# 実行状態確認
haconiwa tool parallel-dev status

# 特定タスクのキャンセル
haconiwa tool parallel-dev cancel task-123

# 実行履歴表示
haconiwa tool parallel-dev history --limit 10
```

## 出力形式

### コンソール出力
```
🚀 Starting parallel Claude Code SDK execution...

📋 Task Summary:
- Total files: 10
- Max concurrent: 5
- Timeout per task: 120s

Progress: [##########----------] 50% (5/10)

✅ Completed: src/models/user.py
✅ Completed: src/models/product.py
⏳ Processing: src/models/order.py
⏳ Processing: src/services/auth.py
⏳ Processing: src/services/payment.py
🔄 Queued: src/api/routes/users.py
🔄 Queued: src/api/routes/products.py
🔄 Queued: src/utils/validators.py
🔄 Queued: src/utils/formatters.py
🔄 Queued: src/config/settings.py

Summary:
✅ Success: 8/10
❌ Failed: 2/10
⏱️ Total time: 3m 45s
```

### 結果ファイル出力
```
parallel-dev-results/
├── summary.json
├── logs/
│   ├── src_models_user.py.log
│   ├── src_models_product.py.log
│   └── ...
└── errors/
    └── src_services_payment.py.error
```

## エラーハンドリング

- ファイル数とプロンプト数が一致しない場合はエラー
- APIキーが設定されていない場合はエラー
- ファイルが存在しない場合は警告を表示して続行
- 個別タスクの失敗は記録し、他のタスクは継続実行

## 内部実装の概要

```python
# 擬似コード
async def parallel_execute(files, prompts, options):
    tasks = []
    
    for file, prompt in zip(files, prompts):
        task = asyncio.create_task(
            process_file(file, prompt, options)
        )
        tasks.append(task)
    
    # セマフォで同時実行数を制限
    semaphore = asyncio.Semaphore(options.max_concurrent)
    
    async def process_with_semaphore(file, prompt):
        async with semaphore:
            return await process_file(file, prompt, options)
    
    results = await asyncio.gather(*tasks, return_exceptions=True)
    return results
```

## 他のtoolコマンドとの統合

既存の`tool`コマンドグループ：
```bash
haconiwa tool list              # 利用可能なツール一覧
haconiwa tool install <tool>    # ツールのインストール
haconiwa tool configure <tool>  # ツールの設定
haconiwa tool parallel-dev      # 並列開発機能（新規）
```

## 統合方法

1. 既存の`tool`コマンドグループに`parallel-dev`サブコマンドを追加
2. `haconiwa/cli/commands/tool.py` に`parallel-dev`サブコマンドを実装
3. Claude Code SDKの依存関係を追加
4. テストケースの作成

## 将来の拡張案

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
```bash
# バッチ処理
haconiwa tool parallel-dev batch --schedule "0 2 * * *"

# テンプレート機能
haconiwa tool parallel-dev template create refactor-python
haconiwa tool parallel-dev template apply refactor-python --target src/

# プロジェクト全体の一括処理
haconiwa tool parallel-dev project-wide --action "Add type hints to all Python files"
```

## メリット

1. **既存構造との一貫性** - `haconiwa <カテゴリ> <アクション>`パターンに準拠
2. **拡張性** - 他のAIツールやSDKを追加しやすい構造
3. **明確な役割** - `tool`は外部ツール連携を扱うカテゴリとして適切
4. **サブコマンド構造** - status、cancel、historyなどの管理機能も自然に追加可能
5. **統一的なインターフェース** - 異なるAIプロバイダーでも同じコマンド体系で利用可能