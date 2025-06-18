#!/usr/bin/env python3
"""
Basic import test to isolate hanging issue
"""

import sys
sys.path.insert(0, 'py-src')

print("Starting basic import test...")

try:
    print("1. Testing config import...")
    from lets_talk.config import OUTPUT_DIR
    print(f"   ✓ config imported, OUTPUT_DIR={OUTPUT_DIR}")
    
    print("2. Testing pipeline_job import...")
    from lets_talk.pipeline_job import pipeline_job_function
    print("   ✓ pipeline_job_function imported")
    
    print("3. Testing APScheduler basic imports...")
    from apscheduler.schedulers.background import BackgroundScheduler
    from apscheduler.jobstores.memory import MemoryJobStore
    from apscheduler.executors.pool import ThreadPoolExecutor
    print("   ✓ APScheduler imports successful")
    
    print("4. Testing scheduler class import...")
    from lets_talk.scheduler import PipelineScheduler
    print("   ✓ PipelineScheduler imported")
    
    print("\n🎉 All imports successful!")
    
except Exception as e:
    print(f"✗ Import failed: {e}")
    import traceback
    traceback.print_exc()
