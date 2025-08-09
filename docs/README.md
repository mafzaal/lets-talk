# Documentation Index

This directory contains comprehensive documentation for the Let's Talk system.

## Core Documentation

### 📖 Main Guides

- **[Architecture Documentation](ARCHITECTURE.md)** - Complete system architecture overview
- **[Migration Guide](MIGRATION_GUIDE.md)** - Migrate from legacy to new structure
- **[Pipeline Usage Guide](PIPELINE_USAGE_GUIDE.md)** - Comprehensive guide for using the pipeline
- **[Pipeline Quick Reference](PIPELINE_QUICK_REFERENCE.md)** - Quick commands and common scenarios
- **[Pipeline Scheduling API](PIPELINE_SCHEDULING_API.md)** - FastAPI scheduling endpoints
- **[Scheduler Documentation](SCHEDULER.md)** - Complete scheduler documentation
- **[Pipeline Configuration Template](PIPELINE_CONFIG_TEMPLATE.env)** - Environment variables template

### 📋 Technical Reports

- **[Incremental Indexing Final Report](INCREMENTAL_INDEXING_FINAL_REPORT.md)** - Detailed technical implementation report
- **[Scheduler Implementation Report](SCHEDULER_IMPLEMENTATION_REPORT.md)** - Scheduler implementation details

## Quick Start

### 1. First Time Setup

```bash
# Copy and customize configuration
cp docs/PIPELINE_CONFIG_TEMPLATE.env .env

# Edit .env with your settings
nano .env

# Create initial vector store
cd py-src && uv run python -m lets_talk.core.pipeline.engine --force-recreate
```

### 2. Start the Application

```bash
# Start the FastAPI server
cd py-src && uv run python lets_talk/main.py

# Or use the web frontend
cd frontend && pnpm dev
```

### 3. Daily Usage

```bash
# Update with incremental indexing
cd py-src && uv run python -m lets_talk.core.pipeline.engine --auto-incremental

# Use scheduler for automation
cd py-src && uv run python -m lets_talk.core.scheduler.cli start --daemon
```

### 4. Development

```bash
# Use programmatic API
cd py-src && uv run python -c "
from lets_talk.core.pipeline.engine import run_pipeline
from lets_talk.agents import create_rag_agent
from lets_talk.shared.config import load_configuration_with_prompts

# Run pipeline
result = run_pipeline(data_dir='data/', force_recreate=False)

# Create agents
config = load_configuration_with_prompts()
agent = create_rag_agent(config)
"
```

### 5. Troubleshooting

```bash
# Health check
cd py-src && uv run python -m lets_talk.core.pipeline.engine --health-check-only

# See what would be processed
cd py-src && uv run python -m lets_talk.core.pipeline.engine --dry-run --incremental

# Check imports
cd py-src && uv run python -c "import lets_talk; print('All imports working')"
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
