#!/bin/bash
# haconiwa の包括的なシナリオテスト: apply -> verify -> cleanup

set -euo pipefail

# 出力用の色定義
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # 色なし

# テスト設定
YAML_FILE="${1:-test-multiroom-with-tasks.yaml}"
SESSION_NAME="${2:-test-company-multiroom-tasks}"
CLEANUP="${3:-true}"

echo -e "${BLUE}🚀 シナリオテスト開始: ${YAML_FILE}${NC}"
echo "============================================================"

# ステップを表示する関数
print_step() {
    echo -e "\n${YELLOW}$1${NC}"
}

# コマンドの実行結果をチェックする関数
check_result() {
    if [ $? -eq 0 ]; then
        echo -e "${GREEN}✅ $1${NC}"
        return 0
    else
        echo -e "${RED}❌ $1${NC}"
        return 1
    fi
}

# テストの成功状態を追跡
TEST_PASSED=true

# ステップ1: YAML適用
print_step "📋 ステップ1: YAML設定ファイルの適用"
if haconiwa apply -f "$YAML_FILE" --no-attach; then
    check_result "YAMLの適用に成功しました"
else
    check_result "YAMLの適用に失敗しました"
    TEST_PASSED=false
    exit 1
fi

# ステップ2: セッションの準備待機
print_step "⏳ ステップ2: セッションの準備を待機中..."
TIMEOUT=30
ELAPSED=0
while [ $ELAPSED -lt $TIMEOUT ]; do
    if tmux has-session -t "$SESSION_NAME" 2>/dev/null; then
        check_result "セッション '$SESSION_NAME' の準備が完了しました"
        sleep 2  # 完全に初期化されるまで少し待つ
        break
    fi
    sleep 1
    ELAPSED=$((ELAPSED + 1))
done

if [ $ELAPSED -ge $TIMEOUT ]; then
    echo -e "${RED}❌ セッション待機がタイムアウトしました${NC}"
    TEST_PASSED=false
    exit 1
fi

# ステップ3: ウィンドウとペインの検証
print_step "🔍 ステップ3: ウィンドウとペインの検証"
WINDOW_COUNT=$(tmux list-windows -t "$SESSION_NAME" 2>/dev/null | wc -l)
# 各ウィンドウのペイン数を合計して正確にカウント
TOTAL_PANES=0
for window in $(tmux list-windows -t "$SESSION_NAME" -F '#{window_index}' 2>/dev/null); do
    WINDOW_PANES=$(tmux list-panes -t "$SESSION_NAME:$window" 2>/dev/null | wc -l)
    TOTAL_PANES=$((TOTAL_PANES + WINDOW_PANES))
done

echo "   ウィンドウ数: $WINDOW_COUNT"
echo "   総ペイン数: $TOTAL_PANES"

# カウントの検証
if [ "$WINDOW_COUNT" -eq 2 ] && [ "$TOTAL_PANES" -eq 32 ]; then
    check_result "ウィンドウとペインの数が正しいです"
else
    check_result "ウィンドウ/ペインの数が不正です (期待値: 2ウィンドウ、32ペイン)"
    TEST_PASSED=false
fi

# ステップ4: ペインタイトルの検証
print_step "🔍 ステップ4: ペインタイトルの検証"
# タイトル付きペインを正確にカウント
PANES_WITH_TITLES=0
for window in $(tmux list-windows -t "$SESSION_NAME" -F '#{window_index}' 2>/dev/null); do
    WINDOW_TITLED=$(tmux list-panes -t "$SESSION_NAME:$window" -F '#{pane_title}' 2>/dev/null | grep -v '^tmux$' | grep -v '^$' | wc -l)
    PANES_WITH_TITLES=$((PANES_WITH_TITLES + WINDOW_TITLED))
done
echo "   タイトル付きペイン数: $PANES_WITH_TITLES/$TOTAL_PANES"

if [ "$PANES_WITH_TITLES" -gt 0 ]; then
    check_result "ペインタイトルが確認できました"
else
    check_result "ペインタイトルが見つかりません"
    TEST_PASSED=false
fi

# ステップ5: タスク割り当ての検証
print_step "🔍 ステップ5: タスク割り当ての検証"
# Space CRDの仕様に基づいてタスクディレクトリが作成される
TASK_DIR="./test-world-multiroom-tasks/tasks"
if [ -d "$TASK_DIR" ]; then
    ASSIGNMENT_COUNT=$(find "$TASK_DIR" -name "agent_assignment.json" 2>/dev/null | wc -l)
    echo "   タスク割り当て数: $ASSIGNMENT_COUNT"
    
    if [ "$ASSIGNMENT_COUNT" -gt 0 ]; then
        check_result "タスク割り当てが確認できました"
        
        # サンプル割り当てを表示
        echo "   割り当ての例:"
        find "$TASK_DIR" -name "agent_assignment.json" -exec sh -c '
            TASK=$(dirname $(dirname "$1") | xargs basename)
            AGENT=$(jq -r ".[0].agent_id" "$1" 2>/dev/null)
            if [ ! -z "$AGENT" ]; then
                echo "     $AGENT -> $TASK"
            fi
        ' _ {} \; | head -3
    else
        check_result "タスク割り当てが見つかりません"
        TEST_PASSED=false
    fi
else
    echo "   タスクディレクトリが見つかりません"
    TEST_PASSED=false
fi

# ステップ6: ペインの作業ディレクトリ検証
print_step "🔍 ステップ6: ペインの作業ディレクトリ検証"
# タスク/スタンバイディレクトリのペインを正確にカウント
PANES_IN_TASKS=0
PANES_IN_STANDBY=0
for window in $(tmux list-windows -t "$SESSION_NAME" -F '#{window_index}' 2>/dev/null); do
    WINDOW_TASKS=$(tmux list-panes -t "$SESSION_NAME:$window" -F '#{pane_current_path}' 2>/dev/null | grep -c "/tasks/" || true)
    WINDOW_STANDBY=$(tmux list-panes -t "$SESSION_NAME:$window" -F '#{pane_current_path}' 2>/dev/null | grep -c "standby" || true)
    PANES_IN_TASKS=$((PANES_IN_TASKS + WINDOW_TASKS))
    PANES_IN_STANDBY=$((PANES_IN_STANDBY + WINDOW_STANDBY))
done

echo "   タスクディレクトリのペイン数: $PANES_IN_TASKS"
echo "   スタンバイディレクトリのペイン数: $PANES_IN_STANDBY"

if [ "$PANES_IN_TASKS" -gt 0 ] || [ "$PANES_IN_STANDBY" -gt 0 ]; then
    check_result "ペインディレクトリが設定されています"
else
    check_result "ペインが期待されるディレクトリにいません"
    TEST_PASSED=false
fi

# ステップ7: claudeコマンド実行の検証
print_step "🔍 ステップ7: claudeコマンド実行の確認"
# 直接検証は難しいが、ペインの内容から証拠を確認できる
echo "   ペインの内容からclaude実行の証拠を検索中..."
CLAUDE_EVIDENCE=$(tmux capture-pane -t "$SESSION_NAME:0.0" -p 2>/dev/null | grep -c "claude" || true)

if [ "$CLAUDE_EVIDENCE" -gt 0 ]; then
    check_result "claudeコマンドの実行証拠が確認できました"
else
    echo -e "${YELLOW}⚠️  直接的なclaude実行の証拠はありません (正常な場合があります)${NC}"
fi

# ステップ8: クリーンアップ (指定された場合)
if [ "$CLEANUP" = "true" ]; then
    print_step "🧹 ステップ8: haconiwaコマンドでクリーンアップ"
    
    # haconiwa space deleteコマンドを使用
    if haconiwa space delete -c "$SESSION_NAME" --clean-dirs --force; then
        check_result "haconiwaコマンドでクリーンアップしました"
    else
        echo -e "${YELLOW}⚠️  haconiwaクリーンアップが失敗、手動クリーンアップを試行${NC}"
        
        # tmuxセッションを手動で終了
        if tmux kill-session -t "$SESSION_NAME" 2>/dev/null; then
            echo -e "${GREEN}✅ tmuxセッションを手動で終了しました${NC}"
        fi
        
        # ディレクトリを手動でクリーンアップ
        DIRS_TO_CLEAN=(
            "./${SESSION_NAME}"
            "./${SESSION_NAME}-desks"
            "./test-world-multiroom-tasks"
            "./test-multiroom-desks"
        )
        
        for dir in "${DIRS_TO_CLEAN[@]}"; do
            if [ -d "$dir" ]; then
                rm -rf "$dir"
                echo -e "${GREEN}✅ 手動で削除: $dir${NC}"
            fi
        done
    fi
else
    echo -e "${YELLOW}⚠️  クリーンアップをスキップします (CLEANUP=false)${NC}"
    echo "   アタッチするには: haconiwa space attach -c $SESSION_NAME"
fi

# 最終サマリー
echo
echo "============================================================"
if [ "$TEST_PASSED" = "true" ]; then
    echo -e "${GREEN}✅ シナリオテスト成功!${NC}"
    exit 0
else
    echo -e "${RED}❌ シナリオテスト失敗!${NC}"
    exit 1
fi