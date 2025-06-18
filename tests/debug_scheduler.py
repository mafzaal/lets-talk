#!/usr/bin/env python3
"""
Debug APScheduler job attributes
"""

from apscheduler.schedulers.background import BackgroundScheduler
from apscheduler.triggers.interval import IntervalTrigger

def test_job():
    print("Job executed!")

# Create scheduler
scheduler = BackgroundScheduler()

# Add a job
job = scheduler.add_job(test_job, IntervalTrigger(minutes=1), id='test_job')

print("Job object type:", type(job))
print("Job attributes:", [attr for attr in dir(job) if not attr.startswith('_')])

# Check if job has next_run_time before starting
print("Before start:")
print("  Has next_run_time:", hasattr(job, 'next_run_time'))
if hasattr(job, 'next_run_time'):
    print("  next_run_time:", job.next_run_time)

# Start scheduler
scheduler.start()

print("After start:")
print("  Has next_run_time:", hasattr(job, 'next_run_time'))
if hasattr(job, 'next_run_time'):
    print("  next_run_time:", job.next_run_time)

# List jobs from scheduler
jobs = scheduler.get_jobs()
print("Jobs from scheduler:")
for j in jobs:
    print(f"  Job ID: {j.id}")
    print(f"  Has next_run_time: {hasattr(j, 'next_run_time')}")
    if hasattr(j, 'next_run_time'):
        print(f"  next_run_time: {j.next_run_time}")

scheduler.shutdown()
