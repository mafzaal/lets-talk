#!/usr/bin/env python3
"""Standalone application startup script.

This script handles all the initialization that needs to happen before
the FastAPI application starts. It's run as part of the Docker entrypoint
to ensure proper database migration and system setup before the web server starts.
"""
import sys
import os
import logging
from pathlib import Path

# Try to import directly first, if that fails add backend to path and try again
try:
    from lets_talk.core.startup import startup_application
except ImportError:
    # Add the backend directory to Python path so we can import modules
    backend_dir = Path(__file__).parent / "backend"
    sys.path.insert(0, str(backend_dir))
    from lets_talk.core.startup import startup_application

# Set up basic logging before importing our modules
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.StreamHandler(sys.stdout)
    ]
)

def main():
    """Run the complete application startup sequence."""
    exit_code = 0
    
    try:
        # Import our startup modules after setting up the path
        from lets_talk.core.startup import (
            
            log_startup_summary,
            
        )
        from lets_talk.shared.config import LOGGER_NAME
        
        # Set up application logger
        logger = logging.getLogger(f"{LOGGER_NAME}.startup_main")
        
        logger.info("=" * 79)
        logger.info("🚀 Starting Let's Talk Application Initialization")
        logger.info("=" * 79)
        
        # Run the complete startup sequence
        # This includes database initialization, migrations, scheduler setup, etc.
        # For container startup, we only require database to be working
        startup_info = startup_application(
            app_name="Let's Talk Startup",
            fail_on_migration_error=True,  # Don't fail completely if migration fails
        )
        
        # Log detailed startup summary
        log_startup_summary(startup_info)
        
        if startup_info["success"]:
            logger.info("✅ Application startup completed successfully")
            logger.info("🌐 Ready to start web server...")
            exit_code = 0
        else:
            logger.error("❌ Application startup failed")
            logger.error("🚫 Container will not proceed to start web server")
            for error in startup_info.get("errors", []):
                logger.error(f"   • {error}")
            exit_code = 1
            
    except Exception as e:
        # Create a minimal logger if our imports failed
        basic_logger = logging.getLogger("startup_error")
        basic_logger.error(f"❌ Critical error during application startup: {e}")
        basic_logger.exception("Startup error details:")
        exit_code = 1
        
    finally:
        print("=" * 79)
        if exit_code == 0:
            print("🎉 Startup completed - proceeding to web server")
        else:
            print("💥 Startup failed - container will exit")
        print("=" * 79)
    
    return exit_code


if __name__ == "__main__":
    exit_code = main()
    sys.exit(exit_code)
