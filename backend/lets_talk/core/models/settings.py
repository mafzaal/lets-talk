"""SQLAlchemy models for system settings."""
from __future__ import annotations

from sqlalchemy import Column, String, Text, Boolean, DateTime, create_engine
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker
from datetime import datetime, timezone
from typing import Optional, Dict, Any
import os
from pathlib import Path

from lets_talk.shared.config import OUTPUT_DIR, DATABASE_URL

Base = declarative_base()


class Setting(Base):
    """Model for storing system settings."""
    __tablename__ = "settings"
    
    key = Column(String(255), primary_key=True, nullable=False)
    value = Column(Text, nullable=False)
    default_value = Column(Text, nullable=False)
    data_type = Column(String(50), nullable=False)  # "string", "integer", "boolean", "float"
    is_secret = Column(Boolean, default=False, nullable=False)
    section = Column(String(100), nullable=False)  # e.g., "General", "API", "Database"
    description = Column(Text, nullable=True)
    is_read_only = Column(Boolean, default=False, nullable=False)
    created_at = Column(DateTime, default=lambda: datetime.now(timezone.utc))
    updated_at = Column(DateTime, default=lambda: datetime.now(timezone.utc), onupdate=lambda: datetime.now(timezone.utc))
    
    def __repr__(self):
        return f"<Setting(key='{self.key}', section='{self.section}', is_read_only={self.is_read_only})>"


def get_settings_database_url() -> str:
    """Get the database URL for settings storage."""
    os.makedirs(OUTPUT_DIR, exist_ok=True)
    return DATABASE_URL


def create_settings_engine():
    """Create SQLAlchemy engine for settings."""
    database_url = get_settings_database_url()
    engine = create_engine(database_url, echo=False)
    return engine


def create_settings_tables(engine):
    """Create settings tables if they don't exist."""
    Base.metadata.create_all(engine)


def get_settings_session():
    """Get a session for interacting with the settings database."""
    engine = create_settings_engine()
    create_settings_tables(engine)
    SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
    return SessionLocal()


def init_settings_db():
    """Initialize the settings database and tables."""
    # Import migration integration here to avoid circular imports
    from lets_talk.core.migrations.integration import initialize_database
    
    # Use migrations to initialize database
    migration_success = initialize_database()
    
    if not migration_success:
        # Fallback to direct table creation for development
        engine = create_settings_engine()
        create_settings_tables(engine)
        return engine
    
    engine = create_settings_engine()
    return engine