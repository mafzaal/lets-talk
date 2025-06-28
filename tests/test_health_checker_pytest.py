#!/usr/bin/env python3
"""
Pytest test suite for the HealthChecker service.

This test script covers:
- HealthChecker initialization
- Comprehensive health checks
- Quick health checks
- Vector store health validation
- Metadata integrity checks
- System resource monitoring
- Configuration validation
- Backup file management
- Health analysis and recommendations
- Error handling and edge cases
"""

import os
import sys
import tempfile
import time
import json
import glob
import pytest
from pathlib import Path
from typing import Dict, Any
from unittest.mock import Mock, patch, MagicMock, mock_open

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
except ImportError as e:
    print(f"Failed to import health_checker module: {e}")
    IMPORT_SUCCESS = False


class TestHealthChecker:
    """Test cases for the HealthChecker class."""
    
    @pytest.fixture
    def temp_dir(self):
        """Create a temporary directory for test files."""
        with tempfile.TemporaryDirectory() as temp_dir:
            yield temp_dir
    
    @pytest.fixture
    def sample_metadata_csv(self, temp_dir):
        """Create a sample metadata CSV file for testing."""
        metadata_path = os.path.join(temp_dir, "test_metadata.csv")
        df = pd.DataFrame({
            "source": ["doc1.md", "doc2.md", "doc3.md"],
            "content_checksum": ["abc123", "def456", "ghi789"],
            "indexed_timestamp": [1640995200, 1640995300, 1640995400]
        })
        df.to_csv(metadata_path, index=False)
        return metadata_path
    
    @pytest.fixture
    def health_checker(self, temp_dir, sample_metadata_csv):
        """Create a HealthChecker instance for testing."""
        storage_path = os.path.join(temp_dir, "vector_store")
        collection_name = "test_collection"
        qdrant_url = "http://localhost:6333"
        embedding_model = "sentence-transformers/all-MiniLM-L6-v2"
        
        return HealthChecker(
            storage_path=storage_path,
            collection_name=collection_name,
            qdrant_url=qdrant_url,
            embedding_model=embedding_model,
            metadata_csv_path=sample_metadata_csv
        )
    
    @pytest.fixture
    def mock_vector_store_manager(self):
        """Mock VectorStoreManager for testing."""
        with patch('lets_talk.core.pipeline.services.health_checker.VectorStoreManager') as mock:
            mock_instance = Mock()
            mock.return_value = mock_instance
            yield mock_instance
    
    @pytest.fixture
    def mock_performance_monitor(self):
        """Mock PerformanceMonitor for testing."""
        with patch('lets_talk.core.pipeline.services.health_checker.PerformanceMonitor') as mock:
            mock_instance = Mock()
            mock.return_value = mock_instance
            yield mock_instance
    
    @pytest.mark.skipif(not IMPORT_SUCCESS, reason="Could not import health_checker module")
    def test_health_checker_initialization(self, health_checker):
        """Test HealthChecker initialization."""
        assert health_checker.storage_path.endswith("vector_store")
        assert health_checker.collection_name == "test_collection"
        assert health_checker.qdrant_url == "http://localhost:6333"
        assert health_checker.embedding_model == "sentence-transformers/all-MiniLM-L6-v2"
        assert os.path.exists(health_checker.metadata_csv_path)
        assert health_checker.vector_store_manager is not None
        assert health_checker.performance_monitor is not None
    
    @pytest.mark.skipif(not IMPORT_SUCCESS, reason="Could not import health_checker module")
    def test_comprehensive_health_check_healthy_system(self, health_checker, mock_vector_store_manager, mock_performance_monitor):
        """Test comprehensive health check with a healthy system."""
        # Mock healthy responses
        mock_vector_store_manager.validate_health.return_value = True
        mock_performance_monitor.get_system_stats.return_value = {
            "memory_percent": 50.0,
            "disk_percent": 60.0,
            "cpu_percent": 30.0
        }
        
        result = health_checker.comprehensive_health_check()
        
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
        assert result["checks"]["backups"]["status"] in ["healthy", "warning"]
        
        # Should have no recommendations for a healthy system
        assert len(result["recommendations"]) == 0 or all(
            "backup" in rec.lower() for rec in result["recommendations"]
        )
    
    @pytest.mark.skipif(not IMPORT_SUCCESS, reason="Could not import health_checker module")
    def test_comprehensive_health_check_unhealthy_vector_store(self, health_checker, mock_vector_store_manager, mock_performance_monitor):
        """Test comprehensive health check with unhealthy vector store."""
        # Mock unhealthy vector store
        mock_vector_store_manager.validate_health.return_value = False
        mock_performance_monitor.get_system_stats.return_value = {
            "memory_percent": 50.0,
            "disk_percent": 60.0,
            "cpu_percent": 30.0
        }
        
        result = health_checker.comprehensive_health_check()
        
        assert result["overall_status"] == "unhealthy"
        assert result["checks"]["vector_store"]["status"] == "unhealthy"
        assert "Check vector store configuration and connectivity" in result["recommendations"]
    
    @pytest.mark.skipif(not IMPORT_SUCCESS, reason="Could not import health_checker module")
    def test_comprehensive_health_check_missing_metadata(self, temp_dir, mock_vector_store_manager, mock_performance_monitor):
        """Test comprehensive health check with missing metadata file."""
        # Create health checker with non-existent metadata file
        missing_metadata_path = os.path.join(temp_dir, "missing_metadata.csv")
        health_checker = HealthChecker(
            storage_path=os.path.join(temp_dir, "vector_store"),
            collection_name="test_collection",
            qdrant_url="http://localhost:6333",
            embedding_model="sentence-transformers/all-MiniLM-L6-v2",
            metadata_csv_path=missing_metadata_path
        )
        
        # Mock healthy vector store
        mock_vector_store_manager.validate_health.return_value = True
        mock_performance_monitor.get_system_stats.return_value = {
            "memory_percent": 50.0,
            "disk_percent": 60.0,
            "cpu_percent": 30.0
        }
        
        result = health_checker.comprehensive_health_check()
        
        assert result["overall_status"] == "unhealthy"
        assert result["checks"]["metadata"]["status"] == "unhealthy"
        assert not result["checks"]["metadata"]["exists"]
        assert "Recreate or repair metadata file" in result["recommendations"]
    
    @pytest.mark.skipif(not IMPORT_SUCCESS, reason="Could not import health_checker module")
    def test_comprehensive_health_check_high_resource_usage(self, health_checker, mock_vector_store_manager, mock_performance_monitor):
        """Test comprehensive health check with high resource usage."""
        # Mock healthy vector store but high resource usage
        mock_vector_store_manager.validate_health.return_value = True
        mock_performance_monitor.get_system_stats.return_value = {
            "memory_percent": 95.0,
            "disk_percent": 98.0,
            "cpu_percent": 99.0
        }
        
        result = health_checker.comprehensive_health_check()
        
        assert result["overall_status"] == "unhealthy"
        assert result["checks"]["system_resources"]["status"] == "unhealthy"
        assert not result["checks"]["system_resources"]["memory_ok"]
        assert not result["checks"]["system_resources"]["disk_ok"]
        assert not result["checks"]["system_resources"]["cpu_ok"]
        
        recommendations = result["recommendations"]
        assert any("memory" in rec.lower() for rec in recommendations)
        assert any("disk" in rec.lower() for rec in recommendations)
        assert any("cpu" in rec.lower() for rec in recommendations)
    
    @pytest.mark.skipif(not IMPORT_SUCCESS, reason="Could not import health_checker module")
    def test_check_vector_store_health_success(self, health_checker, mock_vector_store_manager):
        """Test vector store health check with successful validation."""
        mock_vector_store_manager.validate_health.return_value = True
        
        result = health_checker._check_vector_store_health()
        
        assert result["status"] == "healthy"
        assert "accessible and responsive" in result["details"]
        assert result["url"] == "http://localhost:6333"
        assert result["collection"] == "test_collection"
    
    @pytest.mark.skipif(not IMPORT_SUCCESS, reason="Could not import health_checker module")
    def test_check_vector_store_health_failure(self, health_checker, mock_vector_store_manager):
        """Test vector store health check with validation failure."""
        mock_vector_store_manager.validate_health.return_value = False
        
        result = health_checker._check_vector_store_health()
        
        assert result["status"] == "unhealthy"
        assert "not accessible" in result["details"]
    
    @pytest.mark.skipif(not IMPORT_SUCCESS, reason="Could not import health_checker module")
    def test_check_vector_store_health_exception(self, health_checker, mock_vector_store_manager):
        """Test vector store health check with exception."""
        mock_vector_store_manager.validate_health.side_effect = Exception("Connection error")
        
        result = health_checker._check_vector_store_health()
        
        assert result["status"] == "error"
        assert "Connection error" in result["details"]
    
    @pytest.mark.skipif(not IMPORT_SUCCESS, reason="Could not import health_checker module")
    def test_check_metadata_integrity_healthy(self, health_checker):
        """Test metadata integrity check with healthy file."""
        result = health_checker._check_metadata_integrity()
        
        assert result["status"] == "healthy"
        assert result["exists"] is True
        assert result["readable"] is True
        assert result["record_count"] == 3
        assert result["error_details"] is None
    
    @pytest.mark.skipif(not IMPORT_SUCCESS, reason="Could not import health_checker module")
    def test_check_metadata_integrity_missing_columns(self, temp_dir):
        """Test metadata integrity check with missing required columns."""
        # Create CSV with missing columns
        metadata_path = os.path.join(temp_dir, "bad_metadata.csv")
        df = pd.DataFrame({
            "source": ["doc1.md", "doc2.md"],
            "wrong_column": ["abc123", "def456"]
        })
        df.to_csv(metadata_path, index=False)
        
        health_checker = HealthChecker(
            storage_path=os.path.join(temp_dir, "vector_store"),
            collection_name="test_collection",
            qdrant_url="http://localhost:6333",
            embedding_model="sentence-transformers/all-MiniLM-L6-v2",
            metadata_csv_path=metadata_path
        )
        
        result = health_checker._check_metadata_integrity()
        
        assert result["status"] == "unhealthy"
        assert result["exists"] is True
        assert result["readable"] is True
        assert "Missing required columns" in result["error_details"]
    
    @pytest.mark.skipif(not IMPORT_SUCCESS, reason="Could not import health_checker module")
    def test_check_metadata_integrity_corrupted_file(self, temp_dir):
        """Test metadata integrity check with corrupted file."""
        # Create corrupted CSV file
        metadata_path = os.path.join(temp_dir, "corrupted_metadata.csv")
        with open(metadata_path, 'w') as f:
            f.write("invalid,csv,content\nwith,missing\nquotes")
        
        health_checker = HealthChecker(
            storage_path=os.path.join(temp_dir, "vector_store"),
            collection_name="test_collection",
            qdrant_url="http://localhost:6333",
            embedding_model="sentence-transformers/all-MiniLM-L6-v2",
            metadata_csv_path=metadata_path
        )
        
        result = health_checker._check_metadata_integrity()
        
        assert result["status"] == "unhealthy"
        assert result["exists"] is True
        assert result["readable"] is False
        assert "Error reading metadata file" in result["error_details"]
    
    @pytest.mark.skipif(not IMPORT_SUCCESS, reason="Could not import health_checker module")
    def test_check_system_resources_healthy(self, health_checker, mock_performance_monitor):
        """Test system resources check with healthy values."""
        mock_performance_monitor.get_system_stats.return_value = {
            "memory_percent": 50.0,
            "disk_percent": 60.0,
            "cpu_percent": 30.0
        }
        
        result = health_checker._check_system_resources()
        
        assert result["status"] == "healthy"
        assert result["memory_ok"] is True
        assert result["disk_ok"] is True
        assert result["cpu_ok"] is True
        assert len(result["warnings"]) == 0
    
    @pytest.mark.skipif(not IMPORT_SUCCESS, reason="Could not import health_checker module")
    def test_check_system_resources_warnings(self, health_checker, mock_performance_monitor):
        """Test system resources check with warning levels."""
        mock_performance_monitor.get_system_stats.return_value = {
            "memory_percent": 85.0,
            "disk_percent": 88.0,
            "cpu_percent": 85.0
        }
        
        result = health_checker._check_system_resources()
        
        assert result["status"] == "warning"
        assert result["memory_ok"] is True
        assert result["disk_ok"] is True
        assert result["cpu_ok"] is True
        assert len(result["warnings"]) == 3
        assert any("memory usage" in warning.lower() for warning in result["warnings"])
        assert any("disk space" in warning.lower() for warning in result["warnings"])
        assert any("cpu usage" in warning.lower() for warning in result["warnings"])
    
    @pytest.mark.skipif(not IMPORT_SUCCESS, reason="Could not import health_checker module")
    def test_check_system_resources_critical(self, health_checker, mock_performance_monitor):
        """Test system resources check with critical levels."""
        mock_performance_monitor.get_system_stats.return_value = {
            "memory_percent": 95.0,
            "disk_percent": 98.0,
            "cpu_percent": 99.0
        }
        
        result = health_checker._check_system_resources()
        
        assert result["status"] == "unhealthy"
        assert result["memory_ok"] is False
        assert result["disk_ok"] is False
        assert result["cpu_ok"] is False
        assert len(result["warnings"]) == 3
    
    @pytest.mark.skipif(not IMPORT_SUCCESS, reason="Could not import health_checker module")
    def test_check_configuration_valid(self, health_checker):
        """Test configuration check with valid settings."""
        result = health_checker._check_configuration()
        
        assert result["status"] == "healthy"
        assert len(result["issues"]) == 0
        assert result["batch_size"] == BATCH_SIZE
        assert result["chunk_size"] == CHUNK_SIZE
        assert result["checksum_algorithm"] == CHECKSUM_ALGORITHM
        assert result["embedding_model"] == "sentence-transformers/all-MiniLM-L6-v2"
    
    @pytest.mark.skipif(not IMPORT_SUCCESS, reason="Could not import health_checker module")
    @patch('lets_talk.shared.config.BATCH_SIZE', 0)
    @patch('lets_talk.shared.config.CHUNK_SIZE', -1)
    @patch('lets_talk.shared.config.CHECKSUM_ALGORITHM', 'invalid')
    def test_check_configuration_invalid(self, health_checker):
        """Test configuration check with invalid settings."""
        # Create health checker with empty embedding model
        health_checker.embedding_model = ""
        
        result = health_checker._check_configuration()
        
        assert result["status"] == "unhealthy"
        assert len(result["issues"]) >= 4
        assert any("batch size" in issue.lower() for issue in result["issues"])
        assert any("chunk size" in issue.lower() for issue in result["issues"])
        assert any("checksum algorithm" in issue.lower() for issue in result["issues"])
        assert any("embedding model" in issue.lower() for issue in result["issues"])
    
    @pytest.mark.skipif(not IMPORT_SUCCESS, reason="Could not import health_checker module")
    def test_check_backup_files_healthy(self, health_checker):
        """Test backup files check with healthy backup situation."""
        result = health_checker._check_backup_files()
        
        # Should be healthy or warning (no backup files yet)
        assert result["status"] in ["healthy", "warning"]
        assert result["backup_count"] == 0
        assert result["max_allowed"] == MAX_BACKUP_FILES
        assert result["old_backup_count"] == 0
    
    @pytest.mark.skipif(not IMPORT_SUCCESS, reason="Could not import health_checker module")
    def test_check_backup_files_too_many(self, health_checker, temp_dir):
        """Test backup files check with too many backup files."""
        # Create many backup files
        for i in range(MAX_BACKUP_FILES + 3):
            backup_file = f"{health_checker.metadata_csv_path}.backup.{i}"
            with open(backup_file, 'w') as f:
                f.write("dummy backup content")
        
        result = health_checker._check_backup_files()
        
        assert result["status"] == "warning"
        assert result["backup_count"] == MAX_BACKUP_FILES + 3
        assert any("too many backup files" in warning.lower() for warning in result["warnings"])
    
    @pytest.mark.skipif(not IMPORT_SUCCESS, reason="Could not import health_checker module")
    def test_check_backup_files_old_backups(self, health_checker, temp_dir):
        """Test backup files check with old backup files."""
        # Create old backup file
        backup_file = f"{health_checker.metadata_csv_path}.backup.old"
        with open(backup_file, 'w') as f:
            f.write("old backup content")
        
        # Set old modification time (35 days ago)
        old_time = time.time() - (35 * 24 * 3600)
        os.utime(backup_file, (old_time, old_time))
        
        result = health_checker._check_backup_files()
        
        assert result["status"] == "warning"
        assert result["old_backup_count"] == 1
        assert any("older than" in warning.lower() for warning in result["warnings"])
    
    @pytest.mark.skipif(not IMPORT_SUCCESS, reason="Could not import health_checker module")
    def test_quick_health_check_healthy(self, health_checker, mock_vector_store_manager):
        """Test quick health check with healthy system."""
        mock_vector_store_manager.validate_health.return_value = True
        
        result = health_checker.quick_health_check()
        
        assert result["overall"] == "healthy"
        assert result["vector_store"] == "healthy"
        assert result["metadata"] == "healthy"
        assert "timestamp" in result
    
    @pytest.mark.skipif(not IMPORT_SUCCESS, reason="Could not import health_checker module")
    def test_quick_health_check_issues(self, health_checker, mock_vector_store_manager):
        """Test quick health check with issues detected."""
        mock_vector_store_manager.validate_health.return_value = False
        
        result = health_checker.quick_health_check()
        
        assert result["overall"] == "issues_detected"
        assert result["vector_store"] == "unhealthy"
    
    @pytest.mark.skipif(not IMPORT_SUCCESS, reason="Could not import health_checker module")
    def test_quick_health_check_missing_metadata(self, temp_dir, mock_vector_store_manager):
        """Test quick health check with missing metadata."""
        # Create health checker with non-existent metadata file
        missing_metadata_path = os.path.join(temp_dir, "missing_metadata.csv")
        health_checker = HealthChecker(
            storage_path=os.path.join(temp_dir, "vector_store"),
            collection_name="test_collection",
            qdrant_url="http://localhost:6333",
            embedding_model="sentence-transformers/all-MiniLM-L6-v2",
            metadata_csv_path=missing_metadata_path
        )
        
        mock_vector_store_manager.validate_health.return_value = True
        
        result = health_checker.quick_health_check()
        
        assert result["overall"] == "issues_detected"
        assert result["metadata"] == "missing"
    
    @pytest.mark.skipif(not IMPORT_SUCCESS, reason="Could not import health_checker module")
    def test_quick_health_check_exception(self, health_checker, mock_vector_store_manager):
        """Test quick health check with exception."""
        mock_vector_store_manager.validate_health.side_effect = Exception("Test error")
        
        result = health_checker.quick_health_check()
        
        assert result["overall"] == "error"
        assert "error" in result
        assert "Test error" in result["error"]
    
    @pytest.mark.skipif(not IMPORT_SUCCESS, reason="Could not import health_checker module")
    def test_comprehensive_health_check_with_exception(self, health_checker, mock_vector_store_manager):
        """Test comprehensive health check handles exceptions gracefully."""
        mock_vector_store_manager.validate_health.side_effect = Exception("Test error")
        
        result = health_checker.comprehensive_health_check()
        
        assert result["overall_status"] == "error"
        assert len(result["errors"]) > 0
        assert "Test error" in str(result["errors"])
    
    @pytest.mark.skipif(not IMPORT_SUCCESS, reason="Could not import health_checker module")
    def test_analyze_health_results_error_status(self, health_checker):
        """Test health results analysis with error status."""
        health_report = {
            "checks": {
                "vector_store": {"status": "error"},
                "metadata": {"status": "healthy"},
                "system_resources": {"status": "healthy"},
                "configuration": {"status": "healthy"},
                "backups": {"status": "healthy"}
            },
            "recommendations": []
        }
        
        health_checker._analyze_health_results(health_report)
        
        assert health_report["overall_status"] == "error"
    
    @pytest.mark.skipif(not IMPORT_SUCCESS, reason="Could not import health_checker module")
    def test_analyze_health_results_unhealthy_status(self, health_checker):
        """Test health results analysis with unhealthy status."""
        health_report = {
            "checks": {
                "vector_store": {"status": "unhealthy"},
                "metadata": {"status": "healthy"},
                "system_resources": {"status": "healthy"},
                "configuration": {"status": "healthy"},
                "backups": {"status": "healthy"}
            },
            "recommendations": []
        }
        
        health_checker._analyze_health_results(health_report)
        
        assert health_report["overall_status"] == "unhealthy"
        assert any("vector store" in rec.lower() for rec in health_report["recommendations"])
    
    @pytest.mark.skipif(not IMPORT_SUCCESS, reason="Could not import health_checker module")
    def test_analyze_health_results_warning_status(self, health_checker):
        """Test health results analysis with warning status."""
        health_report = {
            "checks": {
                "vector_store": {"status": "healthy"},
                "metadata": {"status": "healthy"},
                "system_resources": {"status": "warning", "memory_ok": True, "disk_ok": True, "cpu_ok": True},
                "configuration": {"status": "healthy"},
                "backups": {"status": "healthy"}
            },
            "recommendations": []
        }
        
        health_checker._analyze_health_results(health_report)
        
        assert health_report["overall_status"] == "warning"


class TestHealthCheckerConvenienceFunction:
    """Test cases for the convenience function."""
    
    @pytest.fixture
    def temp_dir(self):
        """Create a temporary directory for test files."""
        with tempfile.TemporaryDirectory() as temp_dir:
            yield temp_dir
    
    @pytest.fixture
    def sample_metadata_csv(self, temp_dir):
        """Create a sample metadata CSV file for testing."""
        metadata_path = os.path.join(temp_dir, "test_metadata.csv")
        df = pd.DataFrame({
            "source": ["doc1.md", "doc2.md"],
            "content_checksum": ["abc123", "def456"],
            "indexed_timestamp": [1640995200, 1640995300]
        })
        df.to_csv(metadata_path, index=False)
        return metadata_path
    
    @pytest.mark.skipif(not IMPORT_SUCCESS, reason="Could not import health_checker module")
    @patch('lets_talk.core.pipeline.services.health_checker.VectorStoreManager')
    @patch('lets_talk.core.pipeline.services.health_checker.PerformanceMonitor')
    def test_comprehensive_system_health_check_function(self, mock_perf_monitor, mock_vector_manager, temp_dir, sample_metadata_csv):
        """Test the convenience function for comprehensive health check."""
        # Mock healthy responses
        mock_vector_manager.return_value.validate_health.return_value = True
        mock_perf_monitor.return_value.get_system_stats.return_value = {
            "memory_percent": 50.0,
            "disk_percent": 60.0,
            "cpu_percent": 30.0
        }
        
        storage_path = os.path.join(temp_dir, "vector_store")
        collection_name = "test_collection"
        qdrant_url = "http://localhost:6333"
        embedding_model = "sentence-transformers/all-MiniLM-L6-v2"
        
        result = comprehensive_system_health_check(
            storage_path=storage_path,
            collection_name=collection_name,
            qdrant_url=qdrant_url,
            embedding_model=embedding_model,
            metadata_csv_path=sample_metadata_csv
        )
        
        assert result["overall_status"] == "healthy"
        assert "timestamp" in result
        assert "checks" in result
        assert "recommendations" in result
        assert "errors" in result


class TestHealthCheckerEdgeCases:
    """Test edge cases and error scenarios."""
    
    @pytest.fixture
    def temp_dir(self):
        """Create a temporary directory for test files."""
        with tempfile.TemporaryDirectory() as temp_dir:
            yield temp_dir
    
    @pytest.mark.skipif(not IMPORT_SUCCESS, reason="Could not import health_checker module")
    def test_health_checker_with_none_values(self, temp_dir):
        """Test HealthChecker with None values."""
        metadata_path = os.path.join(temp_dir, "metadata.csv")
        
        # Create health checker with None qdrant_url (using local storage)
        health_checker = HealthChecker(
            storage_path=os.path.join(temp_dir, "vector_store"),
            collection_name="test_collection",
            qdrant_url=None,
            embedding_model="sentence-transformers/all-MiniLM-L6-v2",
            metadata_csv_path=metadata_path
        )
        
        assert health_checker.qdrant_url is None
        assert health_checker.storage_path.endswith("vector_store")
    
    @pytest.mark.skipif(not IMPORT_SUCCESS, reason="Could not import health_checker module")
    @patch('lets_talk.core.pipeline.services.health_checker.VectorStoreManager')
    @patch('lets_talk.core.pipeline.services.health_checker.PerformanceMonitor')
    def test_health_checker_partial_system_stats(self, mock_perf_monitor, mock_vector_manager, temp_dir):
        """Test health checker with partial system stats."""
        metadata_path = os.path.join(temp_dir, "metadata.csv")
        pd.DataFrame({
            "source": ["doc1.md"],
            "content_checksum": ["abc123"],
            "indexed_timestamp": [1640995200]
        }).to_csv(metadata_path, index=False)
        
        health_checker = HealthChecker(
            storage_path=os.path.join(temp_dir, "vector_store"),
            collection_name="test_collection",
            qdrant_url="http://localhost:6333",
            embedding_model="sentence-transformers/all-MiniLM-L6-v2",
            metadata_csv_path=metadata_path
        )
        
        # Mock partial system stats (missing some metrics)
        mock_vector_manager.return_value.validate_health.return_value = True
        mock_perf_monitor.return_value.get_system_stats.return_value = {
            "memory_percent": 50.0
            # Missing disk_percent and cpu_percent
        }
        
        result = health_checker.comprehensive_health_check()
        
        # Should still complete successfully
        assert result["overall_status"] in ["healthy", "warning", "unhealthy"]
        assert "system_resources" in result["checks"]
    
    @pytest.mark.skipif(not IMPORT_SUCCESS, reason="Could not import health_checker module")
    def test_health_checker_empty_metadata_file(self, temp_dir):
        """Test health checker with empty metadata file."""
        metadata_path = os.path.join(temp_dir, "empty_metadata.csv")
        
        # Create empty CSV
        pd.DataFrame().to_csv(metadata_path, index=False)
        
        health_checker = HealthChecker(
            storage_path=os.path.join(temp_dir, "vector_store"),
            collection_name="test_collection",
            qdrant_url="http://localhost:6333",
            embedding_model="sentence-transformers/all-MiniLM-L6-v2",
            metadata_csv_path=metadata_path
        )
        
        result = health_checker._check_metadata_integrity()
        
        assert result["exists"] is True
        assert result["record_count"] == 0
        # Should detect missing required columns
        assert result["status"] == "unhealthy"


if __name__ == "__main__":
    # Run the tests
    pytest.main([__file__, "-v"])
