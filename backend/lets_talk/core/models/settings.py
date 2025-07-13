"""SQLAlchemy models for system settings."""
from __future__ import annotations

from sqlalchemy import Column, String, Text, Boolean, DateTime, create_engine
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker
from datetime import datetime
from typing import Optional, Dict, Any
import os
from pathlib import Path

from lets_talk.shared.config import OUTPUT_DIR

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
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    def __repr__(self):
        return f"<Setting(key='{self.key}', section='{self.section}', is_read_only={self.is_read_only})>"


def get_settings_database_url() -> str:
    """Get the database URL for settings storage."""
    os.makedirs(OUTPUT_DIR, exist_ok=True)
    return f"sqlite:///{OUTPUT_DIR}/settings.db"


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
    engine = create_settings_engine()
    create_settings_tables(engine)
    return engine