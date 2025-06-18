# Migration Guide: From Legacy to New Architecture

This guide helps users migrate from the old monolithic structure to the new modular architecture.

## Overview of Changes

The Let's Talk codebase has been completely restructured from a monolithic design to a modular, layered architecture. This improves maintainability, testability, and extensibility.

## Breaking Changes

### 1. Import Statements

**Before (Old Structure):**
```python
# These imports no longer work
from lets_talk.agent import RAGAgent
from lets_talk.webapp import app
from lets_talk.scheduler import PipelineScheduler
from lets_talk.rag import retriever
from lets_talk.pipeline import create_vector_database
from lets_talk.config import Configuration
from lets_talk import prompts
```

**After (New Structure):**
```python
# New import paths
from lets_talk.agents import create_rag_agent, RAGAgent
from lets_talk.api.main import app
from lets_talk.core.scheduler.manager import PipelineScheduler
from lets_talk.core.rag.retriever import retriever
from lets_talk.core.pipeline.engine import run_pipeline
from lets_talk.shared.config import Configuration, load_configuration_with_prompts
from lets_talk.shared.prompts.templates import RESPONSE_SYSTEM_PROMPT
```

### 2. Entry Points

**Before:**
```bash
# Old command structure
uv run python py-src/lets_talk/pipeline.py
uv run python py-src/lets_talk/scheduler_cli.py
uvicorn lets_talk.webapp:app
```

**After:**
```bash
# New command structure
cd py-src && uv run python -m lets_talk.core.pipeline.engine
cd py-src && uv run python -m lets_talk.core.scheduler.cli
cd py-src && uv run python lets_talk/main.py
```

### 3. Configuration

**Before:**
```python
from lets_talk.config import Configuration, DATA_DIR
config = Configuration()
```

**After:**
```python
from lets_talk.shared.config import Configuration, DATA_DIR, load_configuration_with_prompts
config = load_configuration_with_prompts()
```

## Step-by-Step Migration

### Step 1: Update Import Statements

Use this mapping to update your imports:

| Old Import | New Import |
|------------|------------|
| `from lets_talk.agent import *` | `from lets_talk.agents import *` |
| `from lets_talk.webapp import app` | `from lets_talk.api.main import app` |
| `from lets_talk.scheduler import PipelineScheduler` | `from lets_talk.core.scheduler.manager import PipelineScheduler` |
| `from lets_talk.rag import retriever` | `from lets_talk.core.rag.retriever import retriever` |
| `from lets_talk.pipeline import create_vector_database` | `from lets_talk.core.pipeline.engine import run_pipeline` |
| `from lets_talk.config import *` | `from lets_talk.shared.config import *` |
| `from lets_talk import prompts` | `from lets_talk.shared.prompts.templates import *` |
| `from lets_talk.tools import *` | `from lets_talk.tools.external.* import *` |

### Step 2: Update Command Line Usage

**Pipeline Commands:**
```bash
# Old
uv run python py-src/lets_talk/pipeline.py --force-recreate

# New
cd py-src && uv run python -m lets_talk.core.pipeline.engine --force-recreate
```

**Scheduler Commands:**
```bash
# Old
uv run python py-src/lets_talk/scheduler_cli.py start --daemon

# New
cd py-src && uv run python -m lets_talk.core.scheduler.cli start --daemon
```

**API Server:**
```bash
# Old
uvicorn lets_talk.webapp:app --host 0.0.0.0 --port 8000

# New
cd py-src && uv run python lets_talk/main.py
# Or: cd py-src && uv run uvicorn lets_talk.api.main:app --host 0.0.0.0 --port 8000
```

### Step 3: Update Configuration Usage

**Before:**
```python
from lets_talk.config import Configuration

config = Configuration()
config.response_system_prompt = "Custom prompt"
```

**After:**
```python
from lets_talk.shared.config import load_configuration_with_prompts

config = load_configuration_with_prompts()
# Prompts are automatically loaded from templates
```

### Step 4: Update Agent Creation

**Before:**
```python
from lets_talk.agent import RAGAgent

agent = RAGAgent(config)
```

**After:**
```python
from lets_talk.agents import create_rag_agent
from lets_talk.shared.config import load_configuration_with_prompts

config = load_configuration_with_prompts()
agent = create_rag_agent(config)
```

### Step 5: Update Pipeline Usage

**Before:**
```python
from lets_talk.pipeline import create_vector_database

success, message, stats = create_vector_database(
    data_dir="data/",
    force_recreate=True
)
```

**After:**
```python
from lets_talk.core.pipeline.engine import run_pipeline

success, message, stats, stats_file, stats_content = run_pipeline(
    data_dir="data/",
    force_recreate=True
)
```

### Step 6: Update Scheduler Usage

**Before:**
```python
from lets_talk.scheduler import PipelineScheduler

scheduler = PipelineScheduler()
scheduler.add_cron_job("daily", hour=2)
```

**After:**
```python
from lets_talk.core.scheduler.manager import PipelineScheduler

scheduler = PipelineScheduler()
scheduler.add_cron_job(job_id="daily", hour=2)
```

## Common Migration Issues

### Issue 1: Module Not Found Errors

**Problem:**
```
ModuleNotFoundError: No module named 'lets_talk.agent'
```

**Solution:**
Update import to use new module structure:
```python
# Old
from lets_talk.agent import RAGAgent

# New
from lets_talk.agents.rag_agent import RAGAgent
# Or use factory
from lets_talk.agents import create_rag_agent
```

### Issue 2: Configuration Object Errors

**Problem:**
```
AttributeError: 'Configuration' object has no attribute 'response_temperature'
```

**Solution:**
Use the temperature setting from shared config:
```python
from lets_talk.shared.config import LLM_TEMPERATURE
# Use LLM_TEMPERATURE instead of config.response_temperature
```

### Issue 3: Changed Function Signatures

**Problem:**
Pipeline function returns different number of values.

**Solution:**
```python
# Old (3 return values)
success, message, stats = create_vector_database(...)

# New (5 return values)
success, message, stats, stats_file, stats_content = run_pipeline(...)
```

### Issue 4: Working Directory Issues

**Problem:**
```
FileNotFoundError: No such file or directory
```

**Solution:**
Make sure to run commands from the correct directory:
```bash
cd py-src && uv run python -m lets_talk.core.pipeline.engine
```

## Testing Your Migration

### 1. Test Basic Imports
```bash
cd py-src && uv run python -c "
import lets_talk
from lets_talk.agents import create_rag_agent
from lets_talk.api.main import app
from lets_talk.core.pipeline.engine import run_pipeline
print('All imports successful!')
"
```

### 2. Test Configuration
```bash
cd py-src && uv run python -c "
from lets_talk.shared.config import load_configuration_with_prompts
config = load_configuration_with_prompts()
print(f'Config loaded: {type(config)}')
"
```

### 3. Test API Server
```bash
cd py-src && uv run python lets_talk/main.py &
sleep 2
curl http://localhost:8000/health
kill %1
```

### 4. Test Pipeline
```bash
cd py-src && uv run python -c "
from lets_talk.core.pipeline.engine import run_pipeline
result = run_pipeline(data_dir='../data/', dry_run=True)
print(f'Pipeline test: {result[0]}')
"
```

## Rollback Plan

If you need to rollback to the old structure:

1. **Restore Old Files**: The old files were removed during migration. You can restore them from git history:
   ```bash
   git checkout HEAD~1 -- py-src/lets_talk/agent.py
   git checkout HEAD~1 -- py-src/lets_talk/webapp.py
   git checkout HEAD~1 -- py-src/lets_talk/pipeline.py
   # ... restore other needed files
   ```

2. **Revert Import Changes**: Update your code to use the old import structure.

3. **Use Old Entry Points**: Revert to the old command line usage.

## Benefits of Migration

After migration, you'll have:

1. **Better Organization**: Clear separation of concerns
2. **Easier Testing**: Isolated components for unit testing
3. **Improved Maintainability**: Smaller, focused modules
4. **Enhanced Extensibility**: Easy to add new features
5. **Type Safety**: Better type hints and validation
6. **Modern Architecture**: Follows current best practices

## Getting Help

If you encounter issues during migration:

1. **Check the Documentation**: Review the updated documentation in `docs/`
2. **Test Examples**: Run the test commands provided above
3. **Review Error Messages**: Most errors will be import-related
4. **Check Working Directory**: Ensure you're in the correct directory
5. **Contact Support**: Open an issue on the GitHub repository

## Summary

The migration involves primarily updating import statements and command line usage. The core functionality remains the same, but is now organized in a more maintainable structure. Take time to update your scripts and applications methodically, testing each change to ensure everything works correctly.
