#!/usr/bin/env python3
"""
Simple script to run all pytest-based document loader tests.
"""

import subprocess
import sys
import os


def run_all_document_loader_tests():
    """Run all document loader pytest tests."""
    print("🧪 Running All Document Loader Tests with Pytest")
    print("=" * 60)
    
    # Change to project root
    project_root = os.path.dirname(os.path.abspath(__file__))
    os.chdir(project_root)
    
    test_files = [
        "tests/test_document_loader_simple_pytest.py",
        "tests/test_document_loader_pytest.py", 
        "tests/test_document_loader_comprehensive_pytest.py",
        "tests/test_metadata_manager.py",

    ]
    
    try:
        result = subprocess.run([
            sys.executable, "-m", "pytest"
        ] + test_files + ["-v", "--tb=short"], 
        capture_output=False, text=True)
        
        return result.returncode == 0
    except Exception as e:
        print(f"❌ Failed to run tests: {e}")
        return False


if __name__ == "__main__":
    success = run_all_document_loader_tests()
    
    if success:
        print("\n🎉 All tests passed!")
    else:
        print("\n❌ Some tests failed!")
    
    sys.exit(0 if success else 1)
