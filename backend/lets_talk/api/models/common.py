"""Common API models shared across endpoints."""
from typing import Dict, Any, Optional, List
from pydantic import BaseModel
from datetime import datetime, timezone
from enum import Enum


class ChunkingStrategy(str, Enum):
    """Enumeration for document chunking strategies."""
    SEMANTIC = "semantic"
    TEXT_SPLITTER = "text_splitter"

class SemanticChunkerBreakpointType(str, Enum):
    """Enumeration for SemanticChunker breakpoint threshold types."""
    PERCENTILE = "percentile"
    STANDARD_DEVIATION = "standard_deviation"
    INTERQUARTILE = "interquartile"
    GRADIENT = "gradient"

class SemanticChunkerBreakpointType(str, Enum):
    """Enumeration for SemanticChunker breakpoint threshold types."""
    PERCENTILE = "percentile"
    STANDARD_DEVIATION = "standard_deviation"
    INTERQUARTILE = "interquartile"
    GRADIENT = "gradient"


class JobConfig(BaseModel):
    """Configuration for pipeline jobs."""
    data_dir: str
    data_dir_pattern: str
    web_urls: List[str]
    base_url: str
    blog_base_url: str
    index_only_published_posts: bool
    use_chunking: bool
    chunking_strategy: ChunkingStrategy
    adaptive_chunking: bool
    chunk_size: int
    chunk_overlap: int
    semantic_breakpoint_type: SemanticChunkerBreakpointType
    semantic_breakpoint_threshold_amount: float
    semantic_min_chunk_size: int
    collection_name: str
    embedding_model: str
    force_recreate: bool
    incremental_mode: str
    checksum_algorithm: str
    auto_detect_changes: bool
    incremental_fallback_threshold: float
    enable_batch_processing: bool
    batch_size: int
    enbable_performance_monitoring: bool  # Note: Typo 'enbable' preserved as specified
    batch_pause_seconds: float
    max_concurrent_operations: int
    max_backup_files: int
    metadata_csv: str
    blog_stats_filename: str
    blog_docs_filename: str
    health_report_filename: str
    ci_summary_filename: str
    build_info_filename: str
    job_id: Optional[str] = None

    @classmethod
    def with_defaults(cls) -> "JobConfig":
        """Create a JobConfig with default values from the configuration."""
        from lets_talk.shared.config import (
            DATA_DIR, DATA_DIR_PATTERN, WEB_URLS, BASE_URL, BLOG_BASE_URL,
            INDEX_ONLY_PUBLISHED_POSTS, USE_CHUNKING, CHUNKING_STRATEGY,
            ADAPTIVE_CHUNKING, CHUNK_SIZE, CHUNK_OVERLAP, 
            SEMANTIC_CHUNKER_BREAKPOINT_TYPE, SEMANTIC_CHUNKER_BREAKPOINT_THRESHOLD_AMOUNT,
            SEMANTIC_CHUNKER_MIN_CHUNK_SIZE, QDRANT_COLLECTION, EMBEDDING_MODEL,
            FORCE_RECREATE, INCREMENTAL_MODE, CHECKSUM_ALGORITHM, AUTO_DETECT_CHANGES,
            INCREMENTAL_FALLBACK_THRESHOLD, ENABLE_BATCH_PROCESSING, BATCH_SIZE,
            ENABLE_PERFORMANCE_MONITORING, BATCH_PAUSE_SECONDS, MAX_CONCURRENT_OPERATIONS,
            MAX_BACKUP_FILES, METADATA_CSV_FILE, BLOG_STATS_FILENAME, BLOG_DOCS_FILENAME,
            HEALTH_REPORT_FILENAME, CI_SUMMARY_FILENAME, BUILD_INFO_FILENAME
        )
        
        return cls(
            data_dir=DATA_DIR,
            data_dir_pattern=DATA_DIR_PATTERN,
            web_urls=WEB_URLS,
            base_url=BASE_URL,
            blog_base_url=BLOG_BASE_URL,
            index_only_published_posts=INDEX_ONLY_PUBLISHED_POSTS,
            use_chunking=USE_CHUNKING,
            chunking_strategy=CHUNKING_STRATEGY,
            adaptive_chunking=ADAPTIVE_CHUNKING,
            chunk_size=CHUNK_SIZE,
            chunk_overlap=CHUNK_OVERLAP,
            semantic_breakpoint_type=SEMANTIC_CHUNKER_BREAKPOINT_TYPE,
            semantic_breakpoint_threshold_amount=SEMANTIC_CHUNKER_BREAKPOINT_THRESHOLD_AMOUNT,
            semantic_min_chunk_size=SEMANTIC_CHUNKER_MIN_CHUNK_SIZE,
            collection_name=QDRANT_COLLECTION,
            embedding_model=EMBEDDING_MODEL,
            force_recreate=FORCE_RECREATE,
            incremental_mode=INCREMENTAL_MODE,
            checksum_algorithm=CHECKSUM_ALGORITHM,
            auto_detect_changes=AUTO_DETECT_CHANGES,
            incremental_fallback_threshold=INCREMENTAL_FALLBACK_THRESHOLD,
            enable_batch_processing=ENABLE_BATCH_PROCESSING,
            batch_size=BATCH_SIZE,
            enbable_performance_monitoring=ENABLE_PERFORMANCE_MONITORING,
            batch_pause_seconds=BATCH_PAUSE_SECONDS,
            max_concurrent_operations=MAX_CONCURRENT_OPERATIONS,
            max_backup_files=MAX_BACKUP_FILES,
            metadata_csv=METADATA_CSV_FILE,
            blog_stats_filename=BLOG_STATS_FILENAME,
            blog_docs_filename=BLOG_DOCS_FILENAME,
            health_report_filename=HEALTH_REPORT_FILENAME,
            ci_summary_filename=CI_SUMMARY_FILENAME,
            build_info_filename=BUILD_INFO_FILENAME,
        )



class JobResponse(BaseModel):
    """Response model for job information."""
    id: str
    name: str
    next_run_time: Optional[str]
    trigger: str
    config: Dict[str, Any] = {}


class BaseResponse(BaseModel):
    """Base response model with common fields."""
    message: str
    timestamp: Optional[datetime] = None
    
    def __init__(self, **data):
        if 'timestamp' not in data:
            data['timestamp'] = datetime.now(timezone.utc)
        super().__init__(**data)
