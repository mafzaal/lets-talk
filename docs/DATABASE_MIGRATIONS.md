# Database Migration Guide

This guide covers the database migration system for the `lets_talk` application using Alembic.

## Overview

The migration system provides:
- **Automatic schema management** using Alembic
- **Version control for database changes**
- **Cross-database compatibility** (SQLite, PostgreSQL, MySQL)
- **Integration with application startup**
- **CLI tools for migration management**

## Quick Start

### Check Migration Status
```bash
./migrate.sh status
```

### Apply Pending Migrations
```bash
./migrate.sh upgrade
```

### Create New Migration
```bash
./migrate.sh create "Add user preferences table"
```

## Configuration

### Environment Variables

| Variable | Description | Default |
|----------|-------------|---------|
| `DATABASE_URL` | Database connection string | `sqlite:///output/lets_talk.db` |
| `AUTO_MIGRATE_ON_STARTUP` | Auto-apply migrations on startup | `True` |

### Database URL Examples

```bash
# SQLite (default)
DATABASE_URL="sqlite:///output/lets_talk.db"

# PostgreSQL
DATABASE_URL="postgresql://username:password@localhost:5432/lets_talk"

# MySQL
DATABASE_URL="mysql://username:password@localhost:3306/lets_talk"
```

## Migration Commands

### Using the Migration Script

The `migrate.sh` script provides convenient access to migration commands:

```bash
# Show current status
./migrate.sh status

# Show migration history
./migrate.sh history

# Upgrade to latest version
./migrate.sh upgrade

# Upgrade to specific revision
./migrate.sh upgrade abc123def

# Downgrade by steps
./migrate.sh downgrade 2

# Downgrade to specific revision
./migrate.sh downgrade xyz789abc

# Create new migration
./migrate.sh create "Description of changes"

# Check for pending migrations
./migrate.sh check

# Auto-upgrade if needed
./migrate.sh auto-upgrade

# Reset database (WARNING: destructive)
./migrate.sh reset
```

### Using Python CLI

You can also use the Python CLI directly:

```bash
# Show status
uv run python backend/lets_talk/core/migrations/cli.py status

# Create migration
uv run python backend/lets_talk/core/migrations/cli.py create "Add new table"

# Upgrade database
uv run python backend/lets_talk/core/migrations/cli.py upgrade
```

### Using Alembic Directly

For advanced operations, use Alembic commands directly:

```bash
# Run any Alembic command
./migrate.sh alembic-cmd <command>

# Examples:
./migrate.sh alembic-cmd current
./migrate.sh alembic-cmd history --verbose
./migrate.sh alembic-cmd show abc123def
```

## Migration Workflow

### Development Workflow

1. **Make changes to SQLAlchemy models**
2. **Generate migration**:
   ```bash
   ./migrate.sh create "Description of changes"
   ```
3. **Review generated migration file** in `backend/alembic/versions/`
4. **Apply migration**:
   ```bash
   ./migrate.sh upgrade
   ```
5. **Test your changes**

### Production Deployment

1. **Check pending migrations**:
   ```bash
   ./migrate.sh check
   ```
2. **Apply migrations**:
   ```bash
   ./migrate.sh upgrade
   ```
3. **Verify status**:
   ```bash
   ./migrate.sh status
   ```

## Integration with Application

### Automatic Migration on Startup

By default, the application automatically applies pending migrations on startup. This can be controlled with:

```python
from lets_talk.core.migrations.integration import migrate_on_startup

# In your application startup
success = migrate_on_startup(auto_migrate=True)
if not success:
    # Handle migration failure
    pass
```

### Health Checks

Monitor migration status in your application:

```python
from lets_talk.core.migrations.integration import check_database_health

health = check_database_health()
print(f"Database healthy: {health['healthy']}")
print(f"Pending migrations: {health['pending_migrations']}")
```

### Manual Migration Management

For more control, use the migration manager directly:

```python
from lets_talk.core.migrations.manager import get_migration_manager

manager = get_migration_manager()

# Get status
status = manager.get_status()

# Apply migrations
success = manager.upgrade_to_head()

# Create migration
revision_id = manager.create_migration("Add new feature")
```

## File Structure

```
├── alembic.ini                           # Alembic configuration
├── backend/alembic/                      # Migration files
│   ├── env.py                           # Environment configuration
│   ├── script.py.mako                   # Migration template
│   └── versions/                        # Migration scripts
│       └── 641966a7eb28_initial_migration.py
├── backend/lets_talk/core/migrations/   # Migration utilities
│   ├── __init__.py
│   ├── manager.py                       # Migration manager
│   ├── cli.py                          # CLI interface
│   └── integration.py                   # Application integration
└── migrate.sh                          # Convenient migration script
```

## Best Practices

### Creating Migrations

1. **Use descriptive messages**:
   ```bash
   ./migrate.sh create "Add user authentication tables"
   ```

2. **Review generated migrations** before applying:
   - Check the generated SQL operations
   - Ensure data safety
   - Test on development data

3. **One logical change per migration**:
   - Don't mix unrelated changes
   - Keep migrations focused and atomic

### Migration Safety

1. **Always backup production data** before migrations
2. **Test migrations on staging environment** first
3. **Use downgrade functions** for rollback capability
4. **Monitor migration performance** on large datasets

### Schema Changes

1. **Add columns as nullable initially**, then add constraints
2. **Use batch operations** for large table modifications
3. **Consider data migration** for complex schema changes
4. **Document breaking changes** in migration comments

## Troubleshooting

### Common Issues

**Migration fails with "database is locked"**:
```bash
# For SQLite, ensure no other processes are using the database
# Check for zombie processes or connections
```

**Migration shows as pending but database is current**:
```bash
# Check Alembic version table
./migrate.sh alembic-cmd current --verbose
```

**Autogenerate doesn't detect changes**:
```bash
# Ensure models are imported in env.py
# Check target_metadata is correctly set
```

### Reset Database (Development Only)

**WARNING: This will delete all data**

```bash
./migrate.sh reset
```

### Manual Recovery

If migrations get out of sync:

```bash
# 1. Check current state
./migrate.sh alembic-cmd current

# 2. Mark specific revision as current (without running it)
./migrate.sh alembic-cmd stamp <revision_id>

# 3. Continue with normal migration process
./migrate.sh upgrade
```

## Advanced Usage

### Branching and Merging

For complex development scenarios with multiple feature branches:

```bash
# Create branch
./migrate.sh alembic-cmd revision --branch-label feature_branch -m "Start feature"

# Merge branches
./migrate.sh alembic-cmd merge -m "Merge feature branch" feature_branch main
```

### Custom Migration Operations

Edit migration files to add custom operations:

```python
def upgrade():
    # Auto-generated operations
    op.create_table(...)
    
    # Custom data migration
    connection = op.get_bind()
    connection.execute(text("UPDATE users SET status = 'active' WHERE status IS NULL"))
```

### Performance Considerations

For large databases:
- Use batch operations for bulk changes
- Consider online schema change tools
- Monitor migration duration
- Plan maintenance windows for major migrations

## Integration with CI/CD

### Automated Checks

```bash
# In CI pipeline
./migrate.sh check  # Exit code 1 if pending migrations

# Apply migrations in deployment
./migrate.sh upgrade
```

### Docker Integration

```dockerfile
# In Dockerfile
COPY migrate.sh .
RUN chmod +x migrate.sh

# In entrypoint script
./migrate.sh auto-upgrade
```

## Support

For migration-related issues:
1. Check the logs for detailed error messages
2. Verify database connectivity and permissions
3. Ensure all dependencies are installed
4. Review migration files for syntax errors

## See Also

- [Alembic Documentation](https://alembic.sqlalchemy.org/)
- [SQLAlchemy Documentation](https://docs.sqlalchemy.org/)
- [Application Configuration Guide](PIPELINE_USAGE_GUIDE.md)
