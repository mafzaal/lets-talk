"""
Batch processing utilities for pipeline operations.

This module provides utilities for processing large datasets in batches
to improve performance and memory usage.
"""

import logging
import time
from typing import Any, Callable, Generator, List, TypeVar

from .common_utils import log_execution_time, handle_exceptions, create_progress_callback

# Type variable for batch items
T = TypeVar('T')

logger = logging.getLogger(__name__)


class BatchProcessor:
    """
    A utility class for processing items in batches with progress tracking
    and error handling.
    """
    
    def __init__(
        self,
        batch_size: int = 50,
        pause_between_batches: float = 0.0,
        enable_progress_logging: bool = True,
        log_interval: int = 10
    ):
        """
        Initialize the batch processor.
        
        Args:
            batch_size: Number of items per batch
            pause_between_batches: Seconds to pause between batches
            enable_progress_logging: Whether to log progress
            log_interval: Percentage interval for progress logging
        """
        self.batch_size = batch_size
        self.pause_between_batches = pause_between_batches
        self.enable_progress_logging = enable_progress_logging
        self.log_interval = log_interval
    
    def create_batches(self, items: List[T]) -> Generator[List[T], None, None]:
        """
        Split items into batches.
        
        Args:
            items: List of items to batch
            
        Yields:
            Batches of items
        """
        if not items:
            return
        
        for i in range(0, len(items), self.batch_size):
            batch = items[i:i + self.batch_size]
            yield batch
    
    @handle_exceptions(default_return=False)
    @log_execution_time()
    def process_batches(
        self,
        items: List[T],
        processor_func: Callable[[List[T]], bool],
        operation_name: str = "Batch processing"
    ) -> bool:
        """
        Process items in batches with progress tracking.
        
        Args:
            items: List of items to process
            processor_func: Function to process each batch
            operation_name: Name of the operation for logging
            
        Returns:
            True if all batches processed successfully, False otherwise
        """
        if not items:
            logger.info(f"{operation_name}: No items to process")
            return True
        
        batches = list(self.create_batches(items))
        total_batches = len(batches)
        
        logger.info(f"{operation_name}: Processing {len(items)} items in {total_batches} batches")
        
        # Create progress callback if logging is enabled
        progress_callback = None
        if self.enable_progress_logging:
            progress_callback = create_progress_callback(
                total_batches, self.log_interval, operation_name
            )
        
        processed_items = 0
        for i, batch in enumerate(batches):
            try:
                # Process the batch
                success = processor_func(batch)
                if not success:
                    logger.error(f"{operation_name}: Failed to process batch {i+1}/{total_batches}")
                    return False
                
                processed_items += len(batch)
                
                # Update progress
                if progress_callback:
                    progress_callback(i + 1)
                
                # Pause between batches if configured
                if self.pause_between_batches > 0 and i < total_batches - 1:
                    time.sleep(self.pause_between_batches)
                    
            except Exception as e:
                logger.error(f"{operation_name}: Error processing batch {i+1}/{total_batches}: {e}")
                return False
        
        logger.info(f"{operation_name}: Successfully processed {processed_items} items in {total_batches} batches")
        return True


def batch_process_items(
    items: List[T],
    processor_func: Callable[[List[T]], bool],
    batch_size: int = 50,
    pause_between_batches: float = 0.0,
    operation_name: str = "Processing"
) -> bool:
    """
    Convenience function for batch processing with default settings.
    
    Args:
        items: List of items to process
        processor_func: Function to process each batch
        batch_size: Number of items per batch
        pause_between_batches: Seconds to pause between batches
        operation_name: Name of the operation for logging
        
    Returns:
        True if all batches processed successfully, False otherwise
    """
    processor = BatchProcessor(
        batch_size=batch_size,
        pause_between_batches=pause_between_batches
    )
    return processor.process_batches(items, processor_func, operation_name)


def chunk_list(items: List[T], chunk_size: int) -> List[List[T]]:
    """
    Split a list into chunks of specified size.
    
    Args:
        items: List to split
        chunk_size: Size of each chunk
        
    Returns:
        List of chunks
    """
    if chunk_size <= 0:
        raise ValueError("Chunk size must be positive")
    
    chunks = []
    for i in range(0, len(items), chunk_size):
        chunk = items[i:i + chunk_size]
        chunks.append(chunk)
    
    return chunks


def estimate_batch_size(
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


class ParallelBatchProcessor:
    """
    A batch processor that can handle parallel processing of batches.
    Note: This is a placeholder for future parallel processing implementation.
    """
    
    def __init__(self, max_workers: int = 4, **kwargs):
        """
        Initialize the parallel batch processor.
        
        Args:
            max_workers: Maximum number of worker threads/processes
            **kwargs: Additional arguments passed to BatchProcessor
        """
        self.max_workers = max_workers
        self.sequential_processor = BatchProcessor(**kwargs)
        logger.warning("Parallel processing not yet implemented, falling back to sequential")
    
    def process_batches(self, items: List[T], processor_func: Callable[[List[T]], bool], 
                       operation_name: str = "Parallel batch processing") -> bool:
        """
        Process items in parallel batches.
        
        Currently falls back to sequential processing.
        
        Args:
            items: List of items to process
            processor_func: Function to process each batch
            operation_name: Name of the operation for logging
            
        Returns:
            True if all batches processed successfully, False otherwise
        """
        logger.info(f"Using sequential processing for {operation_name}")
        return self.sequential_processor.process_batches(items, processor_func, operation_name)
