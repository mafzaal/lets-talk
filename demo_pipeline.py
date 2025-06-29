#!/usr/bin/env python3
"""
Demo script showing how to use the pipeline engine.
This script demonstrates the key features of the pipeline implementation.
"""

import logging
from datetime import datetime
import sys
import os
import tempfile
from pathlib import Path

from lets_talk.core.pipeline.processors import PipelineProcessor, get_processor
# Configure logging
def setup_logging():
    """Set up logging configuration for the demo."""
    log_format = "%(asctime)s - %(name)s - %(levelname)s - %(message)s"
    logging.basicConfig(
        level=logging.INFO,
        format=log_format,
        handlers=[
            logging.StreamHandler(sys.stdout),
            logging.FileHandler(f"demo_pipeline_{datetime.now().strftime('%Y%m%d_%H%M%S')}.log")
        ]
    )
    
    # Set specific log levels for different components
    logging.getLogger("lets_talk.core.pipeline").setLevel(logging.INFO)
    logging.getLogger("qdrant_client").setLevel(logging.WARNING)
    logging.getLogger("httpx").setLevel(logging.WARNING)
    
    return logging.getLogger(__name__)

# Initialize logging
logger = setup_logging()

# Add the backend directory to the Python path
backend_dir = Path(__file__).parent / "backend"
sys.path.insert(0, str(backend_dir))

def demo_pipeline_basic():
    """Demonstrate basic pipeline usage."""
    print("🔧 Pipeline Basic Usage Demo")
    print("-" * 40)
    
    try:
        from lets_talk.core.pipeline.engine import run_pipeline
        from lets_talk.shared.config import ChunkingStrategy

        
        # Create temporary directories for demo
        #         with tempfile.TemporaryDirectory() as temp_dir:
        #             data_dir = str(Path(temp_dir) / "data")
        #             output_dir = str(Path(temp_dir) / "output")
        #             storage_path = str(Path(temp_dir) / "vector_store")
                    
        #             os.makedirs(data_dir, exist_ok=True)
                    
        #             # Create a sample markdown file
        #             sample_content = """---
        # title: "Sample Blog Post"
        # date: "2025-06-19"
        # published: true
        # categories: ["demo", "test"]
        # description: "A sample blog post for pipeline demo"
        # ---

        # # Sample Blog Post

        # This is a sample blog post content for demonstrating the pipeline functionality.

        # ## Features

        # - Document loading
        # - Metadata extraction
        # - Checksum calculation
        # - Incremental processing
        # - Vector indexing

        # The pipeline is designed to handle real-world blog content efficiently.
        # """
                    
        #             sample_file = Path(data_dir) / "sample-post" / "index.md"
        #             sample_file.parent.mkdir(parents=True)
        #             sample_file.write_text(sample_content)
                    
        #             print(f"📁 Created sample data in: {data_dir}")
        #             print(f"📄 Sample file: {sample_file}")
                    
        #             # Run the pipeline
        #             print("\n🚀 Running pipeline...")

        # data_dir = "data/" 
        # output_dir = "output/demo"  
        # storage_path = ""  
        
        # result = run_pipeline(
        #         data_dir=data_dir,
        #         output_dir=output_dir,
        #         storage_path=storage_path,
        #         collection_name="demo_collection",
        #         embedding_model="ollama:snowflake-arctic-embed2:latest",
        #         force_recreate=False,
        #         use_chunking=True,
        #         chunk_size=500,
        #         chunk_overlap=50,
        #         chunking_strategy=ChunkingStrategy.TEXT_SPLITTER,
        #         should_save_stats=True,
        #         incremental_mode="auto",
        #         ci_mode=False
        #     )

        pipeline_processor : PipelineProcessor  = get_processor()

        result = pipeline_processor.process_documents_incremental()

        return result
            
        # print(f"\n📊 Pipeline Result:")
        # print(f"  ✅ Success: {result['success']}")
        # print(f"  📝 Message: {result['message']}")
        # print(f"  🗂️  Documents processed: {result.get('documents_processed', 0)}")
        # print(f"  🧩 Chunks created: {result.get('chunks_created', 0)}")
            
        # if result.get('changes_detected'):
        #     changes = result['changes_detected']
        #     print(f"  📈 Changes detected:")
        #     print(f"    - New: {changes.get('new', 0)}")
        #     print(f"    - Modified: {changes.get('modified', 0)}")
        #     print(f"    - Unchanged: {changes.get('unchanged', 0)}")
        #     print(f"    - Deleted: {changes.get('deleted', 0)}")
        
        # if result.get('errors'):
        #     print(f"  ⚠️  Errors: {len(result['errors'])}")
        #     for error in result['errors']:
        #         print(f"    - {error}")
        
        # return result['success']
            
    except Exception as e:
        print(f"❌ Demo failed: {e}")
        return False

def demo_pipeline_features():
    """Demonstrate key pipeline features."""
    print("\n🎯 Pipeline Features Overview")
    print("-" * 40)
    
    features = [
        "📖 Document Loading - Supports markdown files with frontmatter",
        "🏷️  Metadata Processing - Extracts title, date, categories, etc.",
        "🔍 Change Detection - Uses checksums to detect modified files",
        "⚡ Incremental Updates - Only processes changed documents",
        "🧩 Smart Chunking - Semantic or text-based chunking strategies",
        "🗄️  Vector Storage - Qdrant-based vector storage with embeddings",
        "📊 Statistics & Health - Comprehensive reporting and health checks",
        "🔄 Error Recovery - Backup and rollback capabilities",
        "⚙️  Performance Optimization - Batch processing and adaptive chunking",
        "🛡️  Robust Error Handling - Comprehensive error handling and logging"
    ]
    
    for feature in features:
        print(f"  {feature}")
    
    print(f"\n🔧 Configuration Options:")
    print(f"  - Chunking strategies: semantic, text_splitter")
    print(f"  - Incremental modes: auto, force")
    print(f"  - Embedding models: OpenAI, Ollama, etc.")
    print(f"  - Storage: Local Qdrant or remote server")

def main():
    """Run the demo."""
    print("🎉 Pipeline Engine Demo")
    print("=" * 50)
    
    # Show features
    #demo_pipeline_features()
    
    # Run basic demo
    success = demo_pipeline_basic()
    
    print("\n" + "=" * 50)
    if success:
        print("✅ Demo completed successfully!")
    else:
        print("❌ Demo encountered issues.")
if __name__ == "__main__":
    main()
