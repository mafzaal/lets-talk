#!/usr/bin/env python3
"""
Quick test script for the pipeline scheduler functionality.
"""

import json
import os
import tempfile
import time
from datetime import datetime, timedelta

from lets_talk.scheduler import PipelineScheduler, create_default_scheduler_config
from lets_talk.config import OUTPUT_DIR

def test_scheduler_basic():
    """Test basic scheduler functionality."""
    print("Testing basic scheduler functionality...")
    
    # Create a temporary scheduler with memory store
    scheduler = PipelineScheduler(
        scheduler_type="background",
        enable_persistence=False,  # Use memory store for testing
        max_workers=2,
        executor_type="thread"
    )
    
    # Add a simple test job (dry run)
    test_config = {
        "dry_run": True,
        "ci_mode": True,
        "incremental_mode": "auto"
    }
    
    job_id = scheduler.add_interval_job(
        job_id="test_interval_job",
        minutes=1,  # Every minute for testing
        pipeline_config=test_config
    )
    
    print(f"Added test job: {job_id}")
    
    # List jobs
    jobs = scheduler.list_jobs()
    print(f"Jobs in scheduler: {len(jobs)}")
    for job in jobs:
        print(f"  - {job['id']}: next run at {job['next_run_time']}")
    
    # Start scheduler
    scheduler.start()
    print("Scheduler started")
    
    # Run for a short time
    print("Running scheduler for 10 seconds...")
    time.sleep(10)
    
    # Check stats
    stats = scheduler.get_job_stats()
    print(f"Job statistics: {stats}")
    
    # Shutdown
    scheduler.shutdown()
    print("Scheduler shut down")
    
    return True

def test_configuration():
    """Test configuration management."""
    print("\nTesting configuration management...")
    
    # Create default config
    config = create_default_scheduler_config()
    print(f"Default config has {len(config['jobs'])} jobs")
    
    # Save to temp file
    with tempfile.NamedTemporaryFile(mode='w', suffix='.json', delete=False) as f:
        json.dump(config, f, indent=2)
        config_file = f.name
    
    try:
        # Test loading config
        from lets_talk.scheduler import load_scheduler_config_from_file
        loaded_config = load_scheduler_config_from_file(config_file)
        print(f"Loaded config has {len(loaded_config['jobs'])} jobs")
        
        # Verify job types
        job_types = [job['type'] for job in loaded_config['jobs']]
        print(f"Job types: {job_types}")
        
        return loaded_config == config
        
    finally:
        # Cleanup
        os.unlink(config_file)

def test_cron_job():
    """Test cron job functionality."""
    print("\nTesting cron job functionality...")
    
    scheduler = PipelineScheduler(
        scheduler_type="background",
        enable_persistence=False
    )
    
    # Add a cron job for next minute
    next_minute = (datetime.now() + timedelta(minutes=1))
    
    job_id = scheduler.add_cron_job(
        job_id="test_cron_job",
        hour=next_minute.hour,
        minute=next_minute.minute,
        pipeline_config={"dry_run": True, "ci_mode": True}
    )
    
    print(f"Added cron job: {job_id} for {next_minute.strftime('%H:%M')}")
    
    jobs = scheduler.list_jobs()
    for job in jobs:
        print(f"  Job: {job['id']}, Next run: {job['next_run_time']}")
    
    scheduler.shutdown()
    return True

def main():
    """Run all tests."""
    print("=== Pipeline Scheduler Test Suite ===")
    
    # Ensure output directory exists
    os.makedirs(OUTPUT_DIR, exist_ok=True)
    
    tests = [
        ("Basic Scheduler", test_scheduler_basic),
        ("Configuration", test_configuration), 
        ("Cron Jobs", test_cron_job)
    ]
    
    results = {}
    
    for test_name, test_func in tests:
        try:
            print(f"\n{'='*50}")
            result = test_func()
            results[test_name] = "PASS" if result else "FAIL"
            print(f"{test_name}: {'PASS' if result else 'FAIL'}")
        except Exception as e:
            results[test_name] = f"ERROR: {e}"
            print(f"{test_name}: ERROR - {e}")
    
    print(f"\n{'='*50}")
    print("Test Results Summary:")
    for test_name, result in results.items():
        print(f"  {test_name}: {result}")
    
    all_passed = all(result == "PASS" for result in results.values())
    print(f"\nOverall: {'ALL TESTS PASSED' if all_passed else 'SOME TESTS FAILED'}")
    
    return 0 if all_passed else 1

if __name__ == '__main__':
    import sys
    sys.exit(main())
