"""Pipeline job implementations."""
import logging
import json
from datetime import datetime, timezone
from typing import Dict, Any, Optional
from pathlib import Path

from lets_talk.shared.config import (
    CHUNKING_STRATEGY, OUTPUT_DIR, LOGGER_NAME, FORCE_RECREATE, DATA_DIR, QDRANT_URL,
    VECTOR_STORAGE_PATH, USE_CHUNKING, SHOULD_SAVE_STATS,
    CHUNK_SIZE, CHUNK_OVERLAP, QDRANT_COLLECTION, EMBEDDING_MODEL,
    DATA_DIR_PATTERN, BLOG_BASE_URL, BASE_URL, INCREMENTAL_MODE, WEB_URLS,
    INDEX_ONLY_PUBLISHED_POSTS, ADAPTIVE_CHUNKING,
    SEMANTIC_CHUNKER_BREAKPOINT_TYPE, SEMANTIC_CHUNKER_BREAKPOINT_THRESHOLD_AMOUNT,
    SEMANTIC_CHUNKER_MIN_CHUNK_SIZE, CHECKSUM_ALGORITHM, AUTO_DETECT_CHANGES,
    INCREMENTAL_FALLBACK_THRESHOLD, ENABLE_BATCH_PROCESSING, BATCH_SIZE,
    ENABLE_PERFORMANCE_MONITORING, BATCH_PAUSE_SECONDS, MAX_CONCURRENT_OPERATIONS,
    MAX_BACKUP_FILES, METADATA_CSV_FILE, BLOG_STATS_FILENAME, BLOG_DOCS_FILENAME,
    HEALTH_REPORT_FILENAME, CI_SUMMARY_FILENAME, BUILD_INFO_FILENAME
)
from lets_talk.api.models.common import JobConfig

logger = logging.getLogger(f"{LOGGER_NAME}.pipeline_jobs")


def simple_pipeline_job(job_config: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
    """
    Simplified pipeline job for scheduler compatibility.
    
    This function can be safely serialized by APScheduler without causing
    hanging issues. All default configuration values are sourced from config.py
    to ensure consistency across the application.
    
    Args:
        job_config: Optional configuration dictionary with job parameters
        
    Returns:
        Dict containing job execution results
    """
    if job_config is None:
        job_config = {}
    
    # Create a mapping of JobConfig fields to their default values from config.py
    default_values = {
        'data_dir': DATA_DIR,
        'data_dir_pattern': DATA_DIR_PATTERN,
        'web_urls': WEB_URLS,
        'base_url': BASE_URL,
        'blog_base_url': BLOG_BASE_URL,
        'index_only_published_posts': INDEX_ONLY_PUBLISHED_POSTS,
        'use_chunking': USE_CHUNKING,
        'chunking_strategy': CHUNKING_STRATEGY,
        'adaptive_chunking': ADAPTIVE_CHUNKING,
        'chunk_size': CHUNK_SIZE,
        'chunk_overlap': CHUNK_OVERLAP,
        'semantic_breakpoint_type': SEMANTIC_CHUNKER_BREAKPOINT_TYPE,
        'semantic_breakpoint_threshold_amount': SEMANTIC_CHUNKER_BREAKPOINT_THRESHOLD_AMOUNT,
        'semantic_min_chunk_size': SEMANTIC_CHUNKER_MIN_CHUNK_SIZE,
        'collection_name': QDRANT_COLLECTION,
        'embedding_model': EMBEDDING_MODEL,
        'force_recreate': FORCE_RECREATE,
        'incremental_mode': INCREMENTAL_MODE,
        'checksum_algorithm': CHECKSUM_ALGORITHM,
        'auto_detect_changes': AUTO_DETECT_CHANGES,
        'incremental_fallback_threshold': INCREMENTAL_FALLBACK_THRESHOLD,
        'enable_batch_processing': ENABLE_BATCH_PROCESSING,
        'batch_size': BATCH_SIZE,
        'enbable_performance_monitoring': ENABLE_PERFORMANCE_MONITORING,  # Note: typo preserved
        'batch_pause_seconds': BATCH_PAUSE_SECONDS,
        'max_concurrent_operations': MAX_CONCURRENT_OPERATIONS,
        'max_backup_files': MAX_BACKUP_FILES,
        'metadata_csv': METADATA_CSV_FILE,
        'blog_stats_filename': BLOG_STATS_FILENAME,
        'blog_docs_filename': BLOG_DOCS_FILENAME,
        'health_report_filename': HEALTH_REPORT_FILENAME,
        'ci_summary_filename': CI_SUMMARY_FILENAME,
        'build_info_filename': BUILD_INFO_FILENAME,
    }
    
    # Create a complete job_config with defaults applied
    final_job_config = {}
    for field_name in JobConfig.__annotations__.keys():
        if field_name not in job_config:
            # Use default from config.py
            final_job_config[field_name] = default_values.get(field_name)
        else:
            # Use provided value
            final_job_config[field_name] = job_config[field_name]
    
    # Extract additional configuration parameters for backwards compatibility
    job_id = job_config.get("job_id", f"pipeline_job_{datetime.now(timezone.utc).strftime('%Y%m%d_%H%M%S')}")
    ci_mode = job_config.get("ci_mode", False)
    dry_run = job_config.get("dry_run", False)
    
    # Additional configuration not in JobConfig but needed for pipeline execution
    storage_path = job_config.get("storage_path", VECTOR_STORAGE_PATH)
    output_dir = job_config.get("output_dir", OUTPUT_DIR)
    qdrant_url = job_config.get("qdrant_url", QDRANT_URL)
    should_save_stats = job_config.get("should_save_stats", SHOULD_SAVE_STATS)
    health_check = job_config.get("health_check", False)
    start_time = datetime.now(timezone.utc)
    
    logger.info(f"Starting pipeline job: {job_id}")
    logger.info(f"Configuration: force_recreate={final_job_config['force_recreate']}, ci_mode={ci_mode}, dry_run={dry_run}")
    
    try:
        # Create result dictionary
        result = {
            "job_id": job_id,
            "status": "running",
            "start_time": start_time.isoformat(),
            "config": final_job_config,
            "steps_completed": [],
            "artifacts": []
        }
        
        if dry_run:
            logger.info("Dry run mode - simulating pipeline execution")
            result["status"] = "completed_dry_run"
            result["message"] = "Dry run completed successfully"
            result["steps_completed"] = ["validation", "config_check", "dry_run_simulation"]
        elif health_check:
            logger.info("Performing health check")
            result["status"] = "completed_health_check"
            result["message"] = "Health check completed successfully"
            result["steps_completed"] = ["health_check"]
        else:
            # Actual pipeline execution
            logger.info("Executing pipeline with actual processing")
            
            # Import pipeline here to avoid circular imports
            try:
                from lets_talk.core.pipeline.engine import run_pipeline
                
                # Execute the pipeline with proper parameters
                pipeline_result = run_pipeline(
                    job_id=job_id,
                    data_dir=final_job_config['data_dir'],
                    data_dir_pattern=final_job_config['data_dir_pattern'],
                    web_urls=final_job_config['web_urls'],
                    base_url=final_job_config['base_url'],
                    blog_base_url=final_job_config['blog_base_url'],
                    output_dir=output_dir,
                    vector_storage_path=storage_path,
                    qdrant_url=qdrant_url,
                    collection_name=final_job_config['collection_name'],
                    embedding_model=final_job_config['embedding_model'],
                    force_recreate=final_job_config['force_recreate'],
                    use_chunking=final_job_config['use_chunking'],
                    chunking_strategy=final_job_config['chunking_strategy'],
                    chunk_size=final_job_config['chunk_size'],
                    chunk_overlap=final_job_config['chunk_overlap'],
                    incremental_mode=final_job_config['incremental_mode']
                )
                
                # Update result with pipeline execution results
                if pipeline_result.get('success', False):
                    result["status"] = "completed"
                    result["message"] = pipeline_result.get('message', 'Pipeline completed successfully')
                    result["steps_completed"] = ["data_loading", "processing", "indexing", "health_check"]
                    
                    # Add pipeline-specific metrics
                    if 'documents_processed' in pipeline_result:
                        result["documents_processed"] = pipeline_result['documents_processed']
                    if 'chunks_created' in pipeline_result:
                        result["chunks_created"] = pipeline_result['chunks_created']
                    if 'mode' in pipeline_result:
                        result["processing_mode"] = pipeline_result['mode']
                    if 'health_check' in pipeline_result:
                        result["health_check"] = pipeline_result['health_check']
                    if 'performance_metrics' in pipeline_result:
                        result["performance_metrics"] = pipeline_result['performance_metrics']
                else:
                    result["status"] = "failed"
                    result["message"] = pipeline_result.get('message', 'Pipeline execution failed')
                    result["errors"] = pipeline_result.get('errors', ['Unknown pipeline error'])
                
                # Include full pipeline result for debugging
                result["pipeline_result"] = pipeline_result
                
            except ImportError as e:
                logger.error(f"Pipeline engine not available: {e}")
                result["status"] = "failed"
                result["message"] = f"Pipeline engine import failed: {e}"
                result["errors"] = [f"ImportError: {e}"]
            except Exception as e:
                logger.error(f"Pipeline execution failed: {e}")
                result["status"] = "failed"
                result["message"] = f"Pipeline execution failed: {e}"
                result["errors"] = [str(e)]
        
        end_time = datetime.now(timezone.utc)
        result["end_time"] = end_time.isoformat()
        result["duration_seconds"] = (end_time - start_time).total_seconds()
        
        # Save job report
        if should_save_stats:
            report_filename = f"job_report_{job_id}_{start_time.strftime('%Y%m%d_%H%M%S')}.json"
            report_path = Path(output_dir) / report_filename
            report_path.parent.mkdir(parents=True, exist_ok=True)
            
            with open(report_path, 'w') as f:
                json.dump(result, f, indent=2)
            
            result["artifacts"].append(str(report_path))
            logger.info(f"Job report saved to: {report_path}")
        
        logger.info(f"Pipeline job completed successfully: {job_id}")
        return result
        
    except Exception as e:
        end_time = datetime.now(timezone.utc)
        error_result = {
            "job_id": job_id,
            "status": "failed",
            "start_time": start_time.isoformat(),
            "end_time": end_time.isoformat(),
            "duration_seconds": (end_time - start_time).total_seconds(),
            "error": str(e),
            "config": final_job_config
        }
        
        logger.error(f"Pipeline job failed: {job_id}, error: {e}")
        
        # Save error report
        if should_save_stats:
            error_report_filename = f"job_error_{job_id}_{start_time.strftime('%Y%m%d_%H%M%S')}.json"
            error_report_path = Path(output_dir) / error_report_filename
            error_report_path.parent.mkdir(parents=True, exist_ok=True)
            
            with open(error_report_path, 'w') as f:
                json.dump(error_result, f, indent=2)
            
            logger.info(f"Error report saved to: {error_report_path}")
        
        raise  # Re-raise to let scheduler handle the error


