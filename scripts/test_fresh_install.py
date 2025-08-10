#!/usr/bin/env python3
"""
Test script to simulate a fresh first-time installation.

This script will:
1. Backup existing database, settings, and output files
2. Run the first-time detection to show it detects as first-time
3. Run the startup sequence
4. Restore the original files
"""
import sys
import os
import shutil
import logging
from pathlib import Path

# Add the backend to the Python path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'backend'))

from lets_talk.shared.config import LOGGER_NAME, OUTPUT_DIR, DATABASE_URL
from lets_talk.core.first_time import is_first_time_execution, get_first_time_status
from lets_talk.core.startup import startup_fastapi_application

# Set up logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(f"{LOGGER_NAME}.fresh_install_test")


def backup_existing_data():
    """Backup existing data to simulate a fresh install."""
    backups = {}
    
    logger.info("🗄️  Backing up existing data...")
    
    # Backup database file if it exists (for SQLite)
    if DATABASE_URL.startswith('sqlite:'):
        db_path = DATABASE_URL.replace('sqlite:///', '')
        if os.path.exists(db_path):
            backup_db = f"{db_path}.backup"
            shutil.copy2(db_path, backup_db)
            os.remove(db_path)
            backups['database'] = backup_db
            logger.info(f"   Database backed up: {backup_db}")
    
    # Backup output directory
    output_path = Path(OUTPUT_DIR)
    if output_path.exists():
        backup_output = Path(f"{OUTPUT_DIR}.backup")
        if backup_output.exists():
            shutil.rmtree(backup_output)
        shutil.copytree(output_path, backup_output)
        shutil.rmtree(output_path)
        backups['output'] = str(backup_output)
        logger.info(f"   Output directory backed up: {backup_output}")
    
    # Backup vector storage (assuming it's in the db directory)
    vector_path = Path("db")
    if vector_path.exists():
        backup_vector = Path("db.backup")
        if backup_vector.exists():
            shutil.rmtree(backup_vector)
        shutil.copytree(vector_path, backup_vector)
        shutil.rmtree(vector_path)
        backups['vector'] = str(backup_vector)
        logger.info(f"   Vector storage backed up: {backup_vector}")
    
    return backups


def restore_existing_data(backups):
    """Restore the backed up data."""
    logger.info("🔄 Restoring backed up data...")
    
    # Restore database
    if 'database' in backups and os.path.exists(backups['database']):
        db_path = DATABASE_URL.replace('sqlite:///', '')
        # Ensure the output directory exists
        os.makedirs(os.path.dirname(db_path), exist_ok=True)
        shutil.copy2(backups['database'], db_path)
        os.remove(backups['database'])
        logger.info(f"   Database restored: {db_path}")
    
    # Restore output directory
    if 'output' in backups and os.path.exists(backups['output']):
        output_path = Path(OUTPUT_DIR)
        if output_path.exists():
            shutil.rmtree(output_path)
        shutil.copytree(backups['output'], output_path)
        shutil.rmtree(backups['output'])
        logger.info(f"   Output directory restored: {output_path}")
    
    # Restore vector storage
    if 'vector' in backups and os.path.exists(backups['vector']):
        vector_path = Path("db")
        if vector_path.exists():
            shutil.rmtree(vector_path)
        shutil.copytree(backups['vector'], vector_path)
        shutil.rmtree(backups['vector'])
        logger.info(f"   Vector storage restored: {vector_path}")


def test_fresh_first_time_detection():
    """Test first-time detection on a fresh system."""
    logger.info("\n🆕 Testing First-Time Detection on Fresh System")
    logger.info("=" * 60)
    
    # Test the detection
    status = get_first_time_status()
    logger.info(f"Detection enabled: {status.get('detection_enabled')}")
    logger.info(f"Run pipeline job: {status.get('run_pipeline_job')}")
    logger.info(f"Is first time: {status.get('is_first_time')}")
    logger.info(f"Has marker: {status.get('has_marker')}")
    logger.info(f"Indicators: {status.get('indicators')}")
    
    is_first_time = is_first_time_execution()
    logger.info(f"\n📊 First-time execution result: {is_first_time}")
    
    return is_first_time


def test_startup_with_first_time():
    """Test the startup sequence with first-time detection."""
    logger.info("\n🚀 Testing Startup Sequence with First-Time Detection")
    logger.info("=" * 60)
    
    try:
        # Run the startup sequence
        startup_info = startup_fastapi_application(
            app_name="Fresh Install Test",
            fail_on_migration_error=False,
            fail_on_scheduler_error=False,
            fail_on_default_job_error=False
        )
        
        # Log the results
        logger.info(f"Startup success: {startup_info['success']}")
        logger.info(f"Database initialized: {startup_info['database_initialized']}")
        logger.info(f"Scheduler initialized: {startup_info['scheduler_initialized']}")
        logger.info(f"Default jobs initialized: {startup_info['default_jobs_initialized']}")
        
        # Check first-time specific results
        if 'first_time_detected' in startup_info:
            logger.info(f"First-time detected: {startup_info['first_time_detected']}")
            logger.info(f"First-time job created: {startup_info['first_time_job_created']}")
        
        # Check for scheduled jobs
        scheduler_instance = startup_info.get('scheduler_instance')
        if scheduler_instance and scheduler_instance.scheduler:
            jobs = scheduler_instance.scheduler.get_jobs()
            logger.info(f"Scheduled jobs count: {len(jobs)}")
            for job in jobs:
                logger.info(f"  - {job.id}: next run at {job.next_run_time}")
        
        # Clean shutdown
        if scheduler_instance:
            scheduler_instance.shutdown(wait=False)
            logger.info("Scheduler shut down")
        
        return startup_info
        
    except Exception as e:
        logger.error(f"Startup test failed: {e}")
        import traceback
        traceback.print_exc()
        return {"success": False, "error": str(e)}


def main():
    """Main test function."""
    logger.info("🧪 Starting Fresh Install First-Time Detection Test")
    logger.info("=" * 80)
    
    # Step 1: Backup existing data
    backups = backup_existing_data()
    
    try:
        # Step 2: Test first-time detection on fresh system
        is_first_time = test_fresh_first_time_detection()
        
        if not is_first_time:
            logger.warning("⚠️  System still not detected as first-time after cleanup!")
            logger.info("This might indicate that the detection logic needs adjustment")
        else:
            logger.info("✅ System correctly detected as first-time execution!")
            
            # Step 3: Test the full startup sequence
            startup_info = test_startup_with_first_time()
            
            if startup_info['success']:
                logger.info("✅ Startup sequence completed successfully!")
                
                # Check if first-time job was created
                if startup_info.get('first_time_job_created'):
                    logger.info("🎉 First-time pipeline job was successfully scheduled!")
                else:
                    logger.warning("⚠️  First-time job was not created")
            else:
                logger.error("❌ Startup sequence failed")
        
        # Final summary
        logger.info("\n📋 Test Summary:")
        logger.info(f"  First-time detected: {is_first_time}")
        startup_info = locals().get('startup_info', {})
        if startup_info:
            logger.info(f"  Startup successful: {startup_info.get('success', False)}")
            logger.info(f"  First-time job created: {startup_info.get('first_time_job_created', False)}")
        
    except Exception as e:
        logger.error(f"Test failed: {e}")
        import traceback
        traceback.print_exc()
    
    finally:
        # Step 4: Restore original data
        restore_existing_data(backups)
        logger.info("✅ Original data restored")
    
    logger.info("\n🏁 Fresh Install Test Complete")


if __name__ == "__main__":
    main()
