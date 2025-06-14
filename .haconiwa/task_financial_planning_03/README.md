# エージェント割り当て情報

## 基本情報
- **エージェントID**: `cfo-tanaka`
- **タスク名**: `task_financial_planning_03`
- **割り当て日時**: 2025-06-14T18:33:03.010894
- **ステータス**: active

## 環境情報
- **スペースセッション**: `haconiwa-dev-company`
- **tmuxウィンドウ**: None
- **tmuxペイン**: None
- **タスクディレクトリ**: `haconiwa-dev-world/tasks/task_financial_planning_03`

## エージェント役割
**役割**: 未定義

## このディレクトリについて
このディレクトリは、GitのWorktree機能を使用して作成された専用の作業ディレクトリです。
このエージェント専用のブランチで作業を行い、他のエージェントとは独立した開発環境を提供します。

## ログファイル
- `agent_assignment.json`: 割り当て履歴のJSON形式ログ
- `README.md`: この説明ファイル

---

# AICodeConfig CRD 最小限実装仕様

## 実装範囲

### 今回実装する機能（最小限）

1. **AICodeConfig CRD**
   - 新しいCRD `AICodeConfig` の追加
   - プロバイダーは `claude` のみサポート
   - カンパニー全体への一括適用のみ

2. **ファイル参照方式**
   - `settingsFile`: settings.local.json ファイルパスの指定
   - `guidelinesFile`: CLAUDE.md ファイルパスの指定
   - YAMLに直接内容を記述する機能は実装しない

3. **適用範囲**
   - `targetCompany` で指定したカンパニー内の全タスクに適用
   - 階層構造（Room、役職、タスク単位）での適用は実装しない

4. **ファイル配置**
   - 各タスクディレクトリの `.claude/settings.local.json` に配置
   - 各タスクディレクトリの `CLAUDE.md` に配置

## YAML仕様

```yaml
apiVersion: haconiwa.dev/v1
kind: AICodeConfig
metadata:
  name: ai-config-claude-default
spec:
  # プロバイダー（claudeのみ）
  provider: "claude"
  
  # Claude設定
  claude:
    settingsFile: "./claude-settings/settings.local.json"
    guidelinesFile: "./claude-settings/CLAUDE.md"
  
  # 適用対象（カンパニー名）
  targetCompany: "kamui-dev-company"
```

## 実装ファイル

1. **モデル定義**
   - `src/haconiwa/core/crd/models.py` に `AICodeConfigCRD` を追加

2. **パーサー**
   - `src/haconiwa/core/crd/parser.py` に AICodeConfig のパース処理を追加

3. **Applier**
   - `src/haconiwa/core/applier.py` に `_apply_aicode_config_crd` メソッドを追加

4. **TaskManager**
   - 既存の worktree 作成時にAICodeConfig設定をコピーする処理を追加

## テスト手順

1. テスト用ファイルの準備
   ```bash
   mkdir -p ./claude-settings
   echo '{"permissions":{"allow":["Read(*)","Edit(*)","Bash(ls:*)"],"deny":[]}}' > ./claude-settings/settings.local.json
   echo '# Claude Code Guidelines\n\n基本的なコーディング規約に従ってください。' > ./claude-settings/CLAUDE.md
   ```

2. テスト用YAMLの作成
   ```yaml
   # test-aicode.yaml
   ---
   apiVersion: haconiwa.dev/v1
   kind: AICodeConfig
   metadata:
     name: test-claude-config
   spec:
     provider: "claude"
     claude:
       settingsFile: "./claude-settings/settings.local.json"
       guidelinesFile: "./claude-settings/CLAUDE.md"
     targetCompany: "kamui-dev-company"
   
   ---
   apiVersion: haconiwa.dev/v1
   kind: Space
   metadata:
     name: kamui-dev-world
   spec:
     nations:
       - id: jp
         cities:
           - id: tokyo
             villages:
               - id: kamui-village
                 companies:
                   - name: kamui-dev-company
                     gitRepo:
                       url: "https://github.com/dai-motoki/haconiwa"
                       defaultBranch: "main"
   
   ---
   apiVersion: haconiwa.dev/v1
   kind: Task
   metadata:
     name: task_test_01
   spec:
     branch: "test/aicode-config"
     worktree: true
     assignee: "test-agent"
     spaceRef: "kamui-dev-company"
   ```

3. 適用とテスト
   ```bash
   # 適用
   haconiwa apply -f test-aicode.yaml --no-attach
   
   # 確認
   ls -la ./kamui-dev-world/tasks/task_test_01/.claude/
   cat ./kamui-dev-world/tasks/task_test_01/.claude/settings.local.json
   cat ./kamui-dev-world/tasks/task_test_01/CLAUDE.md
   
   # クリーンアップ
   haconiwa space delete -c kamui-dev-company --clean-dirs
   ```

## 実装しない機能（将来実装）

- 他のAIプロバイダー（copilot、cursor、codeium）
- 階層構造での適用（Room単位、役職単位、タスク単位）
- YAML内での設定内容の直接記述
- 複数AICodeConfigの優先順位処理
- テンプレート変数の展開
- 環境変数の参照

## 成功基準

1. AICodeConfig CRDが正しくパースされる
2. 指定したカンパニーの全タスクに設定ファイルがコピーされる
3. `.claude/settings.local.json` が正しい場所に配置される
4. `CLAUDE.md` が正しい場所に配置される

---
*このファイルは Haconiwa v1.0 によって自動生成されました*
