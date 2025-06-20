"""Main pipeline engine for data processing."""
import logging
import os
import time
from pathlib import Path
from typing import Dict, Any, Optional
from datetime import datetime

from lets_talk.core.pipeline.processors import update_document_metadata, update_vector_store_incrementally_with_rollback
from lets_talk.core.pipeline.services.chunking_service import split_documents
from lets_talk.core.pipeline.services.health_checker import comprehensive_system_health_check
from lets_talk.core.pipeline.services.metadata_manager import detect_document_changes, load_existing_metadata, save_document_metadata_csv
from lets_talk.core.pipeline.services.performance_monitor import apply_performance_optimizations
from lets_talk.core.pipeline.services.vector_store_manager import create_vector_store
from lets_talk.core.pipeline.services.document_loader import get_document_stats, load_blog_posts
from lets_talk.shared.config import ChunkingStrategy
# from lets_talk.core.pipeline import processors


logger = logging.getLogger(__name__)


def run_pipeline(
    data_dir: str,
    output_dir: str,
    storage_path: str,
    collection_name: str,
    embedding_model: str,
    force_recreate: bool = False,
    use_chunking: bool = True,
    chunk_size: int = 1000,
    chunk_overlap: int = 200,
    chunking_strategy: ChunkingStrategy = ChunkingStrategy.SEMANTIC,
    should_save_stats: bool = True,
    data_dir_pattern: str = "*.md",
    blog_base_url: Optional[str] = None,
    base_url: Optional[str] = None,
    incremental_mode: str = "auto",
    ci_mode: bool = True,
    
) -> Dict[str, Any]:
    """
    Run the main data processing pipeline.
    
    This function orchestrates the entire pipeline process including:
    - Document loading and processing
    - Vector store creation/updating
    - Statistics generation
    - Health checks and validation
    
    Args:
        data_dir: Directory containing source documents
        output_dir: Directory for outputs and reports
        storage_path: Path for vector store storage
        collection_name: Name of the vector collection
        embedding_model: Model to use for embeddings
        force_recreate: Whether to force recreation of vector store
        use_chunking: Whether to chunk documents
        chunk_size: Size of document chunks
        chunk_overlap: Overlap between chunks
        chunking_strategy: Strategy for chunking (ChunkingStrategy.SEMANTIC or ChunkingStrategy.TEXT_SPLITTER)
        should_save_stats: Whether to save statistics
        data_dir_pattern: Pattern for matching files
        blog_base_url: Base URL for blog posts
        base_url: Base URL for media links
        incremental_mode: Mode for incremental updates
        ci_mode: Whether running in CI mode
        **kwargs: Additional configuration parameters
        
    Returns:
        Dict containing pipeline execution results
    """
    start_time = datetime.now()
    job_id = f"pipeline_{start_time.strftime('%Y%m%d_%H%M%S')}"
    
    logger.info("="*80)
    logger.info("STARTING PIPELINE EXECUTION")
    logger.info("="*80)
    logger.info(f"Job ID: {job_id}")
    logger.info(f"Data directory: {data_dir}")
    logger.info(f"Output directory: {output_dir}")
    logger.info(f"Storage path: {storage_path}")
    logger.info(f"Collection: {collection_name}")
    logger.info(f"Embedding model: {embedding_model}")
    logger.info(f"Force recreate: {force_recreate}")
    logger.info(f"Incremental mode: {incremental_mode}")
    logger.info(f"Use chunking: {use_chunking}")
    logger.info(f"Chunking strategy: {chunking_strategy}")
    
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
        # Ensure output directory exists
        os.makedirs(output_dir, exist_ok=True)
        metadata_csv_path = os.path.join(output_dir, "metadata.csv")
        
        # Step 1: Load documents
        logger.info("\n" + "="*50)
        logger.info("STEP 1: LOADING DOCUMENTS")
        logger.info("="*50)
        
        documents = load_blog_posts(
            data_dir=data_dir,
            glob_pattern=data_dir_pattern,
            recursive=True,
            show_progress=True
        )
        
        if not documents:
            result['message'] = "No documents found to process"
            result['success'] = True
            logger.warning("No documents found in data directory")
            return result
        
        logger.info(f"Loaded {len(documents)} documents")
        result['documents_loaded'] = len(documents)
        
        # Step 2: Update document metadata
        logger.info("\n" + "="*50)
        logger.info("STEP 2: UPDATING DOCUMENT METADATA")
        logger.info("="*50)
        
        documents = update_document_metadata(
            documents=documents,
            data_dir_prefix=data_dir,
            blog_base_url=blog_base_url or "",
            base_url=base_url or "",
            remove_suffix="index.md"
        )
        
        logger.info(f"Updated metadata for {len(documents)} documents")
        result['documents_processed'] = len(documents)
        
        # Step 3: Calculate checksums and detect changes
        logger.info("\n" + "="*50)
        logger.info("STEP 3: DETECTING DOCUMENT CHANGES")
        logger.info("="*50)
        
        # Load existing metadata for change detection
        existing_metadata = load_existing_metadata(metadata_csv_path)
        logger.info(f"Loaded metadata for {len(existing_metadata)} existing documents")
        
        # Detect changes
        changes = detect_document_changes(documents, existing_metadata)
        result['changes_detected'] = {
            'new': len(changes['new']),
            'modified': len(changes['modified']),
            'unchanged': len(changes['unchanged']),
            'deleted': len(changes['deleted_sources'])
        }
        
        logger.info(f"Change detection results:")
        logger.info(f"  - New documents: {len(changes['new'])}")
        logger.info(f"  - Modified documents: {len(changes['modified'])}")
        logger.info(f"  - Unchanged documents: {len(changes['unchanged'])}")
        logger.info(f"  - Deleted documents: {len(changes['deleted_sources'])}")
        
        # Determine processing mode
        docs_to_process = []
        process_mode = "full"
        
        if incremental_mode == "auto" and not force_recreate:
            # Only process new and modified documents
            docs_to_process = changes['new'] + changes['modified']
            if docs_to_process or changes['deleted_sources']:
                process_mode = "incremental"
                logger.info(f"Using incremental mode: {len(docs_to_process)} documents to process")
            else:
                logger.info("No changes detected, skipping indexing")
                result['message'] = "No changes detected - index is up to date"
                result['success'] = True
                return result
        else:
            # Process all documents
            docs_to_process = documents
            process_mode = "full"
            logger.info(f"Using full rebuild mode: {len(docs_to_process)} documents to process")
        
        # Step 4: Chunk documents that need indexing
        chunked_docs = []
        if use_chunking and docs_to_process:
            logger.info("\n" + "="*50)
            logger.info("STEP 4: CHUNKING DOCUMENTS")
            logger.info("="*50)
            
            # Apply performance optimizations if available
            try:
                optimized_docs, perf_metrics = apply_performance_optimizations(
                    docs_to_process, 
                    target_chunk_size=chunk_size,
                    enable_monitoring=True
                )
                result['performance_metrics'].update(perf_metrics)
                
                chunked_docs = split_documents(
                    documents=optimized_docs,
                    chunk_size=chunk_size,
                    chunk_overlap=chunk_overlap,
                    chunking_strategy=chunking_strategy
                )
            except Exception as e:
                logger.warning(f"Performance optimization failed, using standard chunking: {e}")
                chunked_docs = split_documents(
                    documents=docs_to_process,
                    chunk_size=chunk_size,
                    chunk_overlap=chunk_overlap,
                    chunking_strategy=chunking_strategy
                )
            
            logger.info(f"Created {len(chunked_docs)} chunks from {len(docs_to_process)} documents")
            result['chunks_created'] = len(chunked_docs)
        else:
            chunked_docs = docs_to_process
            logger.info("Chunking disabled - using whole documents")
        
        # Step 5: Index documents
        logger.info("\n" + "="*50)
        logger.info("STEP 5: INDEXING DOCUMENTS")
        logger.info("="*50)
        
        index_success = False
        
        if process_mode == "incremental" and not force_recreate:
            # Incremental update with comprehensive error handling
            logger.info("Performing incremental vector store update...")
            
            success, error_msg = update_vector_store_incrementally_with_rollback(
                storage_path=storage_path,
                collection_name=collection_name,
                embedding_model=embedding_model,
                qdrant_url="",  # Use local storage by default
                new_docs=changes['new'] if use_chunking else changes['new'],
                modified_docs=chunked_docs if changes['modified'] else [],
                deleted_sources=changes['deleted_sources'],
                metadata_csv_path=metadata_csv_path,
                all_documents=documents
            )
            
            if success:
                index_success = True
                logger.info("Incremental indexing completed successfully")
            else:
                logger.error(f"Incremental indexing failed: {error_msg}")
                result['errors'].append(f"Incremental indexing failed: {error_msg}")
        else:
            # Full rebuild
            logger.info("Performing full vector store rebuild...")
            
            try:
                vector_store = create_vector_store(
                    documents=chunked_docs,
                    storage_path=storage_path,
                    collection_name=collection_name,
                    embedding_model=embedding_model,
                    force_recreate=force_recreate
                )
                
                if vector_store:
                    index_success = True
                    logger.info("Full indexing completed successfully")
                    
                    # Update indexed timestamps for all documents
                    current_time = time.time()
                    for doc in documents:
                        doc.metadata["indexed_timestamp"] = current_time
                        doc.metadata["index_status"] = "indexed"
                else:
                    logger.error("Failed to create vector store")
                    result['errors'].append("Failed to create vector store")
            except Exception as e:
                logger.error(f"Vector store creation failed: {e}")
                result['errors'].append(f"Vector store creation failed: {e}")
        
        # Step 6: Save states and metadata
        logger.info("\n" + "="*50)
        logger.info("STEP 6: SAVING METADATA AND STATISTICS")
        logger.info("="*50)
        
        # Save document metadata
        metadata_saved = save_document_metadata_csv(
            documents=documents,
            metadata_csv_path=metadata_csv_path
        )
        
        if metadata_saved:
            logger.info(f"Saved metadata to {metadata_csv_path}")
        else:
            logger.warning("Failed to save metadata CSV")
            result['errors'].append("Failed to save metadata CSV")
        
        # Generate and save statistics if requested
        if should_save_stats:
            try:
                stats = get_document_stats(documents)
                result['stats'] = stats
                
                # Save stats to file
                stats_file = os.path.join(output_dir, f"blog_stats_{start_time.strftime('%Y%m%d_%H%M%S')}.json")
                import json
                with open(stats_file, 'w') as f:
                    json.dump(stats, f, indent=2, default=str)
                logger.info(f"Saved statistics to {stats_file}")
                
                # Display summary stats
                # processors.display_document_stats(stats)
                
            except Exception as e:
                logger.warning(f"Failed to generate statistics: {e}")
                result['errors'].append(f"Failed to generate statistics: {e}")
        
        # Perform final health check
        logger.info("\n" + "="*50)
        logger.info("FINAL HEALTH CHECK")
        logger.info("="*50)
        
        try:
            health_report = comprehensive_system_health_check(
                storage_path=storage_path,
                collection_name=collection_name,
                qdrant_url="",
                embedding_model=embedding_model,
                metadata_csv_path=metadata_csv_path
            )
            
            result['health_check'] = health_report
            logger.info(f"System health: {health_report['overall_status']}")
            
            if health_report['recommendations']:
                logger.info("Recommendations:")
                for rec in health_report['recommendations']:
                    logger.info(f"  - {rec}")
                    
        except Exception as e:
            logger.warning(f"Health check failed: {e}")
            result['errors'].append(f"Health check failed: {e}")
        
        # Determine final success status
        if index_success and not result['errors']:
            result['success'] = True
            result['message'] = f"Pipeline completed successfully in {process_mode} mode"
        elif index_success and result['errors']:
            result['success'] = True
            result['message'] = f"Pipeline completed with warnings in {process_mode} mode"
        else:
            result['success'] = False
            result['message'] = f"Pipeline failed during indexing in {process_mode} mode"
        
        # Log final summary
        end_time = datetime.now()
        duration = (end_time - start_time).total_seconds()
        
        logger.info("\n" + "="*80)
        logger.info("PIPELINE EXECUTION COMPLETED")
        logger.info("="*80)
        logger.info(f"Job ID: {job_id}")
        logger.info(f"Status: {'SUCCESS' if result['success'] else 'FAILED'}")
        logger.info(f"Duration: {duration:.2f} seconds")
        logger.info(f"Documents processed: {result['documents_processed']}")
        logger.info(f"Chunks created: {result['chunks_created']}")
        logger.info(f"Mode: {process_mode}")
        if result['errors']:
            logger.info(f"Errors: {len(result['errors'])}")
        logger.info("="*80)
        
        result['duration_seconds'] = duration
        return result
        
    except Exception as e:
        logger.error(f"Pipeline execution failed with unexpected error: {e}", exc_info=True)
        result['success'] = False
        result['message'] = f"Pipeline failed with unexpected error: {e}"
        result['errors'].append(str(e))
        return result
