#!/bin/bash

# Let's Talk Frontend Development Setup Script
# This script sets up and starts both the backend API and frontend development servers

set -e

echo "🚀 Let's Talk Frontend Development Setup"
echo "========================================"

# Check if we're in the correct directory
if [ ! -f "pyproject.toml" ] || [ ! -d "frontend" ]; then
    echo "❌ Error: Please run this script from the root of the lets-talk repository"
    exit 1
fi

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Function to check if a command exists
command_exists() {
    command -v "$1" >/dev/null 2>&1
}

# Function to kill processes on exit
cleanup() {
    echo -e "\n${YELLOW}🧹 Cleaning up processes...${NC}"
    if [ ! -z "$BACKEND_PID" ]; then
        kill $BACKEND_PID 2>/dev/null || true
    fi
    if [ ! -z "$FRONTEND_PID" ]; then
        kill $FRONTEND_PID 2>/dev/null || true
    fi
    exit 0
}

# Set up signal handlers
trap cleanup INT TERM

echo -e "${BLUE}📋 Checking dependencies...${NC}"

# Check for Node.js
if ! command_exists node; then
    echo -e "${RED}❌ Node.js is not installed. Please install Node.js 18 or later.${NC}"
    exit 1
fi

# Check for pnpm
if ! command_exists pnpm; then
    echo -e "${YELLOW}📦 pnpm not found. Installing pnpm...${NC}"
    npm install -g pnpm
fi

# Check for Python/uv
if ! command_exists uv; then
    echo -e "${RED}❌ uv is not installed. Please install uv for Python package management.${NC}"
    exit 1
fi

echo -e "${GREEN}✅ All dependencies are available${NC}"



# Choose backend: langgraph (default) or backend API
BACKEND_CHOICE="langgraph"
if [[ "$1" == "backend" ]]; then
    BACKEND_CHOICE="backend"
fi

if [ "$BACKEND_CHOICE" = "backend" ]; then
    echo -e "${BLUE}🔧 Starting FastAPI Backend API on port 2024...${NC}"
    PORT=2024 ./start_backend_dev.sh > /tmp/backend_api.log 2>&1 &
    BACKEND_PID=$!
    # Wait for backend to start
    echo -e "${BLUE}⏳ Waiting for Backend API to become healthy...${NC}"
    for i in {1..10}; do
        if curl -s http://localhost:2024/health > /dev/null 2>&1; then
            echo -e "${GREEN}✅ Backend API is running on http://localhost:2024${NC}"
            break
        fi
        sleep 1
    done
    if ! curl -s http://localhost:2024/health > /dev/null 2>&1; then
        echo -e "${RED}❌ Backend API failed to start. Check /tmp/backend_api.log for details.${NC}"
        kill $BACKEND_PID 2>/dev/null || true
        exit 1
    fi
else
    echo -e "${BLUE}🔧 Starting LangGraph dev server on port 2024...${NC}"
    ./start_langgraph_dev.sh > /tmp/langgraph_dev.log 2>&1 &
    BACKEND_PID=$!
    # Wait for LangGraph to start
    echo -e "${BLUE}⏳ Waiting for LangGraph dev server to become healthy...${NC}"
    for i in {1..10}; do
        if nc -z localhost 2024; then
            echo -e "${GREEN}✅ LangGraph dev server is running on port 2024${NC}"
            break
        fi
        sleep 1
    done
    if ! nc -z localhost 2024; then
        echo -e "${RED}❌ LangGraph dev server failed to start. Check /tmp/langgraph_dev.log for details.${NC}"
        kill $BACKEND_PID 2>/dev/null || true
        exit 1
    fi
fi


# Install frontend dependencies
echo -e "${BLUE}📦 Installing frontend dependencies...${NC}"
cd frontend
pnpm install

# Start frontend development server
echo -e "${BLUE}🎨 Starting frontend development server...${NC}"
pnpm dev > /tmp/frontend.log 2>&1 &
FRONTEND_PID=$!

# Wait for frontend to start
sleep 5

# Check if frontend started successfully
if curl -s http://localhost:5173 > /dev/null 2>&1; then
    echo -e "${GREEN}✅ Frontend server is running on http://localhost:5173${NC}"
else
    echo -e "${RED}❌ Frontend server failed to start. Check /tmp/frontend.log for details.${NC}"
    kill $BACKEND_PID 2>/dev/null || true
    kill $FRONTEND_PID 2>/dev/null || true
    exit 1
fi

echo -e "${GREEN}🎉 Setup complete!${NC}"
echo ""
echo -e "${BLUE}📱 Access the application:${NC}"
echo "   • Frontend: http://localhost:5173"
if [ "$BACKEND_CHOICE" = "backend" ]; then
    echo "   • Backend API: http://localhost:2024"
    echo "   • API Documentation: http://localhost:2024/docs"
else
    echo "   • LangGraph dev server: http://localhost:2024"
    echo "   • API Documentation: http://localhost:2024/docs"
fi
echo ""
echo -e "${BLUE}🎛️  Available pages:${NC}"
echo "   • Landing page: http://localhost:5173/"
echo "   • Dashboard: http://localhost:5173/dashboard"
echo "   • Jobs: http://localhost:5173/jobs"
echo "   • Analytics: http://localhost:5173/analytics"
echo "   • Activity: http://localhost:5173/activity"
echo ""
echo -e "${YELLOW}Press Ctrl+C to stop all servers${NC}"

# Wait for user to stop the servers
wait