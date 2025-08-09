"""Database creation utilities."""
import os
import logging
from typing import Optional
from urllib.parse import urlparse
import sqlalchemy as sa
from sqlalchemy.exc import ProgrammingError, OperationalError

from lets_talk.shared.config import DATABASE_URL, LOGGER_NAME

logger = logging.getLogger(f"{LOGGER_NAME}.database.creation")


def create_database_if_not_exists() -> bool:
    """
    Create the required databases if they don't exist.
    
    This function works by connecting to the default database (usually 'postgres')
    and creating both the lets_talk and langgraph databases if they don't exist.
    
    Returns:
        bool: True if all databases exist or were created successfully, False otherwise
    """
    try:
        # Parse the database URL
        parsed = urlparse(DATABASE_URL)
        
        if not parsed.scheme.startswith('postgresql'):
            logger.info("Database creation only supported for PostgreSQL, skipping...")
            return True
        
        # Extract connection details
        host = parsed.hostname
        port = parsed.port or 5432
        username = parsed.username
        password = parsed.password
        target_db_name = parsed.path.lstrip('/')
        
        # Get environment variables for database names
        postgres_db = "postgres"
        langgraph_db = os.environ.get("LANGGRAPH_DB", "langgraph")
        lets_talk_db = os.environ.get("LETS_TALK_DB", "lets_talk")
        
        # Use the target database name from environment or URL
        if target_db_name != lets_talk_db:
            logger.warning(f"URL database name '{target_db_name}' differs from LETS_TALK_DB '{lets_talk_db}', using URL value")
        else:
            target_db_name = lets_talk_db
        
        # Create list of unique databases to create
        databases_to_create = list(set([target_db_name, langgraph_db]))
        
        if len(databases_to_create) == 1:
            logger.info(f"LANGGRAPH_DB and LETS_TALK_DB point to the same database: '{databases_to_create[0]}'")
        
        logger.info(f"Checking if databases {databases_to_create} exist...")
        
        # Create connection URL to the default PostgreSQL database
        default_db_url = f"postgresql://{username}:{password}@{host}:{port}/{postgres_db}"
        
        # Connect to the default database
        engine = sa.create_engine(default_db_url, isolation_level='AUTOCOMMIT')
        
        with engine.connect() as conn:
            # Create each database if it doesn't exist
            for db_name in databases_to_create:
                # Check if the database exists
                result = conn.execute(
                    sa.text("SELECT 1 FROM pg_database WHERE datname = :db_name"),
                    {"db_name": db_name}
                )
                
                if result.fetchone():
                    logger.info(f"Database '{db_name}' already exists")
                else:
                    # Create the database
                    logger.info(f"Creating database '{db_name}'...")
                    conn.execute(sa.text(f'CREATE DATABASE "{db_name}"'))
                    logger.info(f"Database '{db_name}' created successfully")
            
        engine.dispose()
        return True
        
    except (ProgrammingError, OperationalError) as e:
        logger.error(f"Database operation failed: {e}")
        return False
    except Exception as e:
        logger.error(f"Unexpected error during database creation: {e}")
        return False


def ensure_database_exists() -> bool:
    """
    Ensure the database exists before attempting migrations.
    
    Returns:
        bool: True if database exists or was created, False otherwise
    """
    try:
        logger.info("Ensuring database exists...")
        
        # First try to connect to the target database directly
        engine = sa.create_engine(DATABASE_URL)
        with engine.connect() as conn:
            # Simple test query
            conn.execute(sa.text("SELECT 1"))
            logger.info("Database connection successful")
            engine.dispose()
            return True
            
    except (ProgrammingError, OperationalError) as e:
        logger.info(f"Cannot connect to target database: {e}")
        logger.info("Attempting to create database...")
        
        # If connection fails, try to create the database
        success = create_database_if_not_exists()
        if success:
            logger.info("Database creation completed, verifying connection...")
            
            # Verify we can now connect
            try:
                engine = sa.create_engine(DATABASE_URL)
                with engine.connect() as conn:
                    conn.execute(sa.text("SELECT 1"))
                engine.dispose()
                logger.info("Database connection verified after creation")
                return True
            except Exception as verify_e:
                logger.error(f"Failed to connect to database after creation: {verify_e}")
                return False
        else:
            logger.error("Failed to create database")
            return False
            
    except Exception as e:
        logger.error(f"Unexpected error during database check: {e}")
        return False
