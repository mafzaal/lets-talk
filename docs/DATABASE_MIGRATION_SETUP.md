# Database Migration Setup

This document describes the database migration system implemented for the Let's Talk application using Alembic.

## Overview

The application now uses a comprehensive migration system that:
- ✅ Provides version-controlled database schema changes
- ✅ Supports automatic migration during application startup
- ✅ Includes CLI tools for manual migration management
- ✅ Works with SQLite, PostgreSQL, and MySQL databases
- ✅ Integrates seamlessly with all application entry points

## Configuration

### Environment Variables

```bash
# Database URL (required)
DATABASE_URL="sqlite:///./output/lets_talk.db"
# DATABASE_URL="postgresql://user:password@localhost/dbname"
# DATABASE_URL="mysql://user:password@localhost/dbname"

# Auto-migration on startup (optional, default: True)
AUTO_MIGRATE_ON_STARTUP=True
```

### Key Files

- `backend/lets_talk/shared/config.py` - Database configuration
- `backend/lets_talk/core/migrations/` - Migration management system
- `backend/lets_talk/core/startup.py` - Application startup with migration integration
- `alembic.ini` - Alembic configuration
- `migrate.sh` - CLI script for migration operations

## Migration Management

### Using the CLI Script

```bash
# Create a new migration
./migrate.sh create "Description of changes"

# Apply all pending migrations
./migrate.sh upgrade

# Downgrade one migration
./migrate.sh downgrade -1

# Show current status
./migrate.sh status

# Show migration history
./migrate.sh history
```

### Using Python API

```python
from lets_talk.core.migrations import MigrationManager

manager = MigrationManager()

# Check for pending migrations
pending = manager.get_pending_migrations()

# Apply migrations
manager.upgrade_to_head()

# Get current revision
current = manager.get_current_revision()
```

## Application Integration

### Automatic Startup Migration

The application automatically checks for and applies pending migrations during startup when `AUTO_MIGRATE_ON_STARTUP=True` (default).

#### FastAPI Integration

```python
# In lets_talk/api/main.py
@asynccontextmanager
async def lifespan(app: FastAPI):
    # Startup with automatic migration
    startup_info = startup_application(
        app_name="FastAPI Server",
        require_database=True,
        fail_on_migration_error=True
    )
    yield
    # Shutdown logic here
```

#### Manual Integration

```python
from lets_talk.core.startup import startup_application

# Initialize application with database
startup_info = startup_application(
    app_name="My App",
    require_database=True,
    fail_on_migration_error=True
)

# Check results
if startup_info['database_status']['success']:
    print("Database ready!")
else:
    print("Database initialization failed")
```

## Startup Behavior

### With Auto-Migration Enabled (Default)

1. Application starts
2. Checks for pending migrations
3. Automatically applies any pending migrations
4. Continues startup if successful
5. Fails startup if migration errors occur (when `fail_on_migration_error=True`)

### With Auto-Migration Disabled

1. Application starts
2. Checks for pending migrations
3. Logs warnings if migrations are pending
4. Continues startup without applying migrations
5. User must manually run `./migrate.sh upgrade`

## Database Health Monitoring

The startup system includes comprehensive health monitoring:

```python
# Startup info includes detailed status
startup_info = {
    'database_status': {
        'success': True,
        'migrations_applied': False,  # True if migrations were applied
        'database_healthy': True,
        'current_revision': '641966a7eb28',
        'pending_migrations': 0,
        'errors': [],  # List of any errors encountered
        'auto_migrate_enabled': True
    }
}
```

## Testing Migration Integration

### Test Auto-Migration Enabled

```bash
cd /home/mafzaal/source/lets-talk
AUTO_MIGRATE_ON_STARTUP=True PYTHONPATH=/home/mafzaal/source/lets-talk/backend uv run python -c "
from lets_talk.core.startup import startup_application, log_startup_summary
startup_info = startup_application('Test App', require_database=True)
log_startup_summary(startup_info)
"
```

### Test Auto-Migration Disabled

```bash
cd /home/mafzaal/source/lets-talk
AUTO_MIGRATE_ON_STARTUP=False PYTHONPATH=/home/mafzaal/source/lets-talk/backend uv run python -c "
from lets_talk.core.startup import startup_application, log_startup_summary
startup_info = startup_application('Test App', require_database=True, fail_on_migration_error=False)
log_startup_summary(startup_info)
"
```

## Migration File Structure

```
backend/alembic/
├── versions/           # Migration files
│   ├── 001_initial_migration.py
│   ├── 002_add_user_table.py
│   └── ...
├── env.py             # Alembic environment configuration
└── script.py.mako    # Migration template
```

## Best Practices

### Creating Migrations

1. Always create migrations for schema changes:
   ```bash
   ./migrate.sh create "Add user authentication table"
   ```

2. Review generated migration files before applying
3. Test migrations in development before production
4. Use descriptive migration messages

### Production Deployment

1. Set `AUTO_MIGRATE_ON_STARTUP=True` for automated deployments
2. Or set `AUTO_MIGRATE_ON_STARTUP=False` and run migrations manually:
   ```bash
   ./migrate.sh upgrade
   ```

3. Always backup database before major migrations
4. Test rollback procedures: `./migrate.sh downgrade -1`

## Troubleshooting

### Common Issues

1. **Migration conflicts**: Resolve by creating merge migration
2. **Database locked**: Ensure no other processes are using the database
3. **Permission errors**: Check database file/directory permissions

### Debug Commands

```bash
# Check current database status
./migrate.sh status

# View migration history
./migrate.sh history

# Test database connection
PYTHONPATH=/home/mafzaal/source/lets-talk/backend uv run python -c "
from lets_talk.core.migrations import MigrationManager
manager = MigrationManager()
print('Current revision:', manager.get_current_revision())
print('Pending migrations:', len(manager.get_pending_migrations()))
"
```

## Architecture

The migration system consists of:

- **MigrationManager**: Core migration logic and Alembic integration
- **Startup Integration**: Automatic migration during application startup
- **CLI Interface**: Command-line tools for manual migration management
- **Health Monitoring**: Comprehensive status reporting and error handling

This provides a robust, production-ready database migration system that integrates seamlessly with the application's startup process.
