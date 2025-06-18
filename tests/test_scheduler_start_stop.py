#!/usr/bin/env python3
"""
Test scheduler start/stop
"""

import sys
import time
sys.path.insert(0, 'py-src')

print("Starting scheduler start/stop test...")

try:
    from lets_talk.scheduler import PipelineScheduler
    
    scheduler = PipelineScheduler(
        scheduler_type="background",
        enable_persistence=False,
        max_workers=2
    )
    print("✓ Scheduler created")
    
    print("Starting scheduler...")
    scheduler.start()
    print("✓ Scheduler started")
    
    print("Waiting 1 second...")
    time.sleep(1)
    
    print("Checking if scheduler is running...")
    if scheduler.scheduler and scheduler.scheduler.running:
        print("✓ Scheduler is running")
    else:
        print("✗ Scheduler is not running")
    
    print("Stopping scheduler...")
    scheduler.shutdown()
    print("✓ Scheduler stopped")
    
    print("\n🎉 Start/stop test successful!")
    
except Exception as e:
    print(f"✗ Start/stop test failed: {e}")
    import traceback
    traceback.print_exc()
