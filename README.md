---
title: Lets Talk
emoji: 🐨
colorFrom: green
colorTo: blue
sdk: docker
pinned: false
---

# Welcome to TheDataGuy Chat! 👋

This is a Q&A chatbot powered by [TheDataGuy blog](https://thedataguy.pro/blog/) blog posts. Ask questions about topics covered in the blog, such as:

- RAGAS and RAG evaluation
- Building research agents
- Metric-driven development
- Data science best practices

## How it works

Under the hood, this application uses:

1. **Snowflake Arctic Embeddings**: To convert text into vector representations
   - Base model: `Snowflake/snowflake-arctic-embed-l`
   - Fine-tuned model: `mafzaal/thedataguy_arctic_ft` (custom-tuned using blog-specific query-context pairs)

2. **Qdrant Vector Database**: To store and search for similar content
   - Efficiently indexes blog post content for fast semantic search
   - Supports real-time updates when new blog posts are published

3. **GPT-4o-mini**: To generate helpful responses based on retrieved content
   - Primary model: OpenAI `gpt-4o-mini` for production inference
   - Evaluation model: OpenAI `gpt-4.1` for complex tasks including synthetic data generation and evaluation

4. **LangChain**: For building the RAG workflow
   - Orchestrates the retrieval and generation components
   - Provides flexible components for LLM application development
   - Structured for easy maintenance and future enhancements

5. **Chainlit**: For the chat interface
   - Offers an interactive UI with message threading
   - Supports file uploads and custom components

## Technology Stack

### Core Components
- **Vector Database**: Qdrant (stores embeddings via `pipeline.py`)
- **Embedding Model**: Snowflake Arctic Embeddings
- **LLM**: OpenAI GPT-4o-mini
- **Framework**: LangChain + Chainlit
- **Development Language**: Python 3.13

### Advanced Features
- **Evaluation**: Ragas metrics for evaluating RAG performance:
  - Faithfulness
  - Context Relevancy
  - Answer Relevancy
  - Topic Adherence
- **Synthetic Data Generation**: For training and testing
- **Vector Store Updates**: Automated pipeline to update when new blog content is published
- **Fine-tuned Embeddings**: Custom embeddings tuned for technical content

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
│   │   └── tools.py       # Tool implementations
│   ├── app.py             # Main application entry point
│   └── pipeline.py        # Data processing pipeline
├── db/                    # Vector database storage
├── evals/                 # Evaluation datasets and results
└── notebooks/             # Jupyter notebooks for analysis
```

## Environment Setup

The application requires the following environment variables:

```
OPENAI_API_KEY=your_openai_api_key
VECTOR_STORAGE_PATH=./db/vector_store_tdg
LLM_MODEL=gpt-4o-mini
EMBEDDING_MODEL=Snowflake/snowflake-arctic-embed-l
```

## Running Locally

### Using Docker

```bash
docker build -t lets-talk .
docker run -p 7860:7860 \
    --env-file ./.env \
    lets-talk
```

### Using Python

```bash
# Install dependencies
uv init && uv sync

# Run the application
chainlit run py-src/app.py --host 0.0.0.0 --port 7860
```

## Deployment

The application is designed to be deployed on:

- **Development**: Hugging Face Spaces ([Live Demo](https://huggingface.co/spaces/mafzaal/lets_talk))
- **Production**: Azure Container Apps (planned)

## Evaluation

This project includes extensive evaluation capabilities using the Ragas framework:

- **Synthetic Data Generation**: For creating test datasets
- **Metric Evaluation**: Measuring faithfulness, relevance, and more
- **Fine-tuning Analysis**: Comparing different embedding models

## Future Enhancements

- **Agentic Reasoning**: Adding more sophisticated agent capabilities
- **Web UI Integration**: Custom Svelte component for the blog
- **CI/CD**: GitHub Actions workflow for automated deployment
- **Monitoring**: LangSmith integration for observability

## License

This project is available under the MIT License.

## Acknowledgements

- [TheDataGuy blog](https://thedataguy.pro/blog/) for the content
- [Ragas](https://docs.ragas.io/) for evaluation framework
- [LangChain](https://python.langchain.com/docs/get_started/introduction.html) for RAG components
- [Chainlit](https://docs.chainlit.io/) for the chat interface

Check out the configuration reference at https://huggingface.co/docs/hub/spaces-config-reference
