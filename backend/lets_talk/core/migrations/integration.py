"""Integration utilities for migrations with application startup."""
import logging
from typing import Optional

from lets_talk.core.migrations.manager import get_migration_manager, ensure_database_is_migrated
from lets_talk.shared.config import LOGGER_NAME

logger = logging.getLogger(f"{LOGGER_NAME}.migrations.integration")


def initialize_database() -> bool:
    """Initialize database with migrations on application startup."""
    try:
        logger.info("Initializing database with migrations...")
        
        # Ensure database is migrated
        success = ensure_database_is_migrated()
        
        if success:
            logger.info("Database initialization completed successfully")
            
            # Log current status
            manager = get_migration_manager()
            current_revision = manager.get_current_revision()
            if current_revision:
                logger.info(f"Database is at revision: {current_revision[:8]}")
            else:
                logger.warning("No database revision found")
        else:
            logger.error("Database initialization failed")
        
        return success
        
    except Exception as e:
        logger.error(f"Error during database initialization: {e}")
        return False


def check_database_health() -> dict:
    """Check database migration health status."""
    try:
        manager = get_migration_manager()
        status = manager.get_status()
        
        health_info = {
            "healthy": status["is_up_to_date"],
            "current_revision": status["current_revision"],
            "pending_migrations": len(status["pending_migrations"]),
            "total_migrations": status["total_migrations"],
            "details": status
        }
        
        if not status["is_up_to_date"]:
            logger.warning(f"Database has {len(status['pending_migrations'])} pending migrations")
        
        return health_info
        
    except Exception as e:
        logger.error(f"Error checking database health: {e}")
        return {
            "healthy": False,
            "error": str(e),
            "current_revision": None,
            "pending_migrations": 0,
            "total_migrations": 0
        }


def migrate_on_startup(auto_migrate: bool = True) -> bool:
    """Handle migrations on application startup.
    
    Args:
        auto_migrate: If True, automatically apply pending migrations
        
    Returns:
        True if database is ready, False otherwise
    """
    try:
        manager = get_migration_manager()
        
        # Check current status
        has_pending = manager.check_for_pending_migrations()
        
        if has_pending:
            if auto_migrate:
                logger.info("Pending migrations detected, applying automatically...")
                success = manager.upgrade_to_head()
                if success:
                    logger.info("Automatic migration completed successfully")
                    return True
                else:
                    logger.error("Automatic migration failed")
                    return False
            else:
                logger.warning("Pending migrations detected but auto-migration is disabled")
                return False
        else:
            logger.info("No pending migrations, database is up to date")
            return True
            
    except Exception as e:
        logger.error(f"Error during startup migration: {e}")
        return False
