# Semantic Chunking Configuration Guide

This guide explains how to configure the SemanticChunker for optimal document chunking based on semantic similarity.

## Environment Variables

Add these environment variables to your `.env` file:

```bash
# Semantic Chunking Configuration
SEMANTIC_CHUNKER_BREAKPOINT_TYPE=percentile
SEMANTIC_CHUNKER_BREAKPOINT_THRESHOLD_AMOUNT=95.0
SEMANTIC_CHUNKER_MIN_CHUNK_SIZE=100
```

## Breakpoint Threshold Types

### 1. Percentile (Default)
- **Use case**: General purpose, works well for most documents
- **Threshold range**: 0.0 - 100.0 (default: 95.0)
- **How it works**: Splits when semantic distance is greater than the X percentile of all distances
- **Recommendations**:
  - 85-90: Smaller, more focused chunks
  - 95 (default): Balanced chunking
  - 97-99: Larger, more comprehensive chunks

```bash
SEMANTIC_CHUNKER_BREAKPOINT_TYPE=percentile
SEMANTIC_CHUNKER_BREAKPOINT_THRESHOLD_AMOUNT=95.0
```

### 2. Standard Deviation
- **Use case**: Documents with consistent structure and predictable content
- **Threshold range**: > 0.0 (default: 3.0)
- **How it works**: Splits when semantic distance is X standard deviations above the mean
- **Recommendations**:
  - 1.5-2.5: More sensitive, creates more chunks
  - 3.0 (default): Conservative approach
  - 3.5-5.0: Less sensitive, creates fewer chunks

```bash
SEMANTIC_CHUNKER_BREAKPOINT_TYPE=standard_deviation
SEMANTIC_CHUNKER_BREAKPOINT_THRESHOLD_AMOUNT=3.0
```

### 3. Interquartile
- **Use case**: Good for outlier detection and handling varied content lengths
- **Threshold range**: > 0.0 (default: 1.5)
- **How it works**: Uses interquartile range to identify breakpoints
- **Recommendations**:
  - 1.0-1.2: More sensitive to outliers
  - 1.5 (default): Balanced outlier detection
  - 2.0-3.0: Less sensitive, fewer splits

```bash
SEMANTIC_CHUNKER_BREAKPOINT_TYPE=interquartile
SEMANTIC_CHUNKER_BREAKPOINT_THRESHOLD_AMOUNT=1.5
```

### 4. Gradient
- **Use case**: Highly correlated or domain-specific content (legal, medical, technical)
- **Threshold range**: 0.0 - 100.0 (default: 95.0)
- **How it works**: Applies anomaly detection on gradient array, then uses percentile method
- **Recommendations**:
  - Use for specialized domains where semantic relationships are subtle
  - Same threshold ranges as percentile method

```bash
SEMANTIC_CHUNKER_BREAKPOINT_TYPE=gradient
SEMANTIC_CHUNKER_BREAKPOINT_THRESHOLD_AMOUNT=95.0
```

## Configuration Examples by Use Case

### Blog Posts and Articles
```bash
SEMANTIC_CHUNKER_BREAKPOINT_TYPE=percentile
SEMANTIC_CHUNKER_BREAKPOINT_THRESHOLD_AMOUNT=90.0
SEMANTIC_CHUNKER_MIN_CHUNK_SIZE=150
```

### Technical Documentation
```bash
SEMANTIC_CHUNKER_BREAKPOINT_TYPE=standard_deviation
SEMANTIC_CHUNKER_BREAKPOINT_THRESHOLD_AMOUNT=2.5
SEMANTIC_CHUNKER_MIN_CHUNK_SIZE=200
```

### Legal Documents
```bash
SEMANTIC_CHUNKER_BREAKPOINT_TYPE=gradient
SEMANTIC_CHUNKER_BREAKPOINT_THRESHOLD_AMOUNT=97.0
SEMANTIC_CHUNKER_MIN_CHUNK_SIZE=300
```

### Mixed Content Types
```bash
SEMANTIC_CHUNKER_BREAKPOINT_TYPE=interquartile
SEMANTIC_CHUNKER_BREAKPOINT_THRESHOLD_AMOUNT=1.8
SEMANTIC_CHUNKER_MIN_CHUNK_SIZE=100
```

## Programmatic Configuration

You can also configure semantic chunking programmatically:

```python
from lets_talk.core.pipeline.services.chunking_service import ChunkingService
from lets_talk.shared.config import SemanticChunkerBreakpointType

# Create service with custom semantic chunking configuration
service = ChunkingService(
    semantic_breakpoint_type=SemanticChunkerBreakpointType.PERCENTILE,
    semantic_breakpoint_threshold_amount=92.0,
    semantic_min_chunk_size=150
)

# Validate configuration
if service.validate_semantic_chunker_config():
    print("Configuration is valid")
    
# Get configuration info and recommendations
config_info = service.get_semantic_chunker_config_info()
print(f"Using {config_info['breakpoint_type']} with threshold {config_info['breakpoint_threshold_amount']}")
print(f"Recommendation: {config_info['recommendation']}")
```

## Tuning Guidelines

1. **Start with percentile (95.0)** for most use cases
2. **Monitor chunk sizes** and adjust threshold accordingly:
   - Too many small chunks → Increase threshold
   - Too few large chunks → Decrease threshold
3. **Consider content type**:
   - Narrative content: percentile or interquartile
   - Technical content: standard_deviation
   - Legal/medical: gradient
4. **Test with sample documents** to find optimal settings
5. **Use validation methods** to ensure configuration is correct

## Troubleshooting

### Chunks too small
- Increase `SEMANTIC_CHUNKER_BREAKPOINT_THRESHOLD_AMOUNT`
- Increase `SEMANTIC_CHUNKER_MIN_CHUNK_SIZE`
- Consider switching to `standard_deviation` or `interquartile`

### Chunks too large
- Decrease `SEMANTIC_CHUNKER_BREAKPOINT_THRESHOLD_AMOUNT`
- Switch to `percentile` with lower threshold (85-90)

### Inconsistent chunking
- Try `interquartile` for better outlier handling
- Use `gradient` for highly correlated content

### Performance issues
- `percentile` is generally fastest
- `gradient` is most computationally intensive
