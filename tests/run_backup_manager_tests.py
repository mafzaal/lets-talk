#!/usr/bin/env python3
"""
Test runner script for BackupManager tests.

This script provides an easy way to run the BackupManager tests
and can be executed directly.
"""

import sys
import os
import subprocess

def main():
    """Run the BackupManager tests."""
    # Get the directory of this script
    script_dir = os.path.dirname(os.path.abspath(__file__))
    project_root = os.path.dirname(script_dir)
    
    # Change to project root
    os.chdir(project_root)
    
    # Run the tests using uv
    cmd = [
        'uv', 'run', 'pytest', 
        'tests/test_backup_manager_pytest.py',
        '-v',
        '--tb=short'
    ]
    
    print(f"Running: {' '.join(cmd)}")
    print(f"Working directory: {os.getcwd()}")
    print("-" * 60)
    
    try:
        result = subprocess.run(cmd, check=True)
        print("\n" + "=" * 60)
        print("✅ All BackupManager tests passed!")
        return 0
    except subprocess.CalledProcessError as e:
        print("\n" + "=" * 60)
        print(f"❌ Tests failed with exit code: {e.returncode}")
        return e.returncode
    except Exception as e:
        print(f"\n❌ Error running tests: {e}")
        return 1

if __name__ == "__main__":
    sys.exit(main())
