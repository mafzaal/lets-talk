#!/usr/bin/env python3
"""
Simple test runner for HealthChecker functionality.

This script runs basic tests to verify the HealthChecker service works correctly.
It tests core functionality without requiring pytest or complex mocking.
"""

import os
import sys
import tempfile
import time
import json
import shutil
from typing import Dict, Any

import pandas as pd

# Add the backend directory to the path
backend_path = os.path.join(os.path.dirname(__file__), '..', 'backend')
if backend_path not in sys.path:
    sys.path.insert(0, backend_path)

# Import the modules to test
try:
    from lets_talk.core.pipeline.services.health_checker import (
        HealthChecker,
        comprehensive_system_health_check
    )
    from lets_talk.shared.config import (
        BATCH_SIZE,
        CHECKSUM_ALGORITHM,
        CHUNK_SIZE,
        MAX_BACKUP_FILES,
        METADATA_CSV_FILE
    )
    IMPORT_SUCCESS = True
    print("✅ Successfully imported HealthChecker module")
except ImportError as e:
    print(f"❌ Failed to import health_checker module: {e}")
    IMPORT_SUCCESS = False


class SimpleHealthCheckerTest:
    """Simple test class for HealthChecker functionality."""
    
    def __init__(self):
        """Initialize the test."""
        self.temp_dir = None
        self.health_checker = None
        self.sample_metadata_path = None
    
    def setup(self):
        """Set up test environment."""
        try:
            # Create temporary directory
            self.temp_dir = tempfile.mkdtemp(prefix="health_checker_test_")
            print(f"📁 Test directory: {self.temp_dir}")
            
            # Create sample metadata CSV
            self.sample_metadata_path = os.path.join(self.temp_dir, "test_metadata.csv")
            sample_data = pd.DataFrame({
                "source": ["doc1.md", "doc2.md", "doc3.md"],
                "content_checksum": ["abc123", "def456", "ghi789"],
                "indexed_timestamp": [1640995200, 1640995300, 1640995400]
            })
            sample_data.to_csv(self.sample_metadata_path, index=False)
            print(f"📄 Created metadata file: {self.sample_metadata_path}")
            
            # Create HealthChecker instance
            storage_path = os.path.join(self.temp_dir, "vector_store")
            collection_name = "test_collection"
            qdrant_url = "http://localhost:6333"
            embedding_model = "sentence-transformers/all-MiniLM-L6-v2"
            
            self.health_checker = HealthChecker(
                storage_path=storage_path,
                collection_name=collection_name,
                qdrant_url=qdrant_url,
                embedding_model=embedding_model,
                metadata_csv_path=self.sample_metadata_path
            )
            print("✅ Created HealthChecker instance")
            return True
            
        except Exception as e:
            print(f"❌ Setup failed: {e}")
            return False
    
    def cleanup(self):
        """Clean up test environment."""
        try:
            if self.temp_dir and os.path.exists(self.temp_dir):
                shutil.rmtree(self.temp_dir)
                print(f"🧹 Cleaned up: {self.temp_dir}")
        except Exception as e:
            print(f"⚠️ Cleanup warning: {e}")
    
    def test_initialization(self):
        """Test HealthChecker initialization."""
        try:
            print("\n🔍 Testing initialization...")
            
            # Check basic attributes
            assert hasattr(self.health_checker, 'storage_path')
            assert hasattr(self.health_checker, 'collection_name')
            assert hasattr(self.health_checker, 'qdrant_url')
            assert hasattr(self.health_checker, 'embedding_model')
            assert hasattr(self.health_checker, 'metadata_csv_path')
            assert hasattr(self.health_checker, 'vector_store_manager')
            assert hasattr(self.health_checker, 'performance_monitor')
            
            # Check values
            assert self.health_checker.collection_name == "test_collection"
            assert self.health_checker.qdrant_url == "http://localhost:6333"
            assert self.health_checker.embedding_model == "sentence-transformers/all-MiniLM-L6-v2"
            assert os.path.exists(self.health_checker.metadata_csv_path)
            
            print("✅ Initialization test passed")
            return True
            
        except Exception as e:
            print(f"❌ Initialization test failed: {e}")
            return False
    
    def test_metadata_integrity(self):
        """Test metadata integrity checking."""
        try:
            print("\n🔍 Testing metadata integrity...")
            
            # Test valid metadata file
            result = self.health_checker._check_metadata_integrity()
            
            assert isinstance(result, dict)
            assert "status" in result
            assert "exists" in result
            assert "readable" in result
            assert "record_count" in result
            assert "file_path" in result
            
            # Should be healthy with our test data
            assert result["status"] == "healthy"
            assert result["exists"] is True
            assert result["readable"] is True
            assert result["record_count"] == 3
            
            print("✅ Metadata integrity test passed")
            return True
            
        except Exception as e:
            print(f"❌ Metadata integrity test failed: {e}")
            return False
    
    def test_configuration_check(self):
        """Test configuration validation."""
        try:
            print("\n🔍 Testing configuration validation...")
            
            result = self.health_checker._check_configuration()
            
            assert isinstance(result, dict)
            assert "status" in result
            assert "issues" in result
            assert "batch_size" in result
            assert "chunk_size" in result
            assert "checksum_algorithm" in result
            assert "embedding_model" in result
            
            # Configuration should be valid
            assert result["status"] == "healthy"
            assert isinstance(result["issues"], list)
            assert result["embedding_model"] == "sentence-transformers/all-MiniLM-L6-v2"
            
            print("✅ Configuration validation test passed")
            return True
            
        except Exception as e:
            print(f"❌ Configuration validation test failed: {e}")
            return False
    
    def test_backup_files_check(self):
        """Test backup files checking."""
        try:
            print("\n🔍 Testing backup files checking...")
            
            result = self.health_checker._check_backup_files()
            
            assert isinstance(result, dict)
            assert "status" in result
            assert "backup_count" in result
            assert "max_allowed" in result
            assert "old_backup_count" in result
            assert "warnings" in result
            
            # Should be healthy or warning (no backups initially)
            assert result["status"] in ["healthy", "warning"]
            assert isinstance(result["warnings"], list)
            
            print("✅ Backup files check test passed")
            return True
            
        except Exception as e:
            print(f"❌ Backup files check test failed: {e}")
            return False
    
    def test_quick_health_check(self):
        """Test quick health check."""
        try:
            print("\n🔍 Testing quick health check...")
            
            result = self.health_checker.quick_health_check()
            
            assert isinstance(result, dict)
            assert "overall" in result
            assert "vector_store" in result
            assert "metadata" in result
            assert "timestamp" in result
            
            # Metadata should be healthy
            assert result["metadata"] == "healthy"
            
            print("✅ Quick health check test passed")
            return True
            
        except Exception as e:
            print(f"❌ Quick health check test failed: {e}")
            return False
    
    def test_comprehensive_health_check(self):
        """Test comprehensive health check."""
        try:
            print("\n🔍 Testing comprehensive health check...")
            
            result = self.health_checker.comprehensive_health_check()
            
            assert isinstance(result, dict)
            assert "overall_status" in result
            assert "timestamp" in result
            assert "checks" in result
            assert "recommendations" in result
            assert "errors" in result
            
            # Check structure of checks
            checks = result["checks"]
            assert "vector_store" in checks
            assert "metadata" in checks
            assert "system_resources" in checks
            assert "configuration" in checks
            assert "backups" in checks
            
            # Metadata should be healthy
            assert checks["metadata"]["status"] == "healthy"
            assert checks["configuration"]["status"] == "healthy"
            
            print("✅ Comprehensive health check test passed")
            return True
            
        except Exception as e:
            print(f"❌ Comprehensive health check test failed: {e}")
            return False
    
    def test_convenience_function(self):
        """Test the convenience function."""
        try:
            print("\n🔍 Testing convenience function...")
            
            storage_path = os.path.join(self.temp_dir, "vector_store_convenience")
            collection_name = "test_collection"
            qdrant_url = "http://localhost:6333"
            embedding_model = "sentence-transformers/all-MiniLM-L6-v2"
            
            result = comprehensive_system_health_check(
                storage_path=storage_path,
                collection_name=collection_name,
                qdrant_url=qdrant_url,
                embedding_model=embedding_model,
                metadata_csv_path=self.sample_metadata_path
            )
            
            assert isinstance(result, dict)
            assert "overall_status" in result
            assert "timestamp" in result
            assert "checks" in result
            assert "recommendations" in result
            assert "errors" in result
            
            print("✅ Convenience function test passed")
            return True
            
        except Exception as e:
            print(f"❌ Convenience function test failed: {e}")
            return False
    
    def run_all_tests(self):
        """Run all tests."""
        if not IMPORT_SUCCESS:
            print("❌ Cannot run tests due to import failures")
            return False
        
        if not self.setup():
            print("❌ Cannot run tests due to setup failures")
            return False
        
        try:
            tests = [
                ("Initialization", self.test_initialization),
                ("Metadata Integrity", self.test_metadata_integrity),
                ("Configuration Check", self.test_configuration_check),
                ("Backup Files Check", self.test_backup_files_check),
                ("Quick Health Check", self.test_quick_health_check),
                ("Comprehensive Health Check", self.test_comprehensive_health_check),
                ("Convenience Function", self.test_convenience_function)
            ]
            
            passed = 0
            total = len(tests)
            
            for test_name, test_func in tests:
                if test_func():
                    passed += 1
                else:
                    print(f"❌ {test_name} failed")
            
            print("\n" + "=" * 60)
            print("TEST SUMMARY")
            print("=" * 60)
            print(f"Passed: {passed}/{total}")
            print(f"Failed: {total - passed}/{total}")
            
            if passed == total:
                print("\n🎉 All tests passed! HealthChecker is working correctly.")
                return True
            else:
                print(f"\n⚠️ {total - passed} test(s) failed.")
                return False
                
        finally:
            self.cleanup()


def main():
    """Main function."""
    print("🧪 HealthChecker Simple Test Runner")
    print("=" * 60)
    
    test = SimpleHealthCheckerTest()
    success = test.run_all_tests()
    
    return 0 if success else 1


if __name__ == "__main__":
    exit_code = main()
    sys.exit(exit_code)
