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
    data_dir: Optional[str] = None
    data_dir_pattern: Optional[str] = "*.md"
    web_urls: Optional[List[str]] = None
    base_url: Optional[str] = None
    blog_base_url: Optional[str] = None
    index_only_published_posts: Optional[bool] = True
    use_chunking: Optional[bool] = True
    chunking_strategy: Optional[ChunkingStrategy] = ChunkingStrategy.TEXT_SPLITTER
    adaptive_chunking: Optional[bool] = True
    chunk_size: Optional[int] = 1000
    chunk_overlap: Optional[int] = 200
    semantic_breakpoint_type: Optional[SemanticChunkerBreakpointType] = SemanticChunkerBreakpointType.PERCENTILE
    semantic_breakpoint_threshold_amount: Optional[float] = 95.0
    semantic_min_chunk_size: Optional[int] = 100
    collection_name: Optional[str] = None
    embedding_model: Optional[str] = None
    force_recreate: Optional[bool] = False
    incremental_mode: Optional[str] = "auto"
    checksum_algorithm: Optional[str] = "sha256"
    auto_detect_changes: Optional[bool] = True
    incremental_fallback_threshold: Optional[float] = None
    enable_batch_processing: Optional[bool] = None
    batch_size: Optional[int] = None
    enbable_performance_monitoring: Optional[bool] = None
    batch_pause_seconds: Optional[float] = None
    max_concurrent_operations: Optional[int] = None
    max_backup_files: Optional[int] = None
    metadata_csv: Optional[str] = None
    blog_stats_filename: Optional[str] = None
    blog_docs_filename: Optional[str] = None
    health_report_filename: Optional[str] = None
    ci_summary_filename: Optional[str] = None
    build_info_filename: Optional[str] = None
    job_id: Optional[str] = None


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
            data['timestamp'] = datetime.now()
        super().__init__(**data)
