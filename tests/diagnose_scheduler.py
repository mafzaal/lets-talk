#!/usr/bin/env python3
"""
Diagnostic script for scheduler issues
"""

import sys
import os

# Add the py-src directory to Python path
sys.path.insert(0, 'py-src')

print("=== Scheduler Diagnostic ===")

# Test 1: Basic imports
print("Test 1: Basic imports")
try:
    import lets_talk
    print("  ✓ lets_talk package imported")
except Exception as e:
    print(f"  ✗ lets_talk import failed: {e}")
    sys.exit(1)

try:
    from lets_talk.config import OUTPUT_DIR
    print(f"  ✓ config imported, OUTPUT_DIR={OUTPUT_DIR}")
except Exception as e:
    print(f"  ✗ config import failed: {e}")
    sys.exit(1)

# Test 2: Pipeline job function
print("\nTest 2: Pipeline job function")
try:
    from lets_talk.pipeline_job import pipeline_job_function
    print("  ✓ pipeline_job_function imported")
except Exception as e:
    print(f"  ✗ pipeline_job_function import failed: {e}")
    import traceback
    traceback.print_exc()
    sys.exit(1)

# Test 3: Scheduler class
print("\nTest 3: Scheduler class")
try:
    from lets_talk.scheduler import PipelineScheduler
    print("  ✓ PipelineScheduler imported")
except Exception as e:
    print(f"  ✗ PipelineScheduler import failed: {e}")
    import traceback
    traceback.print_exc()
    sys.exit(1)

# Test 4: Create scheduler instance
print("\nTest 4: Create scheduler instance")
try:
    scheduler = PipelineScheduler(enable_persistence=False)
    print("  ✓ PipelineScheduler instance created")
except Exception as e:
    print(f"  ✗ PipelineScheduler instantiation failed: {e}")
    import traceback
    traceback.print_exc()
    sys.exit(1)

# Test 5: Add job
print("\nTest 5: Add job")
try:
    job_id = scheduler.add_interval_job(
        job_id="test_job",
        minutes=5,
        pipeline_config={"dry_run": True}
    )
    print(f"  ✓ Job added: {job_id}")
except Exception as e:
    print(f"  ✗ Add job failed: {e}")
    import traceback
    traceback.print_exc()
    sys.exit(1)

print("\n=== All tests passed! ===")
