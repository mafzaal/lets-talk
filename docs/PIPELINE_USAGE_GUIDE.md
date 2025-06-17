# Pipeline Usage Guide

This guide provides comprehensive documentation for using the `pipeline.py` script to manage your blog data vector store.

## Table of Contents

1. [Overview](#overview)
2. [Quick Start](#quick-start)
3. [Configuration](#configuration)
4. [Command Line Options](#command-line-options)
5. [Indexing Modes](#indexing-modes)
6. [Environment Variables](#environment-variables)
7. [Output Files](#output-files)
8. [Health Checks](#health-checks)
9. [Examples](#examples)
10. [Troubleshooting](#troubleshooting)

## Overview

The pipeline script (`pipeline.py`) is the main tool for creating and updating your blog data vector store. It processes markdown blog posts, creates embeddings, and stores them in a Qdrant vector database for efficient retrieval.

### Key Features

- **Incremental Indexing**: Only processes changed documents
- **Configurable Processing**: Extensive configuration via environment variables
- **Health Monitoring**: Built-in system health checks
- **Batch Processing**: Optimized for large document collections
- **Multiple Output Formats**: Statistics, metadata, and build information
- **CI/CD Integration**: Special modes for automated deployments

## Quick Start

### Basic Usage

```bash
# Create vector store from all documents
uv run python lets_talk/pipeline.py

# Force recreation of the vector store
uv run python lets_talk/pipeline.py --force-recreate

# Run with custom data directory
uv run python lets_talk/pipeline.py --data-dir /path/to/blog/posts

# Dry run to see what would be processed
uv run python lets_talk/pipeline.py --dry-run
```

### First Time Setup

1. Set up your environment variables (see [Configuration](#configuration))
2. Place your blog posts in the data directory
3. Run the pipeline:
   ```bash
   uv run python lets_talk/pipeline.py --force-recreate
   ```

## Configuration

### Required Configuration

Set these environment variables before running the pipeline:

```bash
# Data source
export DATA_DIR="data/"
export VECTOR_STORAGE_PATH="db/vector_store"
export QDRANT_COLLECTION="blog_documents"

# Embedding model
export EMBEDDING_MODEL="ollama:snowflake-arctic-embed2:latest"
```

### Optional Configuration

```bash
# Output settings
export STATS_OUTPUT_DIR="./stats"
export OUTPUT_DIR="output/"

# Processing options
export USE_CHUNKING="True"
export CHUNK_SIZE="1000"
export CHUNK_OVERLAP="200"

# Incremental indexing
export INCREMENTAL_MODE="auto"
export INCREMENTAL_FALLBACK_THRESHOLD="0.8"

# Performance tuning
export BATCH_SIZE="50"
export MAX_CONCURRENT_OPERATIONS="5"
```

## Command Line Options

### Data Processing Options

| Option | Description | Default |
|--------|-------------|---------|
| `--data-dir` | Directory containing blog posts | From `DATA_DIR` config |
| `--data-dir-pattern` | Glob pattern for blog files | `*.md` |
| `--output-dir` | Directory for stats and artifacts | `./stats` |
| `--vector-storage-path` | Vector database storage path | From config |
| `--collection-name` | Qdrant collection name | From config |
| `--embedding-model` | Embedding model to use | From config |

### Processing Control

| Option | Description |
|--------|-------------|
| `--force-recreate` | Force recreation of vector store |
| `--no-chunking` | Don't split documents into chunks |
| `--no-save-stats` | Don't save document statistics |
| `--chunk-size` | Size of each chunk in characters |
| `--chunk-overlap` | Overlap between chunks |

### Indexing Modes

| Option | Description |
|--------|-------------|
| `--incremental` | Enable incremental indexing |
| `--auto-incremental` | Auto-detect indexing mode |
| `--incremental-only` | Force incremental (fail if no metadata) |
| `--incremental-with-fallback` | Try incremental, fallback to full |
| `--dry-run` | Show what would be processed |

### System & Diagnostics

| Option | Description |
|--------|-------------|
| `--health-check` | Perform health check after processing |
| `--health-check-only` | Only perform health check and exit |
| `--ci` | Run in CI mode (no prompts, exit codes) |

## Indexing Modes

### Full Indexing

Processes all documents and recreates the vector store:

```bash
# Force full recreation
uv run python lets_talk/pipeline.py --force-recreate

# First time or when metadata is missing
uv run python lets_talk/pipeline.py
```

### Incremental Indexing

Only processes new and modified documents:

```bash
# Auto-detect mode (recommended)
uv run python lets_talk/pipeline.py --auto-incremental

# Force incremental mode
uv run python lets_talk/pipeline.py --incremental-only

# Incremental with fallback to full rebuild
uv run python lets_talk/pipeline.py --incremental-with-fallback
```

### Dry Run

Preview what would be processed without making changes:

```bash
uv run python lets_talk/pipeline.py --dry-run --incremental
```

## Environment Variables

### Core Configuration

| Variable | Description | Default |
|----------|-------------|---------|
| `DATA_DIR` | Blog posts directory | `data/` |
| `DATA_DIR_PATTERN` | File pattern for blog posts | `*.md` |
| `VECTOR_STORAGE_PATH` | Vector database path | Required |
| `QDRANT_COLLECTION` | Collection name | `lets_talk_documents` |
| `EMBEDDING_MODEL` | Embedding model | `ollama:snowflake-arctic-embed2:latest` |

### Output Configuration

| Variable | Description | Default |
|----------|-------------|---------|
| `STATS_OUTPUT_DIR` | Statistics output directory | `./stats` |
| `BLOG_STATS_FILENAME` | Stats file name | `blog_stats_latest.json` |
| `BLOG_DOCS_FILENAME` | Document details file | `blog_docs.csv` |
| `HEALTH_REPORT_FILENAME` | Health report file | `health_report.json` |
| `CI_SUMMARY_FILENAME` | CI summary file | `ci_summary.json` |
| `BUILD_INFO_FILENAME` | Build information file | `vector_store_build_info.json` |

### Processing Configuration

| Variable | Description | Default |
|----------|-------------|---------|
| `USE_CHUNKING` | Enable document chunking | `True` |
| `CHUNK_SIZE` | Chunk size in characters | `1000` |
| `CHUNK_OVERLAP` | Overlap between chunks | `200` |
| `INCREMENTAL_FALLBACK_THRESHOLD` | Threshold for fallback to full rebuild | `0.8` |
| `BATCH_SIZE` | Documents per batch | `50` |

### Logging Configuration

| Variable | Description | Default |
|----------|-------------|---------|
| `LOG_LEVEL` | Logging level | `INFO` |
| `LOG_FORMAT` | Log message format | Standard format |
| `LOGGER_NAME` | Logger name | `blog-pipeline` |

## Output Files

### Statistics Files

- **`blog_stats_latest.json`**: Latest statistics (CI mode)
- **`blog_stats_YYYYMMDD_HHMMSS.json`**: Timestamped statistics
- **`blog_docs.csv`**: Detailed document information

### Metadata Files

- **`blog_metadata.csv`**: Document metadata for incremental indexing
- **`vector_store_build_info.json`**: Build information (CI mode)
- **`ci_summary.json`**: CI pipeline summary

### Health Reports

- **`health_report.json`**: System health check results

## Health Checks

### Basic Health Check

Run after processing to verify system health:

```bash
uv run python lets_talk/pipeline.py --health-check
```

### Health Check Only

Perform comprehensive health check without processing:

```bash
uv run python lets_talk/pipeline.py --health-check-only
```

### Health Check Components

- Vector store connectivity
- Collection existence and status
- Embedding model availability
- Metadata file integrity
- Index consistency

## Examples

### Development Workflow

```bash
# Initial setup
export DATA_DIR="data/"
export VECTOR_STORAGE_PATH="db/vector_store"
export EMBEDDING_MODEL="ollama:snowflake-arctic-embed2:latest"

# First time creation
uv run python lets_talk/pipeline.py --force-recreate

# Regular updates (incremental)
uv run python lets_talk/pipeline.py --auto-incremental

# Check what would be processed
uv run python lets_talk/pipeline.py --dry-run --incremental
```

### Production Deployment

```bash
# Set production environment
export STATS_OUTPUT_DIR="/var/log/blog-pipeline"
export LOG_LEVEL="WARNING"
export BATCH_SIZE="100"

# Run in CI mode
uv run python lets_talk/pipeline.py --ci --auto-incremental --health-check
```

### Custom Processing

```bash
# Custom chunk sizes
uv run python lets_talk/pipeline.py \
  --chunk-size 2000 \
  --chunk-overlap 400 \
  --auto-incremental

# Different data source
uv run python lets_talk/pipeline.py \
  --data-dir "/path/to/custom/posts" \
  --data-dir-pattern "*.markdown" \
  --output-dir "./custom-stats"

# No chunking for small documents
uv run python lets_talk/pipeline.py \
  --no-chunking \
  --auto-incremental
```

### Debugging and Diagnostics

```bash
# Verbose logging
export LOG_LEVEL="DEBUG"
uv run python lets_talk/pipeline.py --health-check-only

# Dry run with detailed output
uv run python lets_talk/pipeline.py --dry-run --incremental

# Force recreation with health check
uv run python lets_talk/pipeline.py --force-recreate --health-check
```

## Troubleshooting

### Common Issues

#### 1. Vector Store Creation Fails

**Problem**: Error creating vector store

**Solution**:
```bash
# Check vector storage path permissions
ls -la $(dirname $VECTOR_STORAGE_PATH)

# Verify Qdrant is running (if using remote)
curl -f $QDRANT_URL/collections

# Force recreation
uv run python lets_talk/pipeline.py --force-recreate
```

#### 2. Incremental Indexing Not Working

**Problem**: All documents being reprocessed

**Solution**:
```bash
# Check metadata file exists
ls -la $STATS_OUTPUT_DIR/blog_metadata.csv

# Verify checksum algorithm
export CHECKSUM_ALGORITHM="sha256"

# Run health check
uv run python lets_talk/pipeline.py --health-check-only
```

#### 3. Out of Memory Errors

**Problem**: Pipeline crashes with memory errors

**Solution**:
```bash
# Reduce batch size
export BATCH_SIZE="10"

# Disable chunking for large documents
uv run python lets_talk/pipeline.py --no-chunking

# Process smaller chunks
export CHUNK_SIZE="500"
```

#### 4. Embedding Model Issues

**Problem**: Embedding model not available

**Solution**:
```bash
# Check model availability
curl -f $OLLAMA_BASE_URL/api/tags

# Use different model
export EMBEDDING_MODEL="openai:text-embedding-3-small"

# Verify model name
export EMBEDDING_MODEL="ollama:snowflake-arctic-embed2:latest"
```

### Exit Codes

| Code | Description |
|------|-------------|
| 0 | Success |
| 1 | General error |
| 2 | Configuration error |
| 3 | Health check failed |

### Debug Commands

```bash
# Check configuration
uv run python -c "from lets_talk.config import *; print(f'Data dir: {DATA_DIR}')"

# Verify imports
uv run python -c "from lets_talk.pipeline import parse_args; print('Import successful')"

# Test health check
uv run python lets_talk/pipeline.py --health-check-only --output-dir /tmp/test
```

### Log Analysis

```bash
# Enable debug logging
export LOG_LEVEL="DEBUG"

# Custom log format for debugging
export LOG_FORMAT="%(asctime)s [%(levelname)s] %(name)s:%(lineno)d - %(message)s"

# Save logs to file
uv run python lets_talk/pipeline.py 2>&1 | tee pipeline.log
```

## Performance Optimization

### For Large Document Collections

```bash
# Increase batch size
export BATCH_SIZE="100"

# Enable concurrent processing
export MAX_CONCURRENT_OPERATIONS="10"

# Optimize chunking
export CHUNK_SIZE="1500"
export CHUNK_OVERLAP="150"
```

### For Frequent Updates

```bash
# Use incremental mode
export INCREMENTAL_MODE="auto"

# Lower fallback threshold
export INCREMENTAL_FALLBACK_THRESHOLD="0.5"

# Enable performance monitoring
export ENABLE_PERFORMANCE_MONITORING="True"
```

## CI/CD Integration

### GitHub Actions Example

```yaml
- name: Update Vector Store
  run: |
    export VECTOR_STORAGE_PATH="${{ github.workspace }}/db"
    export STATS_OUTPUT_DIR="${{ github.workspace }}/artifacts"
    uv run python py-src/lets_talk/pipeline.py --ci --auto-incremental --health-check
  
- name: Upload Artifacts
  uses: actions/upload-artifact@v3
  with:
    name: pipeline-artifacts
    path: artifacts/
```

### Docker Integration

```dockerfile
ENV DATA_DIR=/data
ENV VECTOR_STORAGE_PATH=/app/db
ENV STATS_OUTPUT_DIR=/app/artifacts

CMD ["uv", "run", "python", "lets_talk/pipeline.py", "--ci", "--auto-incremental"]
```

---

For more information, see the [source code documentation](../py-src/lets_talk/pipeline.py) and [configuration reference](../py-src/lets_talk/config.py).
