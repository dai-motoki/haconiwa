#!/bin/bash

# Exit on any error
set -e

# Delete the companies
echo "Deleting companies..."
haconiwa space delete -c jjz-dev-company --clean-dirs --force
haconiwa space delete -c kamui-dev-company --clean-dirs --force

# Apply the new configuration
echo "Applying configuration..."
haconiwa apply -f haconiwa-world-without-haconiwa-dev.yaml --no-attach

echo "Companies recreated successfully."
