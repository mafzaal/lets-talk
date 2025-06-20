"""
Common utilities and decorators for the pipeline.

This module contains utility functions and decorators that are used
across multiple pipeline components to reduce code duplication.
"""

import functools
import logging
import time
from typing import Any, Callable, Dict, Optional, Union

logger = logging.getLogger(__name__)


def handle_exceptions(
    default_return: Any = None,
    log_error: bool = True,
    reraise: bool = False
) -> Callable:
    """
    Decorator for consistent error handling across pipeline functions.
    
    Args:
        default_return: Value to return if exception occurs
        log_error: Whether to log the exception
        reraise: Whether to reraise the exception after logging
        
    Returns:
        Decorated function with error handling
    """
    def decorator(func):
        @functools.wraps(func)
        def wrapper(*args, **kwargs):
            try:
                return func(*args, **kwargs)
            except Exception as e:
                if log_error:
                    logger.error(f"Error in {func.__name__}: {e}", exc_info=True)
                if reraise:
                    raise
                return default_return
        return wrapper
    return decorator


def log_execution_time(
    log_level: int = logging.INFO,
    include_args: bool = False
) -> Callable:
    """
    Decorator to log function execution time.
    
    Args:
        log_level: Logging level to use
        include_args: Whether to include function arguments in log
        
    Returns:
        Decorated function with execution timing
    """
    def decorator(func):
        @functools.wraps(func)
        def wrapper(*args, **kwargs):
            start_time = time.time()
            
            # Log function start
            if include_args:
                logger.log(log_level, f"Starting {func.__name__} with args: {args[:2]}...")
            else:
                logger.log(log_level, f"Starting {func.__name__}")
            
            try:
                result = func(*args, **kwargs)
                duration = time.time() - start_time
                logger.log(log_level, f"Completed {func.__name__} in {duration:.2f}s")
                return result
            except Exception as e:
                duration = time.time() - start_time
                logger.error(f"Failed {func.__name__} after {duration:.2f}s: {e}")
                raise
                
        return wrapper
    return decorator


def validate_arguments(**validators) -> Callable:
    """
    Decorator to validate function arguments.
    
    Args:
        **validators: Mapping of argument names to validation functions
        
    Returns:
        Decorated function with argument validation
    """
    def decorator(func):
        @functools.wraps(func)
        def wrapper(*args, **kwargs):
            # Get function signature for argument mapping
            import inspect
            sig = inspect.signature(func)
            bound_args = sig.bind(*args, **kwargs)
            bound_args.apply_defaults()
            
            # Validate arguments
            for arg_name, validator in validators.items():
                if arg_name in bound_args.arguments:
                    value = bound_args.arguments[arg_name]
                    if not validator(value):
                        raise ValueError(f"Invalid value for {arg_name}: {value}")
            
            return func(*args, **kwargs)
        return wrapper
    return decorator


def ensure_list(value: Union[Any, list]) -> list:
    """
    Ensure a value is a list.
    
    Args:
        value: Value to convert to list
        
    Returns:
        List containing the value or the value itself if already a list
    """
    if isinstance(value, list):
        return value
    return [value] if value is not None else []


def safe_int(value: Any, default: int = 0) -> int:
    """
    Safely convert a value to integer.
    
    Args:
        value: Value to convert
        default: Default value if conversion fails
        
    Returns:
        Integer value or default
    """
    try:
        return int(value)
    except (ValueError, TypeError):
        return default


def safe_float(value: Any, default: float = 0.0) -> float:
    """
    Safely convert a value to float.
    
    Args:
        value: Value to convert
        default: Default value if conversion fails
        
    Returns:
        Float value or default
    """
    try:
        return float(value)
    except (ValueError, TypeError):
        return default


def merge_metadata(base: Dict[str, Any], additional: Dict[str, Any]) -> Dict[str, Any]:
    """
    Safely merge metadata dictionaries.
    
    Args:
        base: Base metadata dictionary
        additional: Additional metadata to merge
        
    Returns:
        Merged metadata dictionary
    """
    result = base.copy()
    for key, value in additional.items():
        if key in result and isinstance(result[key], dict) and isinstance(value, dict):
            result[key] = merge_metadata(result[key], value)
        else:
            result[key] = value
    return result


def format_file_size(size_bytes: int) -> str:
    """
    Format file size in human-readable format.
    
    Args:
        size_bytes: Size in bytes
        
    Returns:
        Formatted size string
    """
    size = float(size_bytes)
    for unit in ['B', 'KB', 'MB', 'GB', 'TB']:
        if size < 1024.0:
            return f"{size:.1f} {unit}"
        size /= 1024.0
    return f"{size:.1f} PB"


def format_duration(seconds: float) -> str:
    """
    Format duration in human-readable format.
    
    Args:
        seconds: Duration in seconds
        
    Returns:
        Formatted duration string
    """
    if seconds < 60:
        return f"{seconds:.1f}s"
    elif seconds < 3600:
        minutes = seconds / 60
        return f"{minutes:.1f}m"
    else:
        hours = seconds / 3600
        return f"{hours:.1f}h"


def create_progress_callback(
    total_items: int,
    log_interval: int = 10,
    operation_name: str = "Processing"
) -> Callable[[int], None]:
    """
    Create a progress callback function for long-running operations.
    
    Args:
        total_items: Total number of items to process
        log_interval: Percentage interval for logging progress
        operation_name: Name of the operation for logging
        
    Returns:
        Progress callback function
    """
    start_time = time.time()
    last_logged_percentage = 0
    
    def progress_callback(current_item: int) -> None:
        nonlocal last_logged_percentage
        
        if total_items == 0:
            return
            
        percentage = (current_item / total_items) * 100
        
        # Log progress at specified intervals
        if percentage - last_logged_percentage >= log_interval:
            elapsed_time = time.time() - start_time
            items_per_second = current_item / elapsed_time if elapsed_time > 0 else 0
            estimated_total_time = total_items / items_per_second if items_per_second > 0 else 0
            remaining_time = estimated_total_time - elapsed_time
            
            logger.info(
                f"{operation_name}: {percentage:.1f}% ({current_item}/{total_items}) - "
                f"Rate: {items_per_second:.1f} items/s - "
                f"ETA: {format_duration(remaining_time)}"
            )
            last_logged_percentage = int(percentage / log_interval) * log_interval
    
    return progress_callback
