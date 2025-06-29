#!/usr/bin/env python3
"""
Test runner for all OptimizationService tests.

This script runs all available OptimizationService test suites:
- Existing tests from test_performance_monitor_pytest.py
- Comprehensive tests from test_optimization_service_comprehensive_pytest.py  
- Edge cases tests from test_optimization_service_edge_cases_pytest.py

Usage:
    uv run python tests/run_optimization_service_tests.py
"""

import os
import sys
import subprocess
from pathlib import Path

def main():
    """Run all OptimizationService tests."""
    print("🔍 Running comprehensive OptimizationService test suite...\n")
    
    # Get the project root directory
    project_root = Path(__file__).parent.parent
    
    # Test files to run
    test_files = [
        "tests/test_performance_monitor_pytest.py::TestOptimizationService",
        "tests/test_optimization_service_comprehensive_pytest.py",
        "tests/test_optimization_service_edge_cases_pytest.py"
    ]
    
    all_passed = True
    results = {}
    
    for test_file in test_files:
        print(f"📋 Running {test_file}...")
        
        try:
            result = subprocess.run([
                "uv", "run", "pytest", test_file, "-v", "--tb=short"
            ], cwd=project_root, capture_output=True, text=True)
            
            results[test_file] = {
                "returncode": result.returncode,
                "stdout": result.stdout,
                "stderr": result.stderr
            }
            
            if result.returncode == 0:
                print(f"✅ {test_file} - All tests passed!")
            else:
                print(f"❌ {test_file} - Some tests failed!")
                all_passed = False
                
            # Show a summary of test results
            lines = result.stdout.split('\n')
            for line in lines:
                if 'passed' in line and 'failed' in line:
                    print(f"   Summary: {line.strip()}")
                elif line.strip().endswith('passed'):
                    print(f"   Summary: {line.strip()}")
                    
        except Exception as e:
            print(f"❌ Error running {test_file}: {e}")
            all_passed = False
        
        print()
    
    # Final summary
    print("=" * 80)
    print("🏁 FINAL TEST SUMMARY")
    print("=" * 80)
    
    total_files = len(test_files)
    passed_files = sum(1 for r in results.values() if r["returncode"] == 0)
    
    for test_file, result in results.items():
        status = "✅ PASSED" if result["returncode"] == 0 else "❌ FAILED"
        print(f"{status}: {test_file}")
    
    print(f"\nFiles: {passed_files}/{total_files} passed")
    
    if all_passed:
        print("\n🎉 All OptimizationService tests passed successfully!")
        print("\nTest Coverage Summary:")
        print("- ✅ Basic functionality and initialization")
        print("- ✅ Batch size optimization with various constraints")
        print("- ✅ Document chunking parameter optimization")
        print("- ✅ Performance optimization application")
        print("- ✅ Processing efficiency analysis")
        print("- ✅ Edge cases and boundary conditions")
        print("- ✅ Error handling and recovery")
        print("- ✅ Integration with PerformanceMonitor")
        print("- ✅ Memory constraint simulation")
        print("- ✅ Concurrent processing scenarios")
        print("- ✅ Large-scale document processing")
        print("- ✅ State consistency across operations")
        return 0
    else:
        print(f"\n💥 {total_files - passed_files} test file(s) had failures!")
        print("\nCheck the detailed output above for specific failures.")
        return 1

if __name__ == "__main__":
    sys.exit(main())
