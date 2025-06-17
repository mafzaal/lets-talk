"""
Blog Data Update Script

This script updates the blog data vector store when new posts are added.
It can be scheduled to run periodically or manually executed.

Usage:
    python pipeline.py [--force-recreate] [--data-dir DATA_DIR] [--output-dir OUTPUT_DIR] 
                       [--vector-storage-path PATH] [--collection-name NAME] [--embedding-model MODEL] 
                       [--no-chunking] [--no-save-stats] [--ci]

Options:
    --force-recreate         Force recreation of the vector store even if it exists
    --data-dir DIR           Directory containing the blog posts (default: data/)
    --output-dir DIR         Directory to save stats and artifacts (default: ./stats)
    --vector-storage-path PATH  Path to store the vector database (default from config)
    --collection-name NAME   Name of the Qdrant collection (default from config)
    --embedding-model MODEL  Embedding model to use (default from config) 
    --no-chunking            Don't split documents into chunks (use whole documents)
    --no-save-stats          Don't save document statistics
    --data-dir-pattern       Glob pattern to match blog post files within the data directory (default: None)
    --ci                     Run in CI mode (no interactive prompts, exit codes for CI)
    --blog-base-url          Base URL for the blog posts (default from config)
    --base-url               Base URL for absolute media links (default from config)
"""

import os
import sys
import argparse
from datetime import datetime
import json
import logging
from pathlib import Path
from typing import List, Dict, Any, Tuple
from lets_talk.config import (
    BASE_URL, BLOG_BASE_URL, CHUNK_OVERLAP, CHUNK_SIZE, VECTOR_STORAGE_PATH, DATA_DIR,
    FORCE_RECREATE, OUTPUT_DIR, USE_CHUNKING, SHOULD_SAVE_STATS,
    QDRANT_COLLECTION, EMBEDDING_MODEL, METADATA_CSV_FILE
)

# Import the blog utilities module
import lets_talk.utils.blog as blog

# Set up logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[logging.StreamHandler()]
)
logger = logging.getLogger("blog-pipeline")

def parse_args():
    """Parse command-line arguments"""
    parser = argparse.ArgumentParser(description="Update blog data vector store")
    parser.add_argument("--force-recreate", action="store_true", 
                        help="Force recreation of the vector store")
    parser.add_argument("--data-dir", default=DATA_DIR,
                        help=f"Directory containing blog posts (default: {DATA_DIR})")
    parser.add_argument("--output-dir", default="./stats",
                        help="Directory to save stats and artifacts (default: ./stats)")
    parser.add_argument("--vector-storage-path", default=VECTOR_STORAGE_PATH,
                        help=f"Path to store the vector database (default: {VECTOR_STORAGE_PATH})")
    parser.add_argument("--collection-name", default=QDRANT_COLLECTION,
                        help=f"Name of the Qdrant collection (default: {QDRANT_COLLECTION})")
    parser.add_argument("--embedding-model", default=EMBEDDING_MODEL,
                        help=f"Embedding model to use (default: {EMBEDDING_MODEL})")
    parser.add_argument("--ci", action="store_true",
                        help="Run in CI mode (no interactive prompts, exit codes for CI)")
    parser.add_argument("--chunk-size", type=int,
                        help=f"Size of each chunk in characters (default from config)")
    parser.add_argument("--chunk-overlap", type=int,
                        help=f"Overlap between chunks in characters (default from config)")
    parser.add_argument("--no-chunking", action="store_true",
                        help="Don't split documents into chunks (use whole documents)")
    parser.add_argument("--no-save-stats", action="store_true",
                        help="Don't save document statistics")
    parser.add_argument("--data-dir-pattern", default="*.md",
                        help="Glob pattern to match blog post files within the data directory (default: None)")
    parser.add_argument("--blog-base-url", default=BLOG_BASE_URL,
                        help="Base URL for the blog posts (default from config)")
    parser.add_argument("--base-url", default=BASE_URL,
                        help="Base URL for absolute media links (default from config)")
    
    # Incremental indexing options
    parser.add_argument("--incremental", action="store_true",
                        help="Enable incremental indexing mode (only process changed documents)")
    parser.add_argument("--auto-incremental", action="store_true",
                        help="Automatically detect first-time vs incremental indexing")
    parser.add_argument("--incremental-only", action="store_true",
                        help="Force incremental mode (fail if no existing metadata)")
    parser.add_argument("--incremental-with-fallback", action="store_true",
                        help="Try incremental, fallback to full rebuild if needed")
    parser.add_argument("--metadata-file", default=None,
                        help="Custom path for metadata CSV file (default: output_dir/blog_metadata.csv)")
    parser.add_argument("--dry-run", action="store_true",
                        help="Show what would be processed without actually doing it")
    parser.add_argument("--checksum-algorithm", default="sha256",
                        help="Checksum algorithm to use (sha256, md5)")
    
    return parser.parse_args()

def save_stats(stats, output_dir="./stats", ci_mode=False):
    """Save stats to a JSON file for tracking changes over time
    
    Args:
        stats: Dictionary containing statistics about the blog posts
        output_dir: Directory to save the stats file
        ci_mode: Whether to run in CI mode (use fixed filename)
    
    Returns:
        Tuple of (filename, stats_dict)
    """
    # Create directory if it doesn't exist
    Path(output_dir).mkdir(exist_ok=True, parents=True)
    
    # Create filename with timestamp or use fixed name for CI
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    if ci_mode:
        filename = f"{output_dir}/blog_stats_latest.json"
        # Also create a timestamped version for historical tracking
        history_filename = f"{output_dir}/blog_stats_{timestamp}.json"
    else:
        filename = f"{output_dir}/blog_stats_{timestamp}.json"
    
    # Save only the basic stats, not the full document list
    basic_stats = {
        "timestamp": timestamp,
        "total_documents": stats["total_documents"],
        "total_characters": stats["total_characters"],
        "min_length": stats["min_length"],
        "max_length": stats["max_length"],
        "avg_length": stats["avg_length"],
    }
    
    with open(filename, "w") as f:
        json.dump(basic_stats, f, indent=2)

    logger.info(f"Saved stats to {filename}")

    import pandas as pd
    docs_df = pd.DataFrame(stats["documents"])

    docs_df.to_csv(f"{output_dir}/blog_docs.csv", index=False)
    logger.info(f"Saved document details to {output_dir}/blog_docs.csv")    

    return filename, basic_stats

def create_vector_database(data_dir=DATA_DIR, storage_path=VECTOR_STORAGE_PATH, 
                      force_recreate=FORCE_RECREATE, output_dir=OUTPUT_DIR, ci_mode=False, 
                      use_chunking=USE_CHUNKING, should_save_stats=SHOULD_SAVE_STATS, 
                      chunk_size=CHUNK_SIZE, chunk_overlap=CHUNK_OVERLAP,
                      collection_name=QDRANT_COLLECTION, embedding_model=EMBEDDING_MODEL,
                      data_dir_pattern:str="*.md", blog_base_url=None, base_url=None,
                      incremental_mode="auto", metadata_csv_path=None, dry_run=False):
    """
    Create or update the vector database with blog documents.
    
    Args:
        data_dir: Directory containing the blog posts (default from config)
        storage_path: Path where the vector database will be stored (default from config)
        force_recreate: Whether to force recreation of the vector store (default from config)
        output_dir: Directory to save stats and artifacts (default from config)
        ci_mode: Whether to run in CI mode
        use_chunking: Whether to split documents into chunks (default from config)
        should_save_stats: Whether to save statistics about the documents (default from config)
        chunk_size: Size of each chunk in characters (default from config)
        chunk_overlap: Overlap between chunks in characters (default from config)
        collection_name: Name of the Qdrant collection (default from config)
        embedding_model: Embedding model to use (default from config)
        data_dir_pattern: Glob pattern to match blog post files within the data directory (default: None)
        blog_base_url: Base URL for the blog posts (default from config)
        base_url: Base URL for absolute media links (default from config)
        incremental_mode: Indexing mode (auto, incremental, full, etc.)
        metadata_csv_path: Path to metadata CSV file
        dry_run: If True, only show what would be processed
        
    Returns:
        Tuple of (success status, message, stats, stats_file, stats_file_content)
    """
    if dry_run:
        logger.info("=== DRY RUN MODE ===")
    
    # Set default metadata CSV path if not provided
    if metadata_csv_path is None:
        metadata_csv_path = os.path.join(output_dir, "blog_metadata.csv")
    
    try:
        # Load and process documents
        logger.info(f"Loading blog posts from {data_dir} with pattern '{data_dir_pattern}'")
        documents = blog.load_blog_posts(data_dir,glob_pattern=data_dir_pattern) 
        documents = blog.update_document_metadata(
            documents, 
            data_dir_prefix=data_dir,
            blog_base_url=blog_base_url if blog_base_url is not None else blog.BLOG_BASE_URL,
            base_url=base_url if base_url is not None else blog.BASE_URL
        )
        
        # Process incremental indexing
        processing_result = process_incremental_indexing(
            documents, metadata_csv_path, incremental_mode, dry_run
        )
        
        if dry_run:
            # For dry run, just return the results without processing
            stats = blog.get_document_stats(documents)
            return True, "Dry run completed - no changes made", stats, None, None
        
        # Determine which documents to process
        docs_to_process = []
        if processing_result["mode"] == "full":
            docs_to_process = documents
            logger.info("Full indexing: processing all documents")
        else:
            # Incremental mode: only process new and modified documents
            docs_to_process = processing_result["new"] + processing_result["modified"]
            logger.info(f"Incremental indexing: processing {len(docs_to_process)} changed documents")
        
        # If no documents to process in incremental mode, we're done
        if processing_result["mode"] == "incremental" and len(docs_to_process) == 0:
            logger.info("No documents changed - vector store is up to date")
            # Still get stats from all documents for reporting
            stats = blog.get_document_stats(documents)
            # Update indexed timestamps for unchanged documents
            import time
            current_time = time.time()
            for doc in processing_result["unchanged"]:
                doc.metadata["indexed_timestamp"] = current_time
                doc.metadata["index_status"] = "unchanged"
            
            # Save updated metadata
            if should_save_stats:
                stats_file, stats_content = save_stats(stats, output_dir=output_dir, ci_mode=ci_mode)
                return True, "No changes detected - vector store is up to date", stats, stats_file, stats_content
            return True, "No changes detected - vector store is up to date", stats, None, None
        
        # Get stats from all documents (for reporting) but process only changed ones
        stats = blog.get_document_stats(documents)
        blog.display_document_stats(stats)

        # Save stats for tracking
        stats_file = None
        stats_content = None
        if should_save_stats:
            stats_file, stats_content = save_stats(stats, output_dir=output_dir, ci_mode=ci_mode)
        
        # Use docs_to_process for chunking and vector store creation
        documents_for_processing = docs_to_process
        
        if use_chunking and documents_for_processing:
            logger.info("Chunking documents...")
            # Use provided chunk_size and chunk_overlap or default from config
            chunking_params = {}
            if chunk_size is not None:
                chunking_params['chunk_size'] = chunk_size
            if chunk_overlap is not None:
                chunking_params['chunk_overlap'] = chunk_overlap
                
            logger.info(f"Using chunk size: {chunking_params.get('chunk_size', 'default')} and overlap: {chunking_params.get('chunk_overlap', 'default')}")
            documents_for_processing = blog.split_documents(documents_for_processing, **chunking_params)

        # Determine vector store creation strategy
        create_vector_store = (
            (not Path.exists(Path(storage_path))) or 
            force_recreate or 
            processing_result["mode"] == "full"
        )
        
        if create_vector_store and processing_result["mode"] != "incremental":
            logger.info("Creating vector store...")
            if documents_for_processing:
                vector_store = blog.create_vector_store(
                    documents_for_processing, 
                    storage_path=storage_path, 
                    collection_name=collection_name,
                    embedding_model=embedding_model,
                    force_recreate=force_recreate
                )
                vector_store.client.close() # type: ignore
                
                # Update indexed timestamps and status for processed documents
                import time
                current_time = time.time()
                for doc in docs_to_process:
                    doc.metadata["indexed_timestamp"] = current_time
                    doc.metadata["index_status"] = "indexed"
                
                # Save updated metadata to CSV
                success_metadata = blog.save_document_metadata_csv(documents, metadata_csv_path)
                if not success_metadata:
                    logger.warning("Failed to save updated metadata CSV")
            
            logger.info(f"Vector store successfully created at {storage_path}")
            
            # In CI mode, create a metadata file with the build info
            if ci_mode:
                build_info = {
                    "build_timestamp": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
                    "document_count": stats["total_documents"],
                    "processed_count": len(docs_to_process),
                    "indexing_mode": processing_result["mode"],
                    "storage_path": str(storage_path),
                    "collection_name": collection_name,
                    "embedding_model": embedding_model,
                    "vector_store_size_bytes": get_directory_size(storage_path),
                }
                build_info_path = Path(output_dir) / "vector_store_build_info.json"
                with open(build_info_path, "w") as f:
                    json.dump(build_info, f, indent=2)
                logger.info(f"Build info saved to {build_info_path}")
                
            return True, f"Vector store successfully created at {storage_path} ({processing_result['mode']} mode, processed {len(docs_to_process)} documents)", stats, stats_file, stats_content
        elif processing_result["mode"] == "incremental" and documents_for_processing:
            # Implement incremental vector store updates
            logger.info("Performing incremental vector store update")
            
            # Extract the categories of documents
            new_docs = processing_result["new"]
            modified_docs = processing_result["modified"]
            deleted_sources = processing_result["deleted_sources"]
            
            # Apply chunking to new and modified documents if enabled
            docs_to_add = new_docs + modified_docs
            if use_chunking and docs_to_add:
                logger.info(f"Chunking {len(docs_to_add)} new/modified documents...")
                # Use provided chunk_size and chunk_overlap or default from config
                chunking_params = {}
                if chunk_size is not None:
                    chunking_params['chunk_size'] = chunk_size
                if chunk_overlap is not None:
                    chunking_params['chunk_overlap'] = chunk_overlap
                    
                docs_to_add = blog.split_documents(docs_to_add, **chunking_params)
                
                # Update the chunk count in original documents metadata
                for doc in new_docs + modified_docs:
                    source = doc.metadata.get("source", "")
                    chunks_for_doc = [d for d in docs_to_add if d.metadata.get("source", "") == source]
                    doc.metadata["chunk_count"] = len(chunks_for_doc)
            
            # Import QDRANT_URL from config
            from lets_talk.config import QDRANT_URL
            
            # Check if vector store exists
            vector_store_exists = (
                (QDRANT_URL and True) or  # Remote Qdrant assumed to exist
                (Path(storage_path).exists())  # Local Qdrant path exists
            )
            
            if not vector_store_exists:
                logger.warning("Vector store doesn't exist, falling back to full creation")
                # Create new vector store with all documents
                vector_store = blog.create_vector_store(
                    documents if use_chunking else documents_for_processing, 
                    storage_path=storage_path, 
                    collection_name=collection_name,
                    embedding_model=embedding_model,
                    force_recreate=True
                )
                mode_description = "incremental (created new store)"
            else:
                # Perform incremental update using the chunked documents
                if use_chunking:
                    # When chunking, all new+modified docs are in docs_to_add
                    success = blog.update_vector_store_incrementally(
                        storage_path=storage_path,
                        collection_name=collection_name,
                        embedding_model=embedding_model,
                        qdrant_url=QDRANT_URL,
                        new_docs=docs_to_add,  # All chunks from new+modified docs
                        modified_docs=[],  # Empty since included above
                        deleted_sources=deleted_sources
                    )
                else:
                    # When not chunking, separate new and modified docs
                    success = blog.update_vector_store_incrementally(
                        storage_path=storage_path,
                        collection_name=collection_name,
                        embedding_model=embedding_model,
                        qdrant_url=QDRANT_URL,
                        new_docs=new_docs,
                        modified_docs=modified_docs,
                        deleted_sources=deleted_sources
                    )
                
                if not success:
                    logger.error("Incremental update failed, falling back to full recreation")
                    vector_store = blog.create_vector_store(
                        documents if use_chunking else documents_for_processing, 
                        storage_path=storage_path, 
                        collection_name=collection_name,
                        embedding_model=embedding_model,
                        force_recreate=True
                    )
                    mode_description = "incremental (failed, recreated)"
                else:
                    vector_store = None  # We don't need to return the vector store for incremental
                    mode_description = "incremental"
            
            # Update indexed timestamps and status for all documents
            import time
            current_time = time.time()
            
            # Update metadata properly for all documents
            update_documents_metadata_after_indexing(
                documents, new_docs, modified_docs, current_time
            )
            
            # Save updated metadata to CSV
            success_metadata = blog.save_document_metadata_csv(documents, metadata_csv_path)
            if not success_metadata:
                logger.warning("Failed to save updated metadata CSV")
            
            # Close vector store connection if needed
            if vector_store and hasattr(vector_store, 'client') and vector_store.client:
                vector_store.client.close()
            
            return True, f"Vector store updated at {storage_path} ({mode_description}, processed {len(docs_to_process)} documents)", stats, stats_file, stats_content
        else:
            logger.info(f"Vector store already exists at {storage_path}")
            return True, f"Vector store already exists at {storage_path} (use --force-recreate to rebuild)", stats, stats_file, stats_content
    except Exception as e:
        logger.error(f"Error creating vector store: {str(e)}", exc_info=True)
        return False, f"Error creating vector store: {str(e)}", None, None, None

def get_directory_size(path):
    """Get the size of a directory in bytes"""
    total_size = 0
    for dirpath, dirnames, filenames in os.walk(path):
        for filename in filenames:
            filepath = os.path.join(dirpath, filename)
            if not os.path.islink(filepath):
                total_size += os.path.getsize(filepath)
    return total_size

def determine_indexing_mode(args):
    """
    Determine the indexing mode and metadata file path based on CLI arguments.
    
    Args:
        args: Parsed command line arguments
        
    Returns:
        Tuple of (indexing_mode, metadata_csv_path)
    """
    # Determine metadata file path
    if args.metadata_file:
        metadata_csv_path = args.metadata_file
    else:
        metadata_csv_path = os.path.join(args.output_dir, "blog_metadata.csv")
    
    # Determine indexing mode
    if args.force_recreate:
        indexing_mode = "full"
    elif args.incremental_only:
        indexing_mode = "incremental_only"
    elif args.incremental_with_fallback:
        indexing_mode = "incremental_with_fallback"
    elif args.auto_incremental or args.incremental:
        indexing_mode = "auto"
    else:
        # Default behavior - check if metadata exists
        if os.path.exists(metadata_csv_path) and not args.force_recreate:
            indexing_mode = "auto"
        else:
            indexing_mode = "full"
    
    return indexing_mode, metadata_csv_path


def process_incremental_indexing(documents, metadata_csv_path, 
                                indexing_mode, dry_run=False):
    """
    Process documents for incremental indexing.
    
    Args:
        documents: List of loaded documents
        metadata_csv_path: Path to metadata CSV file
        indexing_mode: Indexing mode (auto, incremental_only, incremental_with_fallback, full)
        dry_run: If True, only show what would be processed
        
    Returns:
        Dictionary with processing results and document categories
    """
    logger.info(f"Processing documents in '{indexing_mode}' mode")
    logger.info(f"Metadata file: {metadata_csv_path}")
    
    # Load existing metadata
    existing_metadata = blog.load_existing_metadata(metadata_csv_path)
    metadata_exists = bool(existing_metadata)
    
    logger.info(f"Found {len(existing_metadata)} existing document records")
    
    # Handle different indexing modes
    if indexing_mode == "incremental_only" and not metadata_exists:
        raise ValueError(f"Incremental-only mode requested but no metadata file found at {metadata_csv_path}")
    
    if indexing_mode == "full" or not metadata_exists:
        # Full indexing mode
        logger.info("Performing full indexing (all documents)")
        return {
            "mode": "full",
            "new": documents,
            "modified": [],
            "unchanged": [],
            "deleted_sources": [],
            "total_to_process": len(documents)
        }
    
    # Incremental indexing mode
    logger.info("Analyzing document changes...")
    changes = blog.detect_document_changes(documents, existing_metadata)
    
    new_docs = changes["new"]
    modified_docs = changes["modified"]
    unchanged_docs = changes["unchanged"]
    deleted_sources = changes["deleted_sources"]
    
    total_to_process = len(new_docs) + len(modified_docs)
    
    # Log the analysis results
    logger.info(f"Document analysis results:")
    logger.info(f"  New documents: {len(new_docs)}")
    logger.info(f"  Modified documents: {len(modified_docs)}")
    logger.info(f"  Unchanged documents: {len(unchanged_docs)}")
    logger.info(f"  Deleted documents: {len(deleted_sources)}")
    logger.info(f"  Total to process: {total_to_process}")
    
    if dry_run:
        logger.info("\n=== DRY RUN - No changes will be made ===")
        if new_docs:
            logger.info("New documents that would be processed:")
            for doc in new_docs:
                logger.info(f"  + {doc.metadata.get('source', 'Unknown')}")
        
        if modified_docs:
            logger.info("Modified documents that would be processed:")
            for doc in modified_docs:
                logger.info(f"  ~ {doc.metadata.get('source', 'Unknown')}")
        
        if deleted_sources:
            logger.info("Documents that would be removed:")
            for source in deleted_sources:
                logger.info(f"  - {source}")
        
        logger.info("=== END DRY RUN ===\n")
        return {
            "mode": "dry_run",
            "new": new_docs,
            "modified": modified_docs,
            "unchanged": unchanged_docs,
            "deleted_sources": deleted_sources,
            "total_to_process": total_to_process
        }
    
    # Check if incremental with fallback should fall back to full rebuild
    if indexing_mode == "incremental_with_fallback" and total_to_process > len(documents) * 0.8:
        logger.info("More than 80% of documents changed, falling back to full rebuild")
        return {
            "mode": "full",
            "new": documents,
            "modified": [],
            "unchanged": [],
            "deleted_sources": [],
            "total_to_process": len(documents)
        }
    
    return {
        "mode": "incremental",
        "new": new_docs,
        "modified": modified_docs,
        "unchanged": unchanged_docs,
        "deleted_sources": deleted_sources,
        "total_to_process": total_to_process
    }

def update_documents_metadata_after_indexing(all_documents: List[blog.Document], 
                                            new_docs: List[blog.Document],
                                            modified_docs: List[blog.Document],
                                            current_time: float) -> None:
    """
    Update metadata for processed documents after successful indexing.
    
    Args:
        all_documents: List of all documents (new, modified, unchanged)
        new_docs: List of new documents that were processed
        modified_docs: List of modified documents that were processed  
        current_time: Timestamp to use for indexed_timestamp
    """
    # Create a set of processed document sources for efficient lookup
    processed_sources = set()
    
    for doc in new_docs + modified_docs:
        source = doc.metadata.get("source", "")
        processed_sources.add(source)
    
    # Update metadata for all documents
    for doc in all_documents:
        source = doc.metadata.get("source", "")
        
        if source in processed_sources:
            # This document was processed (new or modified)
            doc.metadata["indexed_timestamp"] = current_time
            doc.metadata["index_status"] = "indexed"
        else:
            # This document was unchanged, preserve existing metadata
            # but ensure it has the required fields
            doc.metadata.setdefault("indexed_timestamp", 0.0)
            doc.metadata.setdefault("index_status", "indexed")  # Assume previously indexed

def main():
    """Main function to update blog data"""
    args = parse_args()
    
    # Determine indexing mode and metadata file path
    indexing_mode, metadata_csv_path = determine_indexing_mode(args)
    
    logger.info("=== Blog Data Update ===")
    logger.info(f"Data directory: {args.data_dir}")
    logger.info(f"Vector storage path: {args.vector_storage_path}")
    logger.info(f"Collection name: {args.collection_name}")
    logger.info(f"Embedding model: {args.embedding_model}")
    logger.info(f"Force recreate: {args.force_recreate}")
    logger.info(f"Output directory: {args.output_dir}")
    logger.info(f"CI mode: {args.ci}")
    logger.info(f"Chunking: {not args.no_chunking}")
    logger.info(f"Save stats: {not args.no_save_stats}")
    logger.info(f"Indexing mode: {indexing_mode}")
    logger.info(f"Metadata file: {metadata_csv_path}")
    logger.info(f"Dry run: {args.dry_run}")
    if not args.no_chunking:
        logger.info(f"Chunk size: {args.chunk_size if args.chunk_size else CHUNK_SIZE}")
        logger.info(f"Chunk overlap: {args.chunk_overlap if args.chunk_overlap else CHUNK_OVERLAP}")
    if args.data_dir_pattern:
        logger.info(f"Data dir pattern: {args.data_dir_pattern}")
    if args.blog_base_url:
        logger.info(f"Blog base URL: {args.blog_base_url}")
    if args.base_url:
        logger.info(f"Base URL: {args.base_url}")
    logger.info("========================")
    
    try:
        # Create or update vector database
        success, message, stats, stats_file, stats_content = create_vector_database(
            data_dir=args.data_dir, 
            storage_path=args.vector_storage_path, 
            force_recreate=args.force_recreate,
            output_dir=args.output_dir,
            ci_mode=args.ci,
            use_chunking=not args.no_chunking,
            should_save_stats=not args.no_save_stats,
            chunk_size=args.chunk_size,
            chunk_overlap=args.chunk_overlap,
            collection_name=args.collection_name,
            embedding_model=args.embedding_model,
            data_dir_pattern=args.data_dir_pattern,
            blog_base_url=args.blog_base_url,
            base_url=args.base_url,
            incremental_mode=indexing_mode,
            metadata_csv_path=metadata_csv_path,
            dry_run=args.dry_run
        )
        
        logger.info("\n=== Update Summary ===")
        if stats:
            logger.info(f"Processed {stats['total_documents']} documents")
            logger.info(f"Stats saved to: {stats_file}")
        logger.info(f"Vector DB status: {message}")
        logger.info("=====================")
        
        # In CI mode, create a summary file that GitHub Actions can use to set outputs
        if args.ci and stats:
            ci_summary_path = Path(args.output_dir) / "ci_summary.json"
            ci_summary = {
                "status": "success" if success else "failure",
                "message": message,
                "stats_file": stats_file,
                "document_count": stats["total_documents"],
                "vector_store_path": str(args.vector_storage_path),
                "collection_name": args.collection_name,
                "embedding_model": args.embedding_model
            }
            with open(ci_summary_path, "w") as f:
                json.dump(ci_summary, f, indent=2)
            logger.info(f"CI summary saved to {ci_summary_path}")
        
        if not success:
            return 1
        return 0
    except Exception as e:
        logger.error(f"Error: {e}", exc_info=True)
        return 1

if __name__ == "__main__":
    sys.exit(main())
