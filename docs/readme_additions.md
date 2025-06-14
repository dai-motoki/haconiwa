# README_JA.md 追加内容

## コマンドリファレンスセクションに追加

### `claude` - Claude Code SDK並列実行コマンド 🚧 **開発中**
Claude Code SDKを使用した高速並列ファイル編集機能
- `haconiwa claude parallel` - 複数ファイルの並列編集実行
- `haconiwa claude parallel --from-yaml <file>` - YAML設定からの並列実行
- `haconiwa claude status` - 実行中タスクの状態確認
- `haconiwa claude cancel <task-id>` - 実行中タスクのキャンセル

**主な機能:**
- 🚀 **高速並列処理**: 最大10ファイルの同時編集
- 📝 **柔軟なプロンプト指定**: ファイルごとに個別のプロンプト
- 🎯 **セマフォ制御**: 同時実行数の制限でAPI負荷を管理
- 📊 **リアルタイム進捗表示**: 処理状況の可視化
- 🔧 **エラーハンドリング**: 個別失敗でも他タスクは継続

**使用例:**
```bash
# 基本的な並列編集（3ファイル）
haconiwa claude parallel \
  --files src/main.py,src/utils.py,src/api.py \
  --prompts "Add type hints","Refactor functions","Add error handling"

# 10ファイルの一斉修正
haconiwa claude parallel \
  --file-list files.txt \
  --prompt-file prompts.txt \
  --max-concurrent 5 \
  --timeout 120

# YAML設定ファイルから実行
haconiwa claude parallel --from-yaml parallel-edits.yaml
```

## 開発中機能セクションに追加

### 🚧 開発中機能
- AIエージェントの生成と管理 (プレースホルダー → 実装)
- git-worktreeとのタスク管理 (プレースホルダー → 実装)
- リソーススキャン機能 (プレースホルダー → 実装)
- リアルタイム監視システム (プレースホルダー → 実装)
- ワールド/環境管理 (プレースホルダー → 実装)
- **🆕 Claude Code SDK並列実行機能** (設計 → 実装中)
  - 複数ファイルの並列編集
  - asyncio.gatherによる高速処理
  - 柔軟なプロンプト管理
  - エラーハンドリングと進捗表示

## 主な機能セクションに追加

- 🤖 **AIエージェント管理**: Boss/Workerエージェントの作成・監視
- 📦 **ワールド管理**: 開発環境の構築・管理
- 🖥️ **tmux会社連携**: 開発スペースの効率的な管理
- 📋 **タスク管理**: git-worktreeと連携したタスク管理システム
- 📊 **リソース管理**: DBやファイルパスの効率的なスキャン
- 👁️ **リアルタイム監視**: エージェントやタスクの進捗監視
- **🚀 Claude Code SDK並列実行**: 最大10ファイルの同時編集による高速開発支援（開発中）