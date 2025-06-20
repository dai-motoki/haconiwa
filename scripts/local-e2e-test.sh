#!/bin/bash
set -e

echo "🚀 Starting Haconiwa Local E2E Test Suite..."

# 1. Install Python dependencies
echo "🐍 Installing Python dependencies..."
python -m pip install --upgrade pip
pip install .

# 2. Install Node.js dependencies
echo "📦 Installing Node.js dependencies..."
npm install

# 3. Run Unit and Integration Tests with pytest
echo "🔬 Running Unit and Integration tests..."
python -m pytest tests/unit/ tests/integration/

# 4. Run Jest tests
echo "🃏 Running Jest tests..."
npx jest __tests__/utils/

# 5. Clean up previous test environments
echo "🧹 Cleaning up previous test environments..."
for company in haconiwa-dev-company kamui-dev-company jjz-dev-company; do
    if [ -d "$company" ]; then
        echo "Deleting company: $company"
        python -m haconiwa space delete -c $company --clean-dirs --force || true # Continue on error
    else
        echo "Company directory $company not found, skipping delete."
    fi
done

# 6. Apply test configuration
echo "🌍 Applying test Haconiwa World..."
python -m haconiwa apply -f test_cases/test-haconiwa-world-ci.yaml --no-attach

# 7. Verify TMUX pane paths
echo "🔍 Verifying TMUX pane paths..."
./scripts/verify-pane-paths.sh

echo "🎉 Haconiwa Local E2E Test Suite completed successfully!"
exit 0 