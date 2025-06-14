# scan コマンド - AIモデル検索・分析

## 概要

`haconiwa scan` コマンドは、プロジェクト内のAIモデル関連ファイルの高度な検索・分析機能を提供します。モデルの発見から比較、開発ガイド生成、並列開発設定の自動生成まで包括的にサポートします。

## サブコマンド一覧

```bash
haconiwa scan model <name>         # モデル名で検索
haconiwa scan content <pattern>    # ファイル内容を検索
haconiwa scan list                 # AIモデル一覧表示
haconiwa scan analyze              # ディレクトリ構造分析
haconiwa scan compare <model1> <model2>  # モデル比較分析
haconiwa scan guide <model>        # 開発ガイド生成
haconiwa scan generate-parallel-config  # 並列開発設定YAML生成
```

## 詳細機能

### 1. モデル名検索 (`scan model`)

```bash
# 基本的なモデル検索（プレフィックス自動削除）
haconiwa scan model gpt-4
haconiwa scan model claude-3-opus

# プレフィックス削除を無効化
haconiwa scan model claude-3-opus --no-strip-prefix

# 出力形式指定
haconiwa scan model gpt-4 --format tree
haconiwa scan model gpt-4 --format json
```

**実装詳細:**
- **プレフィックス自動削除**: `gpt-`, `claude-`, `llama-` などの接頭辞を自動的に除去
- **ファジーマッチング**: 部分一致でのモデル名検索
- **カテゴリ分類**: LLM、Vision、Audio、Multimodal等への自動分類
- **プロバイダー識別**: OpenAI、Anthropic、Meta等の自動識別

### 2. コンテンツ検索 (`scan content`)

```bash
# 基本的なコンテンツ検索
haconiwa scan content "import torch"

# ファイルタイプ指定
haconiwa scan content "import torch" --type .py

# 正規表現検索
haconiwa scan content "model\.forward\(" --context 5

# 複数パターン検索
haconiwa scan content "model|Model" --case-sensitive
```

**実装詳細:**
- **正規表現サポート**: Pythonのreモジュールによる高度なパターンマッチング
- **コンテキスト表示**: マッチした行の前後N行を表示
- **ファイルタイプフィルター**: 拡張子による検索対象の絞り込み
- **大文字小文字の制御**: --case-sensitiveフラグによる制御

### 3. モデル一覧表示 (`scan list`)

```bash
# 全モデル一覧
haconiwa scan list

# プロバイダー別フィルター
haconiwa scan list --provider openai
haconiwa scan list --provider anthropic

# カテゴリ別フィルター
haconiwa scan list --category llm
haconiwa scan list --category multimodal

# 出力形式指定
haconiwa scan list --format json
haconiwa scan list --format yaml
```

**出力例:**
```
          Available AI Models          
┏━━━━━━━━━━┳━━━━━━━━━━━━━━━┳━━━━━━━━━┳━━━━━━━┓
┃ Provider ┃ Model         ┃ Category ┃ Files ┃
┡━━━━━━━━━━╇━━━━━━━━━━━━━━━╇━━━━━━━━━╇━━━━━━━┩
│ openai   │ gpt-4         │ llm      │ 24    │
│ openai   │ gpt-3.5-turbo │ llm      │ 18    │
│ anthropic│ claude-3-opus │ llm      │ 32    │
│ meta     │ llama-2-70b   │ llm      │ 45    │
│ google   │ gemini-pro    │ multimodal│ 28   │
└──────────┴───────────────┴──────────┴───────┘
```

### 4. ディレクトリ構造分析 (`scan analyze`)

```bash
# 基本的な分析
haconiwa scan analyze

# 特定パス分析
haconiwa scan analyze --path ./models

# 詳細構造表示
haconiwa scan analyze --show-structure

# サイズ情報含む
haconiwa scan analyze --include-size
```

**分析結果例:**
```
📊 AI Model Directory Analysis
━━━━━━━━━━━━━━━━━━━━━━━━━━━━
Total models found: 12
Total files: 342
Total size: 2.4 GB

📁 Directory Structure:
models/
├── openai/          (5 models, 89 files)
│   ├── gpt-4/
│   ├── gpt-3.5-turbo/
│   └── embeddings/
├── anthropic/       (3 models, 76 files)
│   ├── claude-3-opus/
│   └── claude-3-sonnet/
└── opensource/      (4 models, 177 files)
    ├── llama-2/
    └── mistral/

📊 Category Distribution:
- LLM: 8 models (66.7%)
- Vision: 2 models (16.7%)
- Multimodal: 2 models (16.7%)

🔍 Insights:
- Most models include example scripts
- Configuration files follow similar patterns
- Test coverage: 78% of models have tests
```

### 5. モデル比較分析 (`scan compare`)

```bash
# 基本的な比較
haconiwa scan compare gpt-4 claude-3-opus

# 詳細比較（JSON出力）
haconiwa scan compare gpt-3.5-turbo gpt-4 --output comparison.json

# YAML形式での比較
haconiwa scan compare model1 model2 --format yaml
```

**比較結果例:**
```
🔍 Model Comparison Analysis
━━━━━━━━━━━━━━━━━━━━━━━━━━

📊 Basic Comparison:
┏━━━━━━━━━━━━━━━┳━━━━━━━━━━━━━━━┳━━━━━━━━━━━━━━━━┓
┃ Feature       ┃ gpt-4         ┃ claude-3-opus  ┃
┡━━━━━━━━━━━━━━━╇━━━━━━━━━━━━━━━╇━━━━━━━━━━━━━━━━┩
│ Provider      │ OpenAI        │ Anthropic      │
│ Category      │ LLM           │ LLM            │
│ Files         │ 24            │ 32             │
│ Config Found  │ ✓             │ ✓              │
│ Examples      │ 6             │ 8              │
│ Tests         │ ✓             │ ✓              │
│ Documentation │ README.md     │ README.md      │
└───────────────┴───────────────┴────────────────┘

📁 Unique Files:
GPT-4 only:
- api_reference.md
- deployment_guide.md

Claude-3-Opus only:
- safety_guidelines.md
- constitutional_ai.md
- context_window.md

💡 Recommendations:
- Both models have comprehensive test coverage
- Claude-3-Opus has more extensive safety documentation
- GPT-4 includes more deployment examples
```

### 6. 開発ガイド生成 (`scan guide`)

```bash
# 開発ガイド生成
haconiwa scan guide gpt-4 --type development

# クイックスタートガイド
haconiwa scan guide claude-3 --type quickstart --output guide.md

# 統合ガイド
haconiwa scan guide model-name --type integration

# 使用方法ガイド
haconiwa scan guide model-name --type usage
```

**ガイドタイプ:**
- **development**: モデル設定、ファイル構造、依存関係、ベストプラクティス
- **usage**: 基本的な使い方、ユースケース、コード例、最適化
- **integration**: システム要件、デプロイ、API統合、監視
- **quickstart**: 5分で始められる最小セットアップ

### 7. 並列開発設定YAML生成 (`scan generate-parallel-config`)

```bash
# 基本例（サンプルYAML生成）
haconiwa scan generate-parallel-config --example

# モデル検索結果から生成
haconiwa scan generate-parallel-config --source model:gpt-4 --action add_tests

# モデル移行用YAML生成
haconiwa scan generate-parallel-config --migration gpt-3.5:gpt-4 --max-files 20

# パターン修正用YAML生成
haconiwa scan generate-parallel-config --pattern-fix "old_api:new_api" 

# プロジェクト全体の変更
haconiwa scan generate-parallel-config --project-wide "*.py" --action add_type_hints

# カスタムプロンプトファイルを使用
haconiwa scan generate-parallel-config --prompt-file prompts.txt
```

**生成されるYAMLの例:**
```yaml
provider: claude
metadata:
  generated_at: '2024-01-15T14:30:00'
  source: haconiwa scan generate-parallel-config
  action: add_tests
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
  permission_mode: confirmEach
  output_dir: ./parallel-dev-results
```

**利用可能なアクションタイプ:**
- `refactor` - コードのリファクタリング
- `add_type_hints` - 型ヒントの追加
- `add_validation` - バリデーションの実装
- `add_tests` - テストコードの作成
- `add_docs` - ドキュメントの追加
- `optimize` - パフォーマンス最適化
- `security` - セキュリティ改善
- `async_conversion` - 非同期化
- `error_handling` - エラーハンドリング追加
- `api_implementation` - API実装

## 実装詳細

### 内部アーキテクチャ

```python
# コア実装構造
src/haconiwa/scan/
├── __init__.py
├── scanner.py          # メインスキャナークラス
├── analyzer.py         # ディレクトリ構造分析
├── comparator.py       # モデル比較機能
├── formatter.py        # 出力フォーマット制御
├── guide_generator.py  # ガイド生成機能
└── parallel_config.py  # 並列設定YAML生成
```

### 主要クラス

#### ModelScanner
- **責任**: ファイルシステムのスキャンとモデル発見
- **機能**: プレフィックス処理、ファジーマッチング、カテゴリ分類

#### ContentAnalyzer  
- **責任**: ファイル内容の検索と分析
- **機能**: 正規表現処理、コンテキスト抽出、フィルタリング

#### ModelComparator
- **責任**: 複数モデルの比較分析
- **機能**: 差分検出、レコメンデーション生成、統計計算

#### GuideGenerator
- **責任**: 開発ガイドの自動生成
- **機能**: テンプレート処理、メタデータ抽出、マークダウン生成

### パフォーマンス最適化

- **並列ファイル読み込み**: concurrent.futuresによる高速処理
- **インデックスキャッシュ**: 大規模プロジェクトでの高速検索
- **増分スキャン**: 変更されたファイルのみ再処理
- **メモリ効率**: ストリーミング処理による低メモリ使用量

## 活用シナリオ

### 1. 新規プロジェクト立ち上げ
```bash
# プロジェクトの全体把握
haconiwa scan list
haconiwa scan analyze --show-structure

# 開発ガイド生成
haconiwa scan guide main-model --type quickstart --output setup-guide.md
```

### 2. 既存コードベースの調査
```bash
# モデル使用パターンの調査
haconiwa scan content "load_model|from_pretrained" --type .py

# 設定ファイルの発見
haconiwa scan content "config\.|configuration" --context 3
```

### 3. モデル移行計画
```bash
# 現在と新しいモデルの比較
haconiwa scan compare old-model new-model --output migration-plan.yaml

# 移行用の並列設定生成
haconiwa scan generate-parallel-config --migration old-model:new-model
```

### 4. 自動ドキュメント生成
```bash
# 全モデルのドキュメント一括生成
for model in $(haconiwa scan list --format json | jq -r '.models[].name'); do
  haconiwa scan guide "$model" --type development --output "docs/${model}-guide.md"
done
```

## エラーハンドリング

- **ファイルアクセス権限**: 読み取り権限のないファイルは警告を表示してスキップ
- **破損ファイル**: バイナリファイルや破損ファイルは自動的に除外
- **大容量ファイル**: 設定可能なサイズ制限（デフォルト100MB）
- **並列処理制限**: CPU使用率制御とメモリ使用量監視

## 設定オプション

### グローバル設定ファイル (~/.haconiwa/scan.yaml)
```yaml
scan:
  max_file_size: 104857600  # 100MB
  max_concurrent: 8         # CPU数に応じて自動調整
  cache_enabled: true       # インデックスキャッシュの有効化
  excluded_dirs:            # 除外ディレクトリ
    - node_modules
    - .git
    - __pycache__
  included_extensions:      # 対象拡張子
    - .py
    - .js
    - .ts
    - .md
    - .yaml
    - .json
```

## 将来の拡張予定

- **プラグインシステム**: カスタムスキャナーの追加
- **チームコラボレーション**: 結果の共有とマージ機能
- **継続的監視**: ファイル変更の自動検知と再スキャン
- **AIアシスタント統合**: 自然言語によるクエリ処理 