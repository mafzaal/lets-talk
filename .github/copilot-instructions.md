# GitHub Copilot Project Instructions

This file provides guidelines for GitHub Copilot to interact with this repository efficiently and consistently.

## Python Package Management and Execution

- Always use the `uv` package manager for Python dependencies
- Use `uv add` instead of regular `pip install`
- Execute Python scripts with `uv run` instead of directly using the Python interpreter
- For virtual environments, use `uv venv` to create them
- When generating requirements files, use `uv pip freeze` instead of `pip freeze`


## Frontend (Svelte 5, SvelteKit, shadcn-svelte) and JS/TS Package Management

- Always use `pnpm` for JavaScript/TypeScript package management
- Use `pnpm install <package>` to add dependencies
- Use `pnpm` scripts (e.g., `pnpm dev`, `pnpm build`, `pnpm preview`) to run, build, and preview the frontend
- The frontend uses **Svelte 5** and **SvelteKit**. Always:
  - Use modern Svelte 5 features such as runes (`$state`, `$derived`, `$effect`, etc.), the new store API, and the latest component patterns
  - Prefer the new Svelte 5 syntax and APIs for reactivity, state management, and component composition
  - Reference the official Svelte 5 and SvelteKit documentation for best practices
  - When in doubt, consult the [Svelte LLM docs](https://svelte.dev/docs/llms) for up-to-date usage and examples
- For all backend communication from the frontend, always add and use functions in `api.ts` instead of making direct calls to the backend (e.g., via fetch or axios) in components or stores.
- For UI components, use **shadcn-svelte**; prefer shadcn-svelte components for new UI work
- When adding new UI components, use the shadcn-svelte CLI (`pnpm shadcn-svelte add <component>`) where possible
- Follow SvelteKit best practices for endpoints, server-side logic, and routing

## Testing Guidelines

## Development and API Documentation
- Use the `start_backend_dev.sh`, `start_frontend_dev.sh`, or `start_langgraph_dev.sh` scripts as needed to start development servers or for testing purposes.
- When API documentation is needed, retrieve it from the backend or from `backend/langgraph` as appropriate.
- Use `uv run pytest` to run tests instead of `pytest` directly
- For running specific test files, use `uv run pytest <test_file>` with the `-v` flag for verbose output
- For running specific test functions, use `uv run pytest <test_file>::<test_function>` with the `-v` flag
- Use `uv run python <script>` to run Python scripts that manage tests or other tasks
- When writing new tests, follow the existing naming conventions:
  - Use `test_document_loader_simple_pytest.py` for simple tests
  - Use `test_document_loader_pytest.py` for main tests
  - Use `test_document_loader_comprehensive_pytest.py` for comprehensive tests 
- Use `_pytest` suffix for new pytest files to avoid conflicts with existing unittest files
