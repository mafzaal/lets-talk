#!/usr/bin/env python3
"""
Pytest test suite for the PerformanceMonitor service.

This test script covers:
- PerformanceMonitor initialization
- System stats collection
- Operation monitoring
- Metrics history management
- Performance summaries
- OptimizationService functionality
- Error handling and edge cases
"""

import os
import sys
import tempfile
import time
import pytest
from pathlib import Path
from typing import List, Dict, Any
from unittest.mock import Mock, patch, MagicMock

# Import langchain Document first
from langchain.schema.document import Document

# Add the backend directory to the path
backend_path = os.path.join(os.path.dirname(__file__), '..', 'backend')
if backend_path not in sys.path:
    sys.path.insert(0, backend_path)

# Import the modules to test
try:
    from lets_talk.core.pipeline.services.performance_monitor import (
        PerformanceMonitor,
        OptimizationService,
        get_processing_stats,
        monitor_incremental_performance,
        apply_performance_optimizations
    )
    from lets_talk.shared.config import (
        ADAPTIVE_CHUNKING,
        CHUNK_SIZE,
        CHUNK_OVERLAP,
        ENABLE_PERFORMANCE_MONITORING
    )
    IMPORT_SUCCESS = True
except ImportError as e:
    print(f"Failed to import performance_monitor module: {e}")
    IMPORT_SUCCESS = False


class TestPerformanceMonitor:
    """Test cases for PerformanceMonitor class."""

    @pytest.fixture
    def performance_monitor(self):
        """Create a PerformanceMonitor instance for testing."""
        return PerformanceMonitor(enable_monitoring=True)

    @pytest.fixture
    def sample_documents(self):
        """Create sample documents for testing."""
        return [
            Document(
                page_content="This is a short test document.",
                metadata={"source": "/path/to/doc1.md", "title": "Short Doc"}
            ),
            Document(
                page_content="This is a much longer test document that contains significantly more content to test chunking optimization. " * 10,
                metadata={"source": "/path/to/doc2.md", "title": "Long Doc"}
            ),
            Document(
                page_content="Medium length document with moderate content.",
                metadata={"source": "/path/to/doc3.md", "title": "Medium Doc"}
            )
        ]

    @pytest.mark.skipif(not IMPORT_SUCCESS, reason="Failed to import performance_monitor module")
    def test_performance_monitor_creation(self):
        """Test creating a PerformanceMonitor instance."""
        monitor = PerformanceMonitor()
        assert monitor is not None
        assert isinstance(monitor.metrics_history, list)
        assert len(monitor.metrics_history) == 0
        assert monitor.enable_monitoring == ENABLE_PERFORMANCE_MONITORING

    @pytest.mark.skipif(not IMPORT_SUCCESS, reason="Failed to import performance_monitor module")
    def test_performance_monitor_with_monitoring_enabled(self):
        """Test PerformanceMonitor with monitoring explicitly enabled."""
        monitor = PerformanceMonitor(enable_monitoring=True)
        assert monitor.enable_monitoring is True

    @pytest.mark.skipif(not IMPORT_SUCCESS, reason="Failed to import performance_monitor module")
    def test_performance_monitor_with_monitoring_disabled(self):
        """Test PerformanceMonitor with monitoring explicitly disabled."""
        monitor = PerformanceMonitor(enable_monitoring=False)
        assert monitor.enable_monitoring is False

    @pytest.mark.skipif(not IMPORT_SUCCESS, reason="Failed to import performance_monitor module")
    def test_get_system_stats_with_psutil(self, performance_monitor):
        """Test get_system_stats when psutil is available."""
        with patch('psutil.virtual_memory') as mock_memory, \
             patch('psutil.cpu_percent') as mock_cpu, \
             patch('psutil.cpu_count') as mock_cpu_count, \
             patch('psutil.disk_usage') as mock_disk:
            
            # Mock memory info
            mock_memory.return_value = Mock(
                total=8 * 1024**3,  # 8GB
                available=4 * 1024**3,  # 4GB
                percent=50.0
            )
            
            # Mock CPU info
            mock_cpu.return_value = 25.5
            mock_cpu_count.return_value = 4
            
            # Mock disk info
            mock_disk.return_value = Mock(
                total=100 * 1024**3,  # 100GB
                free=50 * 1024**3,    # 50GB
                used=50 * 1024**3     # 50GB
            )
            
            stats = performance_monitor.get_system_stats()
            
            assert stats["memory_total_gb"] == 8.0
            assert stats["memory_available_gb"] == 4.0
            assert stats["memory_percent"] == 50.0
            assert stats["cpu_percent"] == 25.5
            assert stats["cpu_count"] == 4
            assert stats["disk_total_gb"] == 100.0
            assert stats["disk_free_gb"] == 50.0
            assert stats["disk_percent"] == 50.0

    @pytest.mark.skipif(not IMPORT_SUCCESS, reason="Failed to import performance_monitor module")
    def test_get_system_stats_without_psutil(self, performance_monitor):
        """Test get_system_stats when psutil is not available."""
        with patch('builtins.__import__', side_effect=ImportError("No module named 'psutil'")):
            stats = performance_monitor.get_system_stats()
            assert "memory_info" in stats
            assert stats["memory_info"] == "psutil not available"

    @pytest.mark.skipif(not IMPORT_SUCCESS, reason="Failed to import performance_monitor module")
    def test_get_system_stats_with_exception(self, performance_monitor):
        """Test get_system_stats when an exception occurs."""
        with patch('psutil.virtual_memory', side_effect=Exception("Test error")):
            stats = performance_monitor.get_system_stats()
            assert "error" in stats
            assert "Test error" in stats["error"]

    @pytest.mark.skipif(not IMPORT_SUCCESS, reason="Failed to import performance_monitor module")
    def test_monitor_operation_basic(self, performance_monitor):
        """Test basic operation monitoring."""
        start_time = time.time()
        time.sleep(0.1)  # Simulate some work
        
        metrics = performance_monitor.monitor_operation(
            operation="test_operation",
            start_time=start_time,
            document_count=10,
            chunk_count=50
        )
        
        assert metrics["operation"] == "test_operation"
        assert metrics["document_count"] == 10
        assert metrics["chunk_count"] == 50
        assert metrics["duration_seconds"] >= 0.1
        assert metrics["documents_per_second"] > 0
        assert metrics["chunks_per_second"] > 0
        assert "timestamp" in metrics
        
        # Check that metrics were added to history
        assert len(performance_monitor.metrics_history) == 1
        assert performance_monitor.metrics_history[0] == metrics

    @pytest.mark.skipif(not IMPORT_SUCCESS, reason="Failed to import performance_monitor module")
    def test_monitor_operation_with_system_stats(self, performance_monitor):
        """Test operation monitoring with system stats enabled."""
        start_time = time.time()
        
        with patch.object(performance_monitor, 'get_system_stats') as mock_stats:
            mock_stats.return_value = {"memory_percent": 50.0, "cpu_percent": 25.0}
            
            metrics = performance_monitor.monitor_operation(
                operation="test_with_stats",
                start_time=start_time,
                document_count=5
            )
            
            assert "system_stats" in metrics
            assert metrics["system_stats"]["memory_percent"] == 50.0
            assert metrics["system_stats"]["cpu_percent"] == 25.0

    @pytest.mark.skipif(not IMPORT_SUCCESS, reason="Failed to import performance_monitor module")
    def test_monitor_operation_with_additional_metrics(self, performance_monitor):
        """Test operation monitoring with additional metrics."""
        start_time = time.time()
        additional_metrics = {
            "custom_metric": 42,
            "processing_mode": "batch"
        }
        
        metrics = performance_monitor.monitor_operation(
            operation="test_additional",
            start_time=start_time,
            document_count=3,
            additional_metrics=additional_metrics
        )
        
        assert metrics["custom_metric"] == 42
        assert metrics["processing_mode"] == "batch"

    @pytest.mark.skipif(not IMPORT_SUCCESS, reason="Failed to import performance_monitor module")
    def test_monitor_operation_zero_duration(self, performance_monitor):
        """Test operation monitoring with zero or very small duration."""
        start_time = time.time()
        
        metrics = performance_monitor.monitor_operation(
            operation="instant_operation",
            start_time=start_time,
            document_count=10,
            chunk_count=50
        )
        
        # Should handle zero duration gracefully
        assert metrics["documents_per_second"] >= 0
        assert metrics["chunks_per_second"] >= 0

    @pytest.mark.skipif(not IMPORT_SUCCESS, reason="Failed to import performance_monitor module")
    def test_monitor_operation_zero_documents(self, performance_monitor):
        """Test operation monitoring with zero documents."""
        start_time = time.time()
        time.sleep(0.01)
        
        metrics = performance_monitor.monitor_operation(
            operation="empty_operation",
            start_time=start_time,
            document_count=0,
            chunk_count=0
        )
        
        assert metrics["documents_per_second"] == 0
        assert metrics["chunks_per_second"] == 0

    @pytest.mark.skipif(not IMPORT_SUCCESS, reason="Failed to import performance_monitor module")
    def test_get_metrics_summary_empty(self, performance_monitor):
        """Test getting metrics summary when no metrics exist."""
        summary = performance_monitor.get_metrics_summary()
        assert summary == {}

    @pytest.mark.skipif(not IMPORT_SUCCESS, reason="Failed to import performance_monitor module")
    def test_get_metrics_summary_basic(self, performance_monitor):
        """Test getting basic metrics summary."""
        # Add some test metrics
        start_time = time.time()
        performance_monitor.monitor_operation("op1", start_time, 10, 50)
        performance_monitor.monitor_operation("op2", start_time, 20, 100)
        performance_monitor.monitor_operation("op1", start_time, 15, 75)
        
        summary = performance_monitor.get_metrics_summary()
        
        assert summary["total_operations"] == 3
        assert summary["total_documents"] == 45  # 10 + 20 + 15
        assert summary["avg_documents_per_operation"] == 15.0  # 45 / 3
        assert "total_duration" in summary
        assert "avg_duration" in summary
        assert "min_duration" in summary
        assert "max_duration" in summary
        assert len(summary["operations"]) == 3

    @pytest.mark.skipif(not IMPORT_SUCCESS, reason="Failed to import performance_monitor module")
    def test_get_metrics_summary_with_filter(self, performance_monitor):
        """Test getting metrics summary with operation filter."""
        start_time = time.time()
        performance_monitor.monitor_operation("load_docs", start_time, 10, 50)
        performance_monitor.monitor_operation("process_docs", start_time, 20, 100)
        performance_monitor.monitor_operation("load_docs", start_time, 15, 75)
        
        summary = performance_monitor.get_metrics_summary(operation_filter="load_docs")
        
        assert summary["total_operations"] == 2
        assert summary["total_documents"] == 25  # 10 + 15
        assert all(op == "load_docs" for op in summary["operations"])

    @pytest.mark.skipif(not IMPORT_SUCCESS, reason="Failed to import performance_monitor module")
    def test_get_metrics_summary_with_invalid_filter(self, performance_monitor):
        """Test getting metrics summary with non-existent operation filter."""
        start_time = time.time()
        performance_monitor.monitor_operation("op1", start_time, 10, 50)
        
        summary = performance_monitor.get_metrics_summary(operation_filter="non_existent")
        assert summary == {}

    @pytest.mark.skipif(not IMPORT_SUCCESS, reason="Failed to import performance_monitor module")
    def test_clear_history(self, performance_monitor):
        """Test clearing metrics history."""
        # Add some metrics
        start_time = time.time()
        performance_monitor.monitor_operation("test_op", start_time, 5, 25)
        performance_monitor.monitor_operation("test_op2", start_time, 10, 50)
        
        assert len(performance_monitor.metrics_history) == 2
        
        performance_monitor.clear_history()
        
        assert len(performance_monitor.metrics_history) == 0

    @pytest.mark.skipif(not IMPORT_SUCCESS, reason="Failed to import performance_monitor module")
    def test_global_functions(self):
        """Test global convenience functions."""
        # Test get_processing_stats
        with patch('lets_talk.core.pipeline.services.performance_monitor._global_monitor') as mock_monitor:
            mock_monitor.get_system_stats.return_value = {"cpu_percent": 30.0}
            
            stats = get_processing_stats()
            assert stats["cpu_percent"] == 30.0
            mock_monitor.get_system_stats.assert_called_once()

        # Test monitor_incremental_performance
        with patch('lets_talk.core.pipeline.services.performance_monitor._global_monitor') as mock_monitor:
            mock_monitor.monitor_operation.return_value = {"operation": "test"}
            
            start_time = time.time()
            result = monitor_incremental_performance("test_op", start_time, 5, 25)
            
            assert result["operation"] == "test"
            mock_monitor.monitor_operation.assert_called_once_with("test_op", start_time, 5, 25)


class TestOptimizationService:
    """Test cases for OptimizationService class."""

    @pytest.fixture
    def optimization_service(self):
        """Create an OptimizationService instance for testing."""
        return OptimizationService()

    @pytest.fixture
    def sample_documents(self):
        """Create sample documents with varying lengths for testing."""
        return [
            Document(page_content="Short doc.", metadata={"source": "doc1.md"}),
            Document(page_content="Medium length document with more content than the short one.", metadata={"source": "doc2.md"}),
            Document(page_content="Very long document " * 100, metadata={"source": "doc3.md"}),  # ~2000 chars
        ]

    @pytest.mark.skipif(not IMPORT_SUCCESS, reason="Failed to import performance_monitor module")
    def test_optimization_service_creation(self):
        """Test creating an OptimizationService instance."""
        service = OptimizationService()
        assert service is not None
        assert isinstance(service.performance_monitor, PerformanceMonitor)
        assert service.adaptive_chunking == ADAPTIVE_CHUNKING
        assert service.chunk_size == CHUNK_SIZE
        assert service.chunk_overlap == CHUNK_OVERLAP

    @pytest.mark.skipif(not IMPORT_SUCCESS, reason="Failed to import performance_monitor module")
    def test_optimization_service_custom_params(self):
        """Test creating OptimizationService with custom parameters."""
        service = OptimizationService(
            adaptive_chunking=True,
            chunk_size=1500,
            chunk_overlap=200
        )
        assert service.adaptive_chunking is True
        assert service.chunk_size == 1500
        assert service.chunk_overlap == 200

    @pytest.mark.skipif(not IMPORT_SUCCESS, reason="Failed to import performance_monitor module")
    def test_optimize_batch_size_basic(self, optimization_service):
        """Test basic batch size optimization."""
        batch_size = optimization_service.optimize_batch_size(
            total_items=1000,
            available_memory_mb=1024,
            item_size_estimate_bytes=1024
        )
        
        # Should be reasonable and within bounds
        assert 10 <= batch_size <= 1000
        assert batch_size <= 1000  # Don't exceed total items

    @pytest.mark.skipif(not IMPORT_SUCCESS, reason="Failed to import performance_monitor module")
    def test_optimize_batch_size_memory_constrained(self, optimization_service):
        """Test batch size optimization with memory constraints."""
        batch_size = optimization_service.optimize_batch_size(
            total_items=10000,
            available_memory_mb=10,  # Very limited memory
            item_size_estimate_bytes=1024 * 1024  # 1MB per item
        )
        
        # Should be very small due to memory constraints
        assert batch_size == 10  # Minimum batch size

    @pytest.mark.skipif(not IMPORT_SUCCESS, reason="Failed to import performance_monitor module")
    def test_optimize_batch_size_large_memory(self, optimization_service):
        """Test batch size optimization with abundant memory."""
        batch_size = optimization_service.optimize_batch_size(
            total_items=100,
            available_memory_mb=8192,  # 8GB
            item_size_estimate_bytes=1024  # 1KB per item
        )
        
        # Should use all items since memory is abundant
        assert batch_size == 100

    @pytest.mark.skipif(not IMPORT_SUCCESS, reason="Failed to import performance_monitor module")
    def test_optimize_chunking_parameters_empty_docs(self, optimization_service):
        """Test chunking optimization with empty document list."""
        chunk_size, overlap = optimization_service.optimize_chunking_parameters([])
        
        assert chunk_size == optimization_service.chunk_size
        assert overlap == optimization_service.chunk_overlap

    @pytest.mark.skipif(not IMPORT_SUCCESS, reason="Failed to import performance_monitor module")
    def test_optimize_chunking_parameters_small_docs(self, optimization_service):
        """Test chunking optimization with small documents."""
        small_docs = [
            Document(page_content="Small doc.", metadata={}),
            Document(page_content="Another small document.", metadata={})
        ]
        
        chunk_size, overlap = optimization_service.optimize_chunking_parameters(
            small_docs, target_chunk_size=1000
        )
        
        # Should use smaller chunks for small documents
        assert chunk_size < 1000
        assert chunk_size >= 500  # Minimum reasonable size
        assert overlap > 0

    @pytest.mark.skipif(not IMPORT_SUCCESS, reason="Failed to import performance_monitor module")
    def test_optimize_chunking_parameters_large_docs(self, optimization_service):
        """Test chunking optimization with large documents."""
        large_docs = [
            Document(page_content="Large document " * 500, metadata={}),  # ~7500 chars
            Document(page_content="Another large document " * 500, metadata={})
        ]
        
        chunk_size, overlap = optimization_service.optimize_chunking_parameters(
            large_docs, target_chunk_size=1000, max_chunk_size=2000
        )
        
        # Should use maximum chunk size for large documents
        assert chunk_size == 2000
        assert overlap >= 100

    @pytest.mark.skipif(not IMPORT_SUCCESS, reason="Failed to import performance_monitor module")
    def test_optimize_chunking_parameters_mixed_docs(self, optimization_service, sample_documents):
        """Test chunking optimization with mixed document sizes."""
        chunk_size, overlap = optimization_service.optimize_chunking_parameters(
            sample_documents, target_chunk_size=1000
        )
        
        # Should find a reasonable middle ground
        assert chunk_size > 0
        assert overlap > 0
        assert chunk_size <= 2000  # Default max

    @pytest.mark.skipif(not IMPORT_SUCCESS, reason="Failed to import performance_monitor module")
    def test_apply_performance_optimizations_basic(self, optimization_service, sample_documents):
        """Test applying basic performance optimizations."""
        optimized_docs, metrics = optimization_service.apply_performance_optimizations(
            sample_documents,
            adaptive_chunking=False,
            enable_monitoring=False
        )
        
        assert len(optimized_docs) == len(sample_documents)
        assert metrics["input_document_count"] == len(sample_documents)
        assert "optimization_duration" in metrics
        assert "documents_per_second" in metrics
        assert isinstance(metrics["optimizations_applied"], list)
        
        # Check that documents have optimization metadata
        for doc in optimized_docs:
            assert doc.metadata["optimization_applied"] is True
            assert "optimized_chunk_size" in doc.metadata
            assert "optimized_chunk_overlap" in doc.metadata

    @pytest.mark.skipif(not IMPORT_SUCCESS, reason="Failed to import performance_monitor module")
    def test_apply_performance_optimizations_with_adaptive_chunking(self, optimization_service, sample_documents):
        """Test applying optimizations with adaptive chunking enabled."""
        optimized_docs, metrics = optimization_service.apply_performance_optimizations(
            sample_documents,
            adaptive_chunking=True,
            enable_monitoring=False
        )
        
        assert "adaptive_chunking" in metrics["optimizations_applied"]
        assert "chunk_size" in metrics
        assert "chunk_overlap" in metrics

    @pytest.mark.skipif(not IMPORT_SUCCESS, reason="Failed to import performance_monitor module")
    def test_apply_performance_optimizations_with_monitoring(self, optimization_service, sample_documents):
        """Test applying optimizations with monitoring enabled."""
        with patch.object(optimization_service.performance_monitor, 'get_system_stats') as mock_stats:
            mock_stats.return_value = {"memory_percent": 60.0}
            
            optimized_docs, metrics = optimization_service.apply_performance_optimizations(
                sample_documents,
                adaptive_chunking=False,
                enable_monitoring=True
            )
            
            assert "resource_monitoring" in metrics["optimizations_applied"]
            assert "performance_stats" in metrics
            assert metrics["performance_stats"]["memory_percent"] == 60.0

    @pytest.mark.skipif(not IMPORT_SUCCESS, reason="Failed to import performance_monitor module")
    def test_apply_performance_optimizations_error_handling(self, optimization_service):
        """Test error handling in performance optimizations."""
        # Test with None documents (should handle gracefully)
        optimized_docs, metrics = optimization_service.apply_performance_optimizations(
            [],
            adaptive_chunking=True
        )
        
        assert len(optimized_docs) == 0
        assert metrics["input_document_count"] == 0
        assert "optimization_duration" in metrics

    @pytest.mark.skipif(not IMPORT_SUCCESS, reason="Failed to import performance_monitor module")
    def test_analyze_processing_efficiency_empty(self, optimization_service):
        """Test efficiency analysis with empty metrics."""
        analysis = optimization_service.analyze_processing_efficiency([])
        assert analysis == {}

    @pytest.mark.skipif(not IMPORT_SUCCESS, reason="Failed to import performance_monitor module")
    def test_analyze_processing_efficiency_basic(self, optimization_service):
        """Test basic efficiency analysis."""
        metrics = [
            {
                "operation": "load_docs",
                "duration_seconds": 2.0,
                "document_count": 10,
                "chunk_count": 50,
                "documents_per_second": 5.0
            },
            {
                "operation": "process_docs", 
                "duration_seconds": 3.0,
                "document_count": 15,
                "chunk_count": 75,
                "documents_per_second": 5.0
            }
        ]
        
        analysis = optimization_service.analyze_processing_efficiency(metrics)
        
        assert analysis["total_operations"] == 2
        assert analysis["total_documents_processed"] == 25
        assert analysis["total_chunks_processed"] == 125
        assert analysis["total_processing_time"] == 5.0
        assert analysis["overall_documents_per_second"] == 5.0  # 25 / 5
        assert analysis["overall_chunks_per_second"] == 25.0   # 125 / 5
        assert analysis["average_operation_duration"] == 2.5   # 5 / 2
        assert analysis["chunks_per_document_ratio"] == 5.0    # 125 / 25
        assert len(analysis["potential_bottlenecks"]) <= 3

    @pytest.mark.skipif(not IMPORT_SUCCESS, reason="Failed to import performance_monitor module")
    def test_global_apply_performance_optimizations(self, sample_documents):
        """Test global apply_performance_optimizations function."""
        with patch('lets_talk.core.pipeline.services.performance_monitor.OptimizationService') as mock_service_class:
            mock_service = Mock()
            mock_service.apply_performance_optimizations.return_value = (sample_documents, {"test": "metrics"})
            mock_service_class.return_value = mock_service
            
            result_docs, result_metrics = apply_performance_optimizations(
                sample_documents,
                target_chunk_size=1200,
                chunk_overlap=150,
                adaptive_chunking=True,
                enable_monitoring=False
            )
            
            # Verify OptimizationService was created with correct parameters
            mock_service_class.assert_called_once_with(
                adaptive_chunking=True,
                chunk_size=1200,
                chunk_overlap=150
            )
            
            # Verify apply_performance_optimizations was called correctly
            mock_service.apply_performance_optimizations.assert_called_once_with(
                sample_documents, 1200, 150, True, False
            )
            
            assert result_docs == sample_documents
            assert result_metrics == {"test": "metrics"}


if __name__ == "__main__":
    # Run the tests
    import subprocess
    import sys
    
    # Use uv to run pytest as specified in the instructions
    result = subprocess.run([
        "uv", "run", "pytest", __file__, "-v"
    ], cwd=os.path.dirname(os.path.dirname(__file__)))
    
    sys.exit(result.returncode)
