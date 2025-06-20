"""
Standalone pipeline job function for APScheduler.

This module contains a standalone function that can be properly serialized
by APScheduler for persistent job storage.
"""

import os
import json
import logging
from datetime import datetime
from pathlib import Path
from typing import Dict, Any, Optional

from lets_talk.shared.config import BASE_URL, BLOG_BASE_URL, DATA_DIR_PATTERN, DEFAULT_METADATA_CSV_FILENAME, LOG_LEVEL, LOG_FORMAT, LOGGER_NAME,CHUNK_OVERLAP, CHUNK_SIZE, CHUNKING_STRATEGY, DATA_DIR, EMBEDDING_MODEL, FORCE_RECREATE, OUTPUT_DIR, QDRANT_COLLECTION, SHOULD_SAVE_STATS, USE_CHUNKING, VECTOR_STORAGE_PATH
logger = logging.getLogger(f"{LOGGER_NAME}.scheduler_job")

def pipeline_job_function(job_config: Dict[str, Any]):
    """
    Standalone pipeline job function that can be serialized by APScheduler.
    
    Args:
        job_config: Configuration dictionary for the pipeline job
    """
    # Initialize variables that might be used in error handling
    job_id = job_config.get('job_id', 'unknown')
    
    try:
        
        
        logger.info(f"Starting pipeline job: {job_id}")
        
        # Import configuration constants
        
        # Import pipeline function
        from lets_talk.core.pipeline.engine import run_pipeline
        
        
        # Extract pipeline parameters with defaults
        data_dir = job_config.get('data_dir', DATA_DIR)
        data_dir_pattern = job_config.get('data_dir_pattern', DATA_DIR_PATTERN)
        storage_path = job_config.get('storage_path', VECTOR_STORAGE_PATH)
        force_recreate = job_config.get('force_recreate', FORCE_RECREATE)
        output_dir = job_config.get('output_dir', OUTPUT_DIR)
        ci_mode = job_config.get('ci_mode', False)
        use_chunking = job_config.get('use_chunking', USE_CHUNKING)
        should_save_stats = job_config.get('should_save_stats', SHOULD_SAVE_STATS)
        chunk_size = job_config.get('chunk_size', CHUNK_SIZE)
        chunk_overlap = job_config.get('chunk_overlap', CHUNK_OVERLAP)
        chunking_strategy = job_config.get('chunking_strategy', CHUNKING_STRATEGY)
        collection_name = job_config.get('collection_name', QDRANT_COLLECTION)
        embedding_model = job_config.get('embedding_model', EMBEDDING_MODEL)
        
        blog_base_url = job_config.get('blog_base_url', BLOG_BASE_URL)
        base_url = job_config.get('base_url',BASE_URL)
        incremental_mode = job_config.get('incremental_mode', "auto")
        metadata_csv_path = job_config.get('metadata_csv_path')
        dry_run = job_config.get('dry_run', False)
        
        # Set default metadata CSV path if not provided
        if metadata_csv_path is None:
            metadata_csv_path = os.path.join(output_dir, DEFAULT_METADATA_CSV_FILENAME)
        
        # Execute the pipeline
        success, message, stats, stats_file, stats_content = run_pipeline(
            data_dir=data_dir,
            storage_path=storage_path,
            force_recreate=force_recreate,
            output_dir=output_dir,
            ci_mode=ci_mode,
            use_chunking=use_chunking,
            should_save_stats=should_save_stats,
            chunk_size=chunk_size,
            chunk_overlap=chunk_overlap,
            chunking_strategy=chunking_strategy,
            collection_name=collection_name,
            embedding_model=embedding_model,
            data_dir_pattern=data_dir_pattern,
            blog_base_url=blog_base_url,
            base_url=base_url,
            incremental_mode=incremental_mode
        )
        
        if success:
            logger.info(f"Pipeline job {job_id} completed successfully: {message}")
            if stats and isinstance(stats, dict) and 'total_documents' in stats:
                logger.info(f"Processed {stats.get('total_documents', 0)} documents")
        else:
            logger.error(f"Pipeline job {job_id} failed: {message}")
            raise Exception(message)
        
        # Save job execution report
        _save_job_report(job_id, success, message, stats, stats_file, output_dir)
        
        return {
            'job_id': job_id,
            'success': success,
            'message': message,
            'stats': stats,
            'timestamp': datetime.now().isoformat()
        }
        
    except Exception as e:
        # Use logger if available, otherwise print
        error_msg = f"Pipeline job {job_id} failed with exception: {str(e)}"
        if logger:
            logger.error(error_msg, exc_info=True)
        else:
            print(error_msg)
        
        # Get OUTPUT_DIR safely
        try:
            from lets_talk.shared.config import OUTPUT_DIR as DEFAULT_OUTPUT_DIR
            output_dir = job_config.get('output_dir', DEFAULT_OUTPUT_DIR)
        except ImportError:
            output_dir = job_config.get('output_dir', './output')
        
        _save_job_report(job_id, False, str(e), None, None, output_dir)
        raise


def _save_job_report(job_id: str, success: bool, message: str, 
                    stats: Optional[Dict[str, Any]] = None, stats_file: Optional[str] = None,
                    output_dir: Optional[str] = None):
    """Save a report of job execution."""
    if output_dir is None:
        from lets_talk.shared.config import OUTPUT_DIR
        output_dir = OUTPUT_DIR
        
    report = {
        "job_id": job_id,
        "timestamp": datetime.now().isoformat(),
        "success": success,
        "message": message,
        "stats": stats,
        "stats_file": stats_file
    }
    
    report_file = Path(output_dir) / f"job_report_{job_id}_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
    os.makedirs(output_dir, exist_ok=True)
    
    try:
        with open(report_file, 'w') as f:
            json.dump(report, f, indent=2)
        
        # Set up basic logging if not already configured
        logger = logging.getLogger("pipeline_job")
        logger.info(f"Job report saved: {report_file}")
    except Exception as e:
        print(f"Failed to save job report: {e}")
