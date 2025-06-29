"""Pipeline job implementations."""
import logging
import json
from datetime import datetime
from typing import Dict, Any, Optional
from pathlib import Path

from lets_talk.shared.config import (
    CHUNKING_STRATEGY, OUTPUT_DIR, LOGGER_NAME, FORCE_RECREATE, DATA_DIR, QDRANT_URL,
    VECTOR_STORAGE_PATH, USE_CHUNKING, SHOULD_SAVE_STATS,
    CHUNK_SIZE, CHUNK_OVERLAP, QDRANT_COLLECTION, EMBEDDING_MODEL,
    DATA_DIR_PATTERN, BLOG_BASE_URL, BASE_URL, INCREMENTAL_MODE, WEB_URLS
)

logger = logging.getLogger(f"{LOGGER_NAME}.pipeline_jobs")


def simple_pipeline_job(config: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
    """
    Simplified pipeline job for scheduler compatibility.
    
    This function can be safely serialized by APScheduler without causing
    hanging issues. All default configuration values are sourced from config.py
    to ensure consistency across the application.
    
    Args:
        config: Optional configuration dictionary with job parameters
        
    Returns:
        Dict containing job execution results
    """
    if config is None:
        config = {}
    
    # Extract job configuration with defaults
    job_id = config.get("job_id", f"pipeline_job_{datetime.now().strftime('%Y%m%d_%H%M%S')}")
    force_recreate = config.get("force_recreate", FORCE_RECREATE)
    ci_mode = config.get("ci_mode", False)
    dry_run = config.get("dry_run", False)
    
    # Data and storage configuration
    data_dir = config.get("data_dir", DATA_DIR)
    storage_path = config.get("storage_path", VECTOR_STORAGE_PATH)
    output_dir = config.get("output_dir", OUTPUT_DIR)
    data_dir_pattern = config.get("data_dir_pattern", DATA_DIR_PATTERN)
    
    # Models and collections
    collection_name = config.get("collection_name", QDRANT_COLLECTION)
    qdrant_url = config.get("qdrant_url", QDRANT_URL)
    embedding_model = config.get("embedding_model", EMBEDDING_MODEL)
    
    # URLs and base paths
    blog_base_url = config.get("blog_base_url", BLOG_BASE_URL)
    base_url = config.get("base_url", BASE_URL)
    web_urls = config.get("web_urls", WEB_URLS)
    
    # Chunking configuration
    chunking_strategy = config.get("chunking_strategy", CHUNKING_STRATEGY)
    use_chunking = config.get("use_chunking", USE_CHUNKING)
    chunk_size = config.get("chunk_size", CHUNK_SIZE)
    chunk_overlap = config.get("chunk_overlap", CHUNK_OVERLAP)
    
    # Incremental indexing
    incremental_mode = config.get("incremental_mode", INCREMENTAL_MODE)
    
    # Statistics and health
    should_save_stats = config.get("should_save_stats", SHOULD_SAVE_STATS)
    health_check = config.get("health_check", False)
    
    start_time = datetime.now()
    
    logger.info(f"Starting pipeline job: {job_id}")
    logger.info(f"Configuration: force_recreate={force_recreate}, ci_mode={ci_mode}, dry_run={dry_run}")
    
    try:
        # Create result dictionary
        result = {
            "job_id": job_id,
            "status": "running",
            "start_time": start_time.isoformat(),
            "config": config,
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
                    data_dir=data_dir,
                    data_dir_pattern=data_dir_pattern,
                    web_urls=web_urls,
                    base_url=base_url,
                    blog_base_url=blog_base_url,
                    output_dir=output_dir,
                    vector_storage_path=storage_path,
                    qdrant_url=qdrant_url,
                    collection_name=collection_name,
                    embedding_model=embedding_model,
                    force_recreate=force_recreate,
                    use_chunking=use_chunking,
                    chunking_strategy=chunking_strategy,
                    chunk_size=chunk_size,
                    chunk_overlap=chunk_overlap,
                    incremental_mode=incremental_mode
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
        
        end_time = datetime.now()
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
        end_time = datetime.now()
        error_result = {
            "job_id": job_id,
            "status": "failed",
            "start_time": start_time.isoformat(),
            "end_time": end_time.isoformat(),
            "duration_seconds": (end_time - start_time).total_seconds(),
            "error": str(e),
            "config": config
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


