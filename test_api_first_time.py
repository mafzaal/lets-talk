#!/usr/bin/env python3
"""
Simple test to verify the first-time detection works in a real API startup.
"""
import sys
import os
import time
import requests
import subprocess
import signal
from pathlib import Path

# Add the backend to the Python path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'backend'))

print("🧪 Testing First-Time Detection with Real API Startup")
print("=" * 60)

def cleanup_for_fresh_start():
    """Remove first-time marker to simulate fresh start."""
    marker_path = Path("output/.first_time_setup_completed")
    if marker_path.exists():
        marker_path.unlink()
        print("🗑️  Removed first-time marker for testing")
        return True
    return False

def restore_marker():
    """Restore the first-time marker."""
    marker_path = Path("output/.first_time_setup_completed")
    marker_path.parent.mkdir(parents=True, exist_ok=True)
    with open(marker_path, 'w') as f:
        f.write("Restored after test\n")
    print("✅ First-time marker restored")

def start_api_server():
    """Start the API server."""
    print("🚀 Starting API server...")
    
    # Start the server using the startup script
    env = os.environ.copy()
    env["PORT"] = "8010"  # Use different port to avoid conflicts
    
    proc = subprocess.Popen(
        ["./start_backend_dev.sh"],
        env=env,
        stdout=subprocess.PIPE,
        stderr=subprocess.STDOUT,
        text=True,
        preexec_fn=os.setsid  # Create new process group
    )
    
    return proc

def wait_for_server(port=8010, timeout=30):
    """Wait for the server to be ready."""
    print(f"⏳ Waiting for server on port {port}...")
    
    for i in range(timeout):
        try:
            response = requests.get(f"http://localhost:{port}/health", timeout=2)
            if response.status_code == 200:
                print(f"✅ Server is ready on port {port}")
                return True
        except requests.exceptions.RequestException:
            pass
        
        time.sleep(1)
        if i % 5 == 0:
            print(f"   Still waiting... ({i}/{timeout}s)")
    
    print(f"❌ Server failed to start within {timeout} seconds")
    return False

def check_first_time_status(port=8010):
    """Check the first-time status via health endpoint."""
    try:
        response = requests.get(f"http://localhost:{port}/health", timeout=5)
        
        if response.status_code == 200:
            health_data = response.json()
            first_time_setup = health_data.get("first_time_setup", {})
            
            print("📊 First-Time Status from Health Endpoint:")
            print(f"   Detection enabled: {first_time_setup.get('detection_enabled')}")
            print(f"   Is first time: {first_time_setup.get('is_first_time')}")
            print(f"   Setup completed: {first_time_setup.get('setup_completed')}")
            print(f"   Job scheduled: {first_time_setup.get('job_scheduled')}")
            print(f"   Run pipeline job: {first_time_setup.get('run_pipeline_job')}")
            
            return first_time_setup
        else:
            print(f"❌ Health check failed: {response.status_code}")
            return None
            
    except Exception as e:
        print(f"❌ Error checking health: {e}")
        return None

def check_scheduler_jobs(port=8010):
    """Check what jobs are scheduled."""
    try:
        response = requests.get(f"http://localhost:{port}/scheduler/jobs", timeout=5)
        
        if response.status_code == 200:
            jobs = response.json()
            print(f"📋 Scheduled Jobs ({len(jobs)}):")
            
            for job in jobs:
                job_id = job.get("id", "unknown")
                next_run = job.get("next_run_time", "not scheduled")
                print(f"   • {job_id}: {next_run}")
            
            return jobs
        else:
            print(f"❌ Jobs endpoint failed: {response.status_code}")
            return []
            
    except Exception as e:
        print(f"❌ Error checking jobs: {e}")
        return []

def main():
    """Main test function."""
    server_proc = None
    had_marker = cleanup_for_fresh_start()
    
    try:
        # Start the API server
        server_proc = start_api_server()
        
        # Wait for server to be ready
        if wait_for_server():
            # Check first-time status
            first_time_status = check_first_time_status()
            
            # Check scheduled jobs
            jobs = check_scheduler_jobs()
            
            # Look for first-time job
            first_time_job_found = any(
                "first_time" in job.get("id", "") 
                for job in jobs
            )
            
            print("\n📋 Test Results:")
            if first_time_status:
                print(f"✅ First-time detection: {first_time_status.get('is_first_time', False)}")
                print(f"✅ Job scheduled: {first_time_status.get('job_scheduled', False)}")
            
            if first_time_job_found:
                print("✅ First-time pipeline job found in scheduler")
            else:
                print("❌ First-time pipeline job not found")
            
            # Wait a bit to see if job executes
            if first_time_job_found:
                print("\n⏰ Waiting to see if first-time job executes...")
                time.sleep(35)  # Wait for the 30-second delay + buffer
                
                # Check status again
                final_status = check_first_time_status()
                if final_status and final_status.get('setup_completed'):
                    print("🎉 First-time setup completed!")
                else:
                    print("⏳ First-time setup may still be in progress")
        
    except KeyboardInterrupt:
        print("\n🛑 Test interrupted by user")
    
    finally:
        # Clean up
        if server_proc:
            print("\n🛑 Shutting down server...")
            try:
                # Kill the entire process group
                os.killpg(os.getpgid(server_proc.pid), signal.SIGTERM)
                server_proc.wait(timeout=10)
            except (ProcessLookupError, subprocess.TimeoutExpired):
                pass
        
        # Restore marker if it existed before
        if had_marker:
            restore_marker()
        
        print("🏁 Test complete")

if __name__ == "__main__":
    main()
