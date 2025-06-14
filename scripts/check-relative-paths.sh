#!/bin/bash
#
# Check relative path usage in tmux panes
#

SESSION="${1:-test-company-multiroom-tasks}"

echo "=== Checking relative path usage in session: $SESSION ==="
echo

# Check first 5 panes
COUNT=0
while read -r pane_info && [ $COUNT -lt 5 ]; do
    window_id=$(echo "$pane_info" | cut -d'.' -f1)
    pane_id=$(echo "$pane_info" | cut -d'.' -f2)
    
    echo "Checking pane $window_id.$pane_id:"
    
    # Capture command history
    content=$(tmux capture-pane -t "$SESSION:$window_id.$pane_id" -p -S -30)
    
    # Look for cd commands
    if echo "$content" | grep -q "cd tasks/"; then
        echo "  ✅ Found relative path: cd tasks/..."
    elif echo "$content" | grep -q "cd standby"; then
        echo "  ✅ Found relative path: cd standby"
    elif echo "$content" | grep -q "cd /"; then
        echo "  ❌ Found absolute path: cd /..."
    else
        echo "  ⚠️  No cd command found"
    fi
    
    # Extract the cd command line
    cd_line=$(echo "$content" | grep -E "cd.*&&.*claude" | tail -1)
    if [ -n "$cd_line" ]; then
        echo "  Command: $cd_line"
    fi
    
    echo
    ((COUNT++))
done < <(tmux list-panes -t "$SESSION" -F "#{window_index}.#{pane_index}")