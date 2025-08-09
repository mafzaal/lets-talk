"""Application startup and initialization utilities."""
import logging
import sys
from typing import Dict, Any, Optional, Union
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


def initialize_scheduler_system(
    scheduler_type: str = "background",
    max_workers: int = 20,
    enable_persistence: Optional[bool] = None,
    fail_on_error: bool = False
) -> Dict[str, Any]:
    """Initialize the scheduler system.
    
    Args:
        scheduler_type: Type of scheduler to create
        max_workers: Maximum number of worker threads
        enable_persistence: Whether to enable persistent storage (None = auto-decide based on DB health)
        fail_on_error: Whether to fail startup if scheduler initialization fails
        
    Returns:
        Dict containing scheduler initialization status and instance
    """
    status = {
        "success": False,
        "scheduler_instance": None,
        "persistence_enabled": False,
        "errors": [],
        "warnings": []
    }
    
    try:
        from lets_talk.core.scheduler.manager import PipelineScheduler
        
        logger.info("Initializing scheduler system...")
        
        # Auto-decide persistence based on database health if not specified
        if enable_persistence is None:
            db_health = check_database_health()
            enable_persistence = db_health["healthy"]
            logger.info(f"Auto-decided persistence: {enable_persistence} (based on DB health)")
        
        # Create scheduler instance
        scheduler_instance = PipelineScheduler(
            scheduler_type=scheduler_type,
            max_workers=max_workers,
            enable_persistence=bool(enable_persistence)
        )
        
        # Start the scheduler
        scheduler_instance.start()
        logger.info(f"Scheduler started successfully (persistence: {enable_persistence})")
        
        status.update({
            "success": True,
            "scheduler_instance": scheduler_instance,
            "persistence_enabled": enable_persistence
        })
        
        return status
        
    except Exception as e:
        error_msg = f"Failed to initialize scheduler: {e}"
        logger.error(error_msg)
        status["errors"].append(error_msg)
        
        if fail_on_error:
            raise StartupError(error_msg)
        else:
            logger.warning("Continuing without scheduler")
            
        return status


def initialize_default_jobs(scheduler_instance, fail_on_error: bool = False) -> Dict[str, Any]:
    """Initialize default jobs if enabled.
    
    Args:
        scheduler_instance: The scheduler instance to add jobs to
        fail_on_error: Whether to fail startup if default job creation fails
        
    Returns:
        Dict containing default job initialization status
    """
    status = {
        "success": False,
        "default_job_created": False,
        "errors": [],
        "warnings": []
    }
    
    if not scheduler_instance:
        status["warnings"].append("No scheduler instance provided, skipping default job initialization")
        return status
    
    try:
        logger.info("Initializing default jobs...")
        default_job_success = scheduler_instance.initialize_default_job_if_needed()
        
        if default_job_success:
            logger.info("Default job initialized successfully")
            status.update({
                "success": True,
                "default_job_created": True
            })
        else:
            warning_msg = "Default job initialization returned False (may be disabled or already exists)"
            logger.info(warning_msg)
            status.update({
                "success": True,  # Still success, just no job created
                "warnings": [warning_msg]
            })
        
        return status
        
    except Exception as e:
        error_msg = f"Failed to initialize default jobs: {e}"
        logger.error(error_msg)
        status["errors"].append(error_msg)
        
        if fail_on_error:
            raise StartupError(error_msg)
        else:
            logger.warning("Continuing without default job initialization")
            status["success"] = True  # Don't fail startup for default job issues
            
        return status


def startup_fastapi_application(
    app_name: str = "FastAPI API Server",
    scheduler_config: Optional[Dict[str, Any]] = None,
    fail_on_migration_error: bool = False,
    fail_on_scheduler_error: bool = False,
    fail_on_default_job_error: bool = False
) -> Dict[str, Any]:
    """Complete startup sequence for FastAPI application.
    
    Args:
        app_name: Name of the application
        scheduler_config: Optional scheduler configuration
        fail_on_migration_error: Whether to fail if database migration fails
        fail_on_scheduler_error: Whether to fail if scheduler initialization fails
        fail_on_default_job_error: Whether to fail if default job creation fails
        
    Returns:
        Dict containing complete startup status and instances
    """
    startup_info = {
        "app_name": app_name,
        "success": False,
        "database_initialized": False,
        "scheduler_initialized": False,
        "default_jobs_initialized": False,
        "database_status": {},
        "scheduler_status": {},
        "default_jobs_status": {},
        "scheduler_instance": None,
        "errors": [],
        "warnings": []
    }
    
    try:
        logger.info(f"Starting {app_name} with full startup sequence...")
        
        # Step 1: Initialize database system
        logger.info("Step 1: Database initialization")
        db_status = initialize_database_system()
        startup_info["database_status"] = db_status
        startup_info["database_initialized"] = db_status["success"]
        
        if not db_status["success"] and fail_on_migration_error:
            error_msg = f"Database initialization failed for {app_name}"
            startup_info["errors"].extend(db_status["errors"])
            raise StartupError(f"{error_msg}: {', '.join(db_status['errors'])}")
        elif not db_status["success"]:
            startup_info["warnings"].append("Database initialization failed but continuing")
        
        # Step 2: Initialize scheduler system
        logger.info("Step 2: Scheduler initialization")
        scheduler_config = scheduler_config or {}
        scheduler_status = initialize_scheduler_system(
            scheduler_type=scheduler_config.get("scheduler_type", "background"),
            max_workers=scheduler_config.get("max_workers", 20),
            enable_persistence=scheduler_config.get("enable_persistence"),
            fail_on_error=fail_on_scheduler_error
        )
        
        startup_info["scheduler_status"] = scheduler_status
        startup_info["scheduler_initialized"] = scheduler_status["success"]
        startup_info["scheduler_instance"] = scheduler_status["scheduler_instance"]
        
        if not scheduler_status["success"]:
            startup_info["errors"].extend(scheduler_status["errors"])
            startup_info["warnings"].extend(scheduler_status["warnings"])
        
        # Step 3: Initialize default jobs (only if scheduler was initialized)
        if scheduler_status["success"] and scheduler_status["scheduler_instance"]:
            logger.info("Step 3: Default jobs initialization")
            default_jobs_status = initialize_default_jobs(
                scheduler_status["scheduler_instance"],
                fail_on_error=fail_on_default_job_error
            )
            
            startup_info["default_jobs_status"] = default_jobs_status
            startup_info["default_jobs_initialized"] = default_jobs_status["success"]
            
            if not default_jobs_status["success"]:
                startup_info["errors"].extend(default_jobs_status["errors"])
            startup_info["warnings"].extend(default_jobs_status["warnings"])
        else:
            logger.warning("Skipping default jobs initialization (scheduler not available)")
            startup_info["warnings"].append("Default jobs skipped (scheduler not available)")
        
        # Determine overall success
        # Success if database is ready OR we're allowed to continue without it
        # AND scheduler is working (or we're allowed to continue without it)
        critical_failures = []
        if not startup_info["database_initialized"] and fail_on_migration_error:
            critical_failures.append("database")
        if not startup_info["scheduler_initialized"] and fail_on_scheduler_error:
            critical_failures.append("scheduler")
        
        if not critical_failures:
            startup_info["success"] = True
            logger.info(f"✅ {app_name} startup completed successfully")
        else:
            error_msg = f"Critical failures in: {', '.join(critical_failures)}"
            startup_info["errors"].append(error_msg)
            logger.error(f"❌ {app_name} startup failed: {error_msg}")
        
        return startup_info
        
    except StartupError:
        raise
    except Exception as e:
        error_msg = f"Unexpected error during {app_name} startup: {e}"
        logger.exception(error_msg)
        startup_info["errors"].append(error_msg)
        return startup_info


def shutdown_application(
    startup_info: Dict[str, Any],
    timeout: int = 30
) -> Dict[str, Any]:
    """Graceful shutdown of application components.
    
    Args:
        startup_info: The startup info dict containing component instances
        timeout: Timeout in seconds for shutdown operations
        
    Returns:
        Dict containing shutdown status
    """
    shutdown_status = {
        "success": True,
        "components_shutdown": [],
        "errors": [],
        "warnings": []
    }
    
    try:
        logger.info("Starting application shutdown sequence...")
        
        # Shutdown scheduler if it exists
        scheduler_instance = startup_info.get("scheduler_instance")
        if scheduler_instance:
            try:
                logger.info("Shutting down scheduler...")
                scheduler_instance.shutdown(wait=True)
                shutdown_status["components_shutdown"].append("scheduler")
                logger.info("Scheduler shut down successfully")
            except Exception as e:
                error_msg = f"Error shutting down scheduler: {e}"
                logger.error(error_msg)
                shutdown_status["errors"].append(error_msg)
                shutdown_status["success"] = False
        
        # Add other component shutdowns here as needed
        
        if shutdown_status["success"]:
            logger.info("✅ Application shutdown completed successfully")
        else:
            logger.warning("⚠️ Application shutdown completed with errors")
        
        return shutdown_status
        
    except Exception as e:
        error_msg = f"Unexpected error during shutdown: {e}"
        logger.exception(error_msg)
        shutdown_status["errors"].append(error_msg)
        shutdown_status["success"] = False
        return shutdown_status
