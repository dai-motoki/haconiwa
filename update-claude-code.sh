#!/bin/bash

# Update @anthropic-ai/claude-code npm package
echo "Updating @anthropic-ai/claude-code in ~/.claude/local..."
cd ~/.claude/local && npm update @anthropic-ai/claude-code
echo "Update complete!"