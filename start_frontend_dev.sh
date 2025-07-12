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

# Start the mock backend server
echo -e "${BLUE}🔧 Starting mock backend server...${NC}"
cat > /tmp/lets_talk_mock_backend.py << 'EOF'
#!/usr/bin/env python3
"""
Mock backend for testing the frontend.
This provides the necessary API endpoints with mock data.
"""

from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from datetime import datetime
import uvicorn
from typing import Dict, Any, List
from pydantic import BaseModel

app = FastAPI(title="Mock Let's Talk API", version="0.1.0")

# Add CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Mock data
mock_stats = {
    "jobs_executed": 42,
    "jobs_failed": 3,
    "jobs_missed": 1,
    "last_execution": datetime.now().isoformat(),
    "last_error": None,
    "active_jobs": 5,
    "scheduler_running": True
}

mock_jobs = [
    {
        "id": "daily_update",
        "name": "Daily Content Update",
        "next_run_time": "2024-07-13T02:00:00",
        "trigger": "cron",
        "config": {"incremental_mode": "auto"}
    },
    {
        "id": "weekly_backup",
        "name": "Weekly Full Backup",
        "next_run_time": "2024-07-14T01:00:00",
        "trigger": "cron",
        "config": {"force_recreate": True}
    }
]

mock_reports = [
    {
        "job_id": "daily_update",
        "execution_time": "2024-07-12T14:30:00",
        "status": "success",
        "duration": 45.2,
        "total_documents": 127,
        "errors": [],
        "warnings": []
    },
    {
        "job_id": "weekly_backup",
        "execution_time": "2024-07-12T10:15:00",
        "status": "success",
        "duration": 182.7,
        "total_documents": 1543,
        "errors": [],
        "warnings": ["Some documents were skipped"]
    },
    {
        "job_id": "hourly_check",
        "execution_time": "2024-07-12T09:00:00",
        "status": "failed",
        "duration": 12.1,
        "total_documents": 0,
        "errors": ["Connection timeout"],
        "warnings": []
    }
]

# Health endpoint
@app.get("/health")
async def get_health():
    return {
        "status": "healthy",
        "timestamp": datetime.now().isoformat(),
        "scheduler_status": "running",
        "version": "0.1.0"
    }

# Scheduler endpoints
@app.get("/scheduler/status")
async def get_scheduler_status():
    return mock_stats

@app.get("/scheduler/jobs")
async def get_jobs():
    return mock_jobs

@app.post("/scheduler/jobs/cron")
async def create_cron_job(data: Dict[str, Any]):
    return {"message": f"Cron job {data.get('job_id', 'unknown')} created successfully"}

@app.post("/scheduler/jobs/interval")
async def create_interval_job(data: Dict[str, Any]):
    return {"message": f"Interval job {data.get('job_id', 'unknown')} created successfully"}

@app.delete("/scheduler/jobs/{job_id}")
async def delete_job(job_id: str):
    return {"message": f"Job {job_id} deleted successfully"}

# Pipeline endpoints
@app.post("/pipeline/run")
async def run_pipeline(config: Dict[str, Any] = None):
    return {
        "message": "Pipeline execution started",
        "job_id": f"pipeline_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
    }

@app.get("/pipeline/reports")
async def get_pipeline_reports():
    return {"reports": mock_reports}

if __name__ == "__main__":
    print("Starting mock backend server...")
    uvicorn.run(app, host="0.0.0.0", port=8000)
EOF

# Start backend in background
echo -e "${BLUE}🔧 Starting backend server on port 8000...${NC}"
uv run python /tmp/lets_talk_mock_backend.py > /tmp/backend.log 2>&1 &
BACKEND_PID=$!

# Wait for backend to start
sleep 3

# Check if backend started successfully
if curl -s http://localhost:8000/health > /dev/null 2>&1; then
    echo -e "${GREEN}✅ Backend server is running on http://localhost:8000${NC}"
else
    echo -e "${RED}❌ Backend server failed to start. Check /tmp/backend.log for details.${NC}"
    exit 1
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
    exit 1
fi

echo -e "${GREEN}🎉 Setup complete!${NC}"
echo ""
echo -e "${BLUE}📱 Access the application:${NC}"
echo "   • Frontend: http://localhost:5173"
echo "   • Backend API: http://localhost:8000"
echo "   • API Documentation: http://localhost:8000/docs"
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
EOF