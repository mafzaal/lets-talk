# Documentation Index

This directory contains comprehensive documentation for the blog pipeline system.

## Pipeline Documentation

### 📖 Main Guides

- **[Pipeline Usage Guide](PIPELINE_USAGE_GUIDE.md)** - Comprehensive guide for using the pipeline
- **[Pipeline Quick Reference](PIPELINE_QUICK_REFERENCE.md)** - Quick commands and common scenarios
- **[Pipeline Configuration Template](PIPELINE_CONFIG_TEMPLATE.env)** - Environment variables template

### 📋 Technical Reports

- **[Incremental Indexing Final Report](INCREMENTAL_INDEXING_FINAL_REPORT.md)** - Detailed technical implementation report

## Quick Start

1. **First Time Setup**:
   ```bash
   # Copy and customize configuration
   cp docs/PIPELINE_CONFIG_TEMPLATE.env .env
   
   # Edit .env with your settings
   nano .env
   
   # Create initial vector store
   uv run python py-src/lets_talk/pipeline.py --force-recreate
   ```

2. **Daily Usage**:
   ```bash
   # Update with incremental indexing
   uv run python py-src/lets_talk/pipeline.py --auto-incremental
   ```

3. **Troubleshooting**:
   ```bash
   # Health check
   uv run python py-src/lets_talk/pipeline.py --health-check-only
   
   # See what would be processed
   uv run python py-src/lets_talk/pipeline.py --dry-run --incremental
   ```

## Documentation Structure

```
docs/
├── README.md                          # This file
├── PIPELINE_USAGE_GUIDE.md           # Complete usage guide
├── PIPELINE_QUICK_REFERENCE.md       # Quick commands reference
├── PIPELINE_CONFIG_TEMPLATE.env      # Configuration template
└── INCREMENTAL_INDEXING_FINAL_REPORT.md  # Technical implementation details
```

## Key Features Covered

### 🔄 **Incremental Indexing**
- Automatic detection of new, modified, and deleted documents
- Configurable fallback thresholds
- Metadata tracking for efficient updates

### ⚙️ **Configuration Management**
- Environment variable-based configuration
- Customizable output files and directories
- Performance tuning options

### 🔍 **Health Monitoring**
- Comprehensive system health checks
- Vector store validation
- Metadata integrity verification

### 🚀 **Performance Optimization**
- Batch processing for large collections
- Concurrent operations
- Memory-efficient chunking

### 🛠️ **Debugging & Troubleshooting**
- Dry-run mode for testing changes
- Detailed logging configuration
- Common problem solutions

## Getting Help

1. **For usage questions**: See [Pipeline Usage Guide](PIPELINE_USAGE_GUIDE.md)
2. **For quick commands**: See [Pipeline Quick Reference](PIPELINE_QUICK_REFERENCE.md)
3. **For configuration**: Use [Pipeline Configuration Template](PIPELINE_CONFIG_TEMPLATE.env)
4. **For technical details**: See [Incremental Indexing Report](INCREMENTAL_INDEXING_FINAL_REPORT.md)

## Common Use Cases

| Use Case | Documentation | Command |
|----------|---------------|---------|
| First-time setup | [Usage Guide](PIPELINE_USAGE_GUIDE.md#quick-start) | `--force-recreate` |
| Regular updates | [Quick Reference](PIPELINE_QUICK_REFERENCE.md#daily-operations) | `--auto-incremental` |
| Debugging issues | [Usage Guide](PIPELINE_USAGE_GUIDE.md#troubleshooting) | `--health-check-only` |
| Configuration | [Config Template](PIPELINE_CONFIG_TEMPLATE.env) | Edit `.env` file |
| Performance tuning | [Usage Guide](PIPELINE_USAGE_GUIDE.md#performance-optimization) | Adjust environment variables |

## Recent Updates

- ✅ **Parameterized Configuration**: All hardcoded values are now configurable via environment variables
- ✅ **Comprehensive Documentation**: Complete usage guides and quick reference
- ✅ **Configuration Templates**: Ready-to-use environment variable templates
- ✅ **Troubleshooting Guides**: Common issues and solutions documented

---

For the latest updates and source code, see the [pipeline implementation](../py-src/lets_talk/pipeline.py) and [configuration](../py-src/lets_talk/config.py).
