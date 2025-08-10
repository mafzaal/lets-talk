#!/bin/sh
set -e

# echo "==============================================================================="
# echo "🚀 Let's Talk Container Entrypoint"
# echo "==============================================================================="

# Function to handle cleanup on exit
cleanup() {
    local exit_code=$?
    echo ""
    echo "==============================================================================="
    if [ $exit_code -eq 0 ]; then
        echo "✅ Container shutdown completed"
    else
        echo "❌ Container exited with error (code: $exit_code)"
    fi
    echo "==============================================================================="
    exit $exit_code
}

# Set up signal handlers for graceful shutdown
trap cleanup EXIT
trap 'echo "🛑 Received SIGTERM, shutting down..."; exit 143' TERM
trap 'echo "🛑 Received SIGINT, shutting down..."; exit 130' INT

# Change to the application directory
cd /deps/lets-talk

# echo "📍 Working directory: $(pwd)"
# echo "👤 Running as user: $(id)"
# echo "🐍 Python version: $(python --version)"
# echo ""

# Phase 1: Run application startup (database migrations, scheduler setup, etc.)
# echo "==============================================================================="
# echo "📋 Phase 1: Application Initialization"
# echo "==============================================================================="

# echo "🔧 Running application startup script..."
if ! python startup_application.py; then
    echo ""
    echo "❌ Application startup failed!"
    echo "🚫 Cannot proceed with web server startup"
    echo "💡 Check the logs above for specific error details"
    echo ""
    echo "Common issues:"
    echo "  • Database connection problems"
    echo "  • Missing environment variables"
    echo "  • Migration failures"
    echo "  • File permission issues"
    exit 1
fi

echo ""
echo "✅ Application initialization completed successfully"

# Phase 2: Execute the original entrypoint or command
echo ""
echo "==============================================================================="
echo "🌐 Phase 2: LangGraph API Startup"
echo "==============================================================================="

# Check if there's a custom entrypoint script to run
if [ -f "/storage/entrypoint.sh" ] && [ -x "/storage/entrypoint.sh" ]; then
    echo "🔧 Found custom entrypoint script at /storage/entrypoint.sh"
    echo "📝 Executing custom entrypoint..."
    exec /storage/entrypoint.sh "$@"
else
    echo "📝 No custom entrypoint found, proceeding with default startup"
    
    # If no arguments provided, start the default langgraph server
    if [ $# -eq 0 ]; then
        echo "🚀 Starting LangGraph API server..."
        echo "📡 Server will be available on port 8000"
        echo "📚 API documentation at http://localhost:8000/docs"
        echo ""

        # Start the langgraph API server (this is the default from the base image)
        exec python -m langgraph_api.api
    else
        # Execute the provided command
        echo "🔧 Executing provided command: $*"
        exec "$@"
    fi
fi
