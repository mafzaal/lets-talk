# Pipeline Scheduling with FastAPI

This document describes the comprehensive pipeline scheduling functionality in the FastAPI application.

## Overview

The FastAPI application includes a complete pipeline scheduling system that allows you to:

- Schedule pipeline runs using cron expressions or intervals
- Manage scheduled jobs through REST API endpoints
- Monitor job execution and health status
- Use preset configurations for common scheduling patterns
- Export/import job configurations
- Run pipelines immediately on demand

## Getting Started

### Starting the API Server

```bash
# Start the server
cd py-src && uv run python lets_talk/main.py

# Or use uvicorn directly
cd py-src && uv run uvicorn lets_talk.api.main:app --host 0.0.0.0 --port 8000

# Access API documentation
# Visit http://localhost:8000/docs
```

### Using the New Architecture

```python
# Import the FastAPI app
from lets_talk.api.main import app

# Use scheduler manager
from lets_talk.core.scheduler.manager import PipelineScheduler

# Access API models
from lets_talk.api.models.scheduler import CreateJobRequest
from lets_talk.api.models.pipeline import PipelineRequest
```

- Schedule pipeline runs using cron expressions or intervals
- Manage scheduled jobs through REST API endpoints
- Monitor job execution and health status
- Use preset configurations for common scheduling patterns
- Export/import job configurations
- Run pipelines immediately on demand

## Features

### 🕐 Scheduling Types

1. **Cron-based scheduling** - Run at specific times using cron syntax
2. **Interval-based scheduling** - Run at regular intervals (minutes, hours, days)
3. **One-time scheduling** - Run once at a specific date/time
4. **Preset schedules** - Common patterns like daily, weekly, hourly

### 📊 Monitoring and Management

- Real-time job status and statistics
- Execution history and error tracking
- Health checks for scheduler and individual jobs
- Background task execution with persistent storage

### 🔧 Configuration Management

- Export/import scheduler configurations
- Preset schedule templates
- Environment-based pipeline configuration
- Persistent job storage using SQLite

## API Endpoints

### Scheduler Status and Management

| Endpoint | Method | Description |
|----------|--------|-------------|
| `/scheduler/status` | GET | Get scheduler status and statistics |
| `/scheduler/jobs` | GET | List all scheduled jobs |
| `/scheduler/health` | GET | Detailed scheduler health check |
| `/health` | GET | Basic health check |

### Job Management

| Endpoint | Method | Description |
|----------|--------|-------------|
| `/scheduler/jobs/cron` | POST | Create cron-based scheduled job |
| `/scheduler/jobs/interval` | POST | Create interval-based scheduled job |
| `/scheduler/jobs/onetime` | POST | Create one-time scheduled job |
| `/scheduler/jobs/{job_id}` | DELETE | Remove a scheduled job |
| `/scheduler/jobs/{job_id}/run` | POST | Trigger immediate job execution |

### Preset Schedules

| Endpoint | Method | Description |
|----------|--------|-------------|
| `/scheduler/presets` | GET | Get available preset schedules |
| `/scheduler/presets/{preset_name}` | POST | Create job using preset |

### Configuration Management

| Endpoint | Method | Description |
|----------|--------|-------------|
| `/scheduler/config/export` | GET | Export current job configuration |
| `/scheduler/config/import` | POST | Import job configuration |
| `/scheduler/config/default` | GET | Get default configuration |
| `/scheduler/config/save` | POST | Save configuration to file |
| `/scheduler/config/load` | GET | Load configuration from file |

### Pipeline Execution

| Endpoint | Method | Description |
|----------|--------|-------------|
| `/pipeline/run` | POST | Run pipeline immediately |
| `/pipeline/reports` | GET | List execution reports |
| `/pipeline/reports/{filename}` | GET | Get specific execution report |

## Usage Examples

### Starting the FastAPI Server

```bash
# Make sure all dependencies are installed
uv add fastapi uvicorn apscheduler sqlalchemy

# Start the server
uv run uvicorn lets_talk.webapp:app --host 0.0.0.0 --port 8000
```

### Creating Scheduled Jobs

#### 1. Daily Incremental Update (Cron)

```bash
curl -X POST "http://localhost:8000/scheduler/jobs/cron" \\
-H "Content-Type: application/json" \\
-d '{
  "job_id": "daily_incremental",
  "hour": 2,
  "minute": 0,
  "config": {
    "incremental_mode": "auto",
    "force_recreate": false,
    "ci_mode": true
  }
}'
```

#### 2. Hourly Check (Interval)

```bash
curl -X POST "http://localhost:8000/scheduler/jobs/interval" \\
-H "Content-Type: application/json" \\
-d '{
  "job_id": "hourly_check",
  "hours": 1,
  "config": {
    "incremental_mode": "auto",
    "dry_run": true,
    "ci_mode": true
  }
}'
```

#### 3. Weekly Full Rebuild (Preset)

```bash
curl -X POST "http://localhost:8000/scheduler/presets/weekly_sunday_1am?job_id=weekly_rebuild" \\
-H "Content-Type: application/json" \\
-d '{
  "incremental_mode": "full",
  "force_recreate": true,
  "ci_mode": true
}'
```

### Monitoring Jobs

#### Check Scheduler Status

```bash
curl "http://localhost:8000/scheduler/status"
```

#### List All Jobs

```bash
curl "http://localhost:8000/scheduler/jobs"
```

#### Get Health Status

```bash
curl "http://localhost:8000/health"
```

### Running Jobs Immediately

```bash
# Trigger specific job
curl -X POST "http://localhost:8000/scheduler/jobs/daily_incremental/run"

# Run pipeline with custom config
curl -X POST "http://localhost:8000/pipeline/run" \\
-H "Content-Type: application/json" \\
-d '{
  "incremental_mode": "auto",
  "dry_run": false,
  "force_recreate": false
}'
```

## Pipeline Configuration Options

When creating scheduled jobs, you can customize the pipeline execution with these options:

```json
{
  "data_dir": "data/",
  "storage_path": "db/vector_store",
  "force_recreate": false,
  "ci_mode": true,
  "use_chunking": true,
  "should_save_stats": true,
  "chunk_size": 1000,
  "chunk_overlap": 200,
  "collection_name": "blog_documents",
  "embedding_model": "ollama:snowflake-arctic-embed2:latest",
  "data_dir_pattern": "*.md",
  "blog_base_url": "https://yourblog.com/blog",
  "base_url": "https://yourblog.com",
  "incremental_mode": "auto",
  "dry_run": false
}
```

## Available Presets

| Preset | Description | Schedule |
|--------|-------------|----------|
| `daily_2am` | Daily at 2:00 AM | Cron: 0 2 * * * |
| `weekly_sunday_1am` | Weekly on Sunday at 1:00 AM | Cron: 0 1 * * 0 |
| `hourly` | Every hour | Interval: 1 hour |
| `every_30_minutes` | Every 30 minutes | Interval: 30 minutes |
| `twice_daily` | 6 AM and 6 PM daily | Multiple cron jobs |

## Programmatic Usage

Use the provided demo script to interact with the API programmatically:

```bash
# Install requests if not already installed
uv add requests

# Run the demo script
python examples/schedule_pipeline_demo.py
```

The demo script shows how to:
- Check health and status
- Create different types of scheduled jobs
- Use preset configurations
- Monitor job execution
- Export/import configurations
- Clean up demo jobs

## Configuration Files

### Default Scheduler Configuration

The system provides a default configuration with common scheduling patterns:

- **Daily incremental update** at 2 AM
- **Weekly full rebuild** on Sunday at 1 AM  
- **Hourly check** (dry run mode)

### Exporting and Importing Configurations

```bash
# Export current configuration
curl "http://localhost:8000/scheduler/config/export" > my_schedule_config.json

# Import configuration
curl -X POST "http://localhost:8000/scheduler/config/import" \\
-H "Content-Type: application/json" \\
-d @my_schedule_config.json
```

## Integration with Existing Pipeline

The FastAPI scheduler integrates seamlessly with the existing pipeline system:

- Uses the same configuration parameters as the command-line pipeline
- Supports all pipeline modes (incremental, full, dry-run)
- Leverages the existing health check and monitoring capabilities
- Maintains job execution history and reports

## Monitoring and Logging

### Execution Reports

All job executions generate detailed reports stored in the output directory:

```json
{
  "job_id": "daily_incremental",
  "timestamp": "2025-06-17T10:00:00",
  "success": true,
  "message": "Pipeline completed successfully",
  "stats": {
    "total_documents": 150,
    "new_documents": 5,
    "modified_documents": 2,
    "deleted_sources": 0
  },
  "stats_file": "output/blog_stats_20250617_100000.json"
}
```

### Health Monitoring

The system provides comprehensive health monitoring:

- Scheduler running status
- Job execution statistics (success/failure rates)
- Last execution times
- Error tracking and reporting

## Security Considerations

When deploying to production:

1. **Authentication**: Add authentication middleware to protect the API endpoints
2. **Rate Limiting**: Implement rate limiting to prevent abuse
3. **HTTPS**: Use HTTPS in production environments
4. **Access Control**: Restrict access to job management endpoints
5. **Input Validation**: The system includes input validation, but review for your use case

## Troubleshooting

### Common Issues

1. **Scheduler not starting**: Check logs for database connectivity issues
2. **Jobs not executing**: Verify scheduler is running and jobs are properly configured
3. **High failure rates**: Check pipeline configuration and resource availability
4. **Import errors**: Validate JSON configuration format

### Debug Mode

Enable debug logging by setting the environment variable:

```bash
export LOG_LEVEL="DEBUG"
```

### Health Checks

Use the health endpoints to diagnose issues:

```bash
# Basic health check
curl "http://localhost:8000/health"

# Detailed scheduler health
curl "http://localhost:8000/scheduler/health"
```

## Dependencies

The pipeline scheduling system requires these additional dependencies:

```toml
[tool.uv.dependencies]
fastapi = ">=0.104.0"
uvicorn = ">=0.24.0"
apscheduler = ">=3.10.0"
sqlalchemy = ">=2.0.0"
pydantic = ">=2.5.0"
```

Install them with:

```bash
uv add fastapi uvicorn apscheduler sqlalchemy pydantic
```

## Future Enhancements

Potential improvements for the scheduling system:

- Web-based management interface
- Advanced notification systems (email, Slack, webhooks)
- Job dependency management
- Distributed scheduling across multiple instances
- Advanced retry and failure handling policies
- Integration with monitoring systems (Prometheus, Grafana)

---

For more information, see the [Pipeline Usage Guide](docs/PIPELINE_USAGE_GUIDE.md) and the [source code](py-src/lets_talk/webapp.py).
