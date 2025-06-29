#!/usr/bin/env python3
"""
Comprehensive pytest test suite for the OptimizationService class.

This test script provides additional coverage for OptimizationService with focus on:
- Edge cases and boundary conditions
- Error handling scenarios
- Integration testing with PerformanceMonitor
- Memory optimization scenarios
- Document chunking optimization
- Performance analysis functionality
- Mock scenarios for system resource testing
"""

import os
import sys
import time
import pytest
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
        OptimizationService
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


class TestOptimizationServiceComprehensive:
    """Comprehensive test cases for OptimizationService class."""

    @pytest.fixture
    def optimization_service(self):
        """Create an OptimizationService instance for testing."""
        return OptimizationService(
            adaptive_chunking=True,
            chunk_size=1000,
            chunk_overlap=100
        )

    @pytest.fixture
    def varied_documents(self):
        """Create documents with varied characteristics for comprehensive testing."""
        return [
            # Very short document
            Document(page_content="Short.", metadata={"source": "short.md", "type": "minimal"}),
            
            # Medium document
            Document(
                page_content="This is a medium length document that contains enough content to test chunking behavior. " * 5,
                metadata={"source": "medium.md", "type": "standard"}
            ),
            
            # Large document
            Document(
                page_content="This is a very large document that will definitely require chunking. " * 50,
                metadata={"source": "large.md", "type": "extended"}
            ),
            
            # Very large document exceeding typical chunk sizes
            Document(
                page_content="Extremely large content. " * 200,
                metadata={"source": "huge.md", "type": "massive"}
            ),
            
            # Empty document
            Document(page_content="", metadata={"source": "empty.md", "type": "empty"}),
        ]

    @pytest.mark.skipif(not IMPORT_SUCCESS, reason="Failed to import performance_monitor module")
    def test_optimization_service_initialization_with_defaults(self):
        """Test OptimizationService initialization with default configuration."""
        service = OptimizationService()
        
        assert isinstance(service.performance_monitor, PerformanceMonitor)
        assert service.adaptive_chunking == ADAPTIVE_CHUNKING
        assert service.chunk_size == CHUNK_SIZE
        assert service.chunk_overlap == CHUNK_OVERLAP
        
        # Verify PerformanceMonitor is properly initialized
        assert service.performance_monitor.enable_monitoring == ENABLE_PERFORMANCE_MONITORING
        assert service.performance_monitor.metrics_history == []

    @pytest.mark.skipif(not IMPORT_SUCCESS, reason="Failed to import performance_monitor module")
    def test_optimization_service_initialization_custom_values(self):
        """Test OptimizationService initialization with custom values."""
        service = OptimizationService(
            adaptive_chunking=False,
            chunk_size=2000,
            chunk_overlap=300
        )
        
        assert service.adaptive_chunking is False
        assert service.chunk_size == 2000
        assert service.chunk_overlap == 300

    @pytest.mark.skipif(not IMPORT_SUCCESS, reason="Failed to import performance_monitor module")
    def test_optimize_batch_size_edge_cases(self, optimization_service):
        """Test batch size optimization with edge cases."""
        
        # Test with zero items
        batch_size = optimization_service.optimize_batch_size(
            total_items=0,
            available_memory_mb=1024,
            item_size_estimate_bytes=1024
        )
        assert batch_size == 0
        
        # Test with single item
        batch_size = optimization_service.optimize_batch_size(
            total_items=1,
            available_memory_mb=1024,
            item_size_estimate_bytes=1024
        )
        assert batch_size == 1
        
        # Test with very large item size
        batch_size = optimization_service.optimize_batch_size(
            total_items=1000,
            available_memory_mb=1,  # 1MB total memory
            item_size_estimate_bytes=1024 * 1024  # 1MB per item
        )
        assert batch_size == 10  # Should hit minimum
        
        # Test with very small item size
        batch_size = optimization_service.optimize_batch_size(
            total_items=5,
            available_memory_mb=8192,  # 8GB
            item_size_estimate_bytes=1  # 1 byte per item
        )
        assert batch_size == 5  # Should not exceed total items

    @pytest.mark.skipif(not IMPORT_SUCCESS, reason="Failed to import performance_monitor module")
    def test_optimize_batch_size_boundary_conditions(self, optimization_service):
        """Test batch size optimization at boundary conditions."""
        
        # Test when calculated batch size exactly hits the recommended max
        batch_size = optimization_service.optimize_batch_size(
            total_items=2000,
            available_memory_mb=1024,
            item_size_estimate_bytes=1024  # Results in exactly 1000 items
        )
        assert batch_size == 1000  # Should hit recommended max
        
        # Test when total items is less than minimum batch size
        batch_size = optimization_service.optimize_batch_size(
            total_items=5,
            available_memory_mb=1,
            item_size_estimate_bytes=1024 * 1024
        )
        assert batch_size == 5  # Should use total items, not minimum

    @pytest.mark.skipif(not IMPORT_SUCCESS, reason="Failed to import performance_monitor module")
    def test_optimize_chunking_parameters_comprehensive(self, optimization_service, varied_documents):
        """Test comprehensive chunking parameter optimization."""
        
        # Test with all varied documents
        chunk_size, overlap = optimization_service.optimize_chunking_parameters(
            documents=varied_documents,
            target_chunk_size=1000,
            chunk_overlap=100,
            max_chunk_size=1500
        )
        
        assert chunk_size > 0
        assert overlap > 0
        assert chunk_size <= 1500  # Should not exceed max
        assert overlap < chunk_size  # Overlap should be less than chunk size

    @pytest.mark.skipif(not IMPORT_SUCCESS, reason="Failed to import performance_monitor module")
    def test_optimize_chunking_parameters_with_none_values(self, optimization_service, varied_documents):
        """Test chunking optimization when target values are None."""
        
        chunk_size, overlap = optimization_service.optimize_chunking_parameters(
            documents=varied_documents,
            target_chunk_size=None,
            chunk_overlap=None
        )
        
        # Should use instance defaults
        assert chunk_size == optimization_service.chunk_size or chunk_size > 0
        assert overlap == optimization_service.chunk_overlap or overlap > 0

    @pytest.mark.skipif(not IMPORT_SUCCESS, reason="Failed to import performance_monitor module")
    def test_optimize_chunking_parameters_all_empty_documents(self, optimization_service):
        """Test chunking optimization with documents that have empty content."""
        
        empty_docs = [
            Document(page_content="", metadata={"source": "empty1.md"}),
            Document(page_content="", metadata={"source": "empty2.md"}),
            Document(page_content="", metadata={"source": "empty3.md"})
        ]
        
        chunk_size, overlap = optimization_service.optimize_chunking_parameters(
            documents=empty_docs,
            target_chunk_size=1000
        )
        
        # Should handle gracefully and return reasonable values
        assert chunk_size >= 500  # Should hit minimum reasonable size
        assert overlap > 0

    @pytest.mark.skipif(not IMPORT_SUCCESS, reason="Failed to import performance_monitor module")
    def test_optimize_chunking_parameters_extremely_large_documents(self, optimization_service):
        """Test chunking optimization with extremely large documents."""
        
        huge_docs = [
            Document(page_content="X" * 10000, metadata={"source": "huge1.md"}),
            Document(page_content="Y" * 15000, metadata={"source": "huge2.md"}),
            Document(page_content="Z" * 20000, metadata={"source": "huge3.md"})
        ]
        
        chunk_size, overlap = optimization_service.optimize_chunking_parameters(
            documents=huge_docs,
            target_chunk_size=1000,
            max_chunk_size=2500
        )
        
        # Should use max chunk size for very large documents
        assert chunk_size == 2500
        assert overlap >= 100  # Should have reasonable overlap

    @pytest.mark.skipif(not IMPORT_SUCCESS, reason="Failed to import performance_monitor module")
    def test_apply_performance_optimizations_comprehensive(self, optimization_service, varied_documents):
        """Test comprehensive performance optimization application."""
        
        optimized_docs, metrics = optimization_service.apply_performance_optimizations(
            documents=varied_documents,
            target_chunk_size=1200,
            chunk_overlap=150,
            adaptive_chunking=True,
            enable_monitoring=True
        )
        
        # Verify document integrity
        assert len(optimized_docs) == len(varied_documents)
        
        # Verify all documents have optimization metadata
        for i, doc in enumerate(optimized_docs):
            assert doc.metadata["optimization_applied"] is True
            assert "optimized_chunk_size" in doc.metadata
            assert "optimized_chunk_overlap" in doc.metadata
            assert doc.metadata["optimized_chunk_size"] > 0
            assert doc.metadata["optimized_chunk_overlap"] > 0
            
            # Original metadata should be preserved
            assert doc.metadata["source"] == varied_documents[i].metadata["source"]
            assert doc.metadata["type"] == varied_documents[i].metadata["type"]
        
        # Verify performance metrics
        assert metrics["input_document_count"] == len(varied_documents)
        assert "optimization_duration" in metrics
        assert "documents_per_second" in metrics
        assert metrics["documents_per_second"] >= 0
        
        # Should include adaptive chunking
        assert "adaptive_chunking" in metrics["optimizations_applied"]
        assert "chunk_size" in metrics
        assert "chunk_overlap" in metrics

    @pytest.mark.skipif(not IMPORT_SUCCESS, reason="Failed to import performance_monitor module")
    def test_apply_performance_optimizations_error_scenarios(self, optimization_service):
        """Test performance optimization error handling scenarios."""
        
        # Test with invalid documents (None values)
        with patch.object(optimization_service, 'optimize_chunking_parameters', side_effect=Exception("Mock error")):
            optimized_docs, metrics = optimization_service.apply_performance_optimizations(
                documents=[Document(page_content="test", metadata={})],
                adaptive_chunking=True
            )
            
            # Should handle error gracefully
            assert "error" in metrics
            assert len(optimized_docs) == 1  # Should return original documents

    @pytest.mark.skipif(not IMPORT_SUCCESS, reason="Failed to import performance_monitor module")
    def test_apply_performance_optimizations_with_monitoring_mock(self, optimization_service, varied_documents):
        """Test performance optimization with mocked system monitoring."""
        
        mock_stats = {
            "memory_total_gb": 16.0,
            "memory_available_gb": 8.0,
            "memory_percent": 50.0,
            "cpu_percent": 25.0,
            "cpu_count": 8
        }
        
        with patch.object(optimization_service.performance_monitor, 'get_system_stats', return_value=mock_stats):
            optimized_docs, metrics = optimization_service.apply_performance_optimizations(
                documents=varied_documents,
                enable_monitoring=True
            )
            
            assert "resource_monitoring" in metrics["optimizations_applied"]
            assert metrics["performance_stats"] == mock_stats

    @pytest.mark.skipif(not IMPORT_SUCCESS, reason="Failed to import performance_monitor module")
    def test_analyze_processing_efficiency_comprehensive(self, optimization_service):
        """Test comprehensive processing efficiency analysis."""
        
        # Create diverse operation metrics
        operation_metrics = [
            {
                "operation": "document_loading",
                "duration_seconds": 1.5,
                "document_count": 20,
                "chunk_count": 100,
                "documents_per_second": 13.33
            },
            {
                "operation": "text_processing",
                "duration_seconds": 3.0,
                "document_count": 15,
                "chunk_count": 90,
                "documents_per_second": 5.0
            },
            {
                "operation": "vectorization",
                "duration_seconds": 2.5,
                "document_count": 25,
                "chunk_count": 150,
                "documents_per_second": 10.0
            },
            {
                "operation": "indexing",
                "duration_seconds": 4.0,
                "document_count": 30,
                "chunk_count": 180,
                "documents_per_second": 7.5
            }
        ]
        
        analysis = optimization_service.analyze_processing_efficiency(operation_metrics)
        
        # Verify comprehensive analysis results
        assert analysis["total_operations"] == 4
        assert analysis["total_documents_processed"] == 90
        assert analysis["total_chunks_processed"] == 520
        assert analysis["total_processing_time"] == 11.0
        assert abs(analysis["overall_documents_per_second"] - (90 / 11.0)) < 0.1
        assert abs(analysis["overall_chunks_per_second"] - (520 / 11.0)) < 0.1
        assert analysis["average_operation_duration"] == 2.75
        assert abs(analysis["chunks_per_document_ratio"] - (520 / 90)) < 0.1
        
        # Verify bottleneck identification
        assert "potential_bottlenecks" in analysis
        assert len(analysis["potential_bottlenecks"]) <= 3
        
        # The slowest operation should be identified
        bottlenecks = analysis["potential_bottlenecks"]
        slowest_bottleneck = min(bottlenecks, key=lambda x: x["documents_per_second"])
        assert slowest_bottleneck["operation"] == "text_processing"  # 5.0 docs/sec
        assert slowest_bottleneck["documents_per_second"] == 5.0

    @pytest.mark.skipif(not IMPORT_SUCCESS, reason="Failed to import performance_monitor module")
    def test_analyze_processing_efficiency_edge_cases(self, optimization_service):
        """Test processing efficiency analysis edge cases."""
        
        # Test with metrics containing zero values
        zero_metrics = [
            {
                "operation": "zero_docs",
                "duration_seconds": 1.0,
                "document_count": 0,
                "chunk_count": 0,
                "documents_per_second": 0
            },
            {
                "operation": "zero_duration",
                "duration_seconds": 0.0,
                "document_count": 10,
                "chunk_count": 50,
                "documents_per_second": 0
            }
        ]
        
        analysis = optimization_service.analyze_processing_efficiency(zero_metrics)
        
        # Should handle zero values gracefully
        assert analysis["total_operations"] == 2
        assert analysis["total_documents_processed"] == 10
        assert analysis["total_chunks_processed"] == 50
        assert analysis["total_processing_time"] == 1.0

    @pytest.mark.skipif(not IMPORT_SUCCESS, reason="Failed to import performance_monitor module")
    def test_analyze_processing_efficiency_missing_fields(self, optimization_service):
        """Test processing efficiency analysis with missing fields."""
        
        incomplete_metrics = [
            {
                "operation": "incomplete1",
                "duration_seconds": 2.0,
                # Missing document_count and chunk_count
            },
            {
                "operation": "incomplete2",
                "duration_seconds": 1.5,
                "document_count": 5,
                # Missing chunk_count
            }
        ]
        
        analysis = optimization_service.analyze_processing_efficiency(incomplete_metrics)
        
        # Should handle missing fields gracefully by using defaults (0)
        assert analysis["total_operations"] == 2
        assert analysis["total_documents_processed"] == 5  # Only one has document_count
        assert analysis["total_chunks_processed"] == 0     # Neither has chunk_count
        assert analysis["total_processing_time"] == 3.5

    @pytest.mark.skipif(not IMPORT_SUCCESS, reason="Failed to import performance_monitor module")
    def test_optimization_service_integration_workflow(self, optimization_service):
        """Test complete optimization workflow integration."""
        
        # Create test documents
        test_docs = [
            Document(page_content="Small document for testing.", metadata={"id": 1}),
            Document(page_content="Medium sized document " * 20, metadata={"id": 2}),
            Document(page_content="Large document " * 100, metadata={"id": 3})
        ]
        
        # Step 1: Optimize batch size
        batch_size = optimization_service.optimize_batch_size(
            total_items=len(test_docs),
            available_memory_mb=512
        )
        assert batch_size <= len(test_docs)
        
        # Step 2: Optimize chunking parameters
        chunk_size, overlap = optimization_service.optimize_chunking_parameters(test_docs)
        assert chunk_size > 0
        assert overlap > 0
        
        # Step 3: Apply comprehensive optimizations
        optimized_docs, metrics = optimization_service.apply_performance_optimizations(
            documents=test_docs,
            target_chunk_size=chunk_size,
            chunk_overlap=overlap,
            adaptive_chunking=True,
            enable_monitoring=True
        )
        
        # Verify integration results
        assert len(optimized_docs) == len(test_docs)
        assert metrics["input_document_count"] == len(test_docs)
        assert "adaptive_chunking" in metrics["optimizations_applied"]
        
        # Step 4: Analyze efficiency (simulate operation metrics)
        mock_operation_metrics = [
            {
                "operation": "test_workflow",
                "duration_seconds": metrics["optimization_duration"],
                "document_count": len(test_docs),
                "chunk_count": len(test_docs) * 2,  # Simulate chunk creation
                "documents_per_second": metrics["documents_per_second"]
            }
        ]
        
        efficiency_analysis = optimization_service.analyze_processing_efficiency(mock_operation_metrics)
        assert efficiency_analysis["total_operations"] == 1
        assert efficiency_analysis["total_documents_processed"] == len(test_docs)

    @pytest.mark.skipif(not IMPORT_SUCCESS, reason="Failed to import performance_monitor module")
    def test_optimization_service_performance_monitoring_integration(self, optimization_service):
        """Test integration between OptimizationService and PerformanceMonitor."""
        
        # Verify the performance monitor is properly integrated
        assert isinstance(optimization_service.performance_monitor, PerformanceMonitor)
        
        # Test that system stats are accessible
        with patch.object(optimization_service.performance_monitor, 'get_system_stats') as mock_stats:
            mock_stats.return_value = {"test": "stats"}
            
            stats = optimization_service.performance_monitor.get_system_stats()
            assert stats == {"test": "stats"}
            mock_stats.assert_called_once()

    @pytest.mark.skipif(not IMPORT_SUCCESS, reason="Failed to import performance_monitor module")
    def test_optimization_service_memory_constraints_simulation(self, optimization_service):
        """Test optimization behavior under simulated memory constraints."""
        
        # Simulate low memory scenario - very constrained
        low_memory_batch = optimization_service.optimize_batch_size(
            total_items=1000,
            available_memory_mb=5,  # Very limited memory
            item_size_estimate_bytes=1024 * 1024  # 1MB per item
        )
        
        # Should use minimum batch size due to severe memory constraints
        assert low_memory_batch == 10
        
        # Simulate high memory scenario
        high_memory_batch = optimization_service.optimize_batch_size(
            total_items=100,
            available_memory_mb=16384,  # 16GB
            item_size_estimate_bytes=1024  # 1KB per item
        )
        
        # Should use all items since memory is abundant
        assert high_memory_batch == 100


if __name__ == "__main__":
    # Run the tests using uv as specified in the instructions
    import subprocess
    
    result = subprocess.run([
        "uv", "run", "pytest", __file__, "-v", "--tb=short"
    ], cwd=os.path.dirname(os.path.dirname(__file__)))
    
    if result.returncode == 0:
        print("\n✅ All OptimizationService comprehensive tests passed!")
    else:
        print(f"\n❌ Some tests failed. Exit code: {result.returncode}")
    
    sys.exit(result.returncode)
