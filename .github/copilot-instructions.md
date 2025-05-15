# GitHub Copilot Project Instructions

This file provides guidelines for GitHub Copilot to interact with this repository efficiently and consistently.

## Python Package Management and Execution

- Always use the `uv` package manager for Python dependencies
- Use `uv add` instead of regular `pip install`
- Execute Python scripts with `uv run` instead of directly using the Python interpreter
- For virtual environments, use `uv venv` to create them
- When generating requirements files, use `uv pip freeze` instead of `pip freeze`