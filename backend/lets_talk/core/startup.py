"""Application startup and initialization utilities."""
import logging
import sys
from typing import Dict, Any, Optional
from pathlib import Path

from lets_talk.shared.config import (
    AUTO_MIGRATE_ON_STARTUP, 
    DATABASE_URL, 
    LOGGER_NAME,
    OUTPUT_DIR
)
from lets_talk.core.migrations.integration import (
    migrate_on_startup,
    check_database_health,
    initialize_database
)

logger = logging.getLogger(f"{LOGGER_NAME}.startup")


class StartupError(Exception):
    """Exception raised during application startup."""
    pass


def ensure_output_directory() -> None:
    """Ensure output directory exists."""
    try:
        Path(OUTPUT_DIR).mkdir(parents=True, exist_ok=True)
        logger.debug(f"Output directory ensured: {OUTPUT_DIR}")
    except Exception as e:
        raise StartupError(f"Failed to create output directory {OUTPUT_DIR}: {e}")


def initialize_database_system() -> Dict[str, Any]:
    """Initialize the database system with migrations.
    
    Returns:
        Dict containing initialization status and details
    """
    status = {
        "success": False,
        "migrations_applied": False,
        "database_healthy": False,
        "current_revision": None,
        "pending_migrations": 0,
        "errors": [],
        "auto_migrate_enabled": AUTO_MIGRATE_ON_STARTUP
    }
    
    try:
        logger.info("Initializing database system...")
        logger.info(f"Database URL: {DATABASE_URL}")
        logger.info(f"Auto-migrate on startup: {AUTO_MIGRATE_ON_STARTUP}")
        
        # Ensure output directory exists
        ensure_output_directory()
        
        # Check database health first
        logger.info("Checking database health...")
        health_info = check_database_health()
        status["database_healthy"] = health_info["healthy"]
        status["current_revision"] = health_info["current_revision"]
        status["pending_migrations"] = health_info["pending_migrations"]
        
        if health_info["healthy"]:
            logger.info("Database is healthy and up to date")
            status["success"] = True
            return status
        
        # If not healthy, check if we should auto-migrate
        if AUTO_MIGRATE_ON_STARTUP:
            logger.info("Auto-migration enabled, applying migrations...")
            migration_success = migrate_on_startup(auto_migrate=True)
            
            if migration_success:
                logger.info("Database migrations applied successfully")
                status["migrations_applied"] = True
                status["success"] = True
                
                # Re-check health after migration
                health_info = check_database_health()
                status["database_healthy"] = health_info["healthy"]
                status["current_revision"] = health_info["current_revision"]
                status["pending_migrations"] = health_info["pending_migrations"]
            else:
                error_msg = "Failed to apply database migrations"
                logger.error(error_msg)
                status["errors"].append(error_msg)
        else:
            # Auto-migration disabled, but database needs migration
            if status["pending_migrations"] > 0:
                warning_msg = f"Database has {status['pending_migrations']} pending migrations but auto-migration is disabled"
                logger.warning(warning_msg)
                logger.warning("To apply migrations manually, run: ./migrate.sh upgrade")
                status["errors"].append(warning_msg)
            else:
                # Try basic initialization without migration
                logger.info("Attempting basic database initialization...")
                init_success = initialize_database()
                if init_success:
                    status["success"] = True
                else:
                    error_msg = "Failed to initialize database"
                    logger.error(error_msg)
                    status["errors"].append(error_msg)
        
        return status
        
    except Exception as e:
        error_msg = f"Error during database initialization: {e}"
        logger.exception(error_msg)
        status["errors"].append(error_msg)
        return status


def startup_application(
    app_name: str,
    require_database: bool = True,
    fail_on_migration_error: bool = True
) -> Dict[str, Any]:
    """Startup sequence for any application component.
    
    Args:
        app_name: Name of the application component starting up
        require_database: Whether database is required for this component
        fail_on_migration_error: Whether to fail startup if migration fails
        
    Returns:
        Dict containing startup status and information
        
    Raises:
        StartupError: If startup fails and fail_on_migration_error is True
    """
    startup_info = {
        "app_name": app_name,
        "success": False,
        "database_initialized": False,
        "database_status": {},
        "errors": [],
        "warnings": []
    }
    
    try:
        logger.info(f"Starting {app_name}...")
        
        if require_database:
            logger.info("Database initialization required")
            db_status = initialize_database_system()
            startup_info["database_status"] = db_status
            startup_info["database_initialized"] = db_status["success"]
            
            if not db_status["success"]:
                error_msg = f"Database initialization failed for {app_name}"
                logger.error(error_msg)
                startup_info["errors"].extend(db_status["errors"])
                
                if fail_on_migration_error:
                    raise StartupError(f"{error_msg}: {', '.join(db_status['errors'])}")
                else:
                    logger.warning(f"Continuing {app_name} startup despite database errors")
                    startup_info["warnings"].append("Database initialization failed but continuing")
            else:
                logger.info(f"Database initialized successfully for {app_name}")
        
        startup_info["success"] = True
        logger.info(f"{app_name} startup completed successfully")
        
        return startup_info
        
    except StartupError:
        raise
    except Exception as e:
        error_msg = f"Unexpected error during {app_name} startup: {e}"
        logger.exception(error_msg)
        startup_info["errors"].append(error_msg)
        
        if fail_on_migration_error:
            raise StartupError(error_msg)
        
        return startup_info


def log_startup_summary(startup_info: Dict[str, Any]) -> None:
    """Log a summary of the startup process."""
    app_name = startup_info.get("app_name", "Application")
    
    if startup_info["success"]:
        logger.info(f"✅ {app_name} started successfully")
    else:
        logger.error(f"❌ {app_name} startup failed")
    
    if startup_info.get("database_initialized"):
        db_status = startup_info.get("database_status", {})
        if db_status.get("migrations_applied"):
            logger.info("🔄 Database migrations applied")
        
        current_rev = db_status.get("current_revision")
        if current_rev:
            logger.info(f"📊 Database at revision: {current_rev[:8]}")
    
    for warning in startup_info.get("warnings", []):
        logger.warning(f"⚠️  {warning}")
    
    for error in startup_info.get("errors", []):
        logger.error(f"❌ {error}")


def get_startup_health_info() -> Dict[str, Any]:
    """Get health information for startup monitoring."""
    try:
        db_health = check_database_health()
        return {
            "database": {
                "healthy": db_health["healthy"],
                "current_revision": db_health["current_revision"],
                "pending_migrations": db_health["pending_migrations"],
                "total_migrations": db_health["total_migrations"]
            },
            "configuration": {
                "database_url": DATABASE_URL,
                "auto_migrate_enabled": AUTO_MIGRATE_ON_STARTUP,
                "output_directory": OUTPUT_DIR
            }
        }
    except Exception as e:
        logger.error(f"Error getting startup health info: {e}")
        return {
            "error": str(e),
            "database": {"healthy": False},
            "configuration": {}
        }
