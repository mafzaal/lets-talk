#!/usr/bin/env python3
"""
Test runner for document loader tests using pytest.

This script runs all available document loader tests and provides a summary.
"""

import os
import sys
import subprocess


def run_simple_tests():
    """Run the simple document loader tests."""
    print("🔍 Running Simple Document Loader Tests...")
    print("=" * 60)
    
    try:
        result = subprocess.run([
            sys.executable, "-m", "pytest", "tests/test_document_loader_simple_pytest.py", "-v"
        ], capture_output=True, text=True, cwd=os.getcwd())
        
        print(result.stdout)
        if result.stderr:
            print("STDERR:", result.stderr)
        
        return result.returncode == 0
    except Exception as e:
        print(f"❌ Failed to run simple tests: {e}")
        return False


def run_comprehensive_tests():
    """Run the comprehensive document loader tests."""
    print("\n🔍 Running Comprehensive Document Loader Tests...")
    print("=" * 60)
    
    try:
        result = subprocess.run([
            sys.executable, "-m", "pytest", "tests/test_document_loader_comprehensive_pytest.py", "-v"
        ], capture_output=True, text=True, cwd=os.getcwd())
        
        print(result.stdout)
        if result.stderr:
            print("STDERR:", result.stderr)
        
        return result.returncode == 0
    except Exception as e:
        print(f"❌ Failed to run comprehensive tests: {e}")
        return False


def run_pytest_tests():
    """Run the pytest version of document loader tests."""
    print("\n🔍 Running Pytest Document Loader Tests...")
    print("=" * 60)
    
    try:
        result = subprocess.run([
            sys.executable, "-m", "pytest", "tests/test_document_loader_pytest.py", "-v"
        ], capture_output=True, text=True, cwd=os.getcwd())
        
        print(result.stdout)
        if result.stderr:
            print("STDERR:", result.stderr)
        
        return result.returncode == 0
    except Exception as e:
        print(f"❌ Failed to run pytest tests: {e}")
        return False


def run_all_pytest_document_tests():
    """Run all pytest document loader tests at once."""
    print("\n🔍 Running All Pytest Document Loader Tests...")
    print("=" * 60)
    
    try:
        result = subprocess.run([
            sys.executable, "-m", "pytest", 
            "tests/test_document_loader_simple_pytest.py",
            "tests/test_document_loader_pytest.py", 
            "tests/test_document_loader_comprehensive_pytest.py",
            "-v"
        ], capture_output=True, text=True, cwd=os.getcwd())
        
        print(result.stdout)
        if result.stderr:
            print("STDERR:", result.stderr)
        
        return result.returncode == 0
    except Exception as e:
        print(f"❌ Failed to run all pytest tests: {e}")
        return False


def main():
    """Run all document loader tests."""
    print("🧪 DOCUMENT LOADER TEST SUITE (PYTEST)")
    print("=" * 80)
    print("This test suite validates the DocumentLoader service functionality using pytest.")
    print()
    
    results = []
    
    # Run simple tests
    simple_success = run_simple_tests()
    results.append(("Simple Tests", simple_success))
    
    # Run comprehensive tests
    comprehensive_success = run_comprehensive_tests()
    results.append(("Comprehensive Tests", comprehensive_success))
    
    # Run pytest tests
    pytest_success = run_pytest_tests()
    results.append(("Pytest Tests", pytest_success))
    
    # Run all pytest tests together
    all_pytest_success = run_all_pytest_document_tests()
    results.append(("All Pytest Tests", all_pytest_success))
    
    # Summary
    print("\n" + "=" * 80)
    print("📊 TEST SUMMARY")
    print("=" * 80)
    
    total_tests = len(results)
    passed_tests = sum(1 for _, success in results if success)
    
    for test_name, success in results:
        status = "✅ PASSED" if success else "❌ FAILED"
        print(f"{test_name:30} {status}")
    
    print("-" * 80)
    print(f"Overall Results: {passed_tests}/{total_tests} test suites passed")
    
    if passed_tests == total_tests:
        print("\n🎉 All test suites passed successfully!")
        print("\nThe DocumentLoader service is working correctly and includes:")
        print("  ✓ Document loading from markdown files")
        print("  ✓ Frontmatter parsing with mixed data types")
        print("  ✓ URL generation and metadata extraction")
        print("  ✓ Statistics calculation")
        print("  ✓ Published/unpublished filtering")
        print("  ✓ Error handling for malformed content")
        return True
    else:
        print(f"\n❌ {total_tests - passed_tests} test suite(s) failed.")
        print("Please check the output above for details.")
        return False


if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)
