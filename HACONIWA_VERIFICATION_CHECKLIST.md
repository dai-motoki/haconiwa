# 🔍 Haconiwa World 適用完全チェックリスト

## 1. 事前クリーンアップ
- [ ] 既存の会社ディレクトリを確認（haconiwa-dev-company, kamui-dev-company, jjz-dev-company）
- [ ] 存在する場合は `haconiwa space delete -c <company> --clean-dirs --force` で削除
- [ ] tmuxセッションが残っていないか確認
- [ ] ディレクトリが完全に削除されたか確認

## 2. haconiwa-world.yaml 適用後の確認
- [ ] `haconiwa apply -f haconiwa-world.yaml --no-attach` を実行
- [ ] 3社すべてが正常に作成されたか確認

## 3. 会社ごとのディレクトリ構造確認

### haconiwa-dev-company
- [ ] `haconiwa-dev-company/` ディレクトリが存在
- [ ] `haconiwa-dev-company/tasks/` ディレクトリが存在
- [ ] `haconiwa-dev-company/tasks/main/` ディレクトリが存在（Gitリポジトリ）
- [ ] `haconiwa-dev-company/tasks/feature/` ディレクトリが存在
- [ ] 各タスクのworktreeが作成されているか：
  - [ ] `tasks/feature/01_ai_strategy`
  - [ ] `tasks/feature/02_tech_architecture`
  - [ ] `tasks/feature/03_financial_planning`
  - [ ] `tasks/feature/04_product_roadmap`
  - [ ] `tasks/feature/05_ai_core_engine`
  - [ ] `tasks/feature/06_backend_optimization`
  - [ ] `tasks/feature/07_frontend_innovation`
  - [ ] `tasks/feature/08_devops_automation`
  - [ ] `tasks/feature/09_security_audit`
  - [ ] `tasks/feature/10_data_platform`
  - [ ] `tasks/feature/11_qa_framework`
  - [ ] `tasks/feature/12_documentation_system`
  - [ ] `tasks/feature/13_community_platform`
  - [ ] `tasks/feature/14_developer_tools`
  - [ ] `tasks/feature/15_operations_optimization`
  - [ ] `tasks/feature/16_engineering_excellence`

### kamui-dev-company
- [ ] `kamui-dev-company/` ディレクトリが存在
- [ ] `kamui-dev-company/tasks/` ディレクトリが存在
- [ ] `kamui-dev-company/tasks/main/` ディレクトリが存在（Gitリポジトリ）
- [ ] `kamui-dev-company/tasks/feature/` ディレクトリが存在
- [ ] 各タスクのworktreeが作成されているか（kamui固有のタスク）

### jjz-dev-company
- [ ] `jjz-dev-company/` ディレクトリが存在
- [ ] `jjz-dev-company/tasks/` ディレクトリが存在
- [ ] `jjz-dev-company/tasks/main/` ディレクトリが存在（Gitリポジトリ）
- [ ] `jjz-dev-company/tasks/feature/` ディレクトリが存在
- [ ] 各タスクのworktreeが作成されているか（jjz固有のタスク）

## 4. Git Worktree 確認
- [ ] `cd haconiwa-dev-company/tasks/main && git worktree list` で全worktreeをリスト
- [ ] 各worktreeが正しいブランチを参照しているか
- [ ] 各worktreeディレクトリが実際に存在するか
- [ ] kamui-dev-companyでも同様の確認
- [ ] jjz-dev-companyでも同様の確認

## 5. TMUXセッション・ペイン確認

### haconiwa-dev-company セッション
- [ ] `tmux ls` でセッションが存在することを確認
- [ ] Room 0 (Executive Room) - 16ペイン
  - [ ] CEO (ceo-motoki) → `tasks/feature/01_ai_strategy`
  - [ ] CTO (cto-yamada) → `tasks/feature/02_tech_architecture`
  - [ ] CFO (cfo-tanaka) → `tasks/feature/03_financial_planning`
  - [ ] VP Engineering (vpe-sato) → `tasks/feature/04_product_roadmap`
  - [ ] VP Product (vpp-suzuki) → `tasks/feature/05_ai_core_engine`
  - [ ] VP Operations (vpo-watanabe) → `tasks/feature/06_backend_optimization`
  - [ ] Senior AI Engineer (ai-lead-nakamura) → `tasks/feature/07_frontend_innovation`
  - [ ] Senior Backend Engineer (backend-lead-kobayashi) → `tasks/feature/08_devops_automation`
  - [ ] Senior Frontend Engineer (frontend-lead-ishii) → `tasks/feature/09_security_audit`
  - [ ] Senior DevOps Engineer (devops-lead-matsui) → `tasks/feature/10_data_platform`
  - [ ] Security Engineer (security-lead-inoue) → `tasks/feature/11_qa_framework`
  - [ ] Data Engineer (data-lead-kimura) → `tasks/feature/12_documentation_system`
  - [ ] QA Manager (qa-manager-hayashi) → `tasks/feature/13_community_platform`
  - [ ] Documentation Lead (docs-lead-yamamoto) → `tasks/feature/14_developer_tools`
  - [ ] Community Manager (community-ito) → `tasks/feature/15_operations_optimization`
  - [ ] Platform Engineer (platform-kato) → `tasks/feature/16_engineering_excellence`
- [ ] Room 1 (Standby Room) - 16ペイン
  - [ ] 全員が `standby/` ディレクトリにいることを確認

### kamui-dev-company セッション
- [ ] 同様の確認（kamui固有のタスク割り当て）

### jjz-dev-company セッション
- [ ] 同様の確認（jjz固有のタスク割り当て）

## 6. エージェント割り当てログ確認
- [ ] 各タスクディレクトリの `.haconiwa/agent_assignment.json` が存在
- [ ] 各タスクディレクトリの `.haconiwa/README.md` が存在
- [ ] 正しいエージェントIDとタスク情報が記録されているか
- [ ] tmuxウィンドウ・ペイン情報が記録されているか

## 7. Claude Code設定確認
- [ ] 各タスクディレクトリの `.claude/settings.local.json` が存在
- [ ] 各タスクディレクトリの `CLAUDE.md` が存在
- [ ] 設定内容が正しくコピーされているか

## 8. 機能テスト
- [ ] `haconiwa space attach -c haconiwa-dev-company -r room-executive` でアタッチ可能か
- [ ] 各ペインで `pwd` を実行して正しいディレクトリにいるか確認
- [ ] 各タスクディレクトリで `git branch` を実行して正しいブランチか確認
- [ ] 各タスクディレクトリで `git status` を実行してクリーンな状態か確認

## 9. 後処理フェーズの確認
- [ ] 「後処理フェーズ」が実行されたか
- [ ] タスク割り当てテーブルが表示されたか
- [ ] エージェントペインの更新が実行されたか
- [ ] 更新されたペイン数が表示されたか

## 実行コマンド例と実際のテスト結果

```bash
# 1. クリーンアップ
for company in haconiwa-dev-company kamui-dev-company jjz-dev-company; do
    python -m haconiwa space delete -c $company --clean-dirs --force
done

# 2. 適用
python -m haconiwa apply -f haconiwa-world.yaml --no-attach

# 3. ディレクトリ確認
ls -la haconiwa-dev-company/tasks/
ls -la haconiwa-dev-company/tasks/feature/

# 4. Worktree確認
cd haconiwa-dev-company/tasks/main && git worktree list

# 5. TMUXペイン確認
tmux list-panes -t haconiwa-dev-company:0 -F "#{pane_index}: #{pane_current_path}"
tmux list-panes -t haconiwa-dev-company:1 -F "#{pane_index}: #{pane_current_path}"

# 6. エージェント割り当て確認
cat haconiwa-dev-company/tasks/feature/01_ai_strategy/.haconiwa/agent_assignment.json
```

## 実際のテストコマンドと結果

### 1. 現在の状態確認
```bash
pwd && ls -la
# 結果: /Users/motokidaisuke/haconiwa で3つの会社ディレクトリが存在
```

### 2. タスクディレクトリ構造確認
```bash
ls -la haconiwa-dev-company/tasks/feature/01_ai_strategy/
# 結果: 58個のファイル/ディレクトリ（Gitリポジトリの全ファイルがコピーされている）
```

### 3. Git Worktree確認
```bash
cd haconiwa-dev-company/tasks/main && git worktree list
# 結果: 
# /Users/motokidaisuke/haconiwa/haconiwa-dev-company/tasks/main                                b407c99 [dev]
# /Users/motokidaisuke/haconiwa/haconiwa-dev-company/tasks/feature/01_ai_strategy              b407c99 [feature/01_ai_strategy]
# ... (全16個のfeatureタスクが正しく作成されている)
```

### 4. TMUXセッション確認
```bash
tmux list-windows -t haconiwa-dev-company:0 -F "#W: #P panes"
# 結果:
# Executive: 14 panes
# Standby: 14 panes
```

### 5. エージェントの現在ディレクトリ確認
```bash
tmux display-message -t haconiwa-dev-company:0.0 -p "#{pane_current_path}"
# 結果: /Users/motokidaisuke/haconiwa/haconiwa-dev-company/tasks/feature/01_ai_strategy
```

### 6. CLAUDE.md確認
```bash
cat haconiwa-dev-company/tasks/feature/01_ai_strategy/CLAUDE.md
# 結果: No such file or directory（featureブランチにはコピーされていない）

cat haconiwa-dev-company/tasks/main/CLAUDE.md
# 結果: 正しいCLAUDE.mdが存在
```

### 7. エージェント割り当てファイル確認
```bash
find haconiwa-dev-company -name "agent_assignment.json" -type f
# 結果: ファイルが見つからない（.haconiwaディレクトリが作成されていない）
```

### 8. featureディレクトリ一覧
```bash
ls -la haconiwa-dev-company/tasks/feature/ | head -10
# 結果: 16個のタスクディレクトリすべてが正しく作成されている
```

## 結果記録欄

### 実行日時: _______________

### 実行者: _______________

### 結果サマリ:
- [ ] すべてのチェック項目がパス
- [ ] 問題があった項目: _______________

### 備考:
_______________________________________________
_______________________________________________
_______________________________________________