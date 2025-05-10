"""
Blog Data Update Script

This script updates the blog data vector store when new posts are added.
It can be scheduled to run periodically or manually executed.

Usage:
    python update_blog_data.py [--force-recreate] [--data-dir DATA_DIR]

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

# Import the blog utilities module
import blog_utils

def parse_args():
    """Parse command-line arguments"""
    parser = argparse.ArgumentParser(description="Update blog data vector store")
    parser.add_argument("--force-recreate", action="store_true", 
                        help="Force recreation of the vector store")
    parser.add_argument("--data-dir", default=blog_utils.DATA_DIR,
                        help=f"Directory containing blog posts (default: {blog_utils.DATA_DIR})")
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

def main():
    """Main function to update blog data"""
    args = parse_args()
    
    print("=== Blog Data Update ===")
    print(f"Data directory: {args.data_dir}")
    print(f"Force recreate: {args.force_recreate}")
    print("========================")
    
    # Process blog posts without creating embeddings
    try:
        # Load and process documents
        documents = blog_utils.load_blog_posts(args.data_dir)
        documents = blog_utils.update_document_metadata(documents)
        
        # Get stats
        stats = blog_utils.get_document_stats(documents)
        blog_utils.display_document_stats(stats)
        
        # Save stats for tracking
        stats_file = save_stats(stats)
        
        # Create a reference file for the vector store
        if args.force_recreate:
            print("\nAttempting to save vector store reference file...")
            blog_utils.create_vector_store(documents, force_recreate=args.force_recreate)
        
        print("\n=== Update Summary ===")
        print(f"Processed {stats['total_documents']} documents")
        print(f"Stats saved to: {stats_file}")
        print("Note: Vector store creation is currently disabled due to pickling issues.")
        print("      See VECTOR_STORE_ISSUES.md for more information and possible solutions.")
        print("=====================")
        
        return 0
    except Exception as e:
        print(f"Error: {e}")
        import traceback
        traceback.print_exc()
        return 1

if __name__ == "__main__":
    sys.exit(main())
