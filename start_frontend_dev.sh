#!/bin/bash

# Let's Talk Frontend Development Setup Script
# This script sets up and starts both the backend and frontend development servers

set -e

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
CYAN='\033[0;36m'
MAGENTA='\033[0;35m'
NC='\033[0m' # No Color

# Configuration
BACKEND_MODE="langgraph"  # Default mode
INTERACTIVE_MODE=true     # Show logs in console by default
LOG_TO_FILE=false        # Option to redirect logs to files

# Parse command line arguments
while [[ $# -gt 0 ]]; do
    case $1 in
        --api-mode)
            BACKEND_MODE="api"
            shift
            ;;
        --langgraph-mode)
            BACKEND_MODE="langgraph"
            shift
            ;;
        --quiet)
            INTERACTIVE_MODE=false
            LOG_TO_FILE=true
            shift
            ;;
        --log-to-file)
            LOG_TO_FILE=true
            shift
            ;;
        --help|-h)
            echo "Usage: $0 [OPTIONS]"
            echo ""
            echo "Backend Mode Options:"
            echo "  --api-mode        Run backend in API mode (FastAPI without LangGraph)"
            echo "  --langgraph-mode  Run backend in LangGraph mode (default)"
            echo ""
            echo "Output Options:"
            echo "  --quiet           Run in background with logs redirected to files"
            echo "  --log-to-file     Also save logs to files (in addition to console)"
            echo "  --help, -h        Show this help message"
            echo ""
            echo "Examples:"
            echo "  $0                    # Default: LangGraph mode with interactive logs"
            echo "  $0 --api-mode        # API mode with interactive logs"
            echo "  $0 --quiet           # Background mode with file logging"
            echo "  $0 --log-to-file     # Interactive + file logging"
            exit 0
            ;;
        *)
            echo "Unknown option: $1"
            echo "Use --help for usage information"
            exit 1
            ;;
    esac
done

# Legacy compatibility: support old 'backend' argument
if [[ "$1" == "backend" ]]; then
    BACKEND_MODE="api"
fi

# Function to check if a command exists
command_exists() {
    command -v "$1" >/dev/null 2>&1
}

# Arrays to track background processes and named pipes
declare -a BACKGROUND_PIDS=()
declare -a NAMED_PIPES=()

# Enhanced cleanup function with better process management
cleanup() {
    if [[ "$CLEANUP_RUNNING" == "true" ]]; then
        return 0  # Avoid double cleanup
    fi
    CLEANUP_RUNNING=true
    
    echo -e "\n${YELLOW}🧹 Cleaning up processes and resources...${NC}"
    
    # Stop all background processes
    for pid in "${BACKGROUND_PIDS[@]}"; do
        if kill -0 "$pid" 2>/dev/null; then
            echo -e "${BLUE}Stopping process $pid...${NC}"
            kill -TERM "$pid" 2>/dev/null || true
            
            # Wait up to 5 seconds for graceful shutdown
            for i in {1..5}; do
                if ! kill -0 "$pid" 2>/dev/null; then
                    break
                fi
                sleep 1
            done
            
            # Force kill if still running
            if kill -0 "$pid" 2>/dev/null; then
                echo -e "${YELLOW}Force killing process $pid...${NC}"
                kill -KILL "$pid" 2>/dev/null || true
            fi
        fi
    done
    
    # Clean up named pipes
    for pipe in "${NAMED_PIPES[@]}"; do
        if [[ -p "$pipe" ]]; then
            rm -f "$pipe"
        fi
    done
    
    # Clean up potential orphaned processes
    pkill -f "uv run langgraph dev" 2>/dev/null || true
    pkill -f "uv run uvicorn.*lets_talk" 2>/dev/null || true
    pkill -f "pnpm dev" 2>/dev/null || true
    
    echo -e "${GREEN}✅ Cleanup completed${NC}"
    exit 0
}

# Set up signal handlers
trap cleanup INT TERM EXIT

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

# Create log directory if logging to files
if [[ "$LOG_TO_FILE" == "true" ]]; then
    mkdir -p logs
    echo -e "${BLUE}📁 Logs will be saved to logs/ directory${NC}"
fi

# Function to start a process with optional log redirection
start_process() {
    local name="$1"
    local command="$2"
    local log_file="$3"
    local check_health="$4"
    local health_url="$5"
    local success_message="$6"
    
    echo -e "${BLUE}🔧 Starting $name...${NC}"
    
    if [[ "$INTERACTIVE_MODE" == "true" && "$LOG_TO_FILE" == "false" ]]; then
        # Interactive mode - show logs in console using named pipes for real-time output
        local pipe_name="/tmp/${name,,}_pipe_$$"
        mkfifo "$pipe_name"
        NAMED_PIPES+=("$pipe_name")
        
        # Start the process and redirect to named pipe
        set +e  # Temporarily disable exit on error
        eval "$command" > "$pipe_name" 2>&1 &
        local process_pid=$!
        set -e  # Re-enable exit on error
        BACKGROUND_PIDS+=("$process_pid")
        
        # Start log display in background
        {
            while IFS= read -r line; do
                echo -e "${CYAN}[$name]${NC} $line"
            done < "$pipe_name"
        } &
        local log_display_pid=$!
        BACKGROUND_PIDS+=("$log_display_pid")
        
    elif [[ "$INTERACTIVE_MODE" == "false" || "$LOG_TO_FILE" == "true" ]]; then
        # Background mode or file logging
        set +e  # Temporarily disable exit on error
        if [[ "$LOG_TO_FILE" == "true" ]]; then
            eval "$command" > "$log_file" 2>&1 &
        else
            eval "$command" > /tmp/"${name,,}".log 2>&1 &
        fi
        local process_pid=$!
        set -e  # Re-enable exit on error
        BACKGROUND_PIDS+=("$process_pid")
    fi
    
    # Health check if specified
    if [[ "$check_health" == "true" ]]; then
        echo -e "${BLUE}⏳ Waiting for $name to become healthy...${NC}"
        local attempts=0
        local max_attempts=90  # Increased to 90 seconds for LangGraph
        
        # Give the process more time to start before checking
        if [[ "$name" == *"LangGraph"* ]]; then
            echo -e "${CYAN}Giving LangGraph extra time to initialize...${NC}"
            sleep 10  # LangGraph needs more time
        else
            sleep 3
        fi
        
        while [[ $attempts -lt $max_attempts ]]; do
            if [[ "$name" == "Frontend" ]]; then
                # For frontend, check multiple possible ports since Vite auto-increments
                for port in 5173 5174 5175 5176 5177; do
                    if nc -z localhost $port 2>/dev/null; then
                        FRONTEND_PORT=$port
                        echo -e "${GREEN}✅ Frontend server is running on http://localhost:$port${NC}"
                        return 0
                    fi
                done
            elif [[ -n "$health_url" ]]; then
                if curl -s "$health_url" >/dev/null 2>&1; then
                    echo -e "${GREEN}✅ $success_message${NC}"
                    return 0
                fi
            else
                # Default to port 2024 for backend services
                if nc -z localhost 2024 2>/dev/null; then
                    echo -e "${GREEN}✅ $success_message${NC}"
                    return 0
                fi
            fi
            
            # Show progress every 15 attempts
            if [[ $((attempts % 15)) -eq 0 && $attempts -gt 0 ]]; then
                echo -e "${CYAN}Still waiting for $name... (${attempts}/${max_attempts})${NC}"
            fi
            
            sleep 1
            ((attempts++))
        done
        
        echo -e "${RED}❌ $name failed to start within ${max_attempts} seconds${NC}"
        if [[ "$LOG_TO_FILE" == "true" || "$INTERACTIVE_MODE" == "false" ]]; then
            echo -e "${YELLOW}Check log file: $log_file${NC}"
        fi
        echo -e "${YELLOW}Continuing anyway...${NC}"
        return 0  # Don't fail the script, just continue
    fi
    
    return 0
}

# Function to check if services are already running
check_existing_services() {
    local services_running=false
    local ports_in_use=()
    
    if nc -z localhost 2024 2>/dev/null; then
        echo -e "${YELLOW}⚠️  Port 2024 is already in use (backend/LangGraph)${NC}"
        ports_in_use+=("2024")
        services_running=true
    fi
    
    if nc -z localhost 5173 2>/dev/null; then
        echo -e "${YELLOW}⚠️  Port 5173 is already in use (frontend will auto-increment to next available port)${NC}"
        ports_in_use+=("5173")
        # Don't set services_running=true for frontend since Vite handles this gracefully
    fi
    
    if [[ "$services_running" == "true" ]]; then
        echo -e "${BLUE}💡 To free up ports, you can run:${NC}"
        for port in "${ports_in_use[@]}"; do
            if [[ "$port" == "2024" ]]; then
                echo "   • pkill -f 'langgraph dev' || pkill -f 'uvicorn.*lets_talk'"
            fi
        done
        echo ""
        echo -e "${CYAN}Continue with current setup? Backend conflicts must be resolved, but frontend will auto-increment port.${NC}"
        read -p "Continue? (Y/n): " -n 1 -r
        echo
        if [[ $REPLY =~ ^[Nn]$ ]]; then
            echo -e "${YELLOW}Exiting...${NC}"
            exit 0
        fi
    elif [[ ${#ports_in_use[@]} -gt 0 ]]; then
        echo -e "${CYAN}Frontend will automatically use the next available port (likely 5174).${NC}"
        echo ""
    fi
}

# Function to display startup banner with current configuration
display_startup_banner() {
    echo -e "${GREEN}🚀 Let's Talk Frontend Development Setup${NC}"
    echo "========================================"
    echo ""
    echo -e "${BLUE}📋 Configuration:${NC}"
    echo "   • Backend Mode: ${BACKEND_MODE}"
    echo "   • Interactive Logs: ${INTERACTIVE_MODE}"
    echo "   • File Logging: ${LOG_TO_FILE}"
    echo ""
}

# Function to display server information
display_server_info() {
    echo -e "${GREEN}🎉 Setup complete!${NC}"
    echo ""
    echo -e "${BLUE}📱 Access the application:${NC}"
    echo "   • Frontend: http://localhost:${FRONTEND_PORT:-5173}"
    
    if [[ "$BACKEND_MODE" == "api" ]]; then
        echo "   • Backend API: http://localhost:2024"
        echo "   • API Documentation: http://localhost:2024/docs"
    else
        echo "   • LangGraph Server: http://localhost:2024"
        echo "   • API Documentation: http://localhost:2024/docs"
    fi
    
    echo ""
    echo -e "${BLUE}🎛️  Available pages:${NC}"
    echo "   • Landing page: http://localhost:${FRONTEND_PORT:-5173}/"
    echo "   • Dashboard: http://localhost:${FRONTEND_PORT:-5173}/dashboard"
    echo "   • Jobs: http://localhost:${FRONTEND_PORT:-5173}/jobs"
    echo "   • Analytics: http://localhost:${FRONTEND_PORT:-5173}/analytics"
    echo "   • Activity: http://localhost:${FRONTEND_PORT:-5173}/activity"
    echo ""
    
    if [[ "$INTERACTIVE_MODE" == "true" ]]; then
        echo -e "${MAGENTA}🎯 Development Mode: Interactive logs enabled${NC}"
        echo -e "${YELLOW}Press Ctrl+C to stop all servers${NC}"
    else
        echo -e "${MAGENTA}🎯 Development Mode: Background with file logging${NC}"
        echo -e "${YELLOW}Logs are saved to logs/ directory${NC}"
        echo -e "${YELLOW}Press Ctrl+C to stop all servers${NC}"
    fi
}

# Check for existing services on required ports
check_existing_services

# Display startup banner
display_startup_banner

# Start backend server based on selected mode
echo -e "${BLUE}🔧 Starting backend in ${BACKEND_MODE} mode...${NC}"

if [[ "$BACKEND_MODE" == "api" ]]; then
    # API mode - FastAPI without LangGraph
    if [[ "$INTERACTIVE_MODE" == "true" && "$LOG_TO_FILE" == "false" ]]; then
        start_process "Backend-API" "PORT=2024 ./start_backend_dev.sh" "logs/backend_api.log" "true" "http://localhost:2024/health" "Backend API is running on http://localhost:2024"
    else
        log_file="logs/backend_api.log"
        if [[ "$LOG_TO_FILE" == "false" ]]; then
            log_file="/tmp/backend_api.log"
        fi
        start_process "Backend-API" "PORT=2024 ./start_backend_dev.sh" "$log_file" "true" "http://localhost:2024/health" "Backend API is running on http://localhost:2024"
    fi
else
    # LangGraph mode - Backend with LangGraph support
    if [[ "$INTERACTIVE_MODE" == "true" && "$LOG_TO_FILE" == "false" ]]; then
        start_process "LangGraph-Server" "./start_langgraph_dev.sh" "logs/langgraph_dev.log" "true" "" "LangGraph dev server is running on port 2024"
    else
        log_file="logs/langgraph_dev.log"
        if [[ "$LOG_TO_FILE" == "false" ]]; then
            log_file="/tmp/langgraph_dev.log"
        fi
        start_process "LangGraph-Server" "./start_langgraph_dev.sh" "$log_file" "true" "" "LangGraph dev server is running on port 2024"
    fi
fi

# Install and start frontend
echo -e "${BLUE}📦 Installing frontend dependencies...${NC}"
cd frontend
set +e  # Allow pnpm install to fail gracefully
pnpm install
install_result=$?
set -e
cd ..

if [[ $install_result -ne 0 ]]; then
    echo -e "${YELLOW}⚠️  Frontend dependency installation failed, but continuing...${NC}"
fi

echo -e "${BLUE}🎨 Starting frontend development server...${NC}"

if [[ "$INTERACTIVE_MODE" == "true" && "$LOG_TO_FILE" == "false" ]]; then
    start_process "Frontend" "cd frontend && pnpm dev" "logs/frontend.log" "true" "" "Frontend server is running"
else
    log_file="logs/frontend.log"
    if [[ "$LOG_TO_FILE" == "false" ]]; then
        log_file="/tmp/frontend.log"
    fi
    start_process "Frontend" "cd frontend && pnpm dev" "$log_file" "true" "" "Frontend server is running"
fi

# Wait a moment for services to stabilize
sleep 3

# Display server information
display_server_info

# Keep the script running and handle shutdown gracefully
if [[ "$INTERACTIVE_MODE" == "true" ]]; then
    echo ""
    echo -e "${CYAN}📋 Logs are displayed in real-time above. Use Ctrl+C to stop all servers.${NC}"
    echo ""
    
    # Wait for user interrupt
    while true; do
        sleep 1
    done
else
    echo ""
    echo -e "${CYAN}📋 All services are running in background mode.${NC}"
    echo -e "${YELLOW}Logs are saved to: ${LOG_TO_FILE:+logs/}${LOG_TO_FILE:-/tmp/}${NC}"
    echo ""
    
    # Wait for user interrupt
    while true; do
        sleep 1
    done
fi