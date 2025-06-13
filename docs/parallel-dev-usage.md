# Haconiwa Tool Parallel-Dev 使用ガイド

## 概要

`haconiwa tool parallel-dev`は、Claude Code SDKを使用して複数のファイルを並列で編集する機能を提供します。最大10ファイルの同時編集が可能で、各ファイルに対して個別のプロンプトを指定できます。

## インストール

```bash
# Haconiwaのインストール
pip install haconiwa

# Claude Code SDKの確認
haconiwa tool install claude-code
```

## 基本的な使い方

### 1. コマンドライン引数での実行

```bash
# 3つのファイルを並列編集
haconiwa tool parallel-dev claude \
  -f src/main.py,src/utils.py,src/api.py \
  -p "Add type hints to all functions","Refactor helper functions","Add error handling"
```

### 2. ファイルリストを使った実行

```bash
# ファイルとプロンプトを別ファイルで管理
haconiwa tool parallel-dev claude \
  --file-list examples/files.txt \
  --prompt-file examples/prompts.txt \
  -m 5 \
  -t 120
```

### 3. YAML設定ファイルでの実行

```yaml
# parallel-dev.yaml
provider: claude
tasks:
  - file: src/models/user.py
    prompt: Add validation methods and type hints
  - file: src/models/product.py
    prompt: Implement inventory tracking
  - file: src/models/order.py
    prompt: Add status management
options:
  max_concurrent: 5
  timeout: 90
  allowed_tools: [Read, Write, Edit, MultiEdit]
```

```bash
# YAML設定で実行
haconiwa tool parallel-dev claude --from-yaml parallel-dev.yaml
```

## 詳細オプション

| オプション | 短縮形 | 説明 | デフォルト |
|-----------|--------|------|------------|
| `--files` | `-f` | カンマ区切りのファイルパスリスト | - |
| `--prompts` | `-p` | カンマ区切りのプロンプトリスト | - |
| `--file-list` | - | ファイルパスを含むテキストファイル | - |
| `--prompt-file` | - | プロンプトを含むテキストファイル | - |
| `--from-yaml` | - | YAML設定ファイル | - |
| `--max-concurrent` | `-m` | 同時実行数 | 3 |
| `--timeout` | `-t` | タスクごとのタイムアウト（秒） | 60 |
| `--dry-run` | - | 実行内容の確認のみ | False |
| `--output-dir` | `-o` | 結果出力ディレクトリ | ./parallel-dev-results |
| `--permission-mode` | - | 権限モード | acceptEdits |
| `--allowed-tools` | - | 許可するツールのリスト | Read,Write,Edit |

## 実行例

### 10ファイルの一斉修正

```bash
haconiwa tool parallel-dev claude \
  -f src/models/user.py,src/models/product.py,src/models/order.py,src/services/auth.py,src/services/payment.py,src/api/routes/users.py,src/api/routes/products.py,src/utils/validators.py,src/utils/formatters.py,src/config/settings.py \
  -p "Add validation and type hints","Implement inventory tracking","Add status management","Implement JWT auth","Add payment gateway","Add CRUD endpoints","Implement search","Create validation functions","Add formatting utilities","Update configuration" \
  -m 5 \
  -t 120
```

### ドライラン（実行確認）

```bash
haconiwa tool parallel-dev claude \
  -f src/main.py,src/test.py \
  -p "Add docstrings","Add unit tests" \
  --dry-run
```

## 管理コマンド

### 実行状態の確認

```bash
# アクティブなタスクの状態を表示
haconiwa tool parallel-dev status
```

### 実行履歴の表示

```bash
# 最近の実行履歴を表示
haconiwa tool parallel-dev history

# 表示件数を指定
haconiwa tool parallel-dev history --limit 20
```

### タスクのキャンセル（将来実装予定）

```bash
# 特定のタスクをキャンセル
haconiwa tool parallel-dev cancel task-001
```

## 出力結果

実行結果は以下の形式で保存されます：

```
parallel-dev-results/
├── summary_20240613_150230.json    # 実行サマリー
├── logs/                           # 個別ログ
│   ├── src_models_user.py_20240613_150230.log
│   ├── src_models_product.py_20240613_150230.log
│   └── ...
└── errors/                         # エラーログ
    └── src_services_payment.py_20240613_150230.error
```

## エラーハンドリング

- ファイル数とプロンプト数が一致しない場合はエラー
- APIキーが設定されていない場合は環境変数`ANTHROPIC_API_KEY`を確認
- 個別のタスクが失敗しても他のタスクは継続実行
- タイムアウトしたタスクは`timeout`ステータスで記録

## ベストプラクティス

1. **同時実行数の調整**: API制限を考慮して3-5程度に設定
2. **タイムアウトの設定**: 複雑な編集には長めのタイムアウトを設定
3. **ドライラン**: 大量のファイルを編集する前に`--dry-run`で確認
4. **YAML設定の活用**: 繰り返し実行する編集はYAMLファイルで管理
5. **エラーログの確認**: 失敗したタスクはログで詳細を確認