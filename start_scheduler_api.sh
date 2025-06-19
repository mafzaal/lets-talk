#!/bin/bash

# FastAPI Pipeline Scheduler Startup Script
# This script starts the FastAPI server with pipeline scheduling capabilities

set -e

# Configuration
HOST="${HOST:-0.0.0.0}"
PORT="${PORT:-8000}"
WORKERS="${WORKERS:-1}"
LOG_LEVEL="${LOG_LEVEL:-info}"

# Color codes for output
RED='\033[0;31m'
GREEN='\033[0;32m'
BLUE='\033[0;34m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

echo -e "${BLUE}🚀 Starting FastAPI Pipeline Scheduler${NC}"
echo "=================================="

# Check if uv is available
if ! command -v uv &> /dev/null; then
    echo -e "${RED}❌ uv is not installed. Please install it first:${NC}"
    echo "   curl -LsSf https://astral.sh/uv/install.sh | sh"
    exit 1
fi

# Check if the API main module exists
if [ ! -f "backend/lets_talk/api/main.py" ]; then
    echo -e "${RED}❌ api/main.py not found. Make sure you're in the project root directory.${NC}"
    exit 1
fi

# Install dependencies if needed
echo -e "${YELLOW}📦 Installing dependencies...${NC}"
uv sync

# Set up environment
echo -e "${YELLOW}⚙️  Setting up environment...${NC}"

# Create output directory if it doesn't exist
mkdir -p output
mkdir -p db

# Check for .env file
if [ ! -f ".env" ]; then
    echo -e "${YELLOW}⚠️  No .env file found. Using default configuration.${NC}"
    echo -e "${BLUE}💡 For custom configuration, copy docs/PIPELINE_CONFIG_TEMPLATE.env to .env${NC}"
fi

# Display configuration
echo -e "${GREEN}📋 Server Configuration:${NC}"
echo "   Host: $HOST"
echo "   Port: $PORT"
echo "   Workers: $WORKERS"
echo "   Log Level: $LOG_LEVEL"
echo ""

# Start the server
echo -e "${GREEN}🎯 Starting FastAPI server...${NC}"
echo -e "${BLUE}📖 API Documentation will be available at: http://$HOST:$PORT/docs${NC}"
echo -e "${BLUE}🔍 Health check: http://$HOST:$PORT/health${NC}"
echo -e "${BLUE}📊 Scheduler status: http://$HOST:$PORT/scheduler/status${NC}"
echo ""
echo -e "${YELLOW}Press Ctrl+C to stop the server${NC}"
echo ""

# Export PYTHONPATH to include py-src
export PYTHONPATH="${PYTHONPATH:+$PYTHONPATH:}$(pwd)/backend"

# Start uvicorn with the FastAPI app
exec uv run uvicorn lets_talk.api.main:app \
    --host "$HOST" \
    --port "$PORT" \
    --workers "$WORKERS" \
    --log-level "$LOG_LEVEL" \
    --reload
