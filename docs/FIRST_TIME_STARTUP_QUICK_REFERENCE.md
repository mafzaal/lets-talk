# First-Time Startup Quick Reference

## Quick Start

### Check First-Time Status
```bash
curl http://localhost:2024/health | jq '.first_time_setup'
```

### Environment Variables
```bash
# Disable first-time detection
export FIRST_TIME_DETECTION_ENABLED="False"

# Custom delay (2 minutes)
export FIRST_TIME_JOB_DELAY_SECONDS="120"

# Detection only (no pipeline job)
export FIRST_TIME_RUN_PIPELINE_JOB="False"
```

### Manual Reset
```bash
# Remove completion marker
rm output/.first_time_setup_completed

# Clear all data (optional)
rm -rf output/* db/*

# Restart application
./start_backend_dev.sh
```

## Detection Indicators

| Indicator | Check | Location |
|-----------|-------|----------|
| Database Empty | No migration history | Database |
| Settings Not Initialized | No settings in DB | Database |
| No Vector Storage | Empty vector directory | `db/` |
| No Output Files | No pipeline artifacts | `output/` |
| No Marker | No completion file | `output/.first_time_setup_completed` |

## Job Configuration

```json
{
  "job_id": "first_time_pipeline_setup",
  "force_recreate": true,
  "incremental_mode": "full",
  "ci_mode": true,
  "dry_run": false,
  "health_check": true,
  "should_save_stats": true
}
```

## API Endpoints

```bash
# Health with first-time status
GET /health

# Scheduled jobs (including first-time)
GET /scheduler/jobs

# Scheduler status
GET /scheduler/status
```

## Log Messages to Watch

```
🎉 First-time execution detected!
⏰ First-time pipeline job scheduled
✅ First-time setup completed successfully!
```

## Troubleshooting Commands

```bash
# Check detection status
python -c "from lets_talk.core.first_time import get_first_time_status; print(get_first_time_status())"

# Check if marker exists
ls -la output/.first_time_setup_completed

# View recent logs
tail -n 50 logs/application.log | grep -i "first"

# Check scheduler jobs
curl -s http://localhost:2024/scheduler/jobs | jq '.[].id'
```

## Testing

```bash
# Run first-time detection tests
uv run python test_first_time_setup.py

# Test fresh installation
uv run python test_fresh_install.py

# Test API integration
uv run python test_api_first_time.py
```

## File Locations

- **Source**: `backend/lets_talk/core/first_time.py`
- **Configuration**: `backend/lets_talk/shared/config.py`
- **Startup Integration**: `backend/lets_talk/core/startup.py`
- **Health Endpoint**: `backend/lets_talk/api/endpoints/health.py`
- **Completion Marker**: `output/.first_time_setup_completed`
- **Tests**: `test_*_first_time*.py`
