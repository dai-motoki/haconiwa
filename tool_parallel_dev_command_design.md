# Tool Parallel-Dev コマンド設計案（改訂版）

## 概要

既存の`tool`コマンドグループにClaude Code SDKを使用した並列開発機能を追加します。

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
   - `-p, --prompts`: カンマ区切りのプロンプトリスト
   - `--prompt-file`: プロンプトを含むテキストファイル（1行1プロンプト）

### オプションフラグ

- `-m, --max-concurrent`: 同時実行数（デフォルト: 3、最大: 10）
- `-t, --timeout`: タイムアウト時間（秒）（デフォルト: 60）
- `--dry-run`: 実行前の確認表示
- `-o, --output-dir`: 結果出力ディレクトリ
- `--permission-mode`: 権限モード（acceptEdits等）
- `--allowed-tools`: 許可するツールのリスト

## 使用例

### 例1: 基本的な使用
```bash
haconiwa tool parallel-dev claude \
  -f src/main.py,src/utils.py,src/api.py \
  -p "Add type hints","Refactor functions","Add error handling"
```

### 例2: 10ファイル一斉修正
```bash
haconiwa tool parallel-dev claude \
  --file-list files.txt \
  --prompt-file prompts.txt \
  -m 5 \
  -t 120
```

### 例3: YAML設定ファイル使用
```yaml
# parallel-dev.yaml
provider: claude
tasks:
  - file: src/models/user.py
    prompt: Add validation methods and type hints
  - file: src/models/product.py
    prompt: Implement inventory tracking
  # ... 最大10タスクまで
options:
  max_concurrent: 5
  timeout: 90
  allowed_tools: [Read, Write, Edit, MultiEdit]
```

```bash
haconiwa tool parallel-dev claude --from-yaml parallel-dev.yaml
```

### 例4: 状態確認とキャンセル
```bash
# 実行状態確認
haconiwa tool parallel-dev status

# 特定タスクのキャンセル
haconiwa tool parallel-dev cancel task-123

# 実行履歴表示
haconiwa tool parallel-dev history --limit 10
```

## 他のtoolコマンドとの統合

既存の`tool`コマンドグループ：
```bash
haconiwa tool list              # 利用可能なツール一覧
haconiwa tool install <tool>    # ツールのインストール
haconiwa tool configure <tool>  # ツールの設定
haconiwa tool parallel-dev      # 並列開発機能（新規）
```

## 将来の拡張案

```bash
# 他のAIプロバイダー対応
haconiwa tool parallel-dev github-copilot ...
haconiwa tool parallel-dev chatgpt ...
haconiwa tool parallel-dev gemini ...

# バッチ処理
haconiwa tool parallel-dev batch --schedule "0 2 * * *"

# テンプレート機能
haconiwa tool parallel-dev template create refactor-python
haconiwa tool parallel-dev template apply refactor-python --target src/
```

## メリット

1. **既存構造との一貫性** - `haconiwa <カテゴリ> <アクション>`パターンに準拠
2. **拡張性** - 他のAIツールやSDKを追加しやすい
3. **明確な役割** - `tool`は外部ツール連携を扱うカテゴリとして適切
4. **サブコマンド構造** - status、cancel、historyなどの管理機能も自然に追加可能