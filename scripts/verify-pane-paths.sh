#!/bin/bash
set -e

SESSION_NAME="haconiwa-dev-company"
WINDOW_INDEX="0"

# Check if the tmux session exists
if ! tmux has-session -t "$SESSION_NAME" 2>/dev/null; then
    echo "Error: tmux session '$SESSION_NAME' not found."
    exit 1
fi

echo "Verifying pane paths for tmux session: $SESSION_NAME"

for i in {0..1}
do
    PANE_INDEX=$i
    TASK_ID=$(printf "%02d" $((i + 1)))
    
    # Construct the expected path fragment
    EXPECTED_PATH_FRAGMENT="tasks/feature/${TASK_ID}_"

    # Get the current path of the pane
    CURRENT_PATH=$(tmux display-message -p -t "${SESSION_NAME}:${WINDOW_INDEX}.${PANE_INDEX}" '#{pane_current_path}')

    echo "Checking Pane ${PANE_INDEX}..."
    echo "  Expected path to contain: .../${EXPECTED_PATH_FRAGMENT}..."
    echo "  Actual path: ${CURRENT_PATH}"

    # Check if the current path contains the expected fragment
    if [[ "$CURRENT_PATH" != *"$EXPECTED_PATH_FRAGMENT"* ]]; then
        echo "Error: Pane ${PANE_INDEX} is in the wrong directory."
        echo "  Expected: .../${EXPECTED_PATH_FRAGMENT}..."
        echo "  Actual:   ${CURRENT_PATH}"
        exit 1
    else
        echo "  ✅ OK"
    fi
done

echo "All checked panes are in their correct task directories."
exit 0 