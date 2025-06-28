#!/usr/bin/env python3
"""
Test runner for HealthChecker tests.

This script runs comprehensive tests for the HealthChecker service,
including initialization, health checks, error handling, and edge cases.
"""

import os
import sys
import subprocess


def main():
    """Run the HealthChecker tests."""
    print("=" * 60)
    print("Running HealthChecker Tests")
    print("=" * 60)
    
    # Get the current directory
    current_dir = os.path.dirname(os.path.abspath(__file__))
    test_file = os.path.join(current_dir, "test_health_checker_pytest.py")
    
    # Check if test file exists
    if not os.path.exists(test_file):
        print(f"Error: Test file not found at {test_file}")
        return 1
    
    # Run the tests using uv
    try:
        print(f"Running tests from: {test_file}")
        print("-" * 40)
        
        # Run with verbose output
        result = subprocess.run([
            "uv", "run", "pytest", test_file, "-v", "--tb=short"
        ], cwd=current_dir, capture_output=False)
        
        print("-" * 40)
        if result.returncode == 0:
            print("✅ All HealthChecker tests passed!")
        else:
            print("❌ Some HealthChecker tests failed!")
        
        return result.returncode
        
    except FileNotFoundError:
        print("Error: 'uv' command not found. Please ensure uv is installed.")
        return 1
    except Exception as e:
        print(f"Error running tests: {e}")
        return 1


if __name__ == "__main__":
    exit_code = main()
    sys.exit(exit_code)
