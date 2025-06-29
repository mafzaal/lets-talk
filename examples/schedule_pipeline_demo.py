#!/usr/bin/env python3
"""
Pipeline Scheduler API Demo

This script demonstrates how to use the FastAPI endpoints to manage
pipeline schedules programmatically.

Usage:
    python schedule_pipeline_demo.py

Make sure the FastAPI server is running first:
    uv run uvicorn lets_talk.webapp:app --host 0.0.0.0 --port 8000
"""

import requests
import json
from datetime import datetime, timedelta
from typing import Dict, Any, Optional

class PipelineSchedulerClient:
    """Client for interacting with the pipeline scheduler API."""
    
    def __init__(self, base_url: str = "http://localhost:8000"):
        self.base_url = base_url.rstrip('/')
    
    def _request(self, method: str, endpoint: str, **kwargs) -> Dict[Any, Any]:
        """Make an HTTP request to the API."""
        url = f"{self.base_url}{endpoint}"
        response = requests.request(method, url, **kwargs)
        response.raise_for_status()
        return response.json()
    
    def get_status(self) -> Dict[str, Any]:
        """Get scheduler status."""
        return self._request("GET", "/scheduler/status")
    
    def list_jobs(self) -> Dict[str, Any]:
        """List all scheduled jobs."""
        return self._request("GET", "/scheduler/jobs")
    
    def create_cron_job(self, job_id: str, hour: Optional[int] = None, minute: int = 0, 
                       day_of_week: Optional[str] = None, config: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        """Create a cron-based scheduled job."""
        data = {
            "job_id": job_id,
            "hour": hour,
            "minute": minute,
            "day_of_week": day_of_week,
            "config": config or {}
        }
        return self._request("POST", "/scheduler/jobs/cron", json=data)
    
    def create_interval_job(self, job_id: str, minutes: Optional[int] = None, 
                           hours: Optional[int] = None, days: Optional[int] = None, 
                           config: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        """Create an interval-based scheduled job."""
        data = {
            "job_id": job_id,
            "minutes": minutes,
            "hours": hours,
            "days": days,
            "config": config or {}
        }
        return self._request("POST", "/scheduler/jobs/interval", json=data)
    
    def create_onetime_job(self, job_id: str, run_date: datetime, 
                          config: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        """Create a one-time scheduled job."""
        data = {
            "job_id": job_id,
            "run_date": run_date.isoformat(),
            "config": config or {}
        }
        return self._request("POST", "/scheduler/jobs/onetime", json=data)
    
    def remove_job(self, job_id: str) -> Dict[str, Any]:
        """Remove a scheduled job."""
        return self._request("DELETE", f"/scheduler/jobs/{job_id}")
    
    def run_job_now(self, job_id: str) -> Dict[str, Any]:
        """Trigger immediate execution of a job."""
        return self._request("POST", f"/scheduler/jobs/{job_id}/run")
    
    def get_presets(self) -> Dict[str, Any]:
        """Get available preset schedules."""
        return self._request("GET", "/scheduler/presets")
    
    def create_preset_job(self, preset_name: str, job_id: str, 
                         config: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        """Create a job using a preset schedule."""
        params = {"job_id": job_id}
        data = config or {}
        return self._request("POST", f"/scheduler/presets/{preset_name}", 
                           params=params, json=data)
    
    def export_config(self) -> Dict[str, Any]:
        """Export current scheduler configuration."""
        return self._request("GET", "/scheduler/config/export")
    
    def run_pipeline(self, config: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        """Run the pipeline immediately."""
        return self._request("POST", "/pipeline/run", json=config or {})
    
    def get_health(self) -> Dict[str, Any]:
        """Get health status."""
        return self._request("GET", "/health")


def demo_basic_scheduling():
    """Demonstrate basic scheduling operations."""
    client = PipelineSchedulerClient()
    
    print("🚀 Pipeline Scheduler API Demo")
    print("=" * 50)
    
    # Check health status
    print("\n1. Checking health status...")
    try:
        health = client.get_health()
        print(f"   ✅ Server is healthy: {health['status']}")
        print(f"   📊 Scheduler status: {health['scheduler_status']}")
    except Exception as e:
        print(f"   ❌ Health check failed: {e}")
        return
    
    # Get current status
    print("\n2. Getting scheduler status...")
    try:
        status = client.get_status()
        print(f"   📈 Jobs executed: {status['jobs_executed']}")
        print(f"   ❌ Jobs failed: {status['jobs_failed']}")
        print(f"   🔄 Active jobs: {status['active_jobs']}")
        print(f"   🏃 Scheduler running: {status['scheduler_running']}")
    except Exception as e:
        print(f"   ❌ Status check failed: {e}")
    
    # List current jobs
    print("\n3. Listing current jobs...")
    try:
        jobs = client.list_jobs()
        if jobs:
            for job in jobs:
                print(f"   📋 {job['id']}: {job['name']}")
                print(f"      Next run: {job['next_run_time']}")
        else:
            print("   📭 No jobs currently scheduled")
    except Exception as e:
        print(f"   ❌ Failed to list jobs: {e}")


def demo_job_creation():
    """Demonstrate creating different types of scheduled jobs."""
    client = PipelineSchedulerClient()
    
    print("\n4. Creating scheduled jobs...")
    
    # Daily incremental update
    print("\n   📅 Creating daily incremental update job...")
    try:
        config = {
            "incremental_mode": "auto",
            "force_recreate": False,
            "ci_mode": True,
            "dry_run": False
        }
        result = client.create_cron_job(
            job_id="demo_daily_incremental",
            hour=2,  # 2 AM
            minute=0,
            config=config
        )
        print(f"   ✅ {result['message']}")
    except Exception as e:
        print(f"   ❌ Failed to create daily job: {e}")
    
    # Hourly check (dry run)
    print("\n   ⏰ Creating hourly dry-run check...")
    try:
        config = {
            "incremental_mode": "auto",
            "dry_run": True,  # Just check for changes
            "ci_mode": True
        }
        result = client.create_interval_job(
            job_id="demo_hourly_check",
            hours=1,
            config=config
        )
        print(f"   ✅ {result['message']}")
    except Exception as e:
        print(f"   ❌ Failed to create hourly job: {e}")
    
    # One-time job in 5 minutes
    print("\n   🎯 Creating one-time job for 5 minutes from now...")
    try:
        run_time = datetime.now() + timedelta(minutes=5)
        config = {
            "incremental_mode": "auto",
            "force_recreate": False,
            "ci_mode": True
        }
        result = client.create_onetime_job(
            job_id="demo_onetime_test",
            run_date=run_time,
            config=config
        )
        print(f"   ✅ {result['message']}")
        print(f"      Scheduled for: {run_time.strftime('%Y-%m-%d %H:%M:%S')}")
    except Exception as e:
        print(f"   ❌ Failed to create one-time job: {e}")


def demo_preset_jobs():
    """Demonstrate using preset job configurations."""
    client = PipelineSchedulerClient()
    
    print("\n5. Working with preset schedules...")
    
    # Get available presets
    print("\n   📋 Available presets:")
    try:
        presets = client.get_presets()
        for name, details in presets.items():
            print(f"      • {name}: {details['description']}")
    except Exception as e:
        print(f"   ❌ Failed to get presets: {e}")
        return
    
    # Create a job using a preset
    print("\n   🎨 Creating job with 'weekly_sunday_1am' preset...")
    try:
        config = {
            "incremental_mode": "full",
            "force_recreate": True,
            "ci_mode": True
        }
        result = client.create_preset_job(
            preset_name="weekly_sunday_1am",
            job_id="demo_weekly_rebuild",
            config=config
        )
        print(f"   ✅ {result['message']}")
    except Exception as e:
        print(f"   ❌ Failed to create preset job: {e}")


def demo_job_management():
    """Demonstrate job management operations."""
    client = PipelineSchedulerClient()
    
    print("\n6. Job management operations...")
    
    # List jobs again to see what we created
    print("\n   📋 Current jobs after creation:")
    try:
        jobs = client.list_jobs()
        for job in jobs:
            if job['id'].startswith('demo_'):
                print(f"      • {job['id']}: {job['trigger']}")
                print(f"        Next run: {job['next_run_time']}")
    except Exception as e:
        print(f"   ❌ Failed to list jobs: {e}")
    
    # Trigger a job immediately
    print("\n   🚀 Triggering immediate execution of hourly check...")
    try:
        result = client.run_job_now("demo_hourly_check")
        print(f"   ✅ {result['message']}")
    except Exception as e:
        print(f"   ❌ Failed to trigger job: {e}")


def demo_config_management():
    """Demonstrate configuration export/import."""
    client = PipelineSchedulerClient()
    
    print("\n7. Configuration management...")
    
    # Export current configuration
    print("\n   📤 Exporting current configuration...")
    try:
        config = client.export_config()
        print(f"   ✅ Exported configuration with {len(config.get('jobs', []))} jobs")
        print(f"      Exported at: {config.get('exported_at', 'unknown')}")
        
        # Save to file for demonstration
        with open("/tmp/scheduler_config_demo.json", "w") as f:
            json.dump(config, f, indent=2)
        print("   💾 Configuration saved to /tmp/scheduler_config_demo.json")
        
    except Exception as e:
        print(f"   ❌ Failed to export configuration: {e}")


def cleanup_demo_jobs():
    """Clean up demonstration jobs."""
    client = PipelineSchedulerClient()
    
    print("\n8. Cleaning up demonstration jobs...")
    
    demo_jobs = [
        "demo_daily_incremental",
        "demo_hourly_check", 
        "demo_onetime_test",
        "demo_weekly_rebuild"
    ]
    
    for job_id in demo_jobs:
        try:
            result = client.remove_job(job_id)
            print(f"   🗑️  Removed {job_id}")
        except Exception as e:
            print(f"   ⚠️  Failed to remove {job_id}: {e}")


def main():
    """Run the complete demonstration."""
    print("Pipeline Scheduler API Demonstration")
    print("Make sure the FastAPI server is running on http://localhost:8000")
    print()
    
    try:
        # Run all demonstration functions
        demo_basic_scheduling()
        demo_job_creation()
        demo_preset_jobs()
        demo_job_management()
        demo_config_management()
        
        # Ask user if they want to clean up
        print("\n" + "=" * 50)
        response = input("Clean up demonstration jobs? (y/N): ").strip().lower()
        if response in ['y', 'yes']:
            cleanup_demo_jobs()
        else:
            print("Keeping demonstration jobs for further testing.")
        
        print("\n✅ Demo completed successfully!")
        print("💡 You can now use these endpoints in your applications.")
        
    except KeyboardInterrupt:
        print("\n\n⚠️  Demo interrupted by user")
    except Exception as e:
        print(f"\n❌ Demo failed: {e}")


if __name__ == "__main__":
    main()
