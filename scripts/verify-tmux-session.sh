#!/bin/bash
#
# Tmux Session Verification Script
# 
# Usage: ./verify-tmux-session.sh [session-name]
#

set -euo pipefail

# Color codes
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Default session name
SESSION="${1:-test-company-multiroom-tasks}"

echo -e "${BLUE}=== Tmux Session Verification: $SESSION ===${NC}\n"

# Check if session exists
if ! tmux has-session -t "$SESSION" 2>/dev/null; then
    echo -e "${RED}✗ Session '$SESSION' does not exist${NC}"
    exit 1
fi

echo -e "${GREEN}✓ Session exists${NC}"

# 1. Window Structure Check
echo -e "\n${YELLOW}1. Window Structure:${NC}"
tmux list-windows -t "$SESSION" -F "Window #{window_index}: #{window_name} (#{window_panes} panes)"

# 2. Pane Title Check
echo -e "\n${YELLOW}2. Pane Titles Check:${NC}"
NO_TITLE_COUNT=0
while read -r line; do
    PANE_ID=$(echo "$line" | cut -d'|' -f1)
    PANE_TITLE=$(echo "$line" | cut -d'|' -f2)
    
    if [ -z "$PANE_TITLE" ]; then
        echo -e "${RED}✗ Pane $PANE_ID has no title${NC}"
        ((NO_TITLE_COUNT++))
    fi
done < <(tmux list-panes -a -t "$SESSION" -F "#{window_index}.#{pane_index}|#{pane_title}")

if [ $NO_TITLE_COUNT -eq 0 ]; then
    echo -e "${GREEN}✓ All panes have titles${NC}"
else
    echo -e "${RED}✗ $NO_TITLE_COUNT panes have no titles${NC}"
fi

# 3. Directory Check
echo -e "\n${YELLOW}3. Directory Placement Check:${NC}"
HACONIWA_ROOT_COUNT=0
STANDBY_COUNT=0
TASK_COUNT=0
OTHER_COUNT=0

while read -r line; do
    PANE_ID=$(echo "$line" | cut -d'|' -f1)
    PANE_PATH=$(echo "$line" | cut -d'|' -f2)
    
    if [[ "$PANE_PATH" =~ /haconiwa$ ]]; then
        ((HACONIWA_ROOT_COUNT++))
    elif [[ "$PANE_PATH" =~ /standby$ ]]; then
        ((STANDBY_COUNT++))
    elif [[ "$PANE_PATH" =~ /tasks/ ]]; then
        ((TASK_COUNT++))
    else
        ((OTHER_COUNT++))
    fi
done < <(tmux list-panes -a -t "$SESSION" -F "#{window_index}.#{pane_index}|#{pane_current_path}")

echo "  - Task directories: $TASK_COUNT panes"
echo "  - Standby directory: $STANDBY_COUNT panes"
echo "  - Haconiwa root: $HACONIWA_ROOT_COUNT panes"
echo "  - Other: $OTHER_COUNT panes"

if [ $HACONIWA_ROOT_COUNT -gt 0 ]; then
    echo -e "${RED}✗ Warning: $HACONIWA_ROOT_COUNT panes are in haconiwa root${NC}"
else
    echo -e "${GREEN}✓ No panes in haconiwa root${NC}"
fi

# 4. Grid Layout Check
echo -e "\n${YELLOW}4. Grid Layout Check:${NC}"
TOTAL_PANES=$(tmux list-panes -a -t "$SESSION" | wc -l)
WINDOW_COUNT=$(tmux list-windows -t "$SESSION" | wc -l)

echo "  - Total panes: $TOTAL_PANES"
echo "  - Windows: $WINDOW_COUNT"
echo "  - Average panes per window: $((TOTAL_PANES / WINDOW_COUNT))"

# 5. Claude Command Check (sample first 5 panes)
echo -e "\n${YELLOW}5. Claude Command Check (sampling):${NC}"
CLAUDE_CHECK_COUNT=0
CLAUDE_FOUND_COUNT=0

while read -r pane_id && [ $CLAUDE_CHECK_COUNT -lt 5 ]; do
    CONTENT=$(tmux capture-pane -t "$SESSION:$pane_id" -p -S -20 2>/dev/null || echo "")
    if echo "$CONTENT" | grep -q "claude"; then
        ((CLAUDE_FOUND_COUNT++))
    fi
    ((CLAUDE_CHECK_COUNT++))
done < <(tmux list-panes -t "$SESSION" -F "#{window_index}.#{pane_index}" | head -5)

echo "  - Checked $CLAUDE_CHECK_COUNT panes, found claude in $CLAUDE_FOUND_COUNT"

if [ $CLAUDE_FOUND_COUNT -eq $CLAUDE_CHECK_COUNT ]; then
    echo -e "${GREEN}✓ Claude command found in all sampled panes${NC}"
else
    echo -e "${YELLOW}⚠ Claude command found in $CLAUDE_FOUND_COUNT/$CLAUDE_CHECK_COUNT sampled panes${NC}"
fi

# 6. Detailed Window Report
echo -e "\n${YELLOW}6. Detailed Window Report:${NC}"
while read -r window_id; do
    WINDOW_NAME=$(tmux display-message -t "$SESSION:$window_id" -p '#{window_name}')
    echo -e "\n${BLUE}Window $window_id: $WINDOW_NAME${NC}"
    
    # Show first 3 panes
    tmux list-panes -t "$SESSION:$window_id" -F "  Pane #{pane_index}: #{pane_title}" | head -3
    
    PANE_COUNT=$(tmux list-panes -t "$SESSION:$window_id" | wc -l)
    if [ $PANE_COUNT -gt 3 ]; then
        echo "  ... and $((PANE_COUNT - 3)) more panes"
    fi
done < <(tmux list-windows -t "$SESSION" -F "#{window_index}")

# Summary
echo -e "\n${BLUE}=== Summary ===${NC}"
if [ $NO_TITLE_COUNT -eq 0 ] && [ $HACONIWA_ROOT_COUNT -eq 0 ]; then
    echo -e "${GREEN}✓ All checks passed!${NC}"
else
    echo -e "${YELLOW}⚠ Some issues found - review details above${NC}"
fi