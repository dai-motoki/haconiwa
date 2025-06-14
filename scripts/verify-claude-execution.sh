#!/bin/bash
#
# Verify claude command execution in tmux panes
#

SESSION="${1:-test-company-multiroom-tasks}"
CHECK_COUNT=5

echo "=== Verifying claude command execution in session: $SESSION ==="
echo

# Check a sample of panes
PANE_COUNT=0
CD_CLAUDE_COUNT=0
CLAUDE_ONLY_COUNT=0
NO_CLAUDE_COUNT=0

while read -r pane_info && [ $PANE_COUNT -lt $CHECK_COUNT ]; do
    window_id=$(echo "$pane_info" | cut -d'.' -f1)
    pane_id=$(echo "$pane_info" | cut -d'.' -f2)
    
    # Capture last 30 lines of pane content
    content=$(tmux capture-pane -t "$SESSION:$window_id.$pane_id" -p -S -30 2>/dev/null)
    
    # Check for cd && claude pattern
    if echo "$content" | grep -q "cd.*&&.*claude"; then
        echo "✅ Pane $window_id.$pane_id: Found 'cd ... && claude' pattern"
        ((CD_CLAUDE_COUNT++))
    elif echo "$content" | grep -q "claude"; then
        echo "⚠️  Pane $window_id.$pane_id: Found 'claude' but not with '&&'"
        ((CLAUDE_ONLY_COUNT++))
    else
        echo "❌ Pane $window_id.$pane_id: No claude command found"
        ((NO_CLAUDE_COUNT++))
    fi
    
    # Also check current directory
    pwd_output=$(tmux send-keys -t "$SESSION:$window_id.$pane_id" "pwd" Enter 2>/dev/null)
    sleep 0.1
    current_dir=$(tmux capture-pane -t "$SESSION:$window_id.$pane_id" -p | tail -2 | head -1)
    echo "   Current directory: $current_dir"
    echo
    
    ((PANE_COUNT++))
done < <(tmux list-panes -t "$SESSION" -F "#{window_index}.#{pane_index}" | head -$CHECK_COUNT)

echo "=== Summary ==="
echo "Checked $PANE_COUNT panes:"
echo "  - With 'cd && claude': $CD_CLAUDE_COUNT"
echo "  - Claude only: $CLAUDE_ONLY_COUNT"
echo "  - No claude: $NO_CLAUDE_COUNT"

if [ $CD_CLAUDE_COUNT -eq $PANE_COUNT ]; then
    echo
    echo "✅ All checked panes use the correct 'cd && claude' pattern!"
else
    echo
    echo "⚠️  Some panes may not have the correct pattern"
fi