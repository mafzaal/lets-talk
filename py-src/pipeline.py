"""
Blog Data Update Script

This script updates the blog data vector store when new posts are added.
It can be scheduled to run periodically or manually executed.

Usage:
    python pipeline.py [--force-recreate] [--data-dir DATA_DIR]

Options:
    --force-recreate   Force recreation of the vector store even if it exists
    --data-dir DIR     Directory containing the blog posts (default: data/)
"""

import os
import sys
import argparse
from datetime import datetime
import json
from pathlib import Path
from lets_talk.config import VECTOR_STORAGE_PATH

# Import the blog utilities module
import lets_talk.utils.blog as blog

def parse_args():
    """Parse command-line arguments"""
    parser = argparse.ArgumentParser(description="Update blog data vector store")
    parser.add_argument("--force-recreate", action="store_true", 
                        help="Force recreation of the vector store")
    parser.add_argument("--data-dir", default=blog.DATA_DIR,
                        help=f"Directory containing blog posts (default: {blog.DATA_DIR})")
    return parser.parse_args()

def save_stats(stats, output_dir="./stats"):
    """Save stats to a JSON file for tracking changes over time"""
    # Create directory if it doesn't exist
    Path(output_dir).mkdir(exist_ok=True, parents=True)
    
    # Create filename with timestamp
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
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
    
    print(f"Saved stats to {filename}")
    return filename

def create_vector_database(documents, data_dir, storage_path=VECTOR_STORAGE_PATH, force_recreate=False):
    """
    Create or update the vector database with blog documents.
    
    Args:
        documents: List of document objects to store in the vector database
        data_dir: Directory containing the blog posts (for reporting)
        storage_path: Path where the vector database will be stored
        force_recreate: Whether to force recreation of the vector store
        
    Returns:
        Tuple of (success status, message)
    """
    try:
        create_vector_store = (not Path.exists(Path(storage_path))) or force_recreate
        
        if create_vector_store:
            print("\nAttempting to save vector store reference file...")
            vector_store = blog.create_vector_store(
                documents, 
                storage_path=storage_path, 
                force_recreate=force_recreate
            )
            vector_store.client.close()
            print("Vector store reference file saved.")
            return True, f"Vector store successfully created at {storage_path}"
        else:
            return True, f"Vector store already exists at {storage_path} (use --force-recreate to rebuild)"
    except Exception as e:
        return False, f"Error creating vector store: {str(e)}"

def main():
    """Main function to update blog data"""
    args = parse_args()
    
    print("=== Blog Data Update ===")
    print(f"Data directory: {args.data_dir}")
    print(f"Force recreate: {args.force_recreate}")
    print("========================")
    
    try:
        # Load and process documents
        documents = blog.load_blog_posts(args.data_dir)
        documents = blog.update_document_metadata(documents)
        
        # Get stats
        stats = blog.get_document_stats(documents)
        blog.display_document_stats(stats)
        
        # Save stats for tracking
        stats_file = save_stats(stats)

        # Create or update vector database
        success, message = create_vector_database(
            documents, 
            args.data_dir, 
            storage_path=VECTOR_STORAGE_PATH, 
            force_recreate=args.force_recreate
        )
        
        print("\n=== Update Summary ===")
        print(f"Processed {stats['total_documents']} documents")
        print(f"Stats saved to: {stats_file}")
        print(f"Vector DB status: {message}")
        print("=====================")
        
        if not success:
            return 1
        return 0
    except Exception as e:
        print(f"Error: {e}")
        import traceback
        traceback.print_exc()
        return 1

if __name__ == "__main__":
    sys.exit(main())
