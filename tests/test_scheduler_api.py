#!/usr/bin/env python3
"""
Basic validation test for Pipeline Scheduler API

This script performs basic tests to ensure the FastAPI endpoints are working correctly.
Run this after starting the FastAPI server to validate the functionality.

Usage:
    python test_scheduler_api.py
"""

import requests
import json
import time
from datetime import datetime, timedelta

def test_health_endpoints():
    """Test basic health check endpoints."""
    print("🔍 Testing health endpoints...")
    
    # Test basic health check
    try:
        response = requests.get("http://localhost:8000/health", timeout=5)
        if response.status_code == 200:
            data = response.json()
            print(f"   ✅ Basic health check: {data['status']}")
            print(f"   📊 Scheduler status: {data['scheduler_status']}")
        else:
            print(f"   ❌ Health check failed: {response.status_code}")
            return False
    except Exception as e:
        print(f"   ❌ Health check failed: {e}")
        return False
    
    # Test scheduler health
    try:
        response = requests.get("http://localhost:8000/scheduler/health", timeout=5)
        if response.status_code == 200:
            data = response.json()
            print(f"   ✅ Scheduler health: {'healthy' if data['healthy'] else 'unhealthy'}")
            print(f"   🏃 Scheduler running: {data['scheduler_running']}")
            print(f"   📋 Total jobs: {data['total_jobs']}")
        else:
            print(f"   ❌ Scheduler health check failed: {response.status_code}")
            return False
    except Exception as e:
        print(f"   ❌ Scheduler health check failed: {e}")
        return False
    
    return True

def test_scheduler_status():
    """Test scheduler status endpoint."""
    print("\n📊 Testing scheduler status...")
    
    try:
        response = requests.get("http://localhost:8000/scheduler/status", timeout=5)
        if response.status_code == 200:
            data = response.json()
            print(f"   ✅ Status retrieved successfully")
            print(f"   📈 Jobs executed: {data['jobs_executed']}")
            print(f"   ❌ Jobs failed: {data['jobs_failed']}")
            print(f"   ⏰ Jobs missed: {data['jobs_missed']}")
            print(f"   🔄 Active jobs: {data['active_jobs']}")
            return True
        else:
            print(f"   ❌ Status check failed: {response.status_code}")
            return False
    except Exception as e:
        print(f"   ❌ Status check failed: {e}")
        return False

def test_list_jobs():
    """Test job listing endpoint."""
    print("\n📋 Testing job listing...")
    
    try:
        response = requests.get("http://localhost:8000/scheduler/jobs", timeout=5)
        if response.status_code == 200:
            jobs = response.json()
            print(f"   ✅ Found {len(jobs)} existing jobs")
            for job in jobs:
                print(f"      • {job['id']}: {job['name']}")
            return True
        else:
            print(f"   ❌ Job listing failed: {response.status_code}")
            return False
    except Exception as e:
        print(f"   ❌ Job listing failed: {e}")
        return False

def test_presets():
    """Test preset schedules endpoint."""
    print("\n🎨 Testing preset schedules...")
    
    try:
        response = requests.get("http://localhost:8000/scheduler/presets", timeout=5)
        if response.status_code == 200:
            presets = response.json()
            print(f"   ✅ Found {len(presets)} preset schedules")
            for name, details in presets.items():
                print(f"      • {name}: {details['description']}")
            return True
        else:
            print(f"   ❌ Preset listing failed: {response.status_code}")
            return False
    except Exception as e:
        print(f"   ❌ Preset listing failed: {e}")
        return False

def test_job_creation():
    """Test job creation endpoints."""
    print("\n➕ Testing job creation...")
    
    # Test creating an interval job
    job_data = {
        "job_id": "test_validation_job",
        "minutes": 60,  # Every hour
        "config": {
            "incremental_mode": "auto",
            "dry_run": True,
            "ci_mode": True
        }
    }
    
    try:
        response = requests.post(
            "http://localhost:8000/scheduler/jobs/interval",
            json=job_data,
            timeout=5
        )
        if response.status_code == 200:
            result = response.json()
            print(f"   ✅ Test job created: {result['job_id']}")
            return result['job_id']
        else:
            print(f"   ❌ Job creation failed: {response.status_code}")
            if response.text:
                print(f"      Error: {response.text}")
            return None
    except Exception as e:
        print(f"   ❌ Job creation failed: {e}")
        return None

def test_job_removal(job_id):
    """Test job removal endpoint."""
    if not job_id:
        print("\n🗑️  Skipping job removal test (no job to remove)")
        return True
    
    print(f"\n🗑️  Testing job removal for: {job_id}")
    
    try:
        response = requests.delete(f"http://localhost:8000/scheduler/jobs/{job_id}", timeout=5)
        if response.status_code == 200:
            result = response.json()
            print(f"   ✅ Test job removed: {result['message']}")
            return True
        else:
            print(f"   ❌ Job removal failed: {response.status_code}")
            return False
    except Exception as e:
        print(f"   ❌ Job removal failed: {e}")
        return False

def test_pipeline_run():
    """Test immediate pipeline run endpoint."""
    print("\n🚀 Testing immediate pipeline run...")
    
    config = {
        "incremental_mode": "auto",
        "dry_run": True,  # Use dry run to avoid actually processing data
        "ci_mode": True
    }
    
    try:
        response = requests.post(
            "http://localhost:8000/pipeline/run",
            json=config,
            timeout=10
        )
        if response.status_code == 200:
            result = response.json()
            print(f"   ✅ Pipeline run started: {result['job_id']}")
            return True
        else:
            print(f"   ❌ Pipeline run failed: {response.status_code}")
            if response.text:
                print(f"      Error: {response.text}")
            return False
    except Exception as e:
        print(f"   ❌ Pipeline run failed: {e}")
        return False

def test_config_export():
    """Test configuration export endpoint."""
    print("\n📤 Testing configuration export...")
    
    try:
        response = requests.get("http://localhost:8000/scheduler/config/export", timeout=5)
        if response.status_code == 200:
            config = response.json()
            print(f"   ✅ Configuration exported successfully")
            print(f"   📋 Contains {len(config.get('jobs', []))} jobs")
            print(f"   📅 Exported at: {config.get('exported_at', 'unknown')}")
            return True
        else:
            print(f"   ❌ Configuration export failed: {response.status_code}")
            return False
    except Exception as e:
        print(f"   ❌ Configuration export failed: {e}")
        return False

def main():
    """Run all validation tests."""
    print("🧪 Pipeline Scheduler API Validation Tests")
    print("=" * 50)
    print("Make sure the FastAPI server is running on http://localhost:8000")
    print()
    
    # Wait a moment for user to see the message
    time.sleep(1)
    
    test_results = []
    
    # Run all tests
    test_results.append(("Health Endpoints", test_health_endpoints()))
    test_results.append(("Scheduler Status", test_scheduler_status()))
    test_results.append(("List Jobs", test_list_jobs()))
    test_results.append(("Presets", test_presets()))
    
    # Job creation and removal
    job_id = test_job_creation()
    test_results.append(("Job Creation", job_id is not None))
    test_results.append(("Job Removal", test_job_removal(job_id)))
    
    test_results.append(("Pipeline Run", test_pipeline_run()))
    test_results.append(("Config Export", test_config_export()))
    
    # Print summary
    print("\n" + "=" * 50)
    print("📊 Test Results Summary")
    print("=" * 50)
    
    passed = 0
    total = len(test_results)
    
    for test_name, result in test_results:
        status = "✅ PASS" if result else "❌ FAIL"
        print(f"   {test_name:20s} {status}")
        if result:
            passed += 1
    
    print("\n" + "=" * 50)
    print(f"📈 Tests Passed: {passed}/{total}")
    
    if passed == total:
        print("🎉 All tests passed! The API is working correctly.")
        return 0
    else:
        print("⚠️  Some tests failed. Check the output above for details.")
        return 1

if __name__ == "__main__":
    exit(main())
