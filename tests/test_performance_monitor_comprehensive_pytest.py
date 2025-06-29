#!/usr/bin/env python3
"""
Simple comprehensive test for PerformanceMonitor.

This test verifies the key functionality of PerformanceMonitor
in a simple, integration-style test.
"""

import os
import sys
import time
import tempfile
import pytest
from pathlib import Path

# Add the backend directory to the path
backend_path = os.path.join(os.path.dirname(__file__), '..', 'backend')
if backend_path not in sys.path:
    sys.path.insert(0, backend_path)

# Import langchain Document first
from langchain.schema.document import Document

# Import the modules to test
from lets_talk.core.pipeline.services.performance_monitor import (
    PerformanceMonitor,
    OptimizationService,
    apply_performance_optimizations
)


def test_performance_monitor_comprehensive():
    """Comprehensive test of PerformanceMonitor functionality."""
    print("Testing PerformanceMonitor comprehensive functionality...")
    
    # Create a performance monitor
    monitor = PerformanceMonitor(enable_monitoring=True)
    
    # Test operation monitoring
    start_time = time.time()
    time.sleep(0.01)  # Simulate some work
    
    metrics = monitor.monitor_operation(
        operation="comprehensive_test",
        start_time=start_time,
        document_count=5,
        chunk_count=25,
        additional_metrics={"test_mode": "comprehensive"}
    )
    
    # Verify metrics
    assert metrics["operation"] == "comprehensive_test"
    assert metrics["document_count"] == 5
    assert metrics["chunk_count"] == 25
    assert metrics["test_mode"] == "comprehensive"
    assert metrics["duration_seconds"] > 0
    assert len(monitor.metrics_history) == 1
    
    # Test metrics summary
    summary = monitor.get_metrics_summary()
    assert summary["total_operations"] == 1
    assert summary["total_documents"] == 5
    
    # Test clear history
    monitor.clear_history()
    assert len(monitor.metrics_history) == 0
    
    print("✓ PerformanceMonitor comprehensive test passed")


def test_optimization_service_comprehensive():
    """Comprehensive test of OptimizationService functionality."""
    print("Testing OptimizationService comprehensive functionality...")
    
    # Create sample documents
    documents = [
        Document(page_content="Short document.", metadata={"source": "doc1.md"}),
        Document(page_content="Medium length document " * 10, metadata={"source": "doc2.md"}),
        Document(page_content="Very long document " * 100, metadata={"source": "doc3.md"}),
    ]
    
    # Create optimization service
    optimizer = OptimizationService(adaptive_chunking=True)
    
    # Test batch size optimization
    batch_size = optimizer.optimize_batch_size(
        total_items=1000,
        available_memory_mb=512,
        item_size_estimate_bytes=1024
    )
    assert 10 <= batch_size <= 1000
    
    # Test chunking optimization
    chunk_size, overlap = optimizer.optimize_chunking_parameters(documents)
    assert chunk_size > 0
    assert overlap > 0
    
    # Test performance optimizations
    optimized_docs, metrics = optimizer.apply_performance_optimizations(
        documents,
        adaptive_chunking=True,
        enable_monitoring=True
    )
    
    assert len(optimized_docs) == len(documents)
    assert metrics["input_document_count"] == len(documents)
    assert "adaptive_chunking" in metrics["optimizations_applied"]
    assert "optimization_duration" in metrics
    
    # Verify documents have optimization metadata
    for doc in optimized_docs:
        assert doc.metadata["optimization_applied"] is True
        assert "optimized_chunk_size" in doc.metadata
    
    print("✓ OptimizationService comprehensive test passed")


def test_global_functions_comprehensive():
    """Test global convenience functions."""
    print("Testing global functions...")
    
    # Create sample documents
    documents = [
        Document(page_content="Test document for global functions.", metadata={"source": "test.md"}),
    ]
    
    # Test global apply_performance_optimizations function
    optimized_docs, metrics = apply_performance_optimizations(
        documents,
        target_chunk_size=1000,
        chunk_overlap=100,
        adaptive_chunking=True,
        enable_monitoring=True
    )
    
    assert len(optimized_docs) == 1
    assert metrics["input_document_count"] == 1
    assert "optimization_duration" in metrics
    
    print("✓ Global functions comprehensive test passed")


def test_error_handling_comprehensive():
    """Test error handling scenarios."""
    print("Testing error handling...")
    
    # Test with empty documents
    optimizer = OptimizationService()
    optimized_docs, metrics = optimizer.apply_performance_optimizations([])
    
    assert len(optimized_docs) == 0
    assert metrics["input_document_count"] == 0
    assert "optimization_duration" in metrics
    
    # Test performance monitor with zero documents
    monitor = PerformanceMonitor()
    start_time = time.time()
    
    metrics = monitor.monitor_operation(
        operation="empty_test",
        start_time=start_time,
        document_count=0
    )
    
    assert metrics["documents_per_second"] == 0
    
    print("✓ Error handling comprehensive test passed")


if __name__ == "__main__":
    print("=" * 60)
    print("Running PerformanceMonitor Comprehensive Tests")
    print("=" * 60)
    
    try:
        test_performance_monitor_comprehensive()
        test_optimization_service_comprehensive()
        test_global_functions_comprehensive()
        test_error_handling_comprehensive()
        
        print("=" * 60)
        print("✅ All comprehensive tests passed!")
        print("=" * 60)
        
    except Exception as e:
        print(f"❌ Test failed: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)
