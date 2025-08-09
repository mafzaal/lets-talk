"""Main pipeline engine for data processing."""
import logging
import os
import time
from pathlib import Path
from typing import Dict, Any, Optional, List
from datetime import datetime, timezone

from lets_talk.core.pipeline.processors import PipelineProcessor
from lets_talk.shared.config import (
    QDRANT_URL, ChunkingStrategy, SemanticChunkerBreakpointType,
    DATA_DIR, DATA_DIR_PATTERN, WEB_URLS, BASE_URL, BLOG_BASE_URL,
    INDEX_ONLY_PUBLISHED_POSTS, OUTPUT_DIR, STATS_OUTPUT_DIR,
    USE_CHUNKING, CHUNKING_STRATEGY, ADAPTIVE_CHUNKING, CHUNK_SIZE,
    CHUNK_OVERLAP, SEMANTIC_CHUNKER_BREAKPOINT_TYPE,
    SEMANTIC_CHUNKER_BREAKPOINT_THRESHOLD_AMOUNT, SEMANTIC_CHUNKER_MIN_CHUNK_SIZE,
    VECTOR_STORAGE_PATH, QDRANT_COLLECTION, FORCE_RECREATE, EMBEDDING_MODEL,
    INCREMENTAL_MODE, CHECKSUM_ALGORITHM, AUTO_DETECT_CHANGES,
    INCREMENTAL_FALLBACK_THRESHOLD, ENABLE_BATCH_PROCESSING, BATCH_SIZE,
    ENABLE_PERFORMANCE_MONITORING, BATCH_PAUSE_SECONDS, MAX_CONCURRENT_OPERATIONS,
    MAX_BACKUP_FILES, METADATA_CSV_FILE, BLOG_STATS_FILENAME, BLOG_DOCS_FILENAME,
    HEALTH_REPORT_FILENAME, CI_SUMMARY_FILENAME, BUILD_INFO_FILENAME
)


logger = logging.getLogger(__name__)


def run_pipeline(
    data_dir: str = DATA_DIR,
    data_dir_pattern: str = DATA_DIR_PATTERN,
    web_urls: List[str] = WEB_URLS,
    base_url: str = BASE_URL,
    blog_base_url: str = BLOG_BASE_URL,
    index_only_published_posts: bool = INDEX_ONLY_PUBLISHED_POSTS,
    output_dir: str = OUTPUT_DIR,
    stats_output_dir: str = STATS_OUTPUT_DIR,
    use_chunking: bool = USE_CHUNKING,
    chunking_strategy: ChunkingStrategy = CHUNKING_STRATEGY,
    adaptive_chunking: bool = ADAPTIVE_CHUNKING,
    chunk_size: int = CHUNK_SIZE,
    chunk_overlap: int = CHUNK_OVERLAP,
    semantic_breakpoint_type: SemanticChunkerBreakpointType = SEMANTIC_CHUNKER_BREAKPOINT_TYPE,
    semantic_breakpoint_threshold_amount: float = SEMANTIC_CHUNKER_BREAKPOINT_THRESHOLD_AMOUNT,
    semantic_min_chunk_size: int = SEMANTIC_CHUNKER_MIN_CHUNK_SIZE,
    vector_storage_path: str = VECTOR_STORAGE_PATH,
    qdrant_url: str = QDRANT_URL,
    collection_name: str = QDRANT_COLLECTION,
    embedding_model: str = EMBEDDING_MODEL,
    force_recreate: bool = FORCE_RECREATE,
    incremental_mode: str = INCREMENTAL_MODE,
    checksum_algorithm: str = CHECKSUM_ALGORITHM,
    auto_detect_changes: bool = AUTO_DETECT_CHANGES,
    incremental_fallback_threshold: float = INCREMENTAL_FALLBACK_THRESHOLD,
    enable_batch_processing: bool = ENABLE_BATCH_PROCESSING,
    batch_size: int = BATCH_SIZE,
    enbable_performance_monitoring: bool = ENABLE_PERFORMANCE_MONITORING,
    batch_pause_seconds: float = BATCH_PAUSE_SECONDS,
    max_concurrent_operations: int = MAX_CONCURRENT_OPERATIONS,
    max_backup_files: int = MAX_BACKUP_FILES,
    metadata_csv: str = METADATA_CSV_FILE,
    blog_stats_filename: str = BLOG_STATS_FILENAME,
    blog_docs_filename: str = BLOG_DOCS_FILENAME,
    health_report_filename: str = HEALTH_REPORT_FILENAME,
    ci_summary_filename: str = CI_SUMMARY_FILENAME,
    build_info_filename: str = BUILD_INFO_FILENAME,
    job_id: Optional[str] = None,  # Job ID for tracking pipeline execution
) -> Dict[str, Any]:
    """
    Run the main data processing pipeline using PipelineProcessor.
    
    This function orchestrates the entire pipeline process by delegating to
    PipelineProcessor which handles all the details internally.
    
    Args:
        data_dir: Directory containing source documents
        data_dir_pattern: Pattern for matching files in data_dir
        web_urls: List of web URLs to process
        base_url: Base URL for media links
        blog_base_url: Base URL for blog posts
        index_only_published_posts: Whether to index only published posts
        output_dir: Directory for outputs and reports
        stats_output_dir: Directory for statistics and artifacts
        use_chunking: Whether to chunk documents
        chunking_strategy: Strategy for chunking (ChunkingStrategy.SEMANTIC or ChunkingStrategy.TEXT_SPLITTER)
        adaptive_chunking: Whether to use adaptive chunking
        chunk_size: Size of document chunks
        chunk_overlap: Overlap between chunks
        semantic_breakpoint_type: Type of breakpoint for semantic chunking
        semantic_breakpoint_threshold_amount: Threshold amount for semantic chunking
        semantic_min_chunk_size: Minimum chunk size for semantic chunking
        vector_storage_path: Path for vector store storage
        qdrant_url: URL for Qdrant vector database
        collection_name: Name of the vector collection
        embedding_model: Model to use for embeddings
        force_recreate: Whether to force recreation of vector store
        incremental_mode: Mode for incremental updates
        checksum_algorithm: Algorithm for checksums
        auto_detect_changes: Whether to auto-detect changes
        incremental_fallback_threshold: Threshold for falling back to full indexing when too many changes detected
        enable_batch_processing: Whether to enable batch processing
        batch_size: Size of processing batches
        enbable_performance_monitoring: Whether to enable performance monitoring
        batch_pause_seconds: Pause between batches in seconds
        max_concurrent_operations: Maximum concurrent operations
        max_backup_files: Maximum backup files to keep
        metadata_csv: CSV file for metadata
        blog_stats_filename: Filename for blog statistics
        blog_docs_filename: Filename for blog documents
        health_report_filename: Filename for health reports
        ci_summary_filename: Filename for CI summaries
        build_info_filename: Filename for build information
        storage_path: Legacy parameter, use vector_storage_path instead
        should_save_stats: Legacy parameter, not used
        ci_mode: Legacy parameter, not used
        job_id: Optional job ID for tracking pipeline execution. If not provided, will be auto-generated
        
    Returns:
        Dict containing pipeline execution results
    """
    start_time = datetime.now(timezone.utc)
    if job_id is None:
        job_id = f"pipeline_{start_time.strftime('%Y%m%d_%H%M%S')}"
    
    logger.info("="*80)
    logger.info("STARTING PIPELINE EXECUTION")
    logger.info("="*80)
    logger.info(f"Job ID: {job_id}")
    
    
    # Initialize result tracking
    result = {
        'job_id': job_id,
        'success': False,
        'message': "",
        'stats': {},
        'performance_metrics': {},
        'documents_processed': 0,
        'chunks_created': 0,
        'changes_detected': {},
        'errors': []
    }
    
    try:
        # Create and configure PipelineProcessor
        logger.info("="*50)
        logger.info("INITIALIZING PIPELINE PROCESSOR")
        logger.info("="*50)
        
        processor = PipelineProcessor(
            data_dir=data_dir,
            data_dir_pattern=data_dir_pattern,
            web_urls=web_urls,
            base_url=base_url,
            blog_base_url=blog_base_url,
            index_only_published_posts=index_only_published_posts,
            output_dir=output_dir,
            stats_output_dir=stats_output_dir,
            use_chunking=use_chunking,
            chunking_strategy=chunking_strategy,
            adaptive_chunking=adaptive_chunking,
            chunk_size=chunk_size,
            chunk_overlap=chunk_overlap,
            semantic_breakpoint_type=semantic_breakpoint_type,
            semantic_breakpoint_threshold_amount=semantic_breakpoint_threshold_amount,
            semantic_min_chunk_size=semantic_min_chunk_size,
            vector_storage_path=vector_storage_path,
            qdrant_url=qdrant_url,
            collection_name=collection_name,
            embedding_model=embedding_model,
            force_recreate=force_recreate,
            incremental_mode=incremental_mode,
            checksum_algorithm=checksum_algorithm,
            auto_detect_changes=auto_detect_changes,
            incremental_fallback_threshold=incremental_fallback_threshold,
            enable_batch_processing=enable_batch_processing,
            batch_size=batch_size,
            enbable_performance_monitoring=enbable_performance_monitoring,
            batch_pause_seconds=batch_pause_seconds,
            max_concurrent_operations=max_concurrent_operations,
            max_backup_files=max_backup_files,
            metadata_csv=metadata_csv,
            blog_stats_filename=blog_stats_filename,
            blog_docs_filename=blog_docs_filename,
            health_report_filename=health_report_filename,
            ci_summary_filename=ci_summary_filename,
            build_info_filename=build_info_filename
        )
        
        logger.info("PipelineProcessor initialized successfully")
        
        # Determine processing mode and execute
        logger.info("="*50)
        logger.info("EXECUTING PIPELINE")
        logger.info("="*50)
        
        success, process_mode = processor.process_documents(show_progress=True)
        
        if success:
            result['success'] = True
            result['message'] = f"Pipeline completed successfully in {process_mode} mode"
            logger.info(f"Pipeline execution completed successfully in {process_mode} mode")
        else:
            result['success'] = False
            result['message'] = f"Pipeline failed during processing in {process_mode} mode"
            result['errors'].append(f"Pipeline processing failed in {process_mode} mode")
            logger.error(f"Pipeline execution failed in {process_mode} mode")
        
        # Perform health check
        logger.info("="*50)
        logger.info("FINAL HEALTH CHECK")
        logger.info("="*50)
        
        try:
            health_report = processor.health_check(comprehensive=True)
            result['health_check'] = health_report
            logger.info(f"System health: {health_report.get('overall_status', 'unknown')}")
            
            if health_report.get('recommendations'):
                logger.info("Health check recommendations:")
                for rec in health_report['recommendations']:
                    logger.info(f"  - {rec}")
                    
        except Exception as e:
            logger.warning(f"Health check failed: {e}")
            result['errors'].append(f"Health check failed: {e}")
        
        # Log final summary
        end_time = datetime.now(timezone.utc)
        duration = (end_time - start_time).total_seconds()
        
        logger.info("\n" + "="*80)
        logger.info("PIPELINE EXECUTION COMPLETED")
        logger.info("="*80)
        logger.info(f"Job ID: {job_id}")
        logger.info(f"Status: {'SUCCESS' if result['success'] else 'FAILED'}")
        logger.info(f"Duration: {duration:.2f} seconds")
        logger.info(f"Mode: {process_mode}")
        if result['errors']:
            logger.info(f"Errors: {len(result['errors'])}")
        logger.info("="*80)
        
        result['duration_seconds'] = duration
        result['mode'] = process_mode
        return result
        
    except Exception as e:
        logger.error(f"Pipeline execution failed with unexpected error: {e}", exc_info=True)
        result['success'] = False
        result['message'] = f"Pipeline failed with unexpected error: {e}"
        result['errors'].append(str(e))
        
        # Calculate duration even for failures
        end_time = datetime.now(timezone.utc)
        duration = (end_time - start_time).total_seconds()
        result['duration_seconds'] = duration
        
        return result
