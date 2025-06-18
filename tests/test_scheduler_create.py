#!/usr/bin/env python3
"""
Test scheduler instantiation without starting
"""

import sys
sys.path.insert(0, 'py-src')

print("Starting scheduler instantiation test...")

try:
    from lets_talk.scheduler import PipelineScheduler
    
    print("1. Creating scheduler with memory store...")
    scheduler = PipelineScheduler(
        scheduler_type="background",
        enable_persistence=False,  # Memory store
        max_workers=2
    )
    print("   ✓ Scheduler created (not started)")
    
    print("2. Testing scheduler properties...")
    print(f"   - Scheduler type: {scheduler.scheduler_type}")
    print(f"   - Max workers: {scheduler.max_workers}")
    print(f"   - Enable persistence: {scheduler.enable_persistence}")
    print(f"   - Job store URL: {scheduler.job_store_url}")
    
    print("3. Testing if scheduler instance exists...")
    if scheduler.scheduler is not None:
        print("   ✓ APScheduler instance exists")
    else:
        print("   ✗ APScheduler instance is None")
    
    print("\n🎉 Scheduler instantiation successful!")
    
except Exception as e:
    print(f"✗ Instantiation failed: {e}")
    import traceback
    traceback.print_exc()
