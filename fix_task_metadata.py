#!/usr/bin/env python3
"""Fix Task CRDs by adding metadata.name field"""

import re

# Read the YAML file
with open('haconiwa-dev-company.yaml', 'r') as f:
    content = f.read()

# Pattern to find Task CRDs without metadata
pattern = r'(apiVersion: haconiwa\.dev/v1\nkind: Task)\n(spec:)'

# Counter for replacements
count = 0

def replacement(match):
    global count
    count += 1
    # Extract the taskBranchName from the following lines
    remaining = content[match.end():]
    branch_match = re.search(r'taskBranchName: ([^\n]+)', remaining)
    if branch_match:
        task_name = branch_match.group(1).strip()
        # Create a simple name from the branch name
        simple_name = task_name.replace('/', '-').replace('_', '-')
        return f"{match.group(1)}\nmetadata:\n  name: {simple_name}\n{match.group(2)}"
    return match.group(0)

# Replace all occurrences
new_content = re.sub(pattern, replacement, content)

# Write the fixed content back
with open('haconiwa-dev-company-fixed.yaml', 'w') as f:
    f.write(new_content)

print(f"Fixed {count} Task CRDs. Output written to haconiwa-dev-company-fixed.yaml")