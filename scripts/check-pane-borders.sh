#!/bin/bash
#
# Check pane border settings for tmux session
#

SESSION="${1:-test-company-multiroom-tasks}"

echo "=== Checking pane border settings for session: $SESSION ==="
echo

# Check session-level settings
echo "Session-level settings:"
echo -n "  pane-border-status: "
tmux show-options -t "$SESSION" pane-border-status 2>/dev/null || echo "(not set)"
echo -n "  pane-border-format: "
tmux show-options -t "$SESSION" pane-border-format 2>/dev/null || echo "(not set)"

echo
echo "Window-level settings:"

# Check each window
while read -r window_info; do
    window_id=$(echo "$window_info" | cut -d: -f1)
    window_name=$(echo "$window_info" | cut -d: -f2)
    
    echo
    echo "Window $window_id ($window_name):"
    echo -n "  pane-border-status: "
    tmux show-options -t "$SESSION:$window_id" pane-border-status 2>/dev/null || echo "(not set)"
    echo -n "  pane-border-format: "
    tmux show-options -t "$SESSION:$window_id" pane-border-format 2>/dev/null || echo "(not set)"
    
    # Show first few pane titles
    echo "  Sample pane titles:"
    tmux list-panes -t "$SESSION:$window_id" -F "    Pane #{pane_index}: #{pane_title}" | head -3
done < <(tmux list-windows -t "$SESSION" -F "#{window_index}:#{window_name}")

echo
echo "=== Applying missing settings if needed ==="

# Apply settings to any windows that don't have them
while read -r window_id; do
    if ! tmux show-options -t "$SESSION:$window_id" pane-border-status &>/dev/null; then
        echo "Applying pane-border-status to window $window_id..."
        tmux set-option -t "$SESSION:$window_id" pane-border-status top
    fi
    
    if ! tmux show-options -t "$SESSION:$window_id" pane-border-format &>/dev/null; then
        echo "Applying pane-border-format to window $window_id..."
        tmux set-option -t "$SESSION:$window_id" pane-border-format '#{pane_title}'
    fi
done < <(tmux list-windows -t "$SESSION" -F "#{window_index}")