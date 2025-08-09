"""First-time execution detection and setup utilities."""
import os
import logging
from typing import Dict, Any, Optional
from pathlib import Path

from lets_talk.shared.config import (
    LOGGER_NAME, DATABASE_URL, OUTPUT_DIR, VECTOR_STORAGE_PATH,
    FIRST_TIME_DETECTION_ENABLED, FIRST_TIME_RUN_PIPELINE_JOB,
    FIRST_TIME_JOB_ID, FIRST_TIME_JOB_DELAY_SECONDS, FIRST_TIME_JOB_FORCE_RECREATE
)
from lets_talk.core.migrations.integration import check_database_health
from lets_talk.core.services.settings_init import settings_initializer

logger = logging.getLogger(f"{LOGGER_NAME}.first_time")


def is_database_empty() -> bool:
    """Check if the database appears to be completely empty (no revision history)."""
    try:
        health_info = check_database_health()
        
        # If there's no current revision and no migrations, it's likely empty
        no_revision = health_info.get("current_revision") is None
        no_migrations = health_info.get("total_migrations", 0) == 0
        
        return no_revision and no_migrations
    except Exception as e:
        logger.warning(f"Could not determine database state: {e}")
        # If we can't determine, assume it's not empty to be safe
        return False


def are_settings_initialized() -> bool:
    """Check if application settings have been initialized in the database."""
    try:
        # Check if any settings exist
        settings = settings_initializer.settings_service.get_all_settings()
        return len(settings) > 0
    except Exception as e:
        logger.warning(f"Could not check settings initialization: {e}")
        # If we can't check, assume they are initialized to be safe
        return True


def has_vector_storage() -> bool:
    """Check if vector storage has been created."""
    try:
        vector_path = Path(VECTOR_STORAGE_PATH)
        
        # Check if the vector storage directory exists and has content
        if not vector_path.exists():
            return False
        
        # Check if it has any files (simple heuristic)
        return any(vector_path.iterdir())
        
    except Exception as e:
        logger.warning(f"Could not check vector storage: {e}")
        return True  # Assume it exists to be safe


def has_output_files() -> bool:
    """Check if any output files exist (indicating previous runs)."""
    try:
        output_path = Path(OUTPUT_DIR)
        
        if not output_path.exists():
            return False
        
        # Look for typical output files
        common_files = [
            "blog_stats_*.json",
            "health_report.json", 
            "test_metadata.csv",
            "validation_metadata.csv"
        ]
        
        for pattern in common_files:
            if list(output_path.glob(pattern)):
                return True
                
        return False
        
    except Exception as e:
        logger.warning(f"Could not check output files: {e}")
        return True  # Assume they exist to be safe


def create_first_time_marker() -> bool:
    """Create a marker file to indicate first-time setup has been completed."""
    try:
        marker_path = Path(OUTPUT_DIR) / ".first_time_setup_completed"
        marker_path.parent.mkdir(parents=True, exist_ok=True)
        
        with open(marker_path, 'w') as f:
            from datetime import datetime
            f.write(f"First-time setup completed at: {datetime.now().isoformat()}\n")
            f.write(f"Database URL: {DATABASE_URL}\n")
        
        logger.info(f"Created first-time setup marker: {marker_path}")
        return True
        
    except Exception as e:
        logger.error(f"Failed to create first-time marker: {e}")
        return False


def has_first_time_marker() -> bool:
    """Check if the first-time setup marker exists."""
    try:
        marker_path = Path(OUTPUT_DIR) / ".first_time_setup_completed"
        return marker_path.exists()
    except Exception as e:
        logger.warning(f"Could not check first-time marker: {e}")
        return True  # Assume it exists to be safe


def is_first_time_execution() -> bool:
    """
    Determine if this is the first time the application is being executed.
    
    Uses multiple indicators to detect first-time execution:
    1. Database is empty (no revision history)
    2. No settings have been initialized
    3. No vector storage exists
    4. No output files exist
    5. No first-time marker file exists
    
    Returns:
        True if this appears to be the first time, False otherwise
    """
    if not FIRST_TIME_DETECTION_ENABLED:
        logger.debug("First-time detection is disabled")
        return False
    
    try:
        logger.info("Checking if this is first-time execution...")
        
        # Check for first-time marker first (most reliable)
        if has_first_time_marker():
            logger.info("First-time marker found - not first time")
            return False
        
        indicators = {
            "database_empty": is_database_empty(),
            "settings_not_initialized": not are_settings_initialized(),
            "no_vector_storage": not has_vector_storage(),
            "no_output_files": not has_output_files()
        }
        
        logger.info(f"First-time indicators: {indicators}")
        
        # If majority of indicators suggest first time, consider it first time
        first_time_count = sum(indicators.values())
        total_indicators = len(indicators)
        
        is_first_time = first_time_count >= (total_indicators // 2 + 1)
        
        if is_first_time:
            logger.info(f"✅ First-time execution detected ({first_time_count}/{total_indicators} indicators)")
        else:
            logger.info(f"❌ Not first-time execution ({first_time_count}/{total_indicators} indicators)")
        
        return is_first_time
        
    except Exception as e:
        logger.error(f"Error detecting first-time execution: {e}")
        # Default to not first-time to be safe
        return False


def get_first_time_job_config() -> Dict[str, Any]:
    """Get configuration for the first-time pipeline job."""
    return {
        "job_id": FIRST_TIME_JOB_ID,
        "force_recreate": FIRST_TIME_JOB_FORCE_RECREATE,
        "incremental_mode": "full",  # Force full processing on first run
        "ci_mode": True,
        "dry_run": False,
        "health_check": True,
        "should_save_stats": True
    }


def setup_first_time_execution_job(scheduler_instance) -> Dict[str, Any]:
    """
    Set up a one-time job to run the pipeline after first-time startup.
    
    Args:
        scheduler_instance: The scheduler instance to add the job to
        
    Returns:
        Dict containing setup status and details
    """
    status = {
        "success": False,
        "job_created": False,
        "job_id": None,
        "delay_seconds": FIRST_TIME_JOB_DELAY_SECONDS,
        "errors": [],
        "warnings": []
    }
    
    if not FIRST_TIME_RUN_PIPELINE_JOB:
        status["warnings"].append("First-time pipeline job is disabled")
        return status
    
    if not scheduler_instance:
        status["errors"].append("No scheduler instance provided")
        return status
    
    try:
        logger.info(f"Setting up first-time pipeline job (delay: {FIRST_TIME_JOB_DELAY_SECONDS}s)...")
        
        # Check if job already exists
        if scheduler_instance.scheduler.get_job(FIRST_TIME_JOB_ID):
            logger.info(f"First-time job '{FIRST_TIME_JOB_ID}' already exists")
            status.update({
                "success": True,
                "job_id": FIRST_TIME_JOB_ID,
                "warnings": ["Job already exists"]
            })
            return status
        
        # Get job configuration
        job_config = get_first_time_job_config()
        
        # Schedule the job to run after startup delay
        from datetime import datetime, timedelta
        run_time = datetime.now() + timedelta(seconds=FIRST_TIME_JOB_DELAY_SECONDS)
        
        job = scheduler_instance.add_one_time_job(
            job_id=FIRST_TIME_JOB_ID,
            run_date=run_time,
            pipeline_config=job_config
        )
        
        if job:
            logger.info(f"✅ First-time pipeline job scheduled: {FIRST_TIME_JOB_ID}")
            logger.info(f"   Will run at: {run_time}")
            logger.info(f"   Configuration: {job_config}")
            
            status.update({
                "success": True,
                "job_created": True,
                "job_id": FIRST_TIME_JOB_ID
            })
        else:
            error_msg = "Failed to create first-time job"
            status["errors"].append(error_msg)
            logger.error(error_msg)
        
        return status
        
    except Exception as e:
        error_msg = f"Error setting up first-time job: {e}"
        logger.error(error_msg)
        status["errors"].append(error_msg)
        return status


def complete_first_time_setup() -> bool:
    """
    Mark first-time setup as completed.
    
    Should be called after successful completion of first-time pipeline job.
    
    Returns:
        True if marker was created successfully
    """
    try:
        logger.info("Completing first-time setup...")
        success = create_first_time_marker()
        
        if success:
            logger.info("✅ First-time setup marked as completed")
        else:
            logger.error("❌ Failed to mark first-time setup as completed")
        
        return success
        
    except Exception as e:
        logger.error(f"Error completing first-time setup: {e}")
        return False


def get_first_time_status() -> Dict[str, Any]:
    """Get detailed status of first-time detection and setup."""
    try:
        return {
            "detection_enabled": FIRST_TIME_DETECTION_ENABLED,
            "run_pipeline_job": FIRST_TIME_RUN_PIPELINE_JOB,
            "is_first_time": is_first_time_execution(),
            "has_marker": has_first_time_marker(),
            "indicators": {
                "database_empty": is_database_empty(),
                "settings_not_initialized": not are_settings_initialized(),
                "no_vector_storage": not has_vector_storage(),
                "no_output_files": not has_output_files()
            },
            "job_config": {
                "job_id": FIRST_TIME_JOB_ID,
                "delay_seconds": FIRST_TIME_JOB_DELAY_SECONDS,
                "force_recreate": FIRST_TIME_JOB_FORCE_RECREATE
            }
        }
    except Exception as e:
        logger.error(f"Error getting first-time status: {e}")
        return {
            "error": str(e),
            "detection_enabled": FIRST_TIME_DETECTION_ENABLED,
            "run_pipeline_job": FIRST_TIME_RUN_PIPELINE_JOB
        }
