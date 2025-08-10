#!/bin/bash
# Example custom entrypoint script for /storage/entrypoint.sh
# This file can be mounted as a volume to customize the web server startup

set -e

echo "🔧 Custom entrypoint script executing..."
echo "📍 Arguments passed: $*"

# Example: You could add custom pre-server setup here
# - Additional environment variable validation
# - Custom health checks
# - Service discovery registration
# - Custom logging setup
# - etc.

echo "🌐 Starting the LangGraph API server with custom configuration..."

# Start the default LangGraph API server
# You can modify this to start different servers or with different parameters
exec python -m langgraph_api.api "$@"
