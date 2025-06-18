#!/usr/bin/env python3
"""
Test scheduler job addition
"""

import sys
import time
sys.path.insert(0, 'py-src')

print("Starting scheduler job addition test...")

try:
    from lets_talk.scheduler import PipelineScheduler
    
    scheduler = PipelineScheduler(
        scheduler_type="background",
        enable_persistence=False,
        max_workers=2
    )
    print("✓ Scheduler created")
    
    scheduler.start()
    print("✓ Scheduler started")
    
    print("Adding interval job...")
    job_id = scheduler.add_interval_job(
        job_id="test_job",
        minutes=5,
        pipeline_config={"dry_run": True, "job_id": "test_job"}
    )
    print(f"✓ Job added: {job_id}")
    
    print("Listing jobs...")
    jobs = scheduler.list_jobs()
    print(f"✓ Found {len(jobs)} jobs")
    
    for job in jobs:
        print(f"  - {job['id']}: {job['next_run_time']}")
    
    print("Testing export/import...")
    config = scheduler.export_job_config()
    print(f"✓ Config exported: {len(config['jobs'])} jobs")
    
    scheduler.shutdown()
    print("✓ Scheduler stopped")
    
    print("\n🎉 Job addition test successful!")
    
except Exception as e:
    print(f"✗ Job addition test failed: {e}")
    import traceback
    traceback.print_exc()
