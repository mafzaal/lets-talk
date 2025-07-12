"""Common API models shared across endpoints."""
from typing import Dict, Any, Optional, List
from pydantic import BaseModel
from datetime import datetime
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


class JobResponse(BaseModel):
    """Response model for job information."""
    id: str
    name: str
    next_run_time: Optional[str]
    trigger: str


class BaseResponse(BaseModel):
    """Base response model with common fields."""
    message: str
    timestamp: Optional[datetime] = None
    
    def __init__(self, **data):
        if 'timestamp' not in data:
            data['timestamp'] = datetime.now()
        super().__init__(**data)
