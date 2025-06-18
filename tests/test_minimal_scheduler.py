#!/usr/bin/env python3
"""
Minimal test for APScheduler + SQLAlchemy integration
"""

def simple_job():
    """Simple test job"""
    print("Test job executed!")
    return "success"

def test_apscheduler_sqlite():
    """Test APScheduler with SQLite directly"""
    print("Testing APScheduler with SQLite...")
    
    try:
        # Import required modules
        from apscheduler.schedulers.background import BackgroundScheduler
        from apscheduler.jobstores.sqlalchemy import SQLAlchemyJobStore
        from apscheduler.executors.pool import ThreadPoolExecutor
        import time
        
        print("✓ Imports successful")
        
        # Create job store
        jobstore = SQLAlchemyJobStore(url='sqlite:///minimal_test.db')
        print("✓ SQLAlchemy job store created")
        
        # Create scheduler
        scheduler = BackgroundScheduler(
            jobstores={'default': jobstore},
            executors={'default': ThreadPoolExecutor(max_workers=1)}
        )
        print("✓ Scheduler created")
        
        # Start scheduler
        scheduler.start()
        print("✓ Scheduler started")
        
        # Add a simple job
        job = scheduler.add_job(simple_job, 'interval', seconds=5, id='test_job')
        print(f"✓ Job added: {job.id}")
        
        # Wait a bit
        print("Waiting 2 seconds...")
        time.sleep(2)
        
        # List jobs
        jobs = scheduler.get_jobs()
        print(f"✓ Found {len(jobs)} jobs")
        
        # Stop scheduler
        scheduler.shutdown()
        print("✓ Scheduler stopped")
        
        return True
        
    except Exception as e:
        print(f"✗ Test failed: {e}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == "__main__":
    success = test_apscheduler_sqlite()
    if success:
        print("\n🎉 APScheduler + SQLite test passed!")
    else:
        print("\n❌ APScheduler + SQLite test failed!")
