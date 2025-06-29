# Pipeline Quick Reference

A quick reference guide for common pipeline operations.

## Quick Commands

### First Time Setup
```bash
# Set required environment variables
export DATA_DIR="data/"
export VECTOR_STORAGE_PATH="db/vector_store"
export QDRANT_COLLECTION="blog_documents"
export EMBEDDING_MODEL="ollama:snowflake-arctic-embed2:latest"

# Create initial vector store
uv run python -m lets_talk.core.pipeline.cli --force-recreate
```

### Daily Operations
```bash
# Update with new/changed posts (recommended)
uv run python -m lets_talk.core.pipeline.cli --auto-incremental

# Check what would be processed
uv run python -m lets_talk.core.pipeline.cli --dry-run --incremental

# Force full rebuild
uv run python -m lets_talk.core.pipeline.cli --force-recreate
```

### System Checks
```bash
# Health check only
uv run python -m lets_talk.core.pipeline.cli --health-check-only

# Process with health check
uv run python -m lets_talk.core.pipeline.cli --auto-incremental --health-check
```

## Common Environment Variables

### Essential Settings
```bash
# Data and storage
export DATA_DIR="data/"
export VECTOR_STORAGE_PATH="db/vector_store"
export QDRANT_COLLECTION="blog_documents"
export EMBEDDING_MODEL="ollama:snowflake-arctic-embed2:latest"

# Output
export STATS_OUTPUT_DIR="./stats"
```

### Performance Tuning
```bash
# For large collections
export BATCH_SIZE="100"
export MAX_CONCURRENT_OPERATIONS="10"

# For small collections
export BATCH_SIZE="25"
export MAX_CONCURRENT_OPERATIONS="3"
```

### Debugging
```bash
export LOG_LEVEL="DEBUG"
export LOG_FORMAT="%(asctime)s [%(levelname)s] %(name)s:%(lineno)d - %(message)s"
```

## Common Scenarios

### Scenario 1: First Time Setup
```bash
# 1. Set environment
export DATA_DIR="data/"
export VECTOR_STORAGE_PATH="db/vector_store_v1"

# 2. Create vector store
uv run python -m lets_talk.core.pipeline.cli --force-recreate --health-check

# 3. Verify output
ls -la stats/
cat stats/blog_stats_latest.json
```

### Scenario 2: Regular Updates
```bash
# Daily/CI pipeline
uv run python -m lets_talk.core.pipeline.cli --ci --auto-incremental --health-check

# Development updates
uv run python -m lets_talk.core.pipeline.cli --auto-incremental
```

### Scenario 3: Troubleshooting
```bash
# 1. Dry run to see what would change
uv run python -m lets_talk.core.pipeline.cli --dry-run --incremental

# 2. Health check
uv run python -m lets_talk.core.pipeline.cli --health-check-only

# 3. Debug mode
export LOG_LEVEL="DEBUG"
uv run python -m lets_talk.core.pipeline.cli --auto-incremental

# 4. Force recreation if needed
uv run python -m lets_talk.core.pipeline.cli --force-recreate
```

### Scenario 4: Custom Processing
```bash
# Custom chunk sizes for better retrieval
uv run python -m lets_talk.core.pipeline.cli \
  --chunk-size 2000 \
  --chunk-overlap 400 \
  --auto-incremental

# Process different file types
uv run python -m lets_talk.core.pipeline.cli \
  --data-dir-pattern "*.txt" \
  --auto-incremental

# No chunking for short documents
uv run python -m lets_talk.core.pipeline.cli \
  --no-chunking \
  --auto-incremental
```

## Output Files Quick Reference

| File | Description | When Created |
|------|-------------|--------------|
| `blog_stats_latest.json` | Latest statistics | CI mode |
| `blog_stats_YYYYMMDD_HHMMSS.json` | Timestamped stats | Always |
| `blog_docs.csv` | Document details | When saving stats |
| `blog_metadata.csv` | Incremental metadata | After first run |
| `health_report.json` | Health check results | With `--health-check` |
| `ci_summary.json` | CI summary | CI mode |
| `vector_store_build_info.json` | Build info | CI mode |

## Exit Codes

| Code | Meaning | Action |
|------|---------|--------|
| 0 | Success | Continue |
| 1 | Error | Check logs, retry |

## Troubleshooting Quick Fixes

### Problem: "No documents to process"
```bash
# Check data directory
ls -la $DATA_DIR
echo "Pattern: $DATA_DIR_PATTERN"

# Verify file pattern
find $DATA_DIR -name "*.md" -type f
```

### Problem: "Vector store creation failed"
```bash
# Check permissions
ls -la $(dirname $VECTOR_STORAGE_PATH)

# Verify Qdrant (if remote)
curl -f $QDRANT_URL/collections || echo "Qdrant not accessible"

# Force recreation
uv run python -m lets_talk.core.pipeline.cli --force-recreate
```

### Problem: "Memory errors"
```bash
# Reduce batch size
export BATCH_SIZE="10"

# Smaller chunks
export CHUNK_SIZE="500"
export CHUNK_OVERLAP="50"

# Try no chunking
uv run python -m lets_talk.core.pipeline.cli --no-chunking
```

### Problem: "All documents being reprocessed"
```bash
# Check metadata file
ls -la stats/blog_metadata.csv

# Verify checksums
head -5 stats/blog_metadata.csv

# Run health check
uv run python -m lets_talk.core.pipeline.cli --health-check-only
```

## Performance Tips

### For Speed
- Use `--auto-incremental` for regular updates
- Increase `BATCH_SIZE` for large collections
- Set `MAX_CONCURRENT_OPERATIONS` based on CPU cores

### For Memory
- Reduce `BATCH_SIZE` if running out of memory
- Use smaller `CHUNK_SIZE` for large documents
- Consider `--no-chunking` for very small documents

### For Accuracy
- Use appropriate `CHUNK_SIZE` for your content (1000-2000 chars)
- Set `CHUNK_OVERLAP` to 10-20% of chunk size
- Run `--health-check` regularly

## CI/CD Quick Setup

### GitHub Actions
```yaml
- name: Update Vector Store
  run: |
    export VECTOR_STORAGE_PATH="db/vector_store"
    uv run python -m lets_talk.core.pipeline.cli --ci --auto-incremental --health-check
```

### Docker
```bash
# Build with environment
docker build --build-arg DATA_DIR=data/ .

# Run with mounted data
docker run -v $(pwd)/data:/app/data -v $(pwd)/db:/app/db my-pipeline
```

---

For detailed documentation, see [PIPELINE_USAGE_GUIDE.md](PIPELINE_USAGE_GUIDE.md).
