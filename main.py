#!/usr/bin/env python3
"""
Main entry point for the lets-talk pipeline.
"""

import sys
import logging
import os
from pathlib import Path

# Add the backend directory to Python path to ensure imports work
backend_dir = Path(__file__).parent / "backend"
sys.path.insert(0, str(backend_dir))

from lets_talk.core.pipeline.engine import run_pipeline


def setup_logging():
    """Configure logging for the pipeline."""
    # Get log level from environment variable, default to INFO
    log_level = os.getenv('LOG_LEVEL', 'INFO').upper()
    
    # Get log format from environment variable or use default
    log_format = os.getenv('LOG_FORMAT', 
                          '%(asctime)s [%(levelname)s] %(name)s - %(message)s')
    
    # Configure logging
    logging.basicConfig(
        level=getattr(logging, log_level, logging.INFO),
        format=log_format,
        datefmt='%Y-%m-%d %H:%M:%S'
    )
    
    # Create logger for main module
    logger = logging.getLogger(__name__)
    logger.info(f"Logging configured with level: {log_level}")
    
    return logger

if __name__ == "__main__":
    # Setup logging first
    logger = setup_logging()
    
    print("Starting the lets-talk pipeline...")
    logger.info("Pipeline execution started")
    
    try:
        # Run the pipeline with default configuration
        logger.info("Calling run_pipeline with default configuration")
        result = run_pipeline()
        
        if result.get('success'):
            success_msg = "Pipeline completed successfully!"
            print(f"✅ {success_msg}")
            logger.info(success_msg)
            
            message = result.get('message', 'No message provided')
            print(f"📝 {message}")
            logger.info(f"Pipeline message: {message}")
            
            # Print basic stats if available
            if result.get('stats'):
                stats = result['stats']
                docs_processed = stats.get('documents_processed', 0)
                chunks_created = stats.get('chunks_created', 0)
                print(f"📊 Documents processed: {docs_processed}")
                print(f"🧩 Chunks created: {chunks_created}")
                logger.info(f"Pipeline stats - Documents: {docs_processed}, Chunks: {chunks_created}")
        else:
            error_msg = f"Pipeline failed: {result.get('message', 'Unknown error')}"
            print(f"❌ {error_msg}")
            logger.error(error_msg)
            
            if result.get('errors'):
                print("Errors:")
                logger.error("Pipeline errors:")
                for error in result['errors']:
                    print(f"  - {error}")
                    logger.error(f"  - {error}")
            sys.exit(1)
            
    except Exception as e:
        error_msg = f"Failed to run pipeline: {e}"
        print(f"❌ {error_msg}")
        logger.exception(error_msg)
        sys.exit(1)
