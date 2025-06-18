#!/usr/bin/env python3
"""
Working scheduler test with memory store and alternative persistence
"""

import json
import os
from datetime import datetime

def test_memory_scheduler():
    """Test our scheduler with memory store"""
    print("=== Testing Memory Scheduler ===")
    
    # Add the py-src directory to Python path
    import sys
    sys.path.insert(0, 'py-src')
    
    try:
        from lets_talk.scheduler import PipelineScheduler
        
        # Create scheduler with memory store (should work)
        scheduler = PipelineScheduler(
            scheduler_type="background",
            enable_persistence=False  # Use memory store
        )
        print("✓ Memory scheduler created")
        
        # Start scheduler
        scheduler.start()
        print("✓ Memory scheduler started")
        
        # Add a test job
        job_id = scheduler.add_interval_job(
            job_id="test_memory_job",
            minutes=1,
            pipeline_config={"dry_run": True, "job_id": "test_memory_job"}
        )
        print(f"✓ Job added: {job_id}")
        
        # List jobs
        jobs = scheduler.list_jobs()
        print(f"✓ Jobs listed: {len(jobs)} jobs")
        for job in jobs:
            print(f"  - {job['id']}: {job['next_run_time']}")
        
        # Test job config export/import (alternative persistence)
        config = scheduler.export_job_config()
        print(f"✓ Job config exported: {len(config['jobs'])} jobs")
        
        # Save config to file
        with open('scheduler_jobs_backup.json', 'w') as f:
            json.dump(config, f, indent=2)
        print("✓ Job config saved to file")
        
        # Stop scheduler
        scheduler.shutdown()
        print("✓ Memory scheduler stopped")
        
        print("\n--- Testing config restoration ---")
        
        # Create new scheduler and import jobs
        scheduler2 = PipelineScheduler(
            scheduler_type="background",
            enable_persistence=False
        )
        scheduler2.start()
        print("✓ New scheduler created and started")
        
        # Import jobs from config
        with open('scheduler_jobs_backup.json', 'r') as f:
            config = json.load(f)
        
        scheduler2.import_job_config(config)
        print("✓ Job config imported")
        
        jobs2 = scheduler2.list_jobs()
        print(f"✓ Restored jobs: {len(jobs2)} jobs")
        for job in jobs2:
            print(f"  - {job['id']}: {job['next_run_time']}")
        
        scheduler2.shutdown()
        print("✓ Second scheduler stopped")
        
        return True
        
    except Exception as e:
        print(f"✗ Test failed: {e}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == "__main__":
    success = test_memory_scheduler()
    if success:
        print("\n🎉 Memory scheduler with config backup works!")
        print("📁 Job configuration saved to 'scheduler_jobs_backup.json'")
        print("💡 This provides persistence without SQLAlchemy dependency")
    else:
        print("\n❌ Memory scheduler test failed!")
