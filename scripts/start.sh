#!/bin/bash
# Start the backend server
cd "$(dirname "$0")/.." && uv run python main.py