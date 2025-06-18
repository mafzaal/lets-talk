#!/usr/bin/env python3
"""
Test persistent job store functionality
"""

import sys
import os
import time
from pathlib import Path

# Add the py-src directory to Python path
sys.path.insert(0, 'py-src')

def test_memory_store():
    """Test with in-memory job store (should work)"""
    print("=== Testing Memory Job Store ===")
    
    try:
        from lets_talk.scheduler import PipelineScheduler
        
        # Create scheduler with memory store
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
            minutes=1,  # 1 minute interval
            pipeline_config={"dry_run": True, "job_id": "test_memory_job"}
        )
        print(f"✓ Job added: {job_id}")
        
        # List jobs
        jobs = scheduler.list_jobs()
        print(f"✓ Jobs listed: {len(jobs)} jobs")
        
        # Stop scheduler
        scheduler.shutdown()
        print("✓ Memory scheduler stopped")
        
        return True
        
    except Exception as e:
        print(f"✗ Memory store test failed: {e}")
        import traceback
        traceback.print_exc()
        return False

def test_sqlite_store():
    """Test with SQLite job store (may have issues)"""
    print("\n=== Testing SQLite Job Store ===")
    
    try:
        from lets_talk.scheduler import PipelineScheduler
        
        # Create scheduler with SQLite store
        scheduler = PipelineScheduler(
            scheduler_type="background",
            enable_persistence=True,  # Use SQLite store
            job_store_url="sqlite:///test_jobs.db"
        )
        print("✓ SQLite scheduler created")
        
        # Start scheduler
        scheduler.start()
        print("✓ SQLite scheduler started")
        
        # Add a test job
        job_id = scheduler.add_interval_job(
            job_id="test_sqlite_job",
            minutes=2,  # 2 minute interval
            pipeline_config={"dry_run": True, "job_id": "test_sqlite_job"}
        )
        print(f"✓ Job added: {job_id}")
        
        # List jobs
        jobs = scheduler.list_jobs()
        print(f"✓ Jobs listed: {len(jobs)} jobs")
        
        # Stop scheduler
        scheduler.shutdown()
        print("✓ SQLite scheduler stopped")
        
        return True
        
    except Exception as e:
        print(f"✗ SQLite store test failed: {e}")
        import traceback
        traceback.print_exc()
        return False

def test_minimal_apscheduler():
    """Test APScheduler directly without our wrapper"""
    print("\n=== Testing APScheduler Directly ===")
    
    try:
        from apscheduler.schedulers.background import BackgroundScheduler
        from apscheduler.jobstores.memory import MemoryJobStore
        from apscheduler.jobstores.sqlalchemy import SQLAlchemyJobStore
        from apscheduler.executors.pool import ThreadPoolExecutor
        
        print("✓ APScheduler imports successful")
        
        # Test memory store
        scheduler = BackgroundScheduler(
            jobstores={'default': MemoryJobStore()},
            executors={'default': ThreadPoolExecutor(max_workers=2)}
        )
        scheduler.start()
        print("✓ APScheduler with memory store started")
        scheduler.shutdown()
        print("✓ APScheduler with memory store stopped")
        
        # Test SQLite store
        scheduler = BackgroundScheduler(
            jobstores={'default': SQLAlchemyJobStore(url='sqlite:///test_direct.db')},
            executors={'default': ThreadPoolExecutor(max_workers=2)}
        )
        scheduler.start()
        print("✓ APScheduler with SQLite store started")
        scheduler.shutdown()
        print("✓ APScheduler with SQLite store stopped")
        
        return True
        
    except Exception as e:
        print(f"✗ Direct APScheduler test failed: {e}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == "__main__":
    print("Starting scheduler persistence tests...")
    
    # Test 1: Memory store (baseline)
    memory_ok = test_memory_store()
    
    # Test 2: Minimal APScheduler
    minimal_ok = test_minimal_apscheduler()
    
    # Test 3: SQLite store (the problematic one)
    sqlite_ok = test_sqlite_store()
    
    print(f"\n=== Results ===")
    print(f"Memory store: {'✓' if memory_ok else '✗'}")
    print(f"Minimal APScheduler: {'✓' if minimal_ok else '✗'}")
    print(f"SQLite store: {'✓' if sqlite_ok else '✗'}")
    
    if memory_ok and minimal_ok and sqlite_ok:
        print("\n🎉 All tests passed!")
    elif memory_ok and minimal_ok:
        print("\n⚠️  Basic functionality works, but SQLite store has issues")
    else:
        print("\n❌ Fundamental issues detected")
