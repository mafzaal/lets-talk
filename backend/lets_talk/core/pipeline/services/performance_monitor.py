"""
Performance monitoring and optimization module.

This module provides utilities for monitoring system performance,
resource usage, and optimizing pipeline operations.
"""

import logging
import time
from typing import Any, Dict, List, Tuple

from langchain.schema.document import Document

from lets_talk.shared.config import (
    ADAPTIVE_CHUNKING,
    BATCH_SIZE,
    CHUNK_OVERLAP,
    CHUNK_SIZE,
    ENABLE_PERFORMANCE_MONITORING
)
from ..utils.common_utils import format_duration, format_file_size, handle_exceptions

logger = logging.getLogger(__name__)


class PerformanceMonitor:
    """
    Monitors and tracks performance metrics for pipeline operations.
    """
    
    def __init__(self, enable_monitoring: bool = ENABLE_PERFORMANCE_MONITORING):
        """
        Initialize the performance monitor.
        
        Args:
            enable_monitoring: Whether to enable detailed performance monitoring
        """
        self.enable_monitoring = enable_monitoring
        self.metrics_history = []
    
    @handle_exceptions(default_return={})
    def get_system_stats(self) -> Dict[str, Any]:
        """
        Get current system resource usage statistics.
        
        Returns:
            Dictionary with system stats
        """
        stats = {}
        
        try:
            import psutil
            
            # Memory usage
            memory = psutil.virtual_memory()
            stats["memory_total_gb"] = round(memory.total / (1024**3), 2)
            stats["memory_available_gb"] = round(memory.available / (1024**3), 2)
            stats["memory_percent"] = memory.percent
            
            # CPU usage
            stats["cpu_percent"] = psutil.cpu_percent(interval=1)
            stats["cpu_count"] = psutil.cpu_count()
            
            # Disk usage for current directory
            disk = psutil.disk_usage('.')
            stats["disk_total_gb"] = round(disk.total / (1024**3), 2)
            stats["disk_free_gb"] = round(disk.free / (1024**3), 2)
            stats["disk_percent"] = round((disk.used / disk.total) * 100, 2)
            
        except ImportError:
            # psutil not available, provide basic stats
            stats["memory_info"] = "psutil not available"
        except Exception as e:
            stats["error"] = str(e)
        
        return stats
    
    def monitor_operation(
        self,
        operation: str,
        start_time: float,
        document_count: int = 0,
        chunk_count: int = 0,
        additional_metrics: Dict[str, Any] | None = None
    ) -> Dict[str, Any]:
        """
        Monitor and log performance metrics for an operation.
        
        Args:
            operation: Name of the operation
            start_time: Operation start time (from time.time())
            document_count: Number of documents processed
            chunk_count: Number of chunks processed
            additional_metrics: Additional metrics to include
            
        Returns:
            Performance metrics dictionary
        """
        end_time = time.time()
        duration = end_time - start_time
        
        metrics = {
            "operation": operation,
            "timestamp": end_time,
            "duration_seconds": round(duration, 2),
            "document_count": document_count,
            "chunk_count": chunk_count,
            "documents_per_second": round(document_count / duration, 2) if duration > 0 and document_count > 0 else 0,
            "chunks_per_second": round(chunk_count / duration, 2) if duration > 0 and chunk_count > 0 else 0,
        }
        
        # Add system stats if monitoring is enabled
        if self.enable_monitoring:
            metrics["system_stats"] = self.get_system_stats()
        
        # Add additional metrics
        if additional_metrics:
            metrics.update(additional_metrics)
        
        # Store in history
        self.metrics_history.append(metrics)
        
        # Log performance summary
        logger.info(f"Performance: {operation} completed in {format_duration(duration)} "
                   f"({document_count} docs, {metrics['documents_per_second']:.1f} docs/sec)")
        
        return metrics
    
    def get_metrics_summary(self, operation_filter: str | None = None) -> Dict[str, Any]:
        """
        Get a summary of performance metrics.
        
        Args:
            operation_filter: Filter metrics by operation name
            
        Returns:
            Summary statistics
        """
        if not self.metrics_history:
            return {}
        
        # Filter metrics if requested
        metrics = self.metrics_history
        if operation_filter:
            metrics = [m for m in metrics if m.get("operation") == operation_filter]
        
        if not metrics:
            return {}
        
        # Calculate summary statistics
        durations = [m["duration_seconds"] for m in metrics]
        doc_counts = [m["document_count"] for m in metrics if m["document_count"] > 0]
        doc_rates = [m["documents_per_second"] for m in metrics if m["documents_per_second"] > 0]
        
        summary = {
            "total_operations": len(metrics),
            "total_duration": sum(durations),
            "avg_duration": sum(durations) / len(durations),
            "min_duration": min(durations),
            "max_duration": max(durations),
            "total_documents": sum(doc_counts) if doc_counts else 0,
            "avg_documents_per_operation": sum(doc_counts) / len(doc_counts) if doc_counts else 0,
            "avg_processing_rate": sum(doc_rates) / len(doc_rates) if doc_rates else 0,
            "operations": [m["operation"] for m in metrics]
        }
        
        return summary
    
    def clear_history(self) -> None:
        """Clear the metrics history."""
        self.metrics_history.clear()
        logger.info("Performance metrics history cleared")


class OptimizationService:
    """
    Provides optimization recommendations and automatic tuning.
    """
    
    def __init__(
        self,
        adaptive_chunking: bool = ADAPTIVE_CHUNKING,
        chunk_size: int = CHUNK_SIZE,
        chunk_overlap: int = CHUNK_OVERLAP
    ):
        """
        Initialize the optimization service.
        
        Args:
            adaptive_chunking: Whether to enable adaptive chunking optimization
            chunk_size: Default chunk size for document processing
            chunk_overlap: Default chunk overlap for document processing
        """
        self.performance_monitor = PerformanceMonitor()
        self.adaptive_chunking = adaptive_chunking
        self.chunk_size = chunk_size
        self.chunk_overlap = chunk_overlap
    
    def optimize_batch_size(
        self,
        total_items: int,
        available_memory_mb: int = 1024,
        item_size_estimate_bytes: int = 1024
    ) -> int:
        """
        Estimate optimal batch size based on memory constraints.
        
        Args:
            total_items: Total number of items to process
            available_memory_mb: Available memory in MB
            item_size_estimate_bytes: Estimated size per item in bytes
            
        Returns:
            Recommended batch size
        """
        available_memory_bytes = available_memory_mb * 1024 * 1024
        max_batch_size = available_memory_bytes // item_size_estimate_bytes
        
        # Use reasonable bounds
        min_batch_size = 10
        recommended_max = 1000
        
        batch_size = max(min_batch_size, min(max_batch_size, recommended_max))
        
        # Don't exceed total items
        batch_size = min(batch_size, total_items)
        
        logger.debug(f"Estimated batch size: {batch_size} (memory: {available_memory_mb}MB, "
                    f"item_size: {item_size_estimate_bytes}B)")
        
        return int(batch_size)
    
    def optimize_chunking_parameters(
        self,
        documents: List[Document],
        target_chunk_size: int | None = None,
        chunk_overlap: int | None = None,
        max_chunk_size: int = 2000
    ) -> Tuple[int, int]:
        """
        Optimize chunking parameters based on document characteristics.
        
        Args:
            documents: List of documents to analyze
            target_chunk_size: Target chunk size (uses instance default if None)
            chunk_overlap: Chunk overlap (uses instance default if None)
            max_chunk_size: Maximum allowed chunk size
            
        Returns:
            Tuple of (optimized_chunk_size, optimized_overlap)
        """
        if not documents:
            return (target_chunk_size or self.chunk_size), (chunk_overlap or self.chunk_overlap)
        
        # Use instance defaults if not provided
        target_chunk_size = target_chunk_size or self.chunk_size
        chunk_overlap = chunk_overlap or self.chunk_overlap
        
        # Analyze document lengths
        lengths = [len(doc.page_content) for doc in documents]
        avg_length = sum(lengths) / len(lengths)
        min_length = min(lengths)
        max_length = max(lengths)
        
        logger.info(f"Document analysis: avg={avg_length:.0f}, min={min_length}, max={max_length}")
        
        # Optimize chunk size based on document characteristics
        if avg_length < target_chunk_size:
            # Documents are small, use smaller chunks to avoid over-chunking
            optimized_chunk_size = max(int(avg_length * 0.7), 500)
            optimized_overlap = max(int(optimized_chunk_size * 0.05), 50)
        elif avg_length > max_chunk_size:
            # Documents are large, use larger chunks
            optimized_chunk_size = max_chunk_size
            optimized_overlap = max(int(optimized_chunk_size * 0.1), 100)
        else:
            # Documents are medium-sized, use target size
            optimized_chunk_size = target_chunk_size
            optimized_overlap = max(int(optimized_chunk_size * 0.1), chunk_overlap)
        
        logger.info(f"Optimized chunking: size={optimized_chunk_size}, overlap={optimized_overlap}")
        return optimized_chunk_size, optimized_overlap
    
    def apply_performance_optimizations(
        self,
        documents: List[Document],
        target_chunk_size: int | None = None,
        chunk_overlap: int | None = None,
        adaptive_chunking: bool | None = None,
        enable_monitoring: bool = ENABLE_PERFORMANCE_MONITORING
    ) -> Tuple[List[Document], Dict[str, Any]]:
        """
        Apply comprehensive performance optimizations to documents.
        
        Args:
            documents: List of documents to optimize
            target_chunk_size: Target chunk size for optimization (uses instance default if None)
            chunk_overlap: Chunk overlap for optimization (uses instance default if None)
            adaptive_chunking: Whether to enable adaptive chunking (uses instance default if None)
            enable_monitoring: Whether to enable performance monitoring
            
        Returns:
            Tuple of (optimized_documents, performance_metrics)
        """
        start_time = time.time()
        
        # Use instance defaults if not provided
        target_chunk_size = target_chunk_size or self.chunk_size
        chunk_overlap = chunk_overlap or self.chunk_overlap
        adaptive_chunking = adaptive_chunking if adaptive_chunking is not None else self.adaptive_chunking
        
        performance_metrics = {
            "input_document_count": len(documents),
            "optimizations_applied": [],
            "performance_stats": {}
        }
        
        try:
            # Apply adaptive chunking if enabled
            if adaptive_chunking and documents:
                logger.info("Applying adaptive chunking optimization...")
                optimized_chunk_size, optimized_overlap = self.optimize_chunking_parameters(
                    documents, target_chunk_size, chunk_overlap
                )
                performance_metrics["optimizations_applied"].append("adaptive_chunking")
                performance_metrics["chunk_size"] = optimized_chunk_size
                performance_metrics["chunk_overlap"] = optimized_overlap
            else:
                optimized_chunk_size = target_chunk_size
                optimized_overlap = chunk_overlap
            
            # Monitor system resources if enabled
            if enable_monitoring:
                performance_metrics["performance_stats"] = self.performance_monitor.get_system_stats()
                performance_metrics["optimizations_applied"].append("resource_monitoring")
            
            # Apply document-level optimizations
            optimized_documents = documents.copy()
            
            # Add performance metadata to documents
            for doc in optimized_documents:
                doc.metadata["optimization_applied"] = True
                doc.metadata["optimized_chunk_size"] = optimized_chunk_size
                doc.metadata["optimized_chunk_overlap"] = optimized_overlap
            
            # Calculate performance metrics
            end_time = time.time()
            performance_metrics["optimization_duration"] = round(end_time - start_time, 3)
            performance_metrics["documents_per_second"] = round(
                len(documents) / (end_time - start_time), 2
            ) if end_time > start_time else 0
            
            logger.info(f"Performance optimizations completed in {performance_metrics['optimization_duration']}s")
            logger.info(f"Applied optimizations: {', '.join(performance_metrics['optimizations_applied'])}")
            
            return optimized_documents, performance_metrics
            
        except Exception as e:
            logger.error(f"Error applying performance optimizations: {e}")
            performance_metrics["error"] = str(e)
            return documents, performance_metrics
    
    def analyze_processing_efficiency(
        self,
        operation_metrics: List[Dict[str, Any]]
    ) -> Dict[str, Any]:
        """
        Analyze processing efficiency across multiple operations.
        
        Args:
            operation_metrics: List of operation metrics
            
        Returns:
            Efficiency analysis results
        """
        if not operation_metrics:
            return {}
        
        # Extract key metrics
        total_documents = sum(m.get("document_count", 0) for m in operation_metrics)
        total_chunks = sum(m.get("chunk_count", 0) for m in operation_metrics)
        total_duration = sum(m.get("duration_seconds", 0) for m in operation_metrics)
        
        # Calculate efficiency metrics
        analysis = {
            "total_operations": len(operation_metrics),
            "total_documents_processed": total_documents,
            "total_chunks_processed": total_chunks,
            "total_processing_time": total_duration,
            "overall_documents_per_second": total_documents / total_duration if total_duration > 0 else 0,
            "overall_chunks_per_second": total_chunks / total_duration if total_duration > 0 else 0,
            "average_operation_duration": total_duration / len(operation_metrics),
            "chunks_per_document_ratio": total_chunks / total_documents if total_documents > 0 else 0
        }
        
        # Identify bottlenecks
        slowest_operations = sorted(
            operation_metrics,
            key=lambda x: x.get("documents_per_second", 0)
        )[:3]
        
        analysis["potential_bottlenecks"] = [
            {
                "operation": op.get("operation", "unknown"),
                "duration": op.get("duration_seconds", 0),
                "documents_per_second": op.get("documents_per_second", 0)
            }
            for op in slowest_operations
        ]
        
        return analysis


# Global performance monitor instance
_global_monitor = PerformanceMonitor()


# Convenience functions for backward compatibility
def get_processing_stats() -> Dict[str, Any]:
    """Get system resource usage statistics for performance monitoring."""
    return _global_monitor.get_system_stats()


def monitor_incremental_performance(
    operation: str,
    start_time: float,
    document_count: int,
    chunk_count: int = 0
) -> Dict[str, Any]:
    """Monitor and log performance metrics for incremental operations."""
    return _global_monitor.monitor_operation(operation, start_time, document_count, chunk_count)


def apply_performance_optimizations(
    documents: List[Document],
    target_chunk_size: int = CHUNK_SIZE,
    chunk_overlap: int = CHUNK_OVERLAP,
    adaptive_chunking: bool = ADAPTIVE_CHUNKING,
    enable_monitoring: bool = ENABLE_PERFORMANCE_MONITORING
) -> Tuple[List[Document], Dict[str, Any]]:
    """Apply comprehensive performance optimizations to documents."""
    optimizer = OptimizationService(
        adaptive_chunking=adaptive_chunking,
        chunk_size=target_chunk_size,
        chunk_overlap=chunk_overlap
    )
    return optimizer.apply_performance_optimizations(
        documents, 
        target_chunk_size, 
        chunk_overlap, 
        adaptive_chunking, 
        enable_monitoring
    )
