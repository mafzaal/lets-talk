"""Initialize settings from config.py into the database."""
from __future__ import annotations

import logging
from typing import Dict, List, Tuple, Any
from lets_talk.core.models.settings import init_settings_db
from lets_talk.core.services.settings import SettingsService
from lets_talk.shared.config import (
    ALLOW_ORIGINS_URLS, DATA_DIR_PATTERN, LOGGER_NAME, DATA_DIR, WEB_URLS, BASE_URL, BLOG_BASE_URL, INDEX_ONLY_PUBLISHED_POSTS, RSS_URL,
    OUTPUT_DIR, STATS_OUTPUT_DIR, VECTOR_STORAGE_PATH, FORCE_RECREATE, QDRANT_URL, QDRANT_COLLECTION,
    USE_CHUNKING, CHUNKING_STRATEGY, CHUNK_SIZE, CHUNK_OVERLAP, ADAPTIVE_CHUNKING,
    SEMANTIC_CHUNKER_BREAKPOINT_TYPE, SEMANTIC_CHUNKER_BREAKPOINT_THRESHOLD_AMOUNT, SEMANTIC_CHUNKER_MIN_CHUNK_SIZE,
    BATCH_SIZE, ENABLE_BATCH_PROCESSING, ENABLE_PERFORMANCE_MONITORING, MAX_CONCURRENT_OPERATIONS,
    EMBEDDING_MODEL, LLM_MODEL, LLM_TEMPERATURE,
    BM25_RETRIEVAL, MULTI_QUERY_RETRIEVAL, PARENT_DOCUMENT_RETRIEVAL, MAX_SEARCH_RESULTS,
    LOG_LEVEL, METADATA_CSV_FILE, DEFAULT_INDEXED_TIMESTAMP
)

logger = logging.getLogger(f"{LOGGER_NAME}.settings_init")


class SettingsInitializer:
    """Initialize settings from config.py into the database."""
    
    def __init__(self):
        self.settings_service = SettingsService()
    
    def get_config_settings_mapping(self) -> List[Dict[str, Any]]:
        """
        Map current config.py settings to database structure.
        
        Returns categorized settings with their metadata.
        """
        return [
            # CORS Settings
            {
                "key": "ALLOW_ORIGINS_URLS",
                "value": ALLOW_ORIGINS_URLS,
                "default_value": ALLOW_ORIGINS_URLS,
                "data_type": "string",
                "is_secret": False,
                "section": "CORS",
                "description": "Comma-separated list of allowed CORS origins",
                "is_read_only": False
            },
            
            # Data Input Settings
            {
                "key": "DATA_DIR",
                "value": DATA_DIR,
                "default_value": DATA_DIR,
                "data_type": "string",
                "is_secret": False,
                "section": "Data Input",
                "description": "Directory containing input data files",
                "is_read_only": False
            },
            {
                "key": "DATA_DIR_PATTERN",
                "value": DATA_DIR_PATTERN,
                "default_value": DATA_DIR_PATTERN,
                "data_type": "string",
                "is_secret": False,
                "section": "Data Input",
                "description": "Pattern for matching input files",
                "is_read_only": False
            },
            {
                "key": "WEB_URLS",
                "value": WEB_URLS,
                "default_value": WEB_URLS,
                "data_type": "string",
                "is_secret": False,
                "section": "Data Input",
                "description": "Comma-separated list of web URLs to scrape",
                "is_read_only": False
            },
            {
                "key": "BASE_URL",
                "value": BASE_URL,
                "default_value": BASE_URL,
                "data_type": "string",
                "is_secret": False,
                "section": "Data Input",
                "description": "Base URL for web scraping",
                "is_read_only": False
            },
            {
                "key": "BLOG_BASE_URL",
                "value": BLOG_BASE_URL,
                "default_value": BLOG_BASE_URL,
                "data_type": "string",
                "is_secret": False,
                "section": "Data Input",
                "description": "Base URL for blog content",
                "is_read_only": False
            },
            {
                "key": "INDEX_ONLY_PUBLISHED_POSTS",
                "value": INDEX_ONLY_PUBLISHED_POSTS,
                "default_value": "True",
                "data_type": "boolean",
                "is_secret": False,
                "section": "Data Input",
                "description": "Whether to index only published posts",
                "is_read_only": False
            },
            {
                "key": "RSS_URL",
                "value": RSS_URL,
                "default_value": RSS_URL,
                "data_type": "string",
                "is_secret": False,
                "section": "Data Input",
                "description": "RSS feed URL for content ingestion",
                "is_read_only": False
            },

            # Output Settings
            {
                "key": "OUTPUT_DIR",
                "value": OUTPUT_DIR,
                "default_value": OUTPUT_DIR,
                "data_type": "string",
                "is_secret": False,
                "section": "Output",
                "description": "Directory for output files and statistics",
                "is_read_only": False
            },
            {
                "key": "STATS_OUTPUT_DIR",
                "value": STATS_OUTPUT_DIR,
                "default_value": STATS_OUTPUT_DIR,
                "data_type": "string",
                "is_secret": False,
                "section": "Output",
                "description": "Directory for statistics output",
                "is_read_only": False
            },

            # Vector Storage Settings
            {
                "key": "VECTOR_STORAGE_PATH",
                "value": VECTOR_STORAGE_PATH,
                "default_value": VECTOR_STORAGE_PATH,
                "data_type": "string",
                "is_secret": False,
                "section": "Vector Storage",
                "description": "Path to vector storage directory",
                "is_read_only": False
            },
            {
                "key": "FORCE_RECREATE",
                "value": FORCE_RECREATE,
                "default_value": "False",
                "data_type": "boolean",
                "is_secret": False,
                "section": "Vector Storage",
                "description": "Force recreation of vector store",
                "is_read_only": False
            },
            {
                "key": "QDRANT_URL",
                "value": QDRANT_URL,
                "default_value": QDRANT_URL,
                "data_type": "string",
                "is_secret": False,
                "section": "Vector Storage",
                "description": "Qdrant vector database URL",
                "is_read_only": False
            },
            {
                "key": "QDRANT_COLLECTION",
                "value": QDRANT_COLLECTION,
                "default_value": QDRANT_COLLECTION,
                "data_type": "string",
                "is_secret": False,
                "section": "Vector Storage",
                "description": "Qdrant collection name",
                "is_read_only": False
            },

            # Chunking Settings
            {
                "key": "USE_CHUNKING",
                "value": USE_CHUNKING,
                "default_value": "True",
                "data_type": "boolean",
                "is_secret": False,
                "section": "Chunking",
                "description": "Whether to use document chunking",
                "is_read_only": False
            },
            {
                "key": "CHUNKING_STRATEGY",
                "value": CHUNKING_STRATEGY,
                "default_value": CHUNKING_STRATEGY,
                "data_type": "string",
                "is_secret": False,
                "section": "Chunking",
                "description": "Chunking strategy: semantic or text_splitter",
                "is_read_only": False
            },
            {
                "key": "CHUNK_SIZE",
                "value": CHUNK_SIZE,
                "default_value": CHUNK_SIZE,
                "data_type": "integer",
                "is_secret": False,
                "section": "Chunking",
                "description": "Size of text chunks",
                "is_read_only": False
            },
            {
                "key": "CHUNK_OVERLAP",
                "value": CHUNK_OVERLAP,
                "default_value": CHUNK_OVERLAP,
                "data_type": "integer",
                "is_secret": False,
                "section": "Chunking",
                "description": "Overlap between chunks",
                "is_read_only": False
            },
            {
                "key": "ADAPTIVE_CHUNKING",
                "value": ADAPTIVE_CHUNKING,
                "default_value": "True",
                "data_type": "boolean",
                "is_secret": False,
                "section": "Chunking",
                "description": "Use adaptive chunking strategies",
                "is_read_only": False
            },

            # Semantic Chunking Settings
            {
                "key": "SEMANTIC_CHUNKER_BREAKPOINT_TYPE",
                "value": SEMANTIC_CHUNKER_BREAKPOINT_TYPE,
                "default_value": SEMANTIC_CHUNKER_BREAKPOINT_TYPE,
                "data_type": "string",
                "is_secret": False,
                "section": "Semantic Chunking",
                "description": "Breakpoint type for semantic chunking",
                "is_read_only": False
            },
            {
                "key": "SEMANTIC_CHUNKER_BREAKPOINT_THRESHOLD_AMOUNT",
                "value": SEMANTIC_CHUNKER_BREAKPOINT_THRESHOLD_AMOUNT,
                "default_value": SEMANTIC_CHUNKER_BREAKPOINT_THRESHOLD_AMOUNT,
                "data_type": "float",
                "is_secret": False,
                "section": "Semantic Chunking",
                "description": "Threshold amount for semantic chunking",
                "is_read_only": False
            },
            {
                "key": "SEMANTIC_CHUNKER_MIN_CHUNK_SIZE",
                "value": SEMANTIC_CHUNKER_MIN_CHUNK_SIZE,
                "default_value": SEMANTIC_CHUNKER_MIN_CHUNK_SIZE,
                "data_type": "integer",
                "is_secret": False,
                "section": "Semantic Chunking",
                "description": "Minimum chunk size for semantic chunking",
                "is_read_only": False
            },

            # Performance Settings
            {
                "key": "BATCH_SIZE",
                "value": BATCH_SIZE,
                "default_value": BATCH_SIZE,
                "data_type": "integer",
                "is_secret": False,
                "section": "Performance",
                "description": "Batch size for processing",
                "is_read_only": False
            },
            {
                "key": "ENABLE_BATCH_PROCESSING",
                "value": ENABLE_BATCH_PROCESSING,
                "default_value": "True",
                "data_type": "boolean",
                "is_secret": False,
                "section": "Performance",
                "description": "Enable batch processing",
                "is_read_only": False
            },
            {
                "key": "ENABLE_PERFORMANCE_MONITORING",
                "value": ENABLE_PERFORMANCE_MONITORING,
                "default_value": "True",
                "data_type": "boolean",
                "is_secret": False,
                "section": "Performance",
                "description": "Enable performance monitoring",
                "is_read_only": False
            },
            {
                "key": "MAX_CONCURRENT_OPERATIONS",
                "value": MAX_CONCURRENT_OPERATIONS,
                "default_value": MAX_CONCURRENT_OPERATIONS,
                "data_type": "integer",
                "is_secret": False,
                "section": "Performance",
                "description": "Maximum concurrent operations",
                "is_read_only": False
            },

            # AI/ML Settings
            {
                "key": "EMBEDDING_MODEL",
                "value": EMBEDDING_MODEL,
                "default_value": EMBEDDING_MODEL,
                "data_type": "string",
                "is_secret": False,
                "section": "AI/ML",
                "description": "Embedding model for vector generation",
                "is_read_only": False
            },
            {
                "key": "LLM_MODEL",
                "value": LLM_MODEL,
                "default_value": LLM_MODEL,
                "data_type": "string",
                "is_secret": False,
                "section": "AI/ML",
                "description": "Large language model for generation",
                "is_read_only": False
            },
            {
                "key": "LLM_TEMPERATURE",
                "value": LLM_TEMPERATURE,
                "default_value": LLM_TEMPERATURE,
                "data_type": "float",
                "is_secret": False,
                "section": "AI/ML",
                "description": "Temperature for LLM generation",
                "is_read_only": False
            },

            # Retrieval Settings
            {
                "key": "BM25_RETRIEVAL",
                "value": BM25_RETRIEVAL,
                "default_value": "True",
                "data_type": "boolean",
                "is_secret": False,
                "section": "Retrieval",
                "description": "Enable BM25 retrieval",
                "is_read_only": False
            },
            {
                "key": "MULTI_QUERY_RETRIEVAL",
                "value": MULTI_QUERY_RETRIEVAL,
                "default_value": "True",
                "data_type": "boolean",
                "is_secret": False,
                "section": "Retrieval",
                "description": "Enable multi-query retrieval",
                "is_read_only": False
            },
            {
                "key": "PARENT_DOCUMENT_RETRIEVAL",
                "value": PARENT_DOCUMENT_RETRIEVAL,
                "default_value": "True",
                "data_type": "boolean",
                "is_secret": False,
                "section": "Retrieval",
                "description": "Enable parent document retrieval",
                "is_read_only": False
            },
            {
                "key": "MAX_SEARCH_RESULTS",
                "value": MAX_SEARCH_RESULTS,
                "default_value": MAX_SEARCH_RESULTS,
                "data_type": "integer",
                "is_secret": False,
                "section": "Retrieval",
                "description": "Maximum search results to return",
                "is_read_only": False
            },

            # Logging Settings
            {
                "key": "LOG_LEVEL",
                "value": LOG_LEVEL,
                "default_value": LOG_LEVEL,
                "data_type": "string",
                "is_secret": False,
                "section": "Logging",
                "description": "Logging level",
                "is_read_only": False
            },
            {
                "key": "LOGGER_NAME",
                "value": LOGGER_NAME,
                "default_value": LOGGER_NAME,
                "data_type": "string",
                "is_secret": False,
                "section": "Logging",
                "description": "Logger name prefix",
                "is_read_only": False
            },

            # Read-Only System Settings
            {
                "key": "METADATA_CSV_FILE",
                "value": METADATA_CSV_FILE,
                "default_value": METADATA_CSV_FILE,
                "data_type": "string",
                "is_secret": False,
                "section": "System",
                "description": "Metadata CSV filename",
                "is_read_only": True
            },
            {
                "key": "DEFAULT_INDEXED_TIMESTAMP",
                "value": DEFAULT_INDEXED_TIMESTAMP,
                "default_value": DEFAULT_INDEXED_TIMESTAMP,
                "data_type": "float",
                "is_secret": False,
                "section": "System",
                "description": "Default timestamp for indexed documents",
                "is_read_only": True
            },
        ]
    
    def initialize_database(self) -> Tuple[int, int]:
        """
        Initialize the settings database with current configuration.
        
        Returns:
            Tuple of (created_count, skipped_count)
        """
        # Initialize the database
        init_settings_db()
        
        settings_mapping = self.get_config_settings_mapping()
        created_count = 0
        skipped_count = 0
        
        for setting_config in settings_mapping:
            created = self.settings_service.create_setting(**setting_config)
            if created:
                created_count += 1
            else:
                skipped_count += 1
        
        logger.info(f"Settings initialization complete: {created_count} created, {skipped_count} skipped")
        return created_count, skipped_count
    
    def ensure_settings_initialized(self) -> bool:
        """
        Ensure settings are initialized, creating them if needed.
        
        Returns:
            True if settings were already initialized or successfully created
        """
        try:
            # Check if any settings exist
            settings = self.settings_service.get_all_settings()
            if settings:
                logger.info("Settings already initialized")
                return True
            
            # Initialize settings
            created_count, skipped_count = self.initialize_database()
            return created_count > 0 or skipped_count > 0
            
        except Exception as e:
            logger.error(f"Error ensuring settings initialized: {e}")
            return False


# Create a global instance
settings_initializer = SettingsInitializer()