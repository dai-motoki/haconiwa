#!/usr/bin/env python3
"""
Simple script to update agent panes based on agent_assignment.json files
"""

import json
import subprocess
import sys
from pathlib import Path

def main():
    # Base path
    base_path = Path("/Users/motokidaisuke/haconiwa")
    if len(sys.argv) > 1:
        company_name = sys.argv[1]
    else:
        company_name = "haconiwa-dev-company"
    
    company_path = base_path / company_name
    tasks_path = company_path / "tasks"
    
    if not tasks_path.exists():
        print(f"Tasks path not found: {tasks_path}")
        return
    
    # Hard-coded agent to pane mapping based on organization structure
    agent_to_pane = {
        "ceo-motoki": 0,
        "cto-yamada": 1,
        "cfo-tanaka": 2,
        "vpe-sato": 3,
        "vpp-suzuki": 4,
        "vpo-watanabe": 5,
        "ai-lead-nakamura": 6,
        "backend-lead-kobayashi": 7,
        "frontend-lead-ishii": 8,
        "devops-lead-matsui": 9,
        "security-lead-inoue": 10,
        "data-lead-kimura": 11,
        "qa-manager-hayashi": 12,
        "docs-lead-yamamoto": 13,
        "community-ito": 14,
        "platform-kato": 15,
    }
    
    updated_count = 0
    
    # Find all agent_assignment.json files
    for assignment_file in tasks_path.rglob(".haconiwa/agent_assignment.json"):
        try:
            with open(assignment_file, 'r') as f:
                assignments = json.load(f)
            
            for assignment in assignments:
                agent_id = assignment.get("agent_id")
                task_name = assignment.get("task_name")
                
                if not agent_id or not task_name:
                    continue
                
                if agent_id in agent_to_pane:
                    pane_index = agent_to_pane[agent_id]
                    task_dir = assignment_file.parent.parent
                    
                    # Update tmux pane directory
                    cmd = ["tmux", "send-keys", "-t", f"{company_name}:0.{pane_index}", 
                           f"cd {task_dir}", "Enter"]
                    result = subprocess.run(cmd, capture_output=True, text=True)
                    
                    if result.returncode == 0:
                        print(f"✅ Updated {agent_id} (pane {pane_index}) -> {task_dir}")
                        updated_count += 1
                        
                        # Update assignment file with pane info
                        assignment["tmux_window"] = 0
                        assignment["tmux_pane"] = pane_index
                        
                        with open(assignment_file, 'w') as f:
                            json.dump(assignments, f, indent=2, ensure_ascii=False)
                            
                    else:
                        print(f"❌ Failed to update {agent_id}: {result.stderr}")
                else:
                    print(f"⚠️  Agent {agent_id} not in pane mapping")
                    
        except Exception as e:
            print(f"Error processing {assignment_file}: {e}")
    
    print(f"\nTotal updated: {updated_count} agent panes")

if __name__ == "__main__":
    main()