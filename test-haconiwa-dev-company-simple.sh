#!/bin/bash

set -e

echo "====================================="
echo "Haconiwa Dev Company 簡易テストスクリプト"
echo "====================================="
echo ""

# 1. 既存のCompanyを削除
echo "Step 1: 既存のCompanyを削除"
echo "-----------------------------------"
for company in haconiwa-dev-company kamui-dev-company jjz-dev-company; do
    if [ -d "$company" ]; then
        echo "Deleting company: $company"
        python -m haconiwa space delete -c $company --clean-dirs --force > /dev/null 2>&1
        echo "  ✓ Deleted"
    else
        echo "  - Company directory $company not found"
    fi
done
echo ""

# 2. Haconiwa Worldを適用
echo "Step 2: Haconiwa Worldを適用"
echo "-----------------------------------"
haconiwa apply -f haconiwa-world.yaml --no-attach
echo "  ✓ Applied successfully"
echo ""

# 3. tmuxセッションが作成されるまで待機
echo "Step 3: tmuxセッションの起動を待機"
echo "-----------------------------------"
sleep 3
echo "  ✓ Ready"
echo ""

# 4. Haconiwa Dev Companyのペインのカレントパスを確認（要約版）
echo "Step 4: Haconiwa Dev Companyのペインカレントパス確認"
echo "-----------------------------------"

# ウィンドウごとにペイン数とサンプルパスを表示
for window in $(tmux list-windows -t haconiwa-dev-company -F "#{window_name}" 2>/dev/null | head -5); do
    echo "ウィンドウ: $window"
    pane_count=$(tmux list-panes -t "haconiwa-dev-company:$window" 2>/dev/null | wc -l)
    echo "  ペイン数: $pane_count"
    
    # 最初の3つのペインのパスを表示
    tmux list-panes -t "haconiwa-dev-company:$window" -F "    ペイン#{pane_index}: #{pane_current_path}" 2>/dev/null | head -3
    
    if [ $pane_count -gt 3 ]; then
        echo "    ..."
    fi
    echo ""
done

# 5. タスク割り当ての要約
echo "Step 5: タスク割り当ての検証（要約）"
echo "-----------------------------------"

# タスクとassigneeのペアを抽出して表示（最初の10個）
echo "タスク割り当て状況:"
awk '
    /taskBranchName:/ {task = $2}
    /assignee:/ && task {
        gsub(/"/, "", $2)
        print "  " task " -> " $2
        task = ""
        count++
        if (count >= 10) exit
    }
' haconiwa-dev-company.yaml

# 残りのタスク数を表示
total_tasks=$(grep -c "taskBranchName:" haconiwa-dev-company.yaml)
if [ $total_tasks -gt 10 ]; then
    echo "  ... 他 $((total_tasks - 10)) タスク"
fi
echo ""

# 6. 全体の検証結果
echo "Step 6: 検証結果サマリー"
echo "-----------------------------------"

# tmuxセッションの存在確認
if tmux has-session -t haconiwa-dev-company 2>/dev/null; then
    echo "✓ tmuxセッション: 正常に作成"
    
    # ウィンドウ数を確認
    window_count=$(tmux list-windows -t haconiwa-dev-company 2>/dev/null | wc -l)
    echo "✓ ウィンドウ数: $window_count"
    
    # 総ペイン数を確認
    total_panes=$(tmux list-panes -t haconiwa-dev-company -a 2>/dev/null | wc -l)
    echo "✓ 総ペイン数: $total_panes"
else
    echo "✗ tmuxセッション: 作成失敗"
fi

# エージェント定義数を確認
agent_count=$(grep -c "agentId:" haconiwa-dev-company.yaml)
echo "✓ 定義されたエージェント数: $agent_count"

# タスク数を確認
task_count=$(grep -c "taskBranchName:" haconiwa-dev-company.yaml)
echo "✓ 定義されたタスク数: $task_count"

echo ""
echo "====================================="
echo "テスト完了"
echo "====================================="