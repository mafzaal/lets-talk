#!/usr/bin/env python3
"""
Performance Monitor Test Runner

This script runs the performance monitor tests using the project's testing standards.
"""

import os
import sys
import subprocess
from pathlib import Path

def run_performance_monitor_tests():
    """Run the performance monitor tests."""
    
    # Get the project root directory
    script_dir = Path(__file__).parent
    project_root = script_dir.parent
    
    # Change to project root directory
    os.chdir(project_root)
    
    # Test file path
    test_file = "tests/test_performance_monitor_pytest.py"
    
    print("=" * 60)
    print("Running Performance Monitor Tests")
    print("=" * 60)
    print(f"Project Root: {project_root}")
    print(f"Test File: {test_file}")
    print("=" * 60)
    
    # Check if test file exists
    if not os.path.exists(test_file):
        print(f"ERROR: Test file {test_file} not found!")
        return 1
    
    try:
        # Run tests using uv as specified in the user instructions
        cmd = ["uv", "run", "pytest", test_file, "-v"]
        print(f"Running command: {' '.join(cmd)}")
        print("-" * 60)
        
        result = subprocess.run(cmd, check=False)
        
        print("-" * 60)
        if result.returncode == 0:
            print("✅ All Performance Monitor tests passed!")
        else:
            print("❌ Some Performance Monitor tests failed!")
        
        return result.returncode
        
    except FileNotFoundError:
        print("ERROR: 'uv' command not found. Please install uv package manager.")
        print("Alternative: Run 'uv run python -m pytest tests/test_performance_monitor_pytest.py -v'")
        return 1
    except Exception as e:
        print(f"ERROR: Failed to run tests: {e}")
        return 1

def run_specific_test(test_name=None):
    """Run a specific test function."""
    
    project_root = Path(__file__).parent.parent
    os.chdir(project_root)
    
    test_file = "tests/test_performance_monitor_pytest.py"
    
    if test_name:
        cmd = ["uv", "run", "pytest", f"{test_file}::{test_name}", "-v"]
        print(f"Running specific test: {test_name}")
    else:
        cmd = ["uv", "run", "pytest", test_file, "-v"]
        print("Running all Performance Monitor tests")
    
    print(f"Command: {' '.join(cmd)}")
    print("-" * 60)
    
    try:
        result = subprocess.run(cmd, check=False)
        return result.returncode
    except Exception as e:
        print(f"ERROR: {e}")
        return 1

if __name__ == "__main__":
    # Parse command line arguments
    if len(sys.argv) > 1:
        if sys.argv[1] == "--help" or sys.argv[1] == "-h":
            print("Usage:")
            print("  python run_performance_monitor_tests.py              # Run all tests")
            print("  python run_performance_monitor_tests.py test_name    # Run specific test")
            print("")
            print("Examples:")
            print("  python run_performance_monitor_tests.py")
            print("  python run_performance_monitor_tests.py TestPerformanceMonitor::test_performance_monitor_creation")
            sys.exit(0)
        else:
            # Run specific test
            exit_code = run_specific_test(sys.argv[1])
    else:
        # Run all tests
        exit_code = run_performance_monitor_tests()
    
    sys.exit(exit_code)
