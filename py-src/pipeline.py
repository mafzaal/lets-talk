"""
Blog Data Update Script

This script updates the blog data vector store when new posts are added.
It can be scheduled to run periodically or manually executed.

Usage:
    python pipeline.py [--force-recreate] [--data-dir DATA_DIR] [--output-dir OUTPUT_DIR] [--ci]

Options:
    --force-recreate   Force recreation of the vector store even if it exists
    --data-dir DIR     Directory containing the blog posts (default: data/)
    --output-dir DIR   Directory to save stats and artifacts (default: ./stats)
    --ci               Run in CI mode (no interactive prompts, exit codes for CI)
"""

import os
import sys
import argparse
from datetime import datetime
import json
import logging
from pathlib import Path
from lets_talk.config import VECTOR_STORAGE_PATH, DATA_DIR

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
    parser.add_argument("--ci", action="store_true",
                        help="Run in CI mode (no interactive prompts, exit codes for CI)")
    parser.add_argument("--chunk-size", type=int,
                        help=f"Size of each chunk in characters (default from config)")
    parser.add_argument("--chunk-overlap", type=int,
                        help=f"Overlap between chunks in characters (default from config)")
    parser.add_argument("--no-chunking", action="store_true",
                        help="Don't split documents into chunks (use whole documents)")
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
    
    # In CI mode, also save a timestamped version
    if ci_mode:
        with open(history_filename, "w") as f:
            json.dump(basic_stats, f, indent=2)
        logger.info(f"Saved stats to {filename} and {history_filename}")
    else:
        logger.info(f"Saved stats to {filename}")
    
    return filename, basic_stats

def create_vector_database(data_dir=DATA_DIR, storage_path=VECTOR_STORAGE_PATH, 
                      force_recreate=False, output_dir="./stats", ci_mode=False, 
                      use_chunking=True, should_save_stats=True, chunk_size=None, chunk_overlap=None):
    """
    Create or update the vector database with blog documents.
    
    Args:
        data_dir: Directory containing the blog posts
        storage_path: Path where the vector database will be stored
        force_recreate: Whether to force recreation of the vector store
        output_dir: Directory to save stats and artifacts
        ci_mode: Whether to run in CI mode
        use_chunking: Whether to split documents into chunks
        should_save_stats: Whether to save statistics about the documents
        chunk_size: Size of each chunk in characters (default from config)
        chunk_overlap: Overlap between chunks in characters (default from config)
        
    Returns:
        Tuple of (success status, message, stats, stats_file, stats_file_content)
    """
    try:
        # Load and process documents
        logger.info(f"Loading blog posts from {data_dir}")
        documents = blog.load_blog_posts(data_dir)
        documents = blog.update_document_metadata(documents)
        
        
        # Get stats
        stats = blog.get_document_stats(documents)
        blog.display_document_stats(stats)

        # Save stats for tracking
        stats_file = None
        stats_content = None
        if should_save_stats:
            stats_file, stats_content = save_stats(stats, output_dir=output_dir, ci_mode=ci_mode)
        
        if use_chunking:
            logger.info("Chunking documents...")
            # Use provided chunk_size and chunk_overlap or default from config
            chunking_params = {}
            if chunk_size is not None:
                chunking_params['chunk_size'] = chunk_size
            if chunk_overlap is not None:
                chunking_params['chunk_overlap'] = chunk_overlap
                
            logger.info(f"Using chunk size: {chunking_params.get('chunk_size', 'default')} and overlap: {chunking_params.get('chunk_overlap', 'default')}")
            documents = blog.split_documents(documents, **chunking_params)

        

        create_vector_store = (not Path.exists(Path(storage_path))) or force_recreate
        
        if create_vector_store:
            logger.info("Creating vector store...")
            vector_store = blog.create_vector_store(
                documents, 
                storage_path=storage_path, 
                force_recreate=force_recreate
            )
            vector_store.client.close()
            logger.info(f"Vector store successfully created at {storage_path}")
            
            # In CI mode, create a metadata file with the build info
            if ci_mode:
                build_info = {
                    "build_timestamp": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
                    "document_count": stats["total_documents"],
                    "storage_path": str(storage_path),
                    "vector_store_size_bytes": get_directory_size(storage_path),
                }
                build_info_path = Path(output_dir) / "vector_store_build_info.json"
                with open(build_info_path, "w") as f:
                    json.dump(build_info, f, indent=2)
                logger.info(f"Build info saved to {build_info_path}")
                
            return True, f"Vector store successfully created at {storage_path}", stats, stats_file, stats_content
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

def main():
    """Main function to update blog data"""
    args = parse_args()
    
    logger.info("=== Blog Data Update ===")
    logger.info(f"Data directory: {args.data_dir}")
    logger.info(f"Force recreate: {args.force_recreate}")
    logger.info(f"Output directory: {args.output_dir}")
    logger.info(f"CI mode: {args.ci}")
    logger.info(f"Chunking: {not args.no_chunking}")
    if not args.no_chunking:
        logger.info(f"Chunk size: {args.chunk_size if args.chunk_size else 'default from config'}")
        logger.info(f"Chunk overlap: {args.chunk_overlap if args.chunk_overlap else 'default from config'}")
    logger.info("========================")
    
    try:
        # Create or update vector database
        success, message, stats, stats_file, stats_content = create_vector_database(
            data_dir=args.data_dir, 
            storage_path=VECTOR_STORAGE_PATH, 
            force_recreate=args.force_recreate,
            output_dir=args.output_dir,
            ci_mode=args.ci,
            use_chunking=not args.no_chunking,
            chunk_size=args.chunk_size,
            chunk_overlap=args.chunk_overlap
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
                "vector_store_path": str(VECTOR_STORAGE_PATH)
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
