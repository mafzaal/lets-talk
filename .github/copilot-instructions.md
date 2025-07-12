# GitHub Copilot Project Instructions

This file provides guidelines for GitHub Copilot to interact with this repository efficiently and consistently.

## Python Package Management and Execution

- Always use the `uv` package manager for Python dependencies
- Use `uv add` instead of regular `pip install`
- Execute Python scripts with `uv run` instead of directly using the Python interpreter
- For virtual environments, use `uv venv` to create them
- When generating requirements files, use `uv pip freeze` instead of `pip freeze`

## Frontend (Svelte, SvelteKit, shadcn-svelte) and JS/TS Package Management

- Always use `pnpm` for JavaScript/TypeScript package management
- Use `pnpm install <package>` to add dependencies
- Use `pnpm` scripts (e.g., `pnpm dev`, `pnpm build`, `pnpm preview`) to run, build, and preview the frontend
- The frontend uses **Svelte 5** and **SvelteKit**; follow their conventions for routing, file structure, and component usage
- For UI components, use **shadcn-svelte**; prefer shadcn-svelte components for new UI work
- When adding new UI components, use the shadcn-svelte CLI (`pnpm shadcn-svelte add <component>`) where possible
- Follow SvelteKit best practices for endpoints, server-side logic, and routing

## Testing Guidelines
- Use `uv run pytest` to run tests instead of `pytest` directly
- For running specific test files, use `uv run pytest <test_file>` with the `-v` flag for verbose output
- For running specific test functions, use `uv run pytest <test_file>::<test_function>` with the `-v` flag
- Use `uv run python <script>` to run Python scripts that manage tests or other tasks
- When writing new tests, follow the existing naming conventions:
  - Use `test_document_loader_simple_pytest.py` for simple tests
  - Use `test_document_loader_pytest.py` for main tests
  - Use `test_document_loader_comprehensive_pytest.py` for comprehensive tests 
- Use `_pytest` suffix for new pytest files to avoid conflicts with existing unittest files
