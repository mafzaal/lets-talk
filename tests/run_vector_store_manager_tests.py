#!/usr/bin/env python3
"""
Test runner script for VectorStoreManager tests.

This script can be used to run the VectorStoreManager tests with proper
environment setup and dependency checking.
"""

import os
import sys
import subprocess

def main():
    """Run the VectorStoreManager tests."""
    print("VectorStoreManager Test Runner")
    print("=" * 50)
    
    # Add backend to path
    backend_path = os.path.join(os.path.dirname(__file__), '..', 'backend')
    if backend_path not in sys.path:
        sys.path.insert(0, backend_path)
    
    # Test files to run
    test_files = [
        "test_vector_store_manager_simple_pytest.py",
        "test_vector_store_manager_comprehensive_pytest.py"
    ]
    
    # Check if pytest is available
    try:
        import pytest
        print("✓ pytest is available")
    except ImportError:
        print("✗ pytest is not available. Please install pytest:")
        print("  uv add pytest")
        return 1
    
    # Check for dependencies
    print("\nChecking dependencies...")
    dependencies = [
        ("langchain", "langchain.schema.document"),
        ("lets_talk.core.pipeline.services.vector_store_manager", "lets_talk.core.pipeline.services.vector_store_manager"),
        ("lets_talk.shared.config", "lets_talk.shared.config")
    ]
    
    missing_deps = []
    for dep_name, import_path in dependencies:
        try:
            __import__(import_path)
            print(f"✓ {dep_name}")
        except ImportError as e:
            print(f"✗ {dep_name}: {e}")
            missing_deps.append(dep_name)
    
    if missing_deps:
        print(f"\nMissing dependencies: {', '.join(missing_deps)}")
        print("Tests will run with import error handling.")
    
    # Run tests
    print("\nRunning VectorStoreManager tests...")
    print("-" * 50)
    
    for test_file in test_files:
        test_path = os.path.join(os.path.dirname(__file__), test_file)
        if os.path.exists(test_path):
            print(f"\nRunning {test_file}...")
            try:
                # Use uv run if available, otherwise use python directly
                if subprocess.run(["which", "uv"], capture_output=True).returncode == 0:
                    result = subprocess.run(["uv", "run", "pytest", test_path, "-v"], 
                                          capture_output=False)
                else:
                    result = subprocess.run([sys.executable, "-m", "pytest", test_path, "-v"], 
                                          capture_output=False)
                
                if result.returncode != 0:
                    print(f"✗ {test_file} failed")
                else:
                    print(f"✓ {test_file} passed")
            except Exception as e:
                print(f"✗ Error running {test_file}: {e}")
        else:
            print(f"✗ {test_file} not found")
    
    print("\nTest run complete!")
    return 0

if __name__ == "__main__":
    sys.exit(main())
