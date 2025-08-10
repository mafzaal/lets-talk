#!/usr/bin/env python3
"""
Test script for first-time execution detection and setup.

This script simulates the first-time execution scenario by:
1. Temporarily removing the first-time marker (if it exists)
2. Testing the detection logic
3. Running the startup sequence 
4. Verifying that the first-time job is scheduled
"""
import sys
import os
import logging
from pathlib import Path

# Add the backend to the Python path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'backend'))

from lets_talk.shared.config import LOGGER_NAME, OUTPUT_DIR, FIRST_TIME_JOB_ID
from lets_talk.core.first_time import (
    is_first_time_execution, 
    get_first_time_status,
    has_first_time_marker,
    create_first_time_marker,
    complete_first_time_setup
)

# Set up logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(f"{LOGGER_NAME}.first_time_test")


def backup_first_time_marker():
    """Backup the first-time marker if it exists."""
    marker_path = Path(OUTPUT_DIR) / ".first_time_setup_completed"
    backup_path = Path(OUTPUT_DIR) / ".first_time_setup_completed.backup"
    
    if marker_path.exists():
        logger.info(f"Backing up first-time marker: {marker_path} -> {backup_path}")
        marker_path.rename(backup_path)
        return True
    return False


def restore_first_time_marker():
    """Restore the first-time marker from backup."""
    marker_path = Path(OUTPUT_DIR) / ".first_time_setup_completed"
    backup_path = Path(OUTPUT_DIR) / ".first_time_setup_completed.backup"
    
    if backup_path.exists():
        logger.info(f"Restoring first-time marker: {backup_path} -> {marker_path}")
        backup_path.rename(marker_path)
        return True
    return False


def test_first_time_detection():
    """Test the first-time execution detection logic."""
    logger.info("="*60)
    logger.info("Testing First-Time Execution Detection")
    logger.info("="*60)
    
    # Test 1: Check detection status
    logger.info("\n1. Testing detection logic...")
    status = get_first_time_status()
    logger.info(f"   Detection enabled: {status.get('detection_enabled')}")
    logger.info(f"   Run pipeline job: {status.get('run_pipeline_job')}")
    logger.info(f"   Is first time: {status.get('is_first_time')}")
    logger.info(f"   Has marker: {status.get('has_marker')}")
    logger.info(f"   Indicators: {status.get('indicators')}")
    
    # Test 2: Check individual functions
    logger.info("\n2. Testing individual detection functions...")
    logger.info(f"   is_first_time_execution(): {is_first_time_execution()}")
    logger.info(f"   has_first_time_marker(): {has_first_time_marker()}")
    
    return status


def test_scheduler_integration():
    """Test the scheduler integration."""
    logger.info("\n3. Testing scheduler integration...")
    
    try:
        from lets_talk.core.scheduler.manager import PipelineScheduler
        from lets_talk.core.first_time import setup_first_time_execution_job
        
        # Create a test scheduler
        logger.info("   Creating test scheduler...")
        scheduler = PipelineScheduler(
            scheduler_type="background",
            enable_persistence=False  # Use memory store for testing
        )
        scheduler.start()
        
        # Test first-time job setup
        logger.info("   Setting up first-time job...")
        job_status = setup_first_time_execution_job(scheduler)
        
        logger.info(f"   Job setup success: {job_status['success']}")
        logger.info(f"   Job created: {job_status['job_created']}")
        logger.info(f"   Job ID: {job_status['job_id']}")
        logger.info(f"   Delay seconds: {job_status['delay_seconds']}")
        
        if job_status['errors']:
            logger.error(f"   Errors: {job_status['errors']}")
        if job_status['warnings']:
            logger.warning(f"   Warnings: {job_status['warnings']}")
        
        # Check if job exists in scheduler
        if scheduler.scheduler:
            job = scheduler.scheduler.get_job(FIRST_TIME_JOB_ID)
            if job:
                logger.info(f"   ✅ Job found in scheduler: {job.id}")
                logger.info(f"   Next run time: {job.next_run_time}")
            else:
                logger.warning(f"   ❌ Job not found in scheduler")
        
        # Cleanup
        scheduler.shutdown(wait=False)
        logger.info("   Scheduler shut down")
        
        return job_status
        
    except Exception as e:
        logger.error(f"   Error testing scheduler integration: {e}")
        return {"success": False, "error": str(e)}


def test_marker_functions():
    """Test the marker creation and completion functions."""
    logger.info("\n4. Testing marker functions...")
    
    # Test marker creation
    logger.info("   Testing create_first_time_marker()...")
    marker_created = create_first_time_marker()
    logger.info(f"   Marker created: {marker_created}")
    
    if marker_created:
        logger.info(f"   Marker exists: {has_first_time_marker()}")
    
    # Test completion function
    logger.info("   Testing complete_first_time_setup()...")
    setup_completed = complete_first_time_setup()
    logger.info(f"   Setup completed: {setup_completed}")
    
    return marker_created and setup_completed


def main():
    """Main test function."""
    logger.info("🧪 Starting First-Time Execution Detection Tests")
    logger.info("=" * 80)
    
    # Backup existing marker
    had_marker = backup_first_time_marker()
    
    try:
        # Run tests
        detection_status = test_first_time_detection()
        scheduler_status = test_scheduler_integration()
        marker_status = test_marker_functions()
        
        # Summary
        logger.info("\n" + "="*60)
        logger.info("Test Summary")
        logger.info("="*60)
        
        logger.info(f"✅ Detection test: {'PASS' if detection_status else 'FAIL'}")
        logger.info(f"✅ Scheduler test: {'PASS' if scheduler_status.get('success') else 'FAIL'}")
        logger.info(f"✅ Marker test: {'PASS' if marker_status else 'FAIL'}")
        
        if detection_status.get('is_first_time'):
            logger.info("🎉 System detected as first-time execution!")
        else:
            logger.info("ℹ️  System not detected as first-time execution")
        
        # Final status check
        logger.info("\nFinal first-time status after tests:")
        final_status = get_first_time_status()
        logger.info(f"   Is first time: {final_status.get('is_first_time')}")
        logger.info(f"   Has marker: {final_status.get('has_marker')}")
        
    except Exception as e:
        logger.error(f"Test failed with error: {e}")
        import traceback
        traceback.print_exc()
    
    finally:
        # Restore original marker if it existed
        if had_marker:
            # Remove test marker first
            marker_path = Path(OUTPUT_DIR) / ".first_time_setup_completed"
            if marker_path.exists():
                marker_path.unlink()
            
            # Restore original
            restore_first_time_marker()
            logger.info("Original first-time marker restored")
    
    logger.info("\n🏁 First-Time Execution Detection Tests Complete")


if __name__ == "__main__":
    main()
