---
title: Lets Talk
emoji: 🐨
colorFrom: green
colorTo: blue
sdk: docker
pinned: false
---

# Let’s Talk: Interactive AI Chat for Technical Blogs 🐨

Have you ever wished you could ask follow-up questions while reading technical content? Meet **Let’s Talk** – an AI-driven chat component designed to make technical blog content more interactive and accessible.

---

## The Problem: Content Navigation Challenges

Technical blogs often present challenges for readers:

- Difficulty finding specific information across multiple posts
- Limited ability to explore topics in depth
- One-way communication without follow-up capabilities
- Reduced information retention

## What Can You Do With Let’s Talk?

- **Ask questions about blog topics** – Get concise answers about RAG systems, LLMs, and more
- **Request code examples** – Receive practical code snippets for your use case
- **Explore concepts deeper** – Get clarification without searching multiple articles
- **Receive personalized guidance** – Information tailored to your background

## Under the Hood: Technical Implementation

Let’s Talk combines several AI technologies:

- **Document Ingestion:** Supports ingesting documents from both the file system and websites
- **Advanced Text Processing:** Utilizes recursive text splitting and semantic chunking for optimal context management
- **Retrievers:** Includes BM25, multiple query retrievers, and semantic search for flexible information retrieval
- **Advanced Embedding Technology:** Leverages powerful models like [Snowflake/snowflake-arctic-embed-l-v2.0](https://huggingface.co/Snowflake/snowflake-arctic-embed-l-v2.0) with flexible support for custom embedding models from any provider
- **Vector Database:** Qdrant for efficient content indexing
- **Language Models:** GPT-4o-mini for production, with GPT-4.1 for evaluation, plus support for integrating other LLMs and providers
- **Orchestration:** LangChain and LangGraph for the complete RAG workflow
- **Interface:** Chainlit for prototyping, with future Svelte component integration

## Try It For Yourself!

Let's Talk is available in multiple implementations:

- **Live on [TheDataGuy.PRO](https://thedataguy.pro/)** - Our initial implementation
- **[D365 Stuff Chat](https://huggingface.co/spaces/mafzaal/d365stuff-chat)** - Powering the [D365 Stuff Blog](https://www.d365stuff.co/)
- **[Hugging Face Spaces](https://huggingface.co/spaces/mafzaal/lets_talk)** - Try the prototype directly

Ask questions about RAG evaluation, research agents, data strategy, or any other topics from my blog to see Let's Talk in action!

## Pipeline Scheduling and Management 🕐

Let's Talk now includes a comprehensive pipeline scheduling system built with FastAPI:

- **Automated Content Updates:** Schedule regular pipeline runs to keep your content up-to-date
- **Flexible Scheduling:** Support for cron expressions, intervals, and one-time runs
- **REST API Management:** Full API for creating, monitoring, and managing scheduled jobs
- **Real-time Monitoring:** Health checks, execution statistics, and error tracking
- **Preset Configurations:** Common scheduling patterns (daily, weekly, hourly)

### Quick Start with Pipeline Scheduling

```bash
# Start the FastAPI scheduler server
./start_scheduler_api.sh

# Or manually with uvicorn
cd py-src && uv run uvicorn lets_talk.api.main:app --host 0.0.0.0 --port 8000

# Alternative: Use the main entry point
cd py-src && uv run python lets_talk/main.py
```

Visit `http://localhost:8000/docs` for the interactive API documentation.

For complete documentation, see [Pipeline Scheduling API Guide](docs/PIPELINE_SCHEDULING_API.md).

## Architecture Overview 🏗️

Let's Talk features a modular, layered architecture for maintainability and scalability:

### Core Components

- **`agents/`** - AI agent implementations (RAG, ReAct) with factory pattern
- **`api/`** - FastAPI application with modular endpoints and Pydantic models
- **`core/`** - Business logic (pipeline, scheduler, RAG retrieval, domain models)
- **`tools/`** - External integrations and utilities (RSS, datetime, contact forms)
- **`utils/`** - Helper functions (blog processing, document formatting)
- **`shared/`** - Configuration, constants, exceptions, and prompt templates

### Getting Started

```bash
# Install dependencies
uv install

# Run the API server
cd py-src && uv run python lets_talk/main.py

# Run pipeline manually
cd py-src && uv run python -m lets_talk.core.pipeline.engine

# Use scheduler CLI
cd py-src && uv run python -m lets_talk.core.scheduler.cli --help
```

### Import Examples

```python
# Create agents
from lets_talk.agents import create_rag_agent, create_react_agent

# Access API
from lets_talk.api.main import app

# Use core components
from lets_talk.core.pipeline.engine import run_pipeline
from lets_talk.core.scheduler.manager import PipelineScheduler
from lets_talk.shared.config import Configuration
```

## Future Enhancements

Planned improvements include:

- Advanced reasoning capabilities
- More immersive user experience with custom Svelte UI integration
- Automated content updates
- Expanded knowledge sources

## Open Source and Available

Let’s Talk is fully open source! You can find the code repository on [GitHub](https://github.com/mafzaal/lets-talk).

If you find this project useful:

- ⭐ Star the repository to show your support
- 🔄 Fork it to contribute your own improvements
- 🔗 Share it with others who might benefit

Looking to add a similar chat component to your technical blog or documentation? Feel free to reach out – I’m happy to assist with integration and customization for your specific needs.

---

## Conclusion

Let’s Talk represents a shift from static content consumption to interactive knowledge exploration, creating a personalized learning experience for every reader.

Have questions about Let’s Talk or suggestions for its improvement? Leave a comment via Let’s Talk or reach out directly. I’d love to hear your feedback!
