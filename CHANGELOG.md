# Changelog

All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [0.1.5] - 2025-08-09

### Added
- Comprehensive entrypoint system with standalone startup script
- First-time execution detection and setup process
- Database existence check and creation logic
- Timezone and user agent configuration to environment setup
- Default job scheduling with environment configuration
- Comprehensive database migration system using Alembic
- System health monitoring and detailed startup banners
- API access control with nginx proxy and dynamic key loading
- CORS support for LangGraph API
- Incremental fallback threshold for document processing
- Comprehensive test suites for various components
- Semantic chunking configuration and implementation
- ChunkingStrategy enum implementation
- Enhanced API documentation with detailed descriptions
- Pipeline scheduling functionality
- Modular architecture with improved import paths
- Custom exceptions and utility tools
- Performance monitoring and optimization services
- Vector store management capabilities
- Backup management functionality
- Health checker functionality
- Enhanced startup process with detailed banners and system information display
- Database migration system with comprehensive error handling
- Default job scheduling functionality
- Comprehensive test coverage for core components

### Changed
- **BREAKING**: Renamed `py-src` folder to `backend` for better organization
- **BREAKING**: Updated import paths and configuration to reflect backend directory structure
- Migrated from legacy test files to pytest framework
- Refactored pipeline engine and job functions
- Enhanced embedding initialization
- Improved scheduler initialization error handling
- Updated document loading URL handling and vector store loading logic
- Enhanced pipeline configuration and logging
- Improved migration status checking logic
- Consolidated startup logic into a single system
- Updated LangGraph agent configuration for improved functionality
- Refactored codebase to modular architecture
- Enhanced scheduler API to include job execution args and kwargs
- Increased max workers and updated misfire grace time
- Improved document processing pipeline with better error handling
- Improved startup logic consolidation
- Enhanced pipeline configuration and logging
- Updated LangGraph configuration for better agent functionality

### Removed
- Legacy parameters from pipeline execution
- Deprecated job_functions module
- Chainlit dependencies for improved maintainability
- Outdated blog posts and related tools
- Legacy test files (converted to pytest)
- Demo pipeline functionality

### Fixed
- Timezone-aware datetime usage across multiple files
- Database URL sanitization for enhanced security
- Scheduler initialization error handling
- Document loader URL handling
- Job configuration access method compatibility
- Frontend build errors and Svelte 5 deprecation issues
- Input component binding for Svelte 5
- TypeScript errors in frontend components
- Dark mode text visibility issues
- System settings management reactivity
- Database creation logic for multiple databases
- Migration status checking accuracy
- Startup logging and entrypoint messages clarity

### Security
- Enhanced database URL sanitization to prevent sensitive information exposure
- Implemented API access control with nginx proxy
- Added CORS support with proper configuration
- Improved security schemes in OpenAPI schema

## [v2025.05.16-docs14] - 2025-05-16

### Added
- Enhanced documentation system
- Improved API documentation structure

## [v2025.05.15-docs14] - 2025-05-15

### Added
- Documentation versioning system
- Comprehensive API documentation

## [0.1.1] - 2025-06-01

### Added
- Initial release of Let's Talk interactive AI chat system
- Core RAG (Retrieval-Augmented Generation) functionality
- Support for multiple embedding models
- Qdrant vector database integration
- LangChain and LangGraph orchestration
- Document ingestion from file system and websites
- Advanced text processing with recursive splitting and semantic chunking
- Multiple retriever support (BM25, multiple query retrievers, semantic search)
- GPT-4o-mini and GPT-4.1 language model support
- Custom Svelte frontend component
- Docker containerization support
- Basic API endpoints for chat functionality

### Technical Features
- **Embedding Models**: Snowflake Arctic Embed L v2.0 support
- **Vector Database**: Qdrant for efficient content indexing
- **Language Models**: OpenAI GPT models with configurable providers
- **Frontend**: Svelte-based chat interface
- **Backend**: FastAPI with comprehensive endpoint support
- **Deployment**: Docker and docker-compose configuration

### Documentation
- Comprehensive README with setup instructions
- Environment configuration examples
- Feature descriptions and technical implementation details

---

## Migration Notes

### From 0.1.1 to 0.1.5+

1. **Directory Structure Change**: The `py-src` directory has been renamed to `backend`. Update any scripts or configurations that reference the old path.

2. **Import Path Updates**: All Python import paths have been updated to reflect the new `backend` directory structure.

3. **Database Migration**: A new Alembic-based database migration system has been implemented. Run migrations using the provided migration scripts.

4. **Environment Variables**: New environment variables have been added for timezone, user agent, and database configuration. Update your `.env` file accordingly.

5. **Testing Framework**: Tests have been migrated to pytest. Use `uv run pytest` instead of the previous test commands.

6. **Startup Process**: A new entrypoint system has been implemented. Use the provided startup scripts for development and production.

## Development Guidelines

- Always use `uv` for Python package management
- Use `pnpm` for JavaScript/TypeScript dependencies  
- Follow the new modular architecture when making changes
- Run tests with `uv run pytest` before submitting changes
- Use the provided development scripts for consistent startup processes

## Contributors

- Muhammad Afzaal (@mafzaal)
- Dependabot for automated dependency updates
- Copilot SWE Agent for various feature implementations and bug fixes
