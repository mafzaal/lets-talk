#!/usr/bin/env python3
"""
Test script for default job functionality.
"""
import os
import sys
import logging

# Add the backend directory to Python path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'backend'))

from lets_talk.core.scheduler.manager import PipelineScheduler
from lets_talk.shared.config import (
    DEFAULT_JOB_ENABLED, DEFAULT_JOB_ID, DEFAULT_JOB_CRON_HOUR, 
    DEFAULT_JOB_CRON_MINUTE, LOGGER_NAME
)

# Set up logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(f"{LOGGER_NAME}.test")

def test_default_job_functionality():
    """Test the default job creation and management."""
    print("="*60)
    print("Testing Default Job Functionality")
    print("="*60)
    
    print(f"\n📋 Configuration:")
    print(f"   • Default job enabled: {DEFAULT_JOB_ENABLED}")
    print(f"   • Default job ID: {DEFAULT_JOB_ID}")
    print(f"   • Schedule time: {DEFAULT_JOB_CRON_HOUR:02d}:{DEFAULT_JOB_CRON_MINUTE:02d}")
    
    if not DEFAULT_JOB_ENABLED:
        print("\n⚠️  Default job is disabled, skipping test")
        return
    
    print(f"\n🔧 Creating scheduler (memory-only for testing)...")
    scheduler = PipelineScheduler(
        scheduler_type="background",
        max_workers=2,
        enable_persistence=False  # Use memory for testing
    )
    
    try:
        print(f"🚀 Starting scheduler...")
        scheduler.start()
        
        print(f"✅ Scheduler started successfully")
        
        # Test default job check (should be false initially)
        print(f"\n🔍 Checking if default job exists...")
        has_default = scheduler.has_default_job()
        print(f"   Default job exists: {has_default}")
        
        # Test default job initialization
        print(f"\n⚡ Initializing default job if needed...")
        success = scheduler.initialize_default_job_if_needed()
        print(f"   Initialization success: {success}")
        
        # Check again
        print(f"\n🔍 Checking if default job exists after initialization...")
        has_default_after = scheduler.has_default_job()
        print(f"   Default job exists: {has_default_after}")
        
        # List all jobs
        print(f"\n📋 Current scheduled jobs:")
        jobs = scheduler.list_jobs()
        if jobs:
            for job in jobs:
                print(f"   • {job['id']}: {job['name']} (next run: {job['next_run_time']})")
        else:
            print("   No jobs scheduled")
        
        # Test initialization again (should skip creation)
        print(f"\n🔄 Testing duplicate initialization (should skip)...")
        success_again = scheduler.initialize_default_job_if_needed()
        print(f"   Second initialization success: {success_again}")
        
        print(f"\n✅ All tests completed successfully!")
        
    except Exception as e:
        print(f"\n❌ Test failed: {e}")
        logger.exception("Test error details:")
    finally:
        print(f"\n🛑 Shutting down scheduler...")
        scheduler.shutdown()
        print(f"✅ Cleanup completed")

if __name__ == "__main__":
    test_default_job_functionality()
