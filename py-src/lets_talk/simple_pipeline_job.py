"""
Simplified pipeline job for scheduler compatibility.

This module provides a simplified job function that can be safely serialized
by APScheduler without causing hanging issues. All default configuration values
are sourced from config.py to ensure consistency across the application.

Available Job Configuration Options:
    Basic Configuration:
        - job_id: Identifier for the job (default: 'pipeline_job')
        - force_recreate: Force recreation of vector store (default from config.FORCE_RECREATE)
        - ci_mode: Run in CI mode, no interactive prompts (default: True)
        - dry_run: Show what would be processed without doing it (default: False)
    
    Data and Storage:
        - data_dir: Directory containing blog posts (default from config.DATA_DIR)
        - storage_path: Path to store vector database (default from config.VECTOR_STORAGE_PATH)
        - output_dir: Directory to save stats and artifacts (default from config.OUTPUT_DIR)
        - data_dir_pattern: Glob pattern for blog files (default from config.DATA_DIR_PATTERN)
    
    Models and Collections:
        - collection_name: Qdrant collection name (default from config.QDRANT_COLLECTION)
        - embedding_model: Embedding model to use (default from config.EMBEDDING_MODEL)
    
    URLs and Base Paths:
        - blog_base_url: Base URL for blog posts (default from config.BLOG_BASE_URL)
        - base_url: Base URL for absolute media links (default from config.BASE_URL)
    
    Chunking Configuration:
        - use_chunking: Split documents into chunks (default from config.USE_CHUNKING)
        - chunk_size: Size of each chunk in characters (default from config.CHUNK_SIZE)
        - chunk_overlap: Overlap between chunks (default from config.CHUNK_OVERLAP)
    
    Incremental Indexing:
        - incremental_mode: Mode for incremental indexing (default from config.INCREMENTAL_MODE)
        - auto_detect_changes: Auto-detect changes (default from config.AUTO_DETECT_CHANGES)
        - checksum_algorithm: Algorithm for checksums (default from config.CHECKSUM_ALGORITHM)
        - metadata_csv_path: Custom path for metadata CSV (default: None)
    
    Performance Optimization:
        - batch_size: Batch size for processing (default from config.BATCH_SIZE)
        - enable_batch_processing: Enable batch processing (default from config.ENABLE_BATCH_PROCESSING)
        - enable_performance_monitoring: Enable perf monitoring (default from config.ENABLE_PERFORMANCE_MONITORING)
        - adaptive_chunking: Enable adaptive chunking (default from config.ADAPTIVE_CHUNKING)
        - max_backup_files: Max backup files to keep (default from config.MAX_BACKUP_FILES)
    
    Statistics and Health:
        - should_save_stats: Save document statistics (default from config.SHOULD_SAVE_STATS)
        - health_check: Perform health check (default: False)
        - health_check_only: Only perform health check and exit (default: False)

Usage:
    # Use default configuration
    from lets_talk.simple_pipeline_job import simple_pipeline_job, get_default_job_config
    
    job_config = get_default_job_config()
    simple_pipeline_job(job_config)
    
    # Override specific values
    from lets_talk.simple_pipeline_job import create_job_config
    
    custom_job_config = create_job_config({
        'job_id': 'my_custom_job',
        'force_recreate': True,
        'data_dir': '/path/to/my/data'
    })
    simple_pipeline_job(custom_job_config)
"""

import os
import json
import logging
from datetime import datetime
from pathlib import Path
from typing import Dict, Any, Optional

# Import default configuration values
from lets_talk.config import (
    DATA_DIR, VECTOR_STORAGE_PATH, FORCE_RECREATE, OUTPUT_DIR,
    USE_CHUNKING, SHOULD_SAVE_STATS, CHUNK_SIZE, CHUNK_OVERLAP,
    QDRANT_COLLECTION, EMBEDDING_MODEL, DATA_DIR_PATTERN,
    BLOG_BASE_URL, BASE_URL, DEFAULT_METADATA_CSV_FILENAME,
    BATCH_SIZE, ENABLE_BATCH_PROCESSING, ENABLE_PERFORMANCE_MONITORING,
    ADAPTIVE_CHUNKING, MAX_BACKUP_FILES, CHECKSUM_ALGORITHM,
    INCREMENTAL_MODE, AUTO_DETECT_CHANGES
)

def simple_pipeline_job(job_config: Dict[str, Any]):
    """
    Simplified pipeline job that avoids complex imports and serialization issues.
    
    This job function uses subprocess to call the pipeline to avoid import/serialization
    issues with APScheduler. All default values are sourced from config.py.
    
    Args:
        job_config: Configuration dictionary for the pipeline job
    """
    import subprocess
    import sys
    
    job_id = job_config.get('job_id', 'unknown')
    
    # Set up basic logging
    logging.basicConfig(level=logging.INFO)
    logger = logging.getLogger(f"scheduler_job.{job_id}")
    
    logger.info(f"Starting simplified pipeline job: {job_id}")
    
    try:
        # Build command to run the pipeline in a subprocess
        cmd = [sys.executable, "-m", "lets_talk.pipeline"]
        
        # Add pipeline arguments with defaults from config
        if job_config.get('force_recreate', FORCE_RECREATE):
            cmd.append('--force-recreate')
        
        if job_config.get('ci_mode', True):  # Default to CI mode for scheduled jobs
            cmd.append('--ci')
        
        if job_config.get('dry_run', False):
            cmd.append('--dry-run')
        
        # Incremental mode configuration
        incremental_mode = job_config.get('incremental_mode', INCREMENTAL_MODE)
        if incremental_mode != 'auto':  # Only add if not default
            if incremental_mode == 'incremental':
                cmd.append('--incremental')
            elif incremental_mode == 'full':
                pass  # Default behavior, no flag needed
            elif incremental_mode == 'incremental_only':
                cmd.append('--incremental-only')
            elif incremental_mode == 'incremental_with_fallback':
                cmd.append('--incremental-with-fallback')
        elif job_config.get('auto_detect_changes', AUTO_DETECT_CHANGES):
            cmd.append('--auto-incremental')
        
        # Data and storage configuration
        data_dir = job_config.get('data_dir', DATA_DIR)
        if data_dir != DATA_DIR:
            cmd.extend(['--data-dir', data_dir])
        
        storage_path = job_config.get('storage_path', VECTOR_STORAGE_PATH)
        if storage_path and storage_path != VECTOR_STORAGE_PATH:
            cmd.extend(['--vector-storage-path', storage_path])
        
        output_dir = job_config.get('output_dir', OUTPUT_DIR)
        if output_dir != OUTPUT_DIR:
            cmd.extend(['--output-dir', output_dir])
        
        # Collection and model configuration
        collection_name = job_config.get('collection_name', QDRANT_COLLECTION)
        if collection_name != QDRANT_COLLECTION:
            cmd.extend(['--collection-name', collection_name])
        
        embedding_model = job_config.get('embedding_model', EMBEDDING_MODEL)
        if embedding_model != EMBEDDING_MODEL:
            cmd.extend(['--embedding-model', embedding_model])
        
        # Data pattern configuration
        data_dir_pattern = job_config.get('data_dir_pattern', DATA_DIR_PATTERN)
        if data_dir_pattern != DATA_DIR_PATTERN:
            cmd.extend(['--data-dir-pattern', data_dir_pattern])
        
        # URL configuration
        blog_base_url = job_config.get('blog_base_url', BLOG_BASE_URL)
        if blog_base_url and blog_base_url != BLOG_BASE_URL:
            cmd.extend(['--blog-base-url', blog_base_url])
        
        base_url = job_config.get('base_url', BASE_URL)
        if base_url and base_url != BASE_URL:
            cmd.extend(['--base-url', base_url])
        
        # Chunking configuration
        if not job_config.get('use_chunking', USE_CHUNKING):
            cmd.append('--no-chunking')
        
        chunk_size = job_config.get('chunk_size', CHUNK_SIZE)
        if chunk_size != CHUNK_SIZE:
            cmd.extend(['--chunk-size', str(chunk_size)])
        
        chunk_overlap = job_config.get('chunk_overlap', CHUNK_OVERLAP)
        if chunk_overlap != CHUNK_OVERLAP:
            cmd.extend(['--chunk-overlap', str(chunk_overlap)])
        
        # Statistics configuration
        if not job_config.get('should_save_stats', SHOULD_SAVE_STATS):
            cmd.append('--no-save-stats')
        
        # Performance optimization configuration
        batch_size = job_config.get('batch_size', BATCH_SIZE)
        if batch_size != BATCH_SIZE:
            cmd.extend(['--batch-size', str(batch_size)])
        
        if not job_config.get('enable_batch_processing', ENABLE_BATCH_PROCESSING):
            cmd.append('--disable-batch-processing')
        
        if not job_config.get('enable_performance_monitoring', ENABLE_PERFORMANCE_MONITORING):
            cmd.append('--disable-performance-monitoring')
        
        if not job_config.get('adaptive_chunking', ADAPTIVE_CHUNKING):
            cmd.append('--disable-adaptive-chunking')
        
        max_backup_files = job_config.get('max_backup_files', MAX_BACKUP_FILES)
        if max_backup_files != MAX_BACKUP_FILES:
            cmd.extend(['--max-backup-files', str(max_backup_files)])
        
        # Checksum algorithm configuration
        checksum_algorithm = job_config.get('checksum_algorithm', CHECKSUM_ALGORITHM)
        if checksum_algorithm != CHECKSUM_ALGORITHM:
            cmd.extend(['--checksum-algorithm', checksum_algorithm])
        
        # Metadata file configuration
        metadata_csv_path = job_config.get('metadata_csv_path')
        if metadata_csv_path:
            cmd.extend(['--metadata-file', metadata_csv_path])
        
        # Health check configuration
        if job_config.get('health_check', False):
            cmd.append('--health-check')
        
        if job_config.get('health_check_only', False):
            cmd.append('--health-check-only')
        
        # Run the pipeline in a subprocess
        logger.info(f"Executing pipeline command: {' '.join(cmd)}")
        
        result = subprocess.run(
            cmd,
            capture_output=True,
            text=True,
            timeout=3600,  # 1 hour timeout
            cwd=os.getcwd()
        )
        
        if result.returncode == 0:
            logger.info(f"Pipeline job {job_id} completed successfully")
            logger.info(f"Output: {result.stdout}")
            
            # Save job report
            _save_simple_job_report(job_id, True, "Pipeline completed successfully", result.stdout)
            return "success"
        else:
            error_msg = f"Pipeline failed with return code {result.returncode}"
            logger.error(f"Pipeline job {job_id} failed: {error_msg}")
            logger.error(f"Error output: {result.stderr}")
            
            # Save job report
            _save_simple_job_report(job_id, False, error_msg, result.stderr)
            raise Exception(error_msg)
            
    except subprocess.TimeoutExpired:
        error_msg = "Pipeline job timed out after 1 hour"
        logger.error(f"Pipeline job {job_id} timed out")
        _save_simple_job_report(job_id, False, error_msg, "")
        raise Exception(error_msg)
        
    except Exception as e:
        error_msg = f"Pipeline job failed with exception: {str(e)}"
        logger.error(error_msg)
        _save_simple_job_report(job_id, False, error_msg, "")
        raise


def _save_simple_job_report(job_id: str, success: bool, message: str, output: str):
    """Save a simple job execution report using default OUTPUT_DIR from config."""
    try:
        # Use OUTPUT_DIR from config as default
        output_dir = os.environ.get('OUTPUT_DIR', OUTPUT_DIR)
        os.makedirs(output_dir, exist_ok=True)
        
        report = {
            "job_id": job_id,
            "timestamp": datetime.now().isoformat(),
            "success": success,
            "message": message,
            "output": output[:1000] if output else ""  # Limit output size
        }
        
        report_file = Path(output_dir) / f"job_report_{job_id}_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
        
        with open(report_file, 'w') as f:
            json.dump(report, f, indent=2)
        
        print(f"Job report saved: {report_file}")
        
    except Exception as e:
        print(f"Failed to save job report: {e}")


def get_default_job_config() -> Dict[str, Any]:
    """
    Get default job configuration values from config.py.
    
    This function provides a comprehensive set of default values that can be used
    to create pipeline job configurations. Users can override any of these values
    by providing them in their job_config dictionary.
    
    Returns:
        Dictionary with default configuration values for pipeline jobs
    """
    return {
        # Job identification
        'job_id': 'pipeline_job',
        
        # Basic pipeline configuration
        'force_recreate': FORCE_RECREATE,
        'ci_mode': True,  # Default to CI mode for scheduled jobs
        'dry_run': False,
        
        # Data and storage paths
        'data_dir': DATA_DIR,
        'storage_path': VECTOR_STORAGE_PATH,
        'output_dir': OUTPUT_DIR,
        
        # Collection and model configuration
        'collection_name': QDRANT_COLLECTION,
        'embedding_model': EMBEDDING_MODEL,
        
        # Data processing configuration
        'data_dir_pattern': DATA_DIR_PATTERN,
        'blog_base_url': BLOG_BASE_URL,
        'base_url': BASE_URL,
        
        # Chunking configuration
        'use_chunking': USE_CHUNKING,
        'chunk_size': CHUNK_SIZE,
        'chunk_overlap': CHUNK_OVERLAP,
        
        # Statistics configuration
        'should_save_stats': SHOULD_SAVE_STATS,
        
        # Incremental indexing configuration
        'incremental_mode': INCREMENTAL_MODE,
        'auto_detect_changes': AUTO_DETECT_CHANGES,
        'checksum_algorithm': CHECKSUM_ALGORITHM,
        'metadata_csv_path': None,  # Will use default path if None
        
        # Performance optimization configuration
        'batch_size': BATCH_SIZE,
        'enable_batch_processing': ENABLE_BATCH_PROCESSING,
        'enable_performance_monitoring': ENABLE_PERFORMANCE_MONITORING,
        'adaptive_chunking': ADAPTIVE_CHUNKING,
        'max_backup_files': MAX_BACKUP_FILES,
        
        # Health check configuration
        'health_check': False,
        'health_check_only': False,
    }


def create_job_config(custom_config: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
    """
    Create a job configuration by merging custom values with defaults.
    
    This function takes a custom configuration dictionary and merges it with
    the default values from config.py, allowing users to override only the
    values they need to change.
    
    Args:
        custom_config: Custom configuration values to override defaults
        
    Returns:
        Complete job configuration dictionary
    """
    # Start with defaults
    job_config = get_default_job_config()
    
    # Merge custom configuration if provided
    if custom_config:
        job_config.update(custom_config)
    
    return job_config
