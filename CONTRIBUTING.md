# Contributing to TheDataGuy Chat

Thank you for your interest in contributing to the TheDataGuy Chat project! This document provides guidelines and instructions for contributing to this repository.

## Project Overview

TheDataGuy Chat is a Q&A chatbot powered by the content from [TheDataGuy blog](https://thedataguy.pro/blog/). It uses RAG (Retrieval Augmented Generation) to provide informative answers about topics such as RAGAS, RAG evaluation, building research agents, metric-driven development, and data science best practices.

## Development Environment Setup

### Prerequisites

- Python 3.13 or higher
- [uv](https://github.com/astral-sh/uv) for Python package management
- Docker (optional, for containerized development)
- OpenAI API key

### Local Setup

1. Clone the repository:
   ```bash
   git clone https://github.com/mafzaal/lets-talk.git
   cd lets-talk
   ```

2. Create a `.env` file with the necessary environment variables:
   ```
   OPENAI_API_KEY=your_openai_api_key
   VECTOR_STORAGE_PATH=./db/vector_store_tdg
   LLM_MODEL=gpt-4o-mini
   EMBEDDING_MODEL=Snowflake/snowflake-arctic-embed-l
   ```

3. Install dependencies:
   ```bash
   uv init && uv sync
   ```

4. Build the vector store:
   ```bash
   ./scripts/build-vector-store.sh
   ```

5. Run the application:
   ```bash
   chainlit run py-src/app.py --host 0.0.0.0 --port 7860
   ```

### Using Docker

1. Build the Docker image:
   ```bash
   docker build -t lets-talk .
   ```

2. Run the container:
   ```bash
   docker run -p 7860:7860 --env-file ./.env lets-talk
   ```

## Project Structure

```
lets-talk/
├── data/                  # Raw blog post content
├── py-src/                # Python source code
│   ├── lets_talk/         # Core application modules
│   │   ├── agent.py       # Agent implementation
│   │   ├── config.py      # Configuration settings
│   │   ├── models.py      # Data models
│   │   ├── prompts.py     # LLM prompt templates
│   │   ├── rag.py         # RAG implementation
│   │   ├── rss_tool.py    # RSS feed integration
│   │   ├── tools.py       # Tool implementations
│   │   └── utils/         # Utility functions
│   ├── app.py             # Main application entry point
│   ├── pipeline.py        # Data processing pipeline
│   └── notebooks/         # Jupyter notebooks for analysis
├── db/                    # Vector database storage
├── evals/                 # Evaluation datasets and results
└── scripts/               # Utility scripts
```

## Adding New Blog Posts

When new blog posts are published on TheDataGuy.pro, follow these steps to add them to the chat application:

1. Add the markdown content to the `data/` directory in a new folder named after the post slug
2. Run the vector store update script:
   ```bash
   python py-src/pipeline.py --force-recreate
   ```

## Workflow

1. **Fork** the repository on GitHub
2. **Clone** your fork to your local machine
3. Create a new **branch** for your feature or bug fix
4. Make your changes
5. Run the tests to ensure everything works
6. **Commit** your changes with clear, descriptive commit messages
7. **Push** your branch to your fork on GitHub
8. Submit a **Pull Request** to the main repository

## Code Style

- Follow PEP 8 style guidelines for Python code
- Use meaningful variable and function names
- Add docstrings to all functions and classes
- Include type hints where appropriate

## Testing

- Write tests for new features and bug fixes
- Ensure all tests pass before submitting a Pull Request
- Use the Ragas evaluation framework to test RAG performance

## Documentation

- Update relevant documentation when making changes
- Add docstrings to all functions, classes, and modules
- Keep the README and other documentation up to date

## License

By contributing to this project, you agree that your contributions will be licensed under the same license as the project (MIT License).

## Contact

If you have any questions or need further clarification, please reach out to the project maintainer at [contact form](https://thedataguy.pro/contact/).
