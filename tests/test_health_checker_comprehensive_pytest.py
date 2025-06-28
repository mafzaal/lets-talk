#!/usr/bin/env python3
"""
Comprehensive test suite for the HealthChecker service.

This test script covers all major functionality including:
- Health checker initialization and configuration
- Comprehensive health checks across all system components
- Quick health checks for rapid system status assessment
- Vector store health validation and error handling
- Metadata file integrity checking and validation
- System resource monitoring with threshold-based alerts
- Configuration parameter validation
- Backup file management and cleanup recommendations
- Health analysis with actionable recommendations
- Error handling and exception management
- Edge cases and boundary conditions
"""

import os
import sys
import tempfile
import time
import json
import glob
import shutil
from pathlib import Path
from typing import Dict, Any
from unittest.mock import Mock, patch, MagicMock

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


class HealthCheckerTestSuite:
    """Comprehensive test suite for HealthChecker functionality."""
    
    def __init__(self):
        """Initialize the test suite."""
        self.test_results = {}
        self.temp_dir = None
        self.health_checker = None
        self.sample_metadata_path = None
    
    def setup_test_environment(self):
        """Set up the test environment with temporary files and directories."""
        try:
            # Create temporary directory
            self.temp_dir = tempfile.mkdtemp(prefix="health_checker_test_")
            print(f"📁 Created test directory: {self.temp_dir}")
            
            # Create sample metadata CSV
            self.sample_metadata_path = os.path.join(self.temp_dir, "test_metadata.csv")
            sample_data = pd.DataFrame({
                "source": ["doc1.md", "doc2.md", "doc3.md"],
                "content_checksum": ["abc123", "def456", "ghi789"],
                "indexed_timestamp": [1640995200, 1640995300, 1640995400]
            })
            sample_data.to_csv(self.sample_metadata_path, index=False)
            print(f"📄 Created sample metadata file: {self.sample_metadata_path}")
            
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
            print(f"❌ Failed to set up test environment: {e}")
            return False
    
    def cleanup_test_environment(self):
        """Clean up the test environment."""
        try:
            if self.temp_dir and os.path.exists(self.temp_dir):
                shutil.rmtree(self.temp_dir)
                print(f"🧹 Cleaned up test directory: {self.temp_dir}")
        except Exception as e:
            print(f"⚠️ Warning: Failed to clean up test directory: {e}")
    
    def test_health_checker_initialization(self) -> bool:
        """Test HealthChecker initialization."""
        try:
            print("\n🔍 Testing HealthChecker initialization...")
            
            # Test basic initialization
            assert self.health_checker.storage_path.endswith("vector_store")
            assert self.health_checker.collection_name == "test_collection"
            assert self.health_checker.qdrant_url == "http://localhost:6333"
            assert self.health_checker.embedding_model == "sentence-transformers/all-MiniLM-L6-v2"
            assert os.path.exists(self.health_checker.metadata_csv_path)
            assert self.health_checker.vector_store_manager is not None
            assert self.health_checker.performance_monitor is not None
            
            print("✅ HealthChecker initialization test passed")
            return True
            
        except Exception as e:
            print(f"❌ HealthChecker initialization test failed: {e}")
            return False
    
    def test_metadata_integrity_checking(self) -> bool:
        """Test metadata file integrity checking."""
        try:
            print("\n🔍 Testing metadata integrity checking...")
            
            # Test with valid metadata file
            result = self.health_checker._check_metadata_integrity()
            assert result["status"] == "healthy"
            assert result["exists"] is True
            assert result["readable"] is True
            assert result["record_count"] == 3
            assert result["error_details"] is None
            print("✅ Valid metadata file test passed")
            
            # Test with missing metadata file
            missing_metadata_path = os.path.join(self.temp_dir, "missing_metadata.csv")
            health_checker_missing = HealthChecker(
                storage_path=os.path.join(self.temp_dir, "vector_store_2"),
                collection_name="test_collection",
                qdrant_url="http://localhost:6333",
                embedding_model="sentence-transformers/all-MiniLM-L6-v2",
                metadata_csv_path=missing_metadata_path
            )
            
            result = health_checker_missing._check_metadata_integrity()
            assert result["status"] == "unhealthy"
            assert result["exists"] is False
            print("✅ Missing metadata file test passed")
            
            # Test with corrupted metadata file
            corrupted_metadata_path = os.path.join(self.temp_dir, "corrupted_metadata.csv")
            with open(corrupted_metadata_path, 'w') as f:
                f.write("invalid,csv,content\nwith,missing\nquotes")
            
            health_checker_corrupted = HealthChecker(
                storage_path=os.path.join(self.temp_dir, "vector_store_3"),
                collection_name="test_collection",
                qdrant_url="http://localhost:6333",
                embedding_model="sentence-transformers/all-MiniLM-L6-v2",
                metadata_csv_path=corrupted_metadata_path
            )
            
            result = health_checker_corrupted._check_metadata_integrity()
            assert result["status"] == "unhealthy"
            assert result["exists"] is True
            assert result["readable"] is False
            print("✅ Corrupted metadata file test passed")
            
            # Test with missing required columns
            bad_metadata_path = os.path.join(self.temp_dir, "bad_metadata.csv")
            bad_data = pd.DataFrame({
                "source": ["doc1.md", "doc2.md"],
                "wrong_column": ["abc123", "def456"]
            })
            bad_data.to_csv(bad_metadata_path, index=False)
            
            health_checker_bad = HealthChecker(
                storage_path=os.path.join(self.temp_dir, "vector_store_4"),
                collection_name="test_collection",
                qdrant_url="http://localhost:6333",
                embedding_model="sentence-transformers/all-MiniLM-L6-v2",
                metadata_csv_path=bad_metadata_path
            )
            
            result = health_checker_bad._check_metadata_integrity()
            assert result["status"] == "unhealthy"
            assert "Missing required columns" in result["error_details"]
            print("✅ Missing columns test passed")
            
            print("✅ All metadata integrity tests passed")
            return True
            
        except Exception as e:
            print(f"❌ Metadata integrity test failed: {e}")
            return False
    
    def test_vector_store_health_checking(self) -> bool:
        """Test vector store health checking."""
        try:
            print("\n🔍 Testing vector store health checking...")
            
            # Mock successful vector store validation
            with patch.object(self.health_checker.vector_store_manager, 'validate_health', return_value=True):
                result = self.health_checker._check_vector_store_health()
                assert result["status"] == "healthy"
                assert "accessible and responsive" in result["details"]
                assert result["url"] == "http://localhost:6333"
                assert result["collection"] == "test_collection"
                print("✅ Healthy vector store test passed")
            
            # Mock failed vector store validation
            with patch.object(self.health_checker.vector_store_manager, 'validate_health', return_value=False):
                result = self.health_checker._check_vector_store_health()
                assert result["status"] == "unhealthy"
                assert "not accessible" in result["details"]
                print("✅ Unhealthy vector store test passed")
            
            # Mock exception in vector store validation
            with patch.object(self.health_checker.vector_store_manager, 'validate_health', 
                             side_effect=Exception("Connection error")):
                result = self.health_checker._check_vector_store_health()
                assert result["status"] == "error"
                assert "Connection error" in result["details"]
                print("✅ Vector store exception test passed")
            
            print("✅ All vector store health tests passed")
            return True
            
        except Exception as e:
            print(f"❌ Vector store health test failed: {e}")
            return False
    
    def test_system_resources_checking(self) -> bool:
        """Test system resource checking."""
        try:
            print("\n🔍 Testing system resource checking...")
            
            # Mock healthy system resources
            with patch.object(self.health_checker.performance_monitor, 'get_system_stats') as mock_stats:
                mock_stats.return_value = {
                    "memory_percent": 50.0,
                    "disk_percent": 60.0,
                    "cpu_percent": 30.0
                }
                
                result = self.health_checker._check_system_resources()
                assert result["status"] == "healthy"
                assert result["memory_ok"] is True
                assert result["disk_ok"] is True
                assert result["cpu_ok"] is True
                assert len(result["warnings"]) == 0
                print("✅ Healthy system resources test passed")
            
            # Mock warning-level system resources
            with patch.object(self.health_checker.performance_monitor, 'get_system_stats') as mock_stats:
                mock_stats.return_value = {
                    "memory_percent": 85.0,
                    "disk_percent": 88.0,
                    "cpu_percent": 85.0
                }
                
                result = self.health_checker._check_system_resources()
                assert result["status"] == "warning"
                assert result["memory_ok"] is True
                assert result["disk_ok"] is True
                assert result["cpu_ok"] is True
                assert len(result["warnings"]) == 3
                print("✅ Warning-level system resources test passed")
            
            # Mock critical system resources
            with patch.object(self.health_checker.performance_monitor, 'get_system_stats') as mock_stats:
                mock_stats.return_value = {
                    "memory_percent": 95.0,
                    "disk_percent": 98.0,
                    "cpu_percent": 99.0
                }
                
                result = self.health_checker._check_system_resources()
                assert result["status"] == "unhealthy"
                assert result["memory_ok"] is False
                assert result["disk_ok"] is False
                assert result["cpu_ok"] is False
                assert len(result["warnings"]) == 3
                print("✅ Critical system resources test passed")
            
            print("✅ All system resource tests passed")
            return True
            
        except Exception as e:
            print(f"❌ System resource test failed: {e}")
            return False
    
    def test_configuration_validation(self) -> bool:
        """Test configuration validation."""
        try:
            print("\n🔍 Testing configuration validation...")
            
            # Test with valid configuration
            result = self.health_checker._check_configuration()
            assert result["status"] == "healthy"
            assert len(result["issues"]) == 0
            assert result["batch_size"] == BATCH_SIZE
            assert result["chunk_size"] == CHUNK_SIZE
            assert result["checksum_algorithm"] == CHECKSUM_ALGORITHM
            assert result["embedding_model"] == "sentence-transformers/all-MiniLM-L6-v2"
            print("✅ Valid configuration test passed")
            
            # Test with invalid embedding model
            health_checker_invalid = HealthChecker(
                storage_path=os.path.join(self.temp_dir, "vector_store_invalid"),
                collection_name="test_collection",
                qdrant_url="http://localhost:6333",
                embedding_model="",  # Empty embedding model
                metadata_csv_path=self.sample_metadata_path
            )
            
            result = health_checker_invalid._check_configuration()
            assert any("embedding model" in issue.lower() for issue in result["issues"])
            print("✅ Invalid configuration test passed")
            
            print("✅ All configuration validation tests passed")
            return True
            
        except Exception as e:
            print(f"❌ Configuration validation test failed: {e}")
            return False
    
    def test_backup_files_checking(self) -> bool:
        """Test backup files checking."""
        try:
            print("\n🔍 Testing backup files checking...")
            
            # Test with no backup files
            result = self.health_checker._check_backup_files()
            assert result["status"] in ["healthy", "warning"]
            assert result["backup_count"] == 0
            assert result["max_allowed"] == MAX_BACKUP_FILES
            print("✅ No backup files test passed")
            
            # Test with many backup files
            for i in range(MAX_BACKUP_FILES + 3):
                backup_file = f"{self.sample_metadata_path}.backup.{i}"
                with open(backup_file, 'w') as f:
                    f.write("dummy backup content")
            
            result = self.health_checker._check_backup_files()
            assert result["status"] == "warning"
            assert result["backup_count"] == MAX_BACKUP_FILES + 3
            assert any("too many backup files" in warning.lower() for warning in result["warnings"])
            print("✅ Too many backup files test passed")
            
            # Test with old backup files
            backup_file = f"{self.sample_metadata_path}.backup.old"
            with open(backup_file, 'w') as f:
                f.write("old backup content")
            
            # Set old modification time (35 days ago)
            old_time = time.time() - (35 * 24 * 3600)
            os.utime(backup_file, (old_time, old_time))
            
            result = self.health_checker._check_backup_files()
            assert result["old_backup_count"] >= 1
            print("✅ Old backup files test passed")
            
            print("✅ All backup files tests passed")
            return True
            
        except Exception as e:
            print(f"❌ Backup files test failed: {e}")
            return False
    
    def test_comprehensive_health_check(self) -> bool:
        """Test comprehensive health check functionality."""
        try:
            print("\n🔍 Testing comprehensive health check...")
            
            # Mock all dependencies for healthy system
            with patch.object(self.health_checker.vector_store_manager, 'validate_health', return_value=True), \
                 patch.object(self.health_checker.performance_monitor, 'get_system_stats') as mock_stats:
                
                mock_stats.return_value = {
                    "memory_percent": 50.0,
                    "disk_percent": 60.0,
                    "cpu_percent": 30.0
                }
                
                result = self.health_checker.comprehensive_health_check()
                
                assert result["overall_status"] == "healthy"
                assert "timestamp" in result
                assert "checks" in result
                assert "recommendations" in result
                assert "errors" in result
                
                # Check individual component statuses
                assert result["checks"]["vector_store"]["status"] == "healthy"
                assert result["checks"]["metadata"]["status"] == "healthy"
                assert result["checks"]["system_resources"]["status"] == "healthy"
                assert result["checks"]["configuration"]["status"] == "healthy"
                
                print("✅ Healthy comprehensive check test passed")
            
            # Test with unhealthy vector store
            with patch.object(self.health_checker.vector_store_manager, 'validate_health', return_value=False), \
                 patch.object(self.health_checker.performance_monitor, 'get_system_stats') as mock_stats:
                
                mock_stats.return_value = {
                    "memory_percent": 50.0,
                    "disk_percent": 60.0,
                    "cpu_percent": 30.0
                }
                
                result = self.health_checker.comprehensive_health_check()
                
                assert result["overall_status"] == "unhealthy"
                assert result["checks"]["vector_store"]["status"] == "unhealthy"
                assert "Check vector store configuration and connectivity" in result["recommendations"]
                print("✅ Unhealthy vector store comprehensive check test passed")
            
            # Test with exception handling
            with patch.object(self.health_checker.vector_store_manager, 'validate_health', 
                             side_effect=Exception("Test error")):
                
                result = self.health_checker.comprehensive_health_check()
                
                assert result["overall_status"] == "error"
                assert len(result["errors"]) > 0
                print("✅ Exception handling comprehensive check test passed")
            
            print("✅ All comprehensive health check tests passed")
            return True
            
        except Exception as e:
            print(f"❌ Comprehensive health check test failed: {e}")
            return False
    
    def test_quick_health_check(self) -> bool:
        """Test quick health check functionality."""
        try:
            print("\n🔍 Testing quick health check...")
            
            # Mock healthy system
            with patch.object(self.health_checker.vector_store_manager, 'validate_health', return_value=True):
                result = self.health_checker.quick_health_check()
                
                assert result["overall"] == "healthy"
                assert result["vector_store"] == "healthy"
                assert result["metadata"] == "healthy"
                assert "timestamp" in result
                print("✅ Healthy quick check test passed")
            
            # Mock unhealthy vector store
            with patch.object(self.health_checker.vector_store_manager, 'validate_health', return_value=False):
                result = self.health_checker.quick_health_check()
                
                assert result["overall"] == "issues_detected"
                assert result["vector_store"] == "unhealthy"
                print("✅ Unhealthy quick check test passed")
            
            # Test with missing metadata
            missing_metadata_path = os.path.join(self.temp_dir, "missing_metadata.csv")
            health_checker_missing = HealthChecker(
                storage_path=os.path.join(self.temp_dir, "vector_store_missing"),
                collection_name="test_collection",
                qdrant_url="http://localhost:6333",
                embedding_model="sentence-transformers/all-MiniLM-L6-v2",
                metadata_csv_path=missing_metadata_path
            )
            
            with patch.object(health_checker_missing.vector_store_manager, 'validate_health', return_value=True):
                result = health_checker_missing.quick_health_check()
                
                assert result["overall"] == "issues_detected"
                assert result["metadata"] == "missing"
                print("✅ Missing metadata quick check test passed")
            
            # Test exception handling
            with patch.object(self.health_checker.vector_store_manager, 'validate_health', 
                             side_effect=Exception("Test error")):
                result = self.health_checker.quick_health_check()
                
                assert result["overall"] == "error"
                assert "error" in result
                print("✅ Exception handling quick check test passed")
            
            print("✅ All quick health check tests passed")
            return True
            
        except Exception as e:
            print(f"❌ Quick health check test failed: {e}")
            return False
    
    def test_convenience_function(self) -> bool:
        """Test the convenience function for comprehensive health check."""
        try:
            print("\n🔍 Testing convenience function...")
            
            with patch('lets_talk.core.pipeline.services.health_checker.VectorStoreManager') as mock_vector, \
                 patch('lets_talk.core.pipeline.services.health_checker.PerformanceMonitor') as mock_perf:
                
                # Mock healthy responses
                mock_vector.return_value.validate_health.return_value = True
                mock_perf.return_value.get_system_stats.return_value = {
                    "memory_percent": 50.0,
                    "disk_percent": 60.0,
                    "cpu_percent": 30.0
                }
                
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
                
                assert result["overall_status"] == "healthy"
                assert "timestamp" in result
                assert "checks" in result
                assert "recommendations" in result
                assert "errors" in result
                
                print("✅ Convenience function test passed")
            
            return True
            
        except Exception as e:
            print(f"❌ Convenience function test failed: {e}")
            return False
    
    def run_all_tests(self) -> Dict[str, bool]:
        """Run all tests and return results."""
        if not IMPORT_SUCCESS:
            print("❌ Cannot run tests due to import failures")
            return {"import_success": False}
        
        if not self.setup_test_environment():
            print("❌ Cannot run tests due to setup failures")
            return {"setup_success": False}
        
        try:
            tests = [
                ("Initialization", self.test_health_checker_initialization),
                ("Metadata Integrity", self.test_metadata_integrity_checking),
                ("Vector Store Health", self.test_vector_store_health_checking),
                ("System Resources", self.test_system_resources_checking),
                ("Configuration Validation", self.test_configuration_validation),
                ("Backup Files", self.test_backup_files_checking),
                ("Comprehensive Health Check", self.test_comprehensive_health_check),
                ("Quick Health Check", self.test_quick_health_check),
                ("Convenience Function", self.test_convenience_function)
            ]
            
            results = {}
            passed_count = 0
            total_count = len(tests)
            
            for test_name, test_func in tests:
                try:
                    result = test_func()
                    results[test_name] = result
                    if result:
                        passed_count += 1
                except Exception as e:
                    print(f"❌ Test '{test_name}' failed with exception: {e}")
                    results[test_name] = False
            
            # Print summary
            print("\n" + "=" * 60)
            print("TEST SUMMARY")
            print("=" * 60)
            print(f"Passed: {passed_count}/{total_count}")
            print(f"Failed: {total_count - passed_count}/{total_count}")
            
            for test_name, result in results.items():
                status = "✅ PASS" if result else "❌ FAIL"
                print(f"{status}: {test_name}")
            
            if passed_count == total_count:
                print("\n🎉 All tests passed! HealthChecker is working correctly.")
            else:
                print(f"\n⚠️ {total_count - passed_count} test(s) failed. Please review the results above.")
            
            return results
            
        finally:
            self.cleanup_test_environment()


def main():
    """Main function to run the test suite."""
    print("🧪 HealthChecker Comprehensive Test Suite")
    print("=" * 60)
    
    test_suite = HealthCheckerTestSuite()
    results = test_suite.run_all_tests()
    
    # Return appropriate exit code
    if not IMPORT_SUCCESS:
        return 1
    
    if "setup_success" in results and not results["setup_success"]:
        return 1
    
    # Check if all tests passed
    if all(result for result in results.values()):
        return 0
    else:
        return 1


if __name__ == "__main__":
    exit_code = main()
    sys.exit(exit_code)
