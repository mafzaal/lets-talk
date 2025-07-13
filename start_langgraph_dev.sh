#!/bin/bash

# LangGraph Development Server Startup Script
# This script starts the LangGraph development server with blocking operations allowed

set -e

# Color codes for output
RED='\033[0;31m'
GREEN='\033[0;32m'
BLUE='\033[0;34m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# Function to print colored output
print_info() {
    echo -e "${BLUE}[INFO]${NC} $1"
}

print_success() {
    echo -e "${GREEN}[SUCCESS]${NC} $1"
}

print_warning() {
    echo -e "${YELLOW}[WARNING]${NC} $1"
}

print_error() {
    echo -e "${RED}[ERROR]${NC} $1"
}

# Check if uv is installed
if ! command -v uv &> /dev/null; then
    print_error "uv package manager is not installed or not in PATH"
    print_info "Please install uv: https://docs.astral.sh/uv/getting-started/installation/"
    exit 1
fi

# Check if langgraph.json exists
if [ ! -f "langgraph.json" ]; then
    print_warning "langgraph.json not found in current directory"
    print_info "Make sure you're running this script from the project root directory"
fi

# Function to handle cleanup
cleanup() {
    print_info "Shutting down LangGraph development server..."
    # Kill any remaining LangGraph processes
    pkill -f "uv run langgraph dev" 2>/dev/null || true
    pkill -f "langgraph dev" 2>/dev/null || true
    print_success "LangGraph development server stopped"
    exit 0
}

# Set up signal handlers
trap cleanup INT TERM EXIT

print_info "Starting LangGraph development server..."
print_info "Command: uv run langgraph dev --allow-blocking"
print_info "Press Ctrl+C to stop the server"

# Start the LangGraph development server
exec uv run langgraph dev --allow-blocking
