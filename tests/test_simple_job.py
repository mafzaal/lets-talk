#!/usr/bin/env python3
"""
Test scheduler with simple job function
"""

import sys
import time
sys.path.insert(0, 'py-src')

def simple_test_job(config):
    """Simple test job that doesn't import complex modules"""
    import time
    print(f"Test job executed with config: {config}")
    time.sleep(0.1)  # Simulate some work
    return "success"

print("Starting scheduler with simple job test...")

try:
    from lets_talk.scheduler import PipelineScheduler
    
    # Create scheduler
    scheduler = PipelineScheduler(
        scheduler_type="background",
        enable_persistence=False,
        max_workers=2
    )
    print("✓ Scheduler created")
    
    scheduler.start()
    print("✓ Scheduler started")
    
    # Add job using APScheduler directly to avoid our wrapper
    print("Adding simple job directly...")
    if scheduler.scheduler is not None:
        job = scheduler.scheduler.add_job(
            func=simple_test_job,
            trigger='interval',
            minutes=5,
            args=[{"job_id": "simple_test", "dry_run": True}],
            id="simple_test_job",
            name="Simple Test Job"
        )
        print(f"✓ Simple job added: {job.id}")
    else:
        print("✗ Scheduler instance is None")
    
    print("Listing jobs...")
    jobs = scheduler.list_jobs()
    print(f"✓ Found {len(jobs)} jobs")
    
    for job in jobs:
        print(f"  - {job['id']}: {job['next_run_time']}")
    
    scheduler.shutdown()
    print("✓ Scheduler stopped")
    
    print("\n🎉 Simple job test successful!")
    
except Exception as e:
    print(f"✗ Simple job test failed: {e}")
    import traceback
    traceback.print_exc()
