


#!/usr/bin/env python3
"""
TheDataGuy Chat - Main Entry Point

This script serves as the main entry point for the TheDataGuy Chat application.
It provides a command-line interface to run the app and update the vector database.
"""

import os
import sys
import argparse
from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv()

def main():
    """Main function to run the application or update blog data"""
    parser = argparse.ArgumentParser(description="TheDataGuy Chat - RAG-powered blog assistant")
    
    # Define commands
    subparsers = parser.add_subparsers(dest="command", help="Command to run")
    
    # Run app command
    run_parser = subparsers.add_parser("run", help="Run the chat application")
    run_parser.add_argument("--host", default="0.0.0.0", help="Host to bind to")
    run_parser.add_argument("--port", type=int, default=7860, help="Port to bind to")
    
    # Update vector store command
    update_parser = subparsers.add_parser("update", help="Update the vector database")
    update_parser.add_argument("--force", action="store_true", help="Force recreation of the vector store")
    
    # Parse arguments
    args = parser.parse_args()
    
    # Handle commands
    if args.command == "run":
        # Import here to avoid circular imports
        import chainlit as cl
        os.system(f"chainlit run py-src/app.py --host {args.host} --port {args.port}")
        
    elif args.command == "update":
        # Import here to avoid loading heavy dependencies if not needed
        from lets_talk.pipeline import create_vector_database
        force_flag = "--force-recreate" if args.force else ""
        print(f"Updating vector database (force={args.force})")
        create_vector_database(force_recreate=args.force)
        
    else:
        # Show help if no command provided
        parser.print_help()
        return 1
        
    return 0

if __name__ == "__main__":
    sys.exit(main())
