# Blog Data Utilities

This directory contains utilities for loading, processing, and maintaining blog post data for the RAG system.

## Available Tools

### `blog_utils.py`

This Python module contains utility functions for:
- Loading blog posts from the data directory
- Processing and enriching metadata (adding URLs, titles, etc.)
- Getting statistics about the documents
- Creating and updating vector embeddings
- Loading existing vector stores

### `update_blog_data.py`

This script allows you to:
- Update the blog data when new posts are published
- Process new blog posts
- Update the vector store
- Track changes over time

### Legacy Notebooks (Reference Only)

The following notebooks are kept for reference but the functionality has been moved to Python modules:

- `utils_data_loading.ipynb` - Contains the original utility functions
- `update_blog_data.ipynb` - Demonstrates the update workflow

## How to Use

### Updating Blog Data

When new blog posts are published, follow these steps:

1. Add the markdown files to the `data/` directory
2. Run the update script:
   ```bash
   cd /home/mafzaal/source/lets-talk
   uv run python update_blog_data.py
   ```
   
   You can also force recreation of the vector store:
   ```bash
   uv run python update_blog_data.py --force-recreate
   ```

This will:
- Load all blog posts (including new ones)
- Update the vector embeddings
- Save statistics for tracking

### Customizing the Process

You can customize the process by editing the `.env` file:

```
DATA_DIR=data/                             # Directory containing blog posts
VECTOR_STORAGE_PATH=./db/vectorstore_v3    # Path to vector store
EMBEDDING_MODEL=Snowflake/snowflake-arctic-embed-l  # Embedding model
QDRANT_COLLECTION=thedataguy_documents     # Collection name
BLOG_BASE_URL=https://thedataguy.pro/blog/ # Base URL for blog
```

### In the Chainlit App

The Chainlit app (`app.py`) has been updated to use these utility functions from the `blog_utils.py` module. It falls back to notebook import and direct initialization if there are any issues.

## Adding Custom Processing

To add custom processing for blog posts:

1. Edit the `update_document_metadata` function in `blog_utils.py`
2. Add any additional enrichment or processing steps
3. Update the vector store using the `update_blog_data.py` script

## Future Improvements

- Add scheduled update process for automatically including new blog posts
- Add tracking of embedding models and versions
- Add webhook support to automatically update when new posts are published
