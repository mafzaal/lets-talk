# Blog Data Utilities

This directory contains utilities for loading, processing, and maintaining blog post data for the RAG system.

## Available Tools

### `utils_data_loading.ipynb`

This notebook contains utility functions for:
- Loading blog posts from the data directory
- Processing and enriching metadata (adding URLs, titles, etc.)
- Getting statistics about the documents
- Creating and updating vector embeddings
- Loading existing vector stores

### `update_blog_data.ipynb`

This notebook demonstrates how to:
- Use the utility functions to update the blog data
- Process new blog posts
- Update the vector store
- Test the updated system with sample queries
- Track changes over time

## How to Use

### Updating Blog Data

When new blog posts are published, follow these steps:

1. Add the markdown files to the `data/` directory
2. Run the update notebook:
   ```bash
   cd /home/mafzaal/source/lets-talk
   uv run jupyter nbconvert --to notebook --execute update_blog_data.ipynb --output executed_update_$(date +%Y%m%d).ipynb
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
FORCE_RECREATE_EMBEDDINGS=false           # Whether to force recreation
```

### In the Chainlit App

The Chainlit app (`app.py`) has been updated to use these utility functions if available. It falls back to direct initialization if they can't be loaded.

## Adding Custom Processing

To add custom processing for blog posts:

1. Edit the `update_document_metadata` function in `utils_data_loading.ipynb`
2. Add any additional enrichment or processing steps
3. Update the vector store using the `update_blog_data.ipynb` notebook

## Future Improvements

- Add support for incremental updates (only process new posts)
- Add webhook support to automatically update when new posts are published
- Add tracking of embedding models and versions
