# Claude Code Settings for Haconiwa Project

## Important Guidelines

### 【最重要】音声通知必須ルール
**すべてのタスク完了時は必ず音声通知を実行してください。例外はありません。**

- **ルール**: どんなタスクでも、作業完了後は必ずTTS音声通知を出すこと
- **理由**: ユーザーがタスク完了に気付くのが遅れることを防ぐため
- **実行方法**: `python voice-systems/gemini-tts/quick_tts_test.py "完了メッセージ"`
- **通知内容**: 何の作業を完了したかを具体的に説明すること
- **必須事項**: この音声通知を忘れることは絶対に許されません

```bash
# 例：ファイル編集完了時
python voice-systems/gemini-tts/quick_tts_test.py "ファイル編集が完了しました"

# 例：ビルド完了時  
python voice-systems/gemini-tts/quick_tts_test.py "パッケージのビルドが完了しました"

# 例：調査完了時
python voice-systems/gemini-tts/quick_tts_test.py "調査が完了し、問題の原因を特定しました"
```

### 【重要】エラー発生時の説明ルール
**エラーが発生した場合は、必ずエラーの原因と対処法を詳しく説明してください。**

- **ルール**: エラーメッセージを確認し、根本原因を分析して説明すること
- **説明内容**: 
  - 何が原因でエラーが発生したのか
  - どのような依存関係や設定が不足しているのか
  - 問題解決のための具体的な手順
- **音声通知**: エラー内容と解決策も音声で説明すること

```bash
# 例：依存関係エラーの場合
python voice-systems/gemini-tts/quick_tts_test.py "cryptographyパッケージが不足しているため、haconiwaコマンドが実行できませんでした。pyproject.tomlに依存関係を追加して修正します"

# 例：設定エラーの場合
python voice-systems/gemini-tts/quick_tts_test.py "設定ファイルが見つからないエラーです。指定されたパスに設定ファイルを作成する必要があります"
```

### 【必須】Gitプッシュ前のブランチ戦略確認
**Gitプッシュする前に、必ずブランチ戦略とCI/CD設定を確認してください。**

- **確認ファイル**: [`docs/DEVELOPMENT_STRATEGY.md`](docs/DEVELOPMENT_STRATEGY.md)
- **確認事項**: 
  - 現在のブランチが適切なCI/CDワークフローを使用しているか
  - インストール方法（`pip install -e .` vs `pip install haconiwa==x.x.x`）が正しいか
  - バージョン更新が必要な場合は `scripts/bump_version.py` を使用したか
- **重要**: ブランチ別の戦略に従わないと、CI/CDが失敗する可能性があります

### Path References
- **NEVER use full paths** in documentation or code comments
- Use relative paths or descriptive references instead
- Bad: `/Users/username/project/haconiwa/src/file.py`
- Good: `src/file.py` or `haconiwa/src/file.py`

### Code Development Guidelines
- **絶対にフルパスのハードコーディングをしない**
  - NG: `/Users/username/project/...`
  - OK: `Path.cwd()`, `Path(__file__).parent`, 相対パス
- **ハードコーディングは基本的に避ける**
  - 設定値は設定ファイルや環境変数から取得
  - マジックナンバーは定数として定義
  - 固定値の代わりに動的な計算や設定を使用

## Available Commands

### Haconiwa Apply Commands

#### Haconiwa Apply
```bash
# Haconiwa Dev Company
haconiwa apply -f haconiwa-dev-company.yaml --no-attach

# KAMUI Dev Company  
haconiwa apply -f kamui-dev-company.yaml --no-attach
```

**使用場面**:
- 「Haconiwa apply」「HaconiwaのApply」→ `haconiwa-dev-company.yaml`
- 「KAMUI apply」「KAMUIのApply」→ `kamui-dev-company.yaml`
- アタッチしない方が安全なため `--no-attach` を推奨

### タスクブランチ命名規則

**基本方針**: スラッシュ形式 + 番号 + スネークケース

**推奨形式**: `category/00_task_name`
- `feature/01_user_authentication`
- `bugfix/02_login_validation`
- `hotfix/03_security_patch`

**カテゴリ**: feature, bugfix, hotfix, enhancement, refactor, docs, test, perf

### ripgrep (rg)
Fast file content search tool:
- **Use `rg` command directly** (not `~/bin/rg` or other paths)
- If `rg` is not available, ask user to install it via:
  ```bash
  brew install ripgrep  # macOS
  # or
  apt install ripgrep   # Ubuntu/Debian
  ```

Example usage:
```bash
rg "search_pattern" /path/to/search
rg "function_name" src/ -A5 -B5
```

## Creating Pull Requests

When creating a pull request, always open it in the web browser:

gh pr create --base <target-branch> --title "title" --body "description"
gh pr view <PR-number> --web  # Automatically open in browser

```

## Lint and Type Check Commands

When making code changes, always run:
```bash
# Python linting
ruff check src/

# Type checking
mypy src/
```

## セキュリティチェック

### 【必須】コミット前セキュリティチェック
**すべてのGitコミット前に、必ずセキュリティチェックツールを実行してください。**

```bash
# セキュリティチェック実行（必須）
python tools/security-check/commit_security_check.py

# 問題なければコミット
git commit -m "コミットメッセージ"
```

### チェック項目
- **フルパス**: `/Users/username/` などの個人パス
- **APIキー・トークン**: 実際のAPIキーやアクセストークン
- **パスワード**: ハードコードされたパスワード
- **機密ファイル**: `.env`, 秘密鍵ファイルなど
- **環境変数ハードコーディング**: `.env`ファイルの値がコードに直接記述されていないか
- **プライベートURL**: `localhost`, プライベートIPアドレス
- **実在メールアドレス**: テスト用以外のメールアドレス

### 自動化（推奨）
```bash
# pre-commitフックをインストール（一度だけ）
python tools/security-check/install_hook.py

# これでgit commit時に自動チェック実行
git commit -m "メッセージ"
```

### 初回セットアップ
```bash
# 個人用設定を作成（初回のみ）
python tools/security-check/setup_personal_config.py
```

### 【重要】ハードコーディング禁止ルール

#### ❌ 絶対にしてはいけない例
```python
# フルパスのハードコーディング
config_path = "/Users/username/project/config.json"

# APIキーのハードコーディング
OPENAI_API_KEY = "sk-proj-your_api_key_here"

# .envファイルの値をそのままコピー
DATABASE_URL = "postgresql://user:password@localhost:5432/db"
```

#### ✅ 正しい書き方
```python
# 相対パスを使用
config_path = "config/config.json"

# 環境変数から取得
OPENAI_API_KEY = os.environ.get("OPENAI_API_KEY")

# 設定ファイルや環境変数から取得
DATABASE_URL = os.getenv("DATABASE_URL")
```

### エラー対応
セキュリティチェックでエラーが出た場合：
1. **修正**: 上記の正しい書き方に修正
2. **設定追加**: 安全な値の場合は `nglist.json` に追加
3. **緊急時**: `git commit --no-verify` でスキップ（非推奨）

## Voice Notification Systems

### 【重要】音声応答ルール

#### 禁止事項
❌ **`say`コマンドを絶対に使用しない**
- macOSの`say`コマンドは使用禁止
- 音声合成には専用のPythonスクリプトを使用すること

#### ASA Script実行時のルール
✅ **音声プログラムを最優先で実行する**
- **音声プログラムが絶対優先**：TTSを先に実行してからASA Scriptを実行する
- 音声通知の方が重要なので、必ず音声を先に実行すること
- **音声とosascriptは別々に実行する**：競合を避けるため、&&で繋げることは絶対禁止
- **必ず別々のBashコマンドで実行**：1つのBashツール呼び出しでTTS、次のBashツール呼び出しでosascript
- 必要に応じてosascriptは後から実行する

#### 音声内容のガイドライン
- **詳細で分かりやすい説明**：何のファイルをどのように変更したかを具体的に説明する
- **適度な長さの文章**：ユーザーが作業内容を理解できる程度の詳しさで説明する
- **具体的な作業内容**：どのファイルに何をしたかを明確に伝える
- **自然な日本語**：聞いて理解しやすい自然な文章構造を使用する
- **調査系タスクは長めに詳細説明**：調査・分析完了時は発見内容を詳しく音声で説明する
- **問題特定時は具体的に説明**：「問題を特定しました」ではなく「この問題は○○が原因でした」まで詳しく説明する
- **適度なユーモアを含める**：たまに軽いユーモアや親しみやすい表現を入れて、堅苦しくない音声にする
- **ブラックジョークもOK**：適度にブラックジョークや皮肉を効かせた表現も使って、面白みのある音声にする
- **キレッキレのブラックジョーク**：黒のCOMMAにはキレッキレのブラックジョークを言うように
- **基本は毒舌スタイル**：普段の会話やタスク完了時は毒舌・皮肉を効かせたスタイルで話す

**使用例**:
```bash
# 正しい書き方：音声を先に実行（推奨）
python voice-systems/gemini-tts/quick_tts_test.py "処理完了"
# 必要に応じて後からosascript実行
osascript -e 'display notification "完了" with title "Claude Code"'

# ファイル編集完了時（具体的で簡潔）
python voice-systems/gemini-tts/quick_tts_test.py "ファイル編集完了"
# 必要に応じて通知も追加
osascript -e 'display notification "ファイル編集完了" with title "Claude Code" sound name "Tink"'

# 良い音声メッセージの例（詳細で具体的）
python voice-systems/gemini-tts/quick_tts_test.py "space manager と organization manager ファイルの英語ログメッセージをすべて日本語に変換し、ウィンドウを部屋、ペインをデスクに用語統一しました"
python voice-systems/gemini-tts/quick_tts_test.py "タスクブランチ割り当てテーブルのヘッダーをTask、Room、Role、Agentからタスクブランチ、ルーム、役職、エージェントに日本語化しました"  
python voice-systems/gemini-tts/quick_tts_test.py "applier.py ファイルのリソースという表記を設定に変更し、INFO ログメッセージを日本語に翻訳しました"
python voice-systems/gemini-tts/quick_tts_test.py "Haconiwa apply コマンドの出力を完全に日本語化し、世界観に合わせた表現に統一しました"
```

**禁止**:
```bash
# ❌ osascriptを先に実行（音声優先でない）
osascript -e '...' && python voice-systems/gemini-tts/quick_tts_test.py "..."

# ❌ &&で連結実行（音声システムが競合する可能性）
python voice-systems/gemini-tts/quick_tts_test.py "..." && osascript -e '...'

# ❌ 1つのBashコマンドで両方実行（絶対禁止）
Bash(osascript -e '...' && python voice-systems/gemini-tts/quick_tts_test.py "...")
```

**正しい実行方法**:
```bash
# ✅ 1つ目のBashコマンド：音声を先に実行
Bash(python voice-systems/gemini-tts/quick_tts_test.py "処理完了")

# ✅ 2つ目のBashコマンド：必要に応じてosascript実行
Bash(osascript -e 'display notification "完了" with title "Claude Code" sound name "Tink"')
```

### 状況別TTS使い分けルール

#### OpenAI Realtime API (簡単な対話・即座の応答用)
Located in `voice-systems/openai-realtime/`

**使用場面**:
- 簡単な質問への回答
- 即座に返答できる内容
- 短時間での応答
- 対話的なやり取り

**Main file**: `openai_realtime_test.py`
- Ultra-fast speech synthesis using Shimmer voice
- 50% volume reduction
- Optimized for quick responses
- Handles audio streaming with error recovery

**Usage**:
```bash
python voice-systems/openai-realtime/openai_realtime_test.py "Text to read aloud"
```

#### Gemini TTS (複雑なタスクブランチ・処理完了通知用)
Located in `voice-systems/gemini-tts/`

**使用場面**:
- ファイル作成・編集完了
- 複数ステップの処理完了
- 長時間処理の完了通知
- 複雑なタスクブランチの完了報告

**Files**:
- `voice_notification.py`: Original Gemini TTS implementation
- `quick_tts_test.py`: Quick testing utility (PREFERRED for task completion notifications)

**Usage**:
```bash
python voice-systems/gemini-tts/quick_tts_test.py "ファイル編集完了"
python voice-systems/gemini-tts/quick_tts_test.py "ビルド完了"
python voice-systems/gemini-tts/quick_tts_test.py "テスト実行完了"
```

### Experimental Systems
Located in `voice-systems/experimental/`

Contains various experimental implementations:
- Gemini Live API variants
- Streaming TTS implementations
- Alternative voice synthesis approaches

## Command Permission System
Located in `voice-systems/command-permission/`

### 【必須】コマンド実行ルール
**すべてのBashコマンド実行前に、必ずコマンド許可システムを使用してください。**

#### 高機能版（音声認識対応）【推奨】
```bash
python voice-systems/command-permission/command_permission.py "<コマンド>" "<分かりやすい日本語説明>"
```

#### シンプル版
```bash
python voice-systems/command-permission/simple_command_permission.py "<コマンド>" "<分かりやすい日本語説明>"
```

**例外なく、このシステムを経由してからClaude CodeのBashツールを使用すること。**

### 新機能: 実行方法選択
コマンド許可システムが以下の選択肢を提供します：

1. **[P] Python実行** - スクリプト内で直接コマンドを実行
   - 即座に実行・結果確認
   - 音声での完了通知
   - エラー時の音声フィードバック

2. **[C] Claude実行** - Claude Codeで実行（従来通り）
   - Claude Codeのツールで実行
   - より安全な環境での実行

3. **[N] 実行しない** - キャンセル
   - コマンド実行を中止

### 使用方法
Claude Codeの `.claude/settings.local.json` のホワイトリスト設定を自動で読み取り、コマンド実行前に通知・音声確認を行います。

### システムの動作
1. **ホワイトリストチェック**: 設定ファイルの許可コマンドを確認
2. **安全なコマンド**: Tink音の軽い通知のみ
3. **危険なコマンド**: Sosumi警告音 + Gemini Flash TTS音声確認
4. **実行**: Claude CodeのBashツールで実際に実行

### 使用例とワークフロー

#### 安全なコマンド（ホワイトリスト内）
```bash
python command_permission.py "git status" "Git状態確認"
python command_permission.py "ls -la" "ファイル一覧表示"
```
→ 軽い通知音のみで許可済みを表示

#### 危険なコマンド（ホワイトリスト外）
```bash
python voice-systems/command-permission/command_permission.py "rm -rf old_files" "古いファイルの削除"
python voice-systems/command-permission/command_permission.py "npm install express" "Expressパッケージのインストール"
python voice-systems/command-permission/command_permission.py "git push origin main" "メインブランチへのプッシュ"
python voice-systems/command-permission/command_permission.py "mkdir -p backup" "バックアップディレクトリの作成"
```
→ 警告音 + 音声「ホワイトリストにございません。[説明]を実行しますか？」

#### Claude Codeでの実際の実行
コマンド許可チェック後、Claude CodeのBashツールで実行：
```
Bash(rm -rf old_files)
⎿ Running...

Bash(npm install express)
⎿ Running...

Bash(mkdir -p backup)
⎿ Running...
```

### 第二引数の書き方
第二引数には**そのまま音声で読み上げられる日本語説明**を記述してください：

#### 良い例
- `"古いファイルの削除"`
- `"Expressパッケージのインストール"`
- `"データベースのバックアップ作成"`
- `"ログファイルの圧縮"`
- `"開発サーバーの再起動"`

#### 避けるべき例
- `"rm -rf old_files実行"` （技術的すぎる）
- `"ファイル削除コマンド"` （曖昧）
- `"dangerous operation"` （英語）

### 【厳守】実行フロー
1. **必須**: `python voice-systems/command-permission/command_permission.py "コマンド" "説明"` でチェック
2. ホワイトリスト外なら音声確認を待つ
3. **その後**: Claude CodeのBashツールで実際のコマンド実行
4. 完了

### 重要な注意事項
- **Claude Codeで直接Bashコマンドを実行することは禁止**
- **必ずコマンド許可システムを先に実行すること**
- **このルールに例外はありません**

この手順により、安全性を確保しながら効率的にコマンド実行が可能です。

### 禁止事項
❌ 直接 `Bash(tree voice-systems)` のような実行
❌ コマンド許可システムをスキップした実行
❌ 「緊急だから」という理由でのルール無視

✅ 正しい手順:
1. `python voice-systems/command-permission/command_permission.py "tree voice-systems" "ディレクトリ構造の確認"`
2. 音声確認完了後、`Bash(tree voice-systems)` 実行

## 推奨ワークフロー

### 1. 開発時の基本フロー
```bash
# ファイル編集
vim src/main.py

# セキュリティチェック
python tools/security-check/commit_security_check.py

# 問題なければステージング・コミット
git add .
git commit -m "feat: 新機能追加"
```

### 2. コミット前チェックリスト
- [ ] セキュリティチェック実行
- [ ] Lintエラーなし（該当する場合）
- [ ] テスト通過（該当する場合）
- [ ] 機密情報のハードコーディングなし
- [ ] フルパスの記述なし

### 3. CI/CD環境での使用
```bash
# CI環境用（非対話モード）
python tools/security-check/commit_security_check.py --ci
```

## Claude Code アップデート

Claude Codeのアップデートが必要な場合は、以下のコマンドを実行してください：

```bash
cd ~/.claude/local && npm update @anthropic-ai/claude-code && cd -
```

このコマンドは：
1. Claude Codeのローカルディレクトリに移動
2. Claude Codeパッケージを最新版に更新
3. 元のディレクトリに戻る